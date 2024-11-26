.. _sensor:

Sensors
=======

Sensors in Dr.TVAM are used to define the region where the absorption
measurements are taken. The sensor is a 3D grid centered at the origin,
originally spanning from -0.5 to 0.5 in each dimension. Each sensor takes an
optional rigid transform matrix to place and scele it where the user wants. 

There are three types of sensors available in Dr.TVAM, which only differ in the
way that absorption measurements are implemented, for a given ray that traverses
the grid. We describe each below. 

Sensors are implemented as Mitsuba plugins, therefore their definition follows
Mitsuba's plugin syntax. A sensor can be described as follows:

.. code-block:: python

    sensor_dict = {
        'type': 'dda',
        'to_world': mi.ScalarTransform4f().scale(2.),
        'film': {
            'type': 'vfilm',
            'resx': 256,
            'resy': 256,
            'resz': 256,
        },
    }

The common parameters for all sensors are:

.. list-table::
    :widths: 10 10 80
    :header-rows: 1

    * - Key
      - Type
      - Description

    * - ``type``
      - ``str``
      - The specific type of sensor to use. Can be ``dda``, ``ratio`` or
        ``delta``.

    * - ``to_world``
      - ``mitsuba.ScalarTransform4f``
      - A rigid transform matrix to place and scale the sensor in the scene.
        Default is the identity matrix.

    * - ``film``
      - ``dict``
      - A nested dictionary with the parameters of the film. We describe it in
        more detail below.

.. _film:

Film
----

The film describes how the sensor is discretized in space. There is only one
type of film compatible with our system, the ``vfilm``. The film dictionary
should contain the resolution of the film along each dimension, as well as the
choice of discretization.

The choice of discretization is only relevant for optimization. When optimizing
patterns for a given target shape, we provide two options regarding how the
target shape should be discretized:

* Binary discretization: this is the default option, and what other TVAM
  pipelines do. The target shape is simply discretized as a binary mask, where
  each voxel is either inside or outside the shape. This is the fastest option,
  but can lead to artifacts when the film resolution is too low.
* Surface-aware discretization: this option keeps the surface in the scene, and
  renders a 2-channel tensor, where each voxel now records absorbed energy
  inside *and* outside the shape separately. This allows to keep information
  about the surface, and can improve result accuracy.

The film dictionary should contain the following entries:

.. list-table::
    :widths: 10 10 80
    :header-rows: 1

    * - Key
      - Type
      - Description

    * - ``surface_aware``
      - ``bool``
      - Whether to use surface-aware discretization. Default is ``False``, i.e.
        binary discretization.

    * - ``resx``
      - ``int``
      - Film resolution along the x-axis.

    * - ``resy``
      - ``int``
      - Film resolution along the y-axis.

    * - ``resz``
      - ``int``
      - Film resolution along the z-axis.


DDA Sensor (``dda``)
--------------------

This sensor uses a *differential delta analyzer* (DDA) to traverse the grid and
compute the analytical value of the absorption along the ray for each voxel
along the way. This sensor is the most accurate, but also the slowest. We
recommend using it for the highest quality results.

It requires no additional parameters.


Ratio Sensor (``ratio``)
------------------------

This sensor uses a *majorant* extinction value to sample interaction points
along the ray. The absorption is then computed at each interaction point as the
ratio of absorption to extinction. This allows for a faster traversal of the
grid per ray, at the cost of accuracy. By varying the majorant value, the user
can control the trade-off between speed and accuracy.

It requires one additional parameter:

.. list-table::
    :widths: 10 10 80
    :header-rows: 1

    * - Key
      - Type
      - Description

    * - ``majorant``
      - ``float``
      - The extinction value used to sample interaction points along the ray. It
        should be set to a value higher than the extinction coefficient of the
        printing medium.

Delta Sensor (``delta``)
------------------------

This sensor only records absorption when there is a scattering event. As a
consequence it is not usable for purely absorptive media. It produces extremely
noisy results, and is only recommended for debugging purposes.

