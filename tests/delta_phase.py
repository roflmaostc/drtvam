import mitsuba as mi
import drjit as dr

class DeltaPhase(mi.PhaseFunction):
    def __init__(self, props):
        mi.PhaseFunction.__init__(self, props)

    def sample(self, ctx, mei, sample1, sample2, active):
        return -mei.wi, 1., 1.

    def eval_pdf(self, ctx, mei, wo, active):
        return 1., 1.

mi.register_phasefunction("deltaphase", lambda props: DeltaPhase(props))
