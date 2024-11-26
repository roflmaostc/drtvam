import mitsuba as mi
import drjit as dr

def relu(x):
    return dr.select(x > 0, x, 0)

class Loss:
    def __init__(self, props):
        reduction = props.get('reduction', 'sum')
        if reduction == 'sum':
            self.reduction = dr.sum
        elif reduction == 'mean':
            self.reduction = dr.mean
        else:
            raise ValueError(f"Invalid reduction method: '{reduction}'.")

    def eval_in(self, x):
        raise NotImplementedError

    def eval_out(self, x):
        raise NotImplementedError

    def eval(self, x, target):
        raise NotImplementedError

    def __call__(self, x, target):
        if x.shape != target.shape:
            if len(x.shape) == len(target.shape) + 1 and x.shape[-1] == 1:
                # we expect the last dimension to have 1 or 2 channels
                target = target[..., None]
            else:
                raise ValueError(f"Input and target shapes do not match: {x.shape} != {target.shape}")

        if target.shape[-1] == 1: # binary or grayscale target
            loss = self.eval(x, target)
        elif target.shape[-1] == 2: # Surface-aware discretization
            # Here, the target defines the fractional inside/outside volumes of individual voxels.
            w_in = target[..., 0] / (target[..., 0] + target[..., 1])
            w_out = target[..., 1] / (target[..., 0] + target[..., 1])

            loss = w_in * self.eval_in(x[..., 0]) + w_out * self.eval_out(x[..., 1])
        else:
            raise ValueError(f"[Loss] Received tensors of invalid shape: {target.shape}. The last dimension should be either 1 or 2.")

        return self.reduction(loss, axis=None)

#TODO: implement L1 in an example in the documentation
class L2Loss(Loss):
    def eval_in(self, x):
        return dr.square(x - 1.)

    def eval_out(self, x):
        return dr.square(x)

    def eval(self, x, target):
        return dr.square(x - target)

class ThresholdedLoss(Loss):
    """
    Thresholded loss following Wechsler et al 2024.

    """
    def __init__(self, props):
        super().__init__(props)
        self.K = props.get('K', 2)
        self.tl = props.get('tl', 0.9)
        self.tu = props.get('tu', 0.95)

        if self.tl >= self.tu:
            raise ValueError(f"[ThresholdedLoss] Lower threshold ({self.tl}) must be smaller than upper threshold ({self.tu})")

    def eval_in(self, x):
        return relu(self.tu - x)**self.K + relu(x - 1.)**self.K

    def eval_out(self, x):
        return relu(x - self.tl)**self.K

    def eval(self, x, target):
        # target should be a binary inside/outside mask
        return dr.select(target > 0, self.eval_in(x), self.eval_out(x))

losses = {
    'l2': L2Loss,
    'threshold': ThresholdedLoss,
}

