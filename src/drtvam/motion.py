import mitsuba as mi
import drjit as dr

class Motion:
    """
    This class represents a motion model for a projector.
    For a given normalized time t in [0, 1], it returns
    the corresponding transformation matrix of the projector.
    """
    def __init__(self, props):
        raise NotImplementedError

    def eval(self, time):
        """
        Evaluate the motion model at time t.
        """
        raise NotImplementedError

class CircularMotion(Motion):
    def __init__(self, props):
        self.distance = props['distance']
        self.tilt = props.get('tilt', 0.) #TODO: different motion for tilt ?
        self.clockwise = props.get('clockwise', False)
        #TODO: rotation axis

    def eval(self, time):
        # Angle from the center to the emitter
        alpha = 2 * dr.pi * time
        if self.clockwise:
            alpha *= -1

        #TODO: add a rotation axis
        origin = self.distance * mi.Point3f(dr.cos(alpha), dr.sin(alpha), 0.)
        target = mi.Point3f(0)
        up = mi.Point3f(0, 0, 1)
        return mi.Transform4f().look_at(origin=origin, target=target, up=up)

# List of registered motions
motions = {
    'circular': CircularMotion,
}


