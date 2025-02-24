from __future__ import annotations as __annotations__ # Delayed parsing of type annotations
import mitsuba as mi
import drjit as dr
from drtvam.projector import TVAMProjector
from .common import TVAMIntegrator

class CornerIntegrator(TVAMIntegrator):
    def __init__(self, props):
        super().__init__(props)

        self.dist = props['dist']
        self.radius = props.get('radius', 0.1)

    def to_string(self):
        return 'CornerIntegrator'

    def render(self: mi.SamplingIntegrator,
               scene: mi.Scene,
               sensor: Union[int, mi.Sensor] = 0,
               seed: int = 0,
               spp: int = 0,
               develop: bool = True,
               evaluate: bool = True) -> mi.TensorXf:

        if len(scene.emitters()) == 0:
            raise Exception("No projector found in the scene")
        if len(scene.emitters()) > 1:
            raise Exception("The scene contains more than one projector. Only one is supported")

        projector = scene.emitters()[0]

        with dr.suspend_grad():
            sampler, spp = self.prepare(projector, seed, spp)
            ray, _, weight = self.sample_rays(scene, projector, sampler)

            L = self.sample(
                mode=dr.ADMode.Primal,
                scene=scene,
                sampler=sampler,
                ray=ray,
                depth=mi.UInt32(0),
                active=mi.Bool(True)
            ) * weight

            imgs = dr.zeros(mi.TensorXf, projector.size())
            idx = dr.repeat(projector.active_pixels, spp)
            dr.scatter_reduce(dr.ReduceOp.Add, imgs.array, L, idx)

        return imgs

    @dr.syntax
    def sample(self,
               mode: dr.ADMode,
               scene: mi.Scene,
               sampler: mi.Sampler,
               ray: mi.Ray3f,
               depth: mi.UInt32,
               active: mi.Bool) -> Tuple[mi.Spectrum, mi.Bool, List[mi.Float]]:

        si = scene.ray_intersect(ray)
        active = si.is_valid()

        hit_corner = dr.norm(dr.abs(si.p.xy) - self.dist) < self.radius
        active &= ~hit_corner

        return dr.select(active, 1., 0.)

mi.register_integrator("corner", CornerIntegrator)
