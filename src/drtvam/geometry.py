import mitsuba as mi
import drjit as dr

class Container:
    """
    Base class for the printing medium container.

    The base class defines the properties of the medium:
        - IOR
        - Extinction coefficient
        - Scattering albedo
        - phase function
    IOR and phase functions are intrinsic properties of a given printing medium, while
    extinction and scattering albedo are properties that can vary between experiments.
    Therefore, IOR and phase functions are stored in a list of known media, and the queried
    from a key in the input parameters.

    Also top and bottom occlusions can be added to the container. These are .ply files
    """
    def __init__(self, params):
        self.params = params
        medium = params['medium'] if 'medium' in params else None
        if medium is not None:
            self.medium_ior = medium['ior']
            self.sigma_t = medium['extinction']
            self.albedo = medium['albedo'] # Purely absorptive by default
        # add some occlusions
        self.top_occlusion = params.get('top_occlusion')
        self.bottom_occlusion = params.get('bottom_occlusion')

        if medium is not None:
            if 'phase' in medium.keys():
                self.medium_phase = medium['phase']
            elif self.albedo > 0.:
                raise ValueError(f"[{self.__class__.__name__}] Tried to load a scattering medium without specifying a phase function.")
            else:
                self.medium_phase = None

    def medium_dict(self):
        medium_dict = {
            'type': 'homogeneous',
            'sigma_t': self.sigma_t,
            'albedo': self.albedo,
            }
        if self.medium_phase is not None:
            medium_dict['phase'] = self.medium_phase
        return medium_dict

    def to_dict(self):
        raise NotImplementedError

    # add occulsions to the container such as a bottom and top cap or some
    # inlets to print around
    # the loaded .ply files should be exported as .ply with the
    # relative position to the container. (0,0,0) is the center of the container
    def add_occlusions(self, dd):
        if self.bottom_occlusion is not None:
            dd['insert_bottom'] = {
                'type': 'ply',
                'filename': self.bottom_occlusion,
                'bsdf': {
                    'type': 'diffuse',
                    'reflectance': {
                        'type': 'spectrum',
                        'value': 0.5 # All black
                    }
                }
            }
        if self.top_occlusion is not None:
            dd['insert_top'] = {
                    'type': 'ply',
                    'filename': self.top_occlusion,
                    'bsdf': {
                        'type': 'diffuse',
                        'reflectance': {
                            'type': 'spectrum',
                            'value': 0.5 # All black
                        }
                    }
                }

        return dd


class IndexMatchedVial(Container):
    def __init__(self, params):
        super().__init__(params)

        self.r = params['r']
        self.height = params.get('height', 20.)

    def to_dict(self):
        d = {
            'vial_exterior': {
                'type': 'cylinder',
                'p0': [0., 0., -0.5 * self.height],
                'p1': [0., 0.,  0.5 * self.height],
                'radius': self.r,
                'bsdf': {'type': 'null'},
                #TODO: do this differently for custom geometries with more than one interface with the medium
                'interior': self.medium_dict(),
            }
        }
        d = self.add_occlusions(d)
        return dline


class CylindricalVial(Container):
    def __init__(self, params):
        super().__init__(params)

        self.r_int = params['r_int']
        self.r_ext = params['r_ext']
        self.height = params.get('height', 20.)
        self.vial_ior = params['ior']

    def to_dict(self):
        #TODO: add endcaps
        d = {
            'vial_exterior' : {
                'type': 'cylinder',
                'p0': [0., 0., -0.5 * self.height],
                'p1': [0., 0.,  0.5 * self.height],
                'radius': self.r_ext,
                'bsdf': {
                    'type': 'dielectric',
                    'int_ior': self.vial_ior,
                },
            },
            'vial_interior': {
                'type': 'cylinder',
                'p0': [0., 0., -0.5 * self.height],
                'p1': [0., 0.,  0.5 * self.height],
                'radius': self.r_int,
                'bsdf': {
                    'type': 'dielectric',
                    'ext_ior': self.vial_ior,
                    'int_ior': self.medium_ior,
                },
                #TODO: do this differently for custom geometries with more than one interface with the medium
                'interior': self.medium_dict(),
            }
        }

        d = self.add_occlusions(d)
        return d

class DoubleCylindricalVial(Container):
    def __init__(self, params):
        super().__init__(params)

        # inner radius of inner cylinder
        self.r_1 = params['r_1']
        # outer radius of inner cylinder
        self.r_2 = params['r_2']
        # inner radius of outer cylinder
        self.r_3 = params['r_3']
        # outer radius of outer cylinder
        self.r_4 = params['r_4']
        self.height = params.get('height', 40.)
        # refractive index of inner cylinder material
        self.vial_ior_12 = params['ior_12']
        # refractive index of outer cylinder material
        self.vial_ior_34 = params['ior_34']

        # medium inside the inner cylinder
        medium_1 = params['medium_1']
        self.medium_ior_1 = medium_1['ior']
        self.sigma_t_1 = medium_1['extinction']
        self.albedo_1 = medium_1['albedo'] # Purely absorptive by default
        if 'phase' in medium_1.keys():
            self.medium_phase_1 = medium_1['phase']
        elif self.albedo_1 > 0.:
            raise ValueError(f"[{self.__class__.__name__}] Tried to load a scattering medium without specifying a phase function.")
        else:
            self.medium_phase_1 = None

        # medium between the outer cylinder and the inner cylinder
        medium_2 = params['medium_2']
        self.medium_ior_2 = medium_2['ior']
        self.sigma_t_2 = medium_2['extinction']
        self.albedo_2 = medium_2['albedo'] # Purely absorptive by default
        if 'phase' in medium_2.keys():
            self.medium_phase_2 = medium_2['phase']
        elif self.albedo_2 > 0.:
            raise ValueError(f"[{self.__class__.__name__}] Tried to load a scattering medium without specifying a phase function.")
        else:
            self.medium_phase_2 = None



    def medium_dict_1(self):
        medium_dict_1 = {
            'type': 'homogeneous',
            'sigma_t': self.sigma_t_1,
            'albedo': self.albedo_1,
            }
        if self.medium_phase_1 is not None:
            medium_dict_1['phase'] = self.medium_phase_1
        return medium_dict_1

    def medium_dict_2(self):
        medium_dict_2 = {
            'type': 'homogeneous',
            'sigma_t': self.sigma_t_2,
            'albedo': self.albedo_2,
            }
        if self.medium_phase_2 is not None:
            medium_dict_2['phase'] = self.medium_phase_2
        return medium_dict_2


    def to_dict(self):
        #TODO: add endcaps
        d = {
            'outer_vial' : {
                'type': 'cylinder',
                'p0': [0., 0., -0.5 * self.height],
                'p1': [0., 0.,  0.5 * self.height],
                'radius': self.r_4,
                'bsdf': {
                    'type': 'dielectric',
                    'int_ior': self.vial_ior_34,
                },
            },
            'outer_vial_interior': {
                'type': 'cylinder',
                'p0': [0., 0., -0.5 * self.height],
                'p1': [0., 0.,  0.5 * self.height],
                'radius': self.r_3,
                'bsdf': {
                    'type': 'dielectric',
                    'ext_ior': self.vial_ior_34,
                    'int_ior': self.medium_ior_2,
                },
                'interior': self.medium_dict_2(),
            },
            'inner_vial' : {
                'type': 'cylinder',
                'p0': [0., 0., -0.5 * self.height],
                'p1': [0., 0.,  0.5 * self.height],
                'radius': self.r_2,
                'bsdf': {
                    'type': 'dielectric',
                    'int_ior': self.vial_ior_12,
                },
            },
            'inner_vial_interior': {
                'type': 'cylinder',
                'p0': [0., 0., -0.5 * self.height],
                'p1': [0., 0.,  0.5 * self.height],
                'radius': self.r_1,
                'bsdf': {
                    'type': 'dielectric',
                    'ext_ior': self.vial_ior_12,
                    'int_ior': self.medium_ior_1,
                },
                'interior_inside': self.medium_dict_1(),
            }
        }
        d = self.add_occlusions(d)
        return d


class CylindricalVial(Container):
    def __init__(self, params):
        super().__init__(params)

        self.r_int = params['r_int']
        self.r_ext = params['r_ext']
        self.height = params.get('height', 20.)
        self.vial_ior = params['ior']

    def to_dict(self):
        #TODO: add endcaps
        d = {
            'vial_exterior' : {
                'type': 'cylinder',
                'p0': [0., 0., -0.5 * self.height],
                'p1': [0., 0.,  0.5 * self.height],
                'radius': self.r_ext,
                'bsdf': {
                    'type': 'dielectric',
                    'int_ior': self.vial_ior,
                },
            },
            'vial_interior': {
                'type': 'cylinder',
                'p0': [0., 0., -0.5 * self.height],
                'p1': [0., 0.,  0.5 * self.height],
                'radius': self.r_int,
                'bsdf': {
                    'type': 'dielectric',
                    'ext_ior': self.vial_ior,
                    'int_ior': self.medium_ior,
                },
                #TODO: do this differently for custom geometries with more than one interface with the medium
                'interior': self.medium_dict(),
            }
        }

        d = self.add_occlusions(d)
        return d



class SquareVial(Container):
    def __init__(self, params):
        super().__init__(params)

        self.w_int = params['w_int']
        self.w_ext = params['w_ext']
        self.height = params.get('height', 20.)
        self.vial_ior = params['ior']

    def to_dict(self):
        d = {
            'vial_exterior' : {
                'type': 'cube',
                'to_world': mi.ScalarTransform4f().scale((0.5*self.w_ext, 0.5*self.w_ext, 0.5*self.height)),
                'bsdf': {
                    'type': 'dielectric',
                    'int_ior': self.vial_ior,
                },
            },
            'vial_interior': {
                'type': 'cube',
                'to_world': mi.ScalarTransform4f().scale((0.5*self.w_int, 0.5*self.w_int, 0.5*0.9*self.height)),
                'bsdf': {
                    'type': 'dielectric',
                    'ext_ior': self.vial_ior,
                    'int_ior': self.medium_ior,
                },
                #TODO: do this differently for custom geometries with more than one interface with the medium
                'interior': self.medium_dict(),
            }
        }
        d = self.add_occlusions(d)
        return d

# List of registered geometries
geometries = {
    'index_matched': IndexMatchedVial,
    'cylindrical': CylindricalVial,
    'square': SquareVial,
    'double_cylindrical': DoubleCylindricalVial
}

