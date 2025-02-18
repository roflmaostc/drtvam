import mitsuba as mi
import drjit as dr
from collections import defaultdict

class LBFGS(mi.ad.Optimizer):
    def __init__(self, lr=1.0, m=5, params=None, line_search_fn=None, wolfe=False, search_it=20):
        super().__init__(lr, params)
        # Use Wolfe conditions, otherwise only use Armijo condition
        self.wolfe = wolfe
        # History size
        self.m = m
        # Previous state
        self.p_old = {}
        # Previous gradient
        self.g_old = {}
        # List of state differences
        self.s = {}
        # List of gradient differences
        self.y = {}
        # List of dot products of 'y' and 's'
        self.ys = {}
        # Iteration count
        self.t = {}
        # Function used for line search, should take a dictionary of variables
        # as input and return the loss and gradients for each variable
        self.line_search_fn = line_search_fn
        # How many iterations of backtracking line search to run
        self.search_it = search_it

    def reset(self, k):
        self.s[k] = []
        self.y[k] = []
        self.ys[k] = []
        self.t[k] = 0

    def update_history(self, k):
        # Discard too old entries
        if self.t[k] > self.m:
            self.s[k].pop(0)
            self.y[k].pop(0)
            self.ys[k].pop(0)

        p = dr.ravel(dr.detach(self.variables[k]))
        g_p = dr.ravel(self.variables[k].grad)
        dr.schedule(p, g_p)
        # Update history
        if self.t[k] > 0:
            self.s[k].append(p - self.p_old[k])
            self.y[k].append(g_p - self.g_old[k])
            dr.schedule(self.s[k][-1], self.y[k][-1])
            self.ys[k].append(dr.dot(self.y[k][-1], self.s[k][-1]))

        # Update previous state and gradient
        self.p_old[k] = p
        self.g_old[k] = g_p
        self.t[k] += 1

    def step(self, f):
        search_dirs = {}
        # TODO: unravel arrays for dot products

        # Compute search directions
        for k, p in self.variables.items():
            #TODO: Stopping criterion ?
            # TODO: reset if shape changed
            if k not in self.s:
                self.reset(k)

            # Update history
            self.update_history(k)

            # Find search direction
            q = dr.ravel(p.grad)
            hist_size = len(self.s[k])
            dr.make_opaque(hist_size)
            s = self.s[k]
            y = self.y[k]
            ys = self.ys[k]
            alphas = []
            for i in range(hist_size-1, -1, -1):
                rho = dr.rcp(ys[i])
                a = rho * dr.dot(s[i], q)
                q = q - a * y[i]
                alphas.insert(0, a)

            gamma = 1 if self.t[k] == 1 else ys[-1] / dr.dot(y[-1], y[-1])

            z = gamma * q
            for i in range(hist_size):
                rho = dr.rcp(ys[i])
                b = rho * dr.dot(y[i], z)
                z = z + (alphas[i] - b) * s[i]

            search_dirs[k] = -z

        # Backtracking line search until Wolfe conditions are satisfied /!\ The
        # final step size is the same for all variables, not sure if this is the
        # proper way to do it
        alpha = dr.opaque(mi.Float, 1.) # TODO: expose initial step size as param
        c1 = 1e-4
        c2 = 0.9
        for it in range(self.search_it):
            params = {}
            for k, p in self.variables.items():
                if type(p) == mi.TensorXf:
                    params[k] = dr.detach(p + alpha * type(p)(search_dirs[k], shape=p.shape))
                else:
                    params[k] = dr.detach(p + alpha * dr.unravel(type(p), search_dirs[k]))

                if self.wolfe:
                    dr.enable_grad(params[k])

                dr.schedule(params[k])

            f_new = self.line_search_fn(params)
            if self.wolfe:
                dr.backward(f_new)

            g_dot_z = mi.Float(0.)
            g_new_dot_z = mi.Float(0.)
            for k, p in params.items():
                g_dot_z += dr.dot(self.g_old[k], search_dirs[k])
                if self.wolfe:
                    g_new_dot_z += dr.dot(dr.ravel(p.grad), search_dirs[k])

            wolfe1 = (f_new <= f + c1 * alpha * g_dot_z)
            if not self.wolfe:
                if dr.all(wolfe1):
                    break
            else:
                wolfe2 = (g_new_dot_z >= c2 * g_dot_z)
                if dr.all(wolfe1 & wolfe2):
                    break

            alpha *= 0.5

        for k, p in self.variables.items():
            if type(p) == mi.TensorXf:
                self.variables[k] = dr.detach(p + alpha * type(p)(search_dirs[k], shape=p.shape))
            else:
                self.variables[k] = dr.detach(p + alpha * dr.unravel(type(p), search_dirs[k]))
            # self.variables[k] = type(p)(dr.detach(p + alpha * dr.unravel(type(p), search_dirs[k])))
            dr.enable_grad(self.variables[k])
            dr.schedule(self.variables[k])

class LinearLBFGS(mi.ad.Optimizer):
    def __init__(self, lr=1.0, m=5, params=None, render_fn=None, loss_fn=None, search_it=20):
        super().__init__(lr, params)
        # History size
        self.m = m
        # Previous state
        self.p_old = {}
        # Previous gradient
        self.g_old = {}
        # List of state differences
        self.s = {}
        # List of gradient differences
        self.y = {}
        # List of dot products of 'y' and 's'
        self.ys = {}
        # Iteration count
        self.t = {}
        # Function used for line search, should take a dictionary of variables
        # as input and return the loss and gradients for each variable
        self.render_fn = render_fn
        self.loss_fn = loss_fn
        # How many iterations of backtracking line search to run
        self.search_it = search_it

    def reset(self, k):
        self.s[k] = []
        self.y[k] = []
        self.ys[k] = []
        self.t[k] = 0

    def update_history(self, k):
        # Discard too old entries
        if self.t[k] > self.m:
            self.s[k].pop(0)
            self.y[k].pop(0)
            self.ys[k].pop(0)

        p = dr.ravel(dr.detach(self.variables[k]))
        g_p = dr.ravel(self.variables[k].grad)
        dr.schedule(p, g_p)
        # Update history
        if self.t[k] > 0:
            self.s[k].append(p - self.p_old[k])
            self.y[k].append(g_p - self.g_old[k])
            dr.schedule(self.s[k][-1], self.y[k][-1])
            self.ys[k].append(dr.dot(self.y[k][-1], self.s[k][-1]))

        # Update previous state and gradient
        self.p_old[k] = p
        self.g_old[k] = g_p
        self.t[k] += 1

    def step(self, vol, loss):
        search_dirs = {}
        # TODO: unravel arrays for dot products

        # Compute search directions
        for k, p in self.variables.items():
            #TODO: Stopping criterion ?
            # TODO: reset if shape changed
            if k not in self.s:
                self.reset(k)

            # Update history
            self.update_history(k)

            # Find search direction
            q = dr.ravel(p.grad)
            hist_size = len(self.s[k])
            dr.make_opaque(hist_size)
            s = self.s[k]
            y = self.y[k]
            ys = self.ys[k]
            alphas = []
            for i in range(hist_size-1, -1, -1):
                rho = dr.rcp(ys[i])
                a = rho * dr.dot(s[i], q)
                q = q - a * y[i]
                alphas.insert(0, a)

            gamma = 1 if self.t[k] == 1 else ys[-1] / dr.dot(y[-1], y[-1])

            z = gamma * q
            for i in range(hist_size):
                rho = dr.rcp(ys[i])
                b = rho * dr.dot(y[i], z)
                z = z + (alphas[i] - b) * s[i]

            search_dirs[k] = -z

        # Backtracking line search until Armijo conditions are satisfied
        alpha = dr.opaque(mi.Float, 1.) # TODO: expose initial step size as param
        c1 = 1e-4
        params = {}
        for k, p in self.variables.items():
            if type(p) == mi.TensorXf:
                params[k] = dr.detach(type(p)(search_dirs[k], shape=p.shape))
            else:
                params[k] = dr.detach(dr.unravel(type(p), search_dirs[k]))
            #TODO: clamping ?
            dr.schedule(params[k])

        dvol = self.render_fn(params)
        dr.eval(dvol)

        # Compute dot product of gradient and search direction for Armijo condition
        g_dot_z = mi.Float(0.)
        for k, p in params.items():
            g_dot_z += dr.dot(self.g_old[k], search_dirs[k])

        for _ in range(self.search_it):

            vol_new = vol + alpha * dvol
            mi.Log(mi.LogLevel.Debug, "[drtvam] Calling loss from LBFGS")
            f_new = self.loss_fn(vol_new, params['projector.active_data'])

            armijo = (f_new <= loss + c1 * alpha * g_dot_z)
            if dr.all(armijo):
                break

            alpha *= 0.5

        for k, p in self.variables.items():
            if type(p) == mi.TensorXf:
                self.variables[k] = dr.detach(p + alpha * type(p)(search_dirs[k], shape=p.shape))
            else:
                self.variables[k] = dr.detach(p + alpha * dr.unravel(type(p), search_dirs[k]))
            # self.variables[k] = type(p)(dr.detach(p + alpha * dr.unravel(type(p), search_dirs[k])))
            dr.enable_grad(self.variables[k])
            dr.schedule(self.variables[k])
