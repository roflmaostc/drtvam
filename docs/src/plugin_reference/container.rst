.. _vial:

Containers
==========

Containers in Dr.TVAM are a useful abstraction to define the resin and its
container. Unlike other plugins, it is only a convenience class so that users do
not need to be concerned with the nitty-gritty details of setting up surfaces
and materials in a Mitsuba 3 scene.

Containers are implemented as child classes of the base ``Container`` class, and
they implement one method ``to_dict``, which returns a Mitsuba-compatible
dictionary that can be used to define the container in a Mitsuba 3 scene.

The container class serves two purposes:

1. It defines the printing medium and its optical properties.
2. It defines the container geometry and its optical properties.

A container can be instantiated as follows:

.. code-block:: python

    vial = IndexMatchedVial({
        'r': 2.5,
        'height': 10,
        'medium': {
            'extinction': 0.1,
            'albedo': 0.9,
            'phase': {
                'type': 'hg',
                'g': 0.5
            },
            'ior': 1.5
        }
    })

We explain the parameters of the constructor in the following sections. After
instantiating the container, the Mitsuba-compatible dictionary can be obtained
by calling the ``to_dict`` method, e.g. to add it to an existing Mitsuba scene
dictionary under construction:

.. code-block:: python

    scene_dict |= vial.to_dict()


Printing medium
---------------

The printing medium is characterized by a few aspects:

* its absorbtion and scattering coefficients, which respectively quantify the
  probability of a photon being absorbed or scattered along a ray per unit
  length. These coefficients are summed to form the extinction coefficient,
  which describes the total attenuation of light along a ray in the medium. The
  ratio of scattering to extinction is called the *single-scattering albedo*.
* its phase function, which defines the probability of a photon being scattered
  in a given direction given its incoming direction.
* its refractive index, which defines the speed of light in the medium.

Defining a printing medium in Dr.TVAM is done by specifying each of these
properties in the ``medium`` dictionary of the container class. The medium
dictionary should contain the following entries:


.. list-table::
    :widths: 10 10 80
    :header-rows: 1

    * - Key
      - Type
      - Description

    * - ``extinction``
      - ``float``
      - The extinction coefficient of the medium, in (scene units)^-1.

    * - ``albedo``
      - ``float``
      - The single-scatterig albedo of the medium, in [0, 1]. A value of 0
        indicates that the medium is purely absorptive.

    * - ``phase``
      - ``dict``
      - Mitsuba-compatible dictionary defining the phase function of the medium.
        See the corresponding `section
        <https://mitsuba.readthedocs.io/en/stable/src/generated/plugins_phase.html>`_
        in the Mitsuba 3 documentation for more information.

    * - ``ior``
      - ``float``
      - The refractive index of the medium.

Container geometry
------------------

The container geometry is defined by a set of *surfaces* that enclose the resin.
Each surface is defined by a Mitsuba `shape plugin
<https://mitsuba.readthedocs.io/en/stable/src/generated/plugins_shapes.html>`_.
The ``Container`` class creates the dictionary representation of the container
by combining the surfaces and the printing medium. A few containers are
supported:

Index-matched vial (``index_matched``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This container implements an idealized version of a printing setup with a
cylindrical vial immersed in an index-matching bath. In that case, all
reflections and refractions at the interfaces are ignored, as if the vial was a
perfectly transparent cylinder. This is what this plugin implements. It takes
the following parameters:


.. list-table::
    :widths: 10 10 80
    :header-rows: 1

    * - Key
      - Type
      - Description

    * - ``r``
      - ``float``
      - The radius of the vial, in scene units.

    * - ``height``
      - ``float``
      - The height of the vial, in scene units.

    * - ``medium``
      - ``dict``
      - The medium dictionary, as described above.

Cylindrical vial (``cylindrical``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This container implements a cylindrical vial, with no index-matching bath. The
system correctly accounts for the attenuation and change of direction at the
dielectric interfaces. It takes the following parameters:


.. list-table::
    :widths: 10 10 80
    :header-rows: 1

    * - Key
      - Type
      - Description

    * - ``r_int``
      - ``float``
      - The interior radius of the vial, in scene units.

    * - ``r_ext``
      - ``float``
      - The exterior radius of the vial, in scene units.

    * - ``height``
      - ``float``
      - The height of the vial, in scene units.

    * - ``ior``
      - ``float``
      - The refractive index of the vial.

    * - ``medium``
      - ``dict``
      - The medium dictionary, as described above.

Square vial (``square``)
^^^^^^^^^^^^^^^^^^^^^^^^

This container implements a vial with a square cross-section, like a
spectroscopy cuvette. It takes the following parameters:


.. list-table::
    :widths: 10 10 80
    :header-rows: 1

    * - Key
      - Type
      - Description

    * - ``w_int``
      - ``float``
      - The interior length of one side of the vial, in scene units.

    * - ``w_ext``
      - ``float``
      - The exterior length of one side of the vial, in scene units.

    * - ``height``
      - ``float``
      - The height of the vial, in scene units.

    * - ``ior``
      - ``float``
      - The refractive index of the vial.

    * - ``medium``
      - ``dict``
      - The medium dictionary, as described above.

