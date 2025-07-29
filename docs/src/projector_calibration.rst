.. _projector_calibration:

Projector Calibration
=====================
This tutorial describes how you can calibrate a ``telecentric`` and ``lens`` (perspective) projector.



Trace single projector pixels
-----------------------------
Dr.TVAM has the option to trace single rays instead of doing an optimization.
The following example shows how to trace rays for a single projector pixel.



.. raw:: html

   <details>
   <summary><a>Config file to trace single rays (click to expand)</a></summary>

.. code-block:: json

    {
        "vial": {
            "type": "cylindrical",
            "r_int": 16.363125,
            "r_ext": 17.354374999999999,
            "ior": 1.00,
            "medium": {
                "ior": 1.00,
                "phase": {
                    "type": "rayleigh"
                },
                "extinction": 0.1,
                "albedo": 0.0
            }
        },
        "projector": {
            "type": "telecentric",
            "n_patterns": 1,
            "resx": 740,
            "resy": 700,
            "aperture_radius": 4.0,
            "pixel_size": 20.54e-3,
            "motion": "circular",
            "distance": 150,
            "focus_distance": 150.0
        },
        "sensor": {
            "type": "dda",
            "scalex": 15.2,
            "scaley": 15.2,
            "scalez": 15.2,
            "film": {
                "type": "vfilm",
                "resx": 1000,
                "resy": 1000,
                "resz": 1
            }
        },
        "target": {
            "filename": "cylinder.ply",
            "size": 1000
        },
        "psf_analysis": [
            {
                "x": 370,
                "y": 350,
                "index_pattern": 0,
                "intensity": 1
            },
            {
                "x": 0,
                "y": 350,
                "index_pattern": 0,
                "intensity": 1
            },
            {
                "x": 739,
                "y": 350,
                "index_pattern": 0,
                "intensity": 1
            }
        ],
        "spp_ref": 10000
    }

.. raw:: html

   </details>

Notable we introduce a ``psf_analysis`` section in the JSON file.
This section contains a list of rays to be traced. Each ray is defined by its ``x`` and ``y`` pixel coordinates, the ``index_pattern`` (which pattern to use), and the ``intensity`` of the ray.
In this case we would turn on the most left pixel, the middle pixel, and the most right pixel of the projector pattern.
If ``drtvam config.json`` is run, it will only trace the rays defined in the ``psf_analysis`` section.
The output intensity traces are written in ``final.exr`` and ``final.npy``. The pixel size of the output is defined by the sensor,
hence the output will be 1000x1000 pixels with a pixel size of 0.0152 mm.
Since the refractive index of the vial is 1.0, the rays will not be refracted and will travel in a straight line, as expected in air.
The rays are attenuated by the extinction coefficient of the medium, which is set to 0.1.

The target is irrelevant for this example, but it is required to run the simulation.

We shoot a total of 10000 rays per pixel, as defined by the ``spp_ref`` parameter. It is possible to change this value to increase or decrease the number of rays per pixel. It makes the results more accurate.
Note, in an optimization, increasing the ``spp`` parameters to such high values, will result in very long optimizations. 
So values around 100 (``spp=100``, ``spp_ref=100`` and ``spp_grad=100``) are more realistic and sufficient for most applications.


Calibration a real ``lens`` projector
-------------------------------------
This example shows how to calibrate a :ref:`real lens projector <lens_projector>` setup.
The parameters for such a projector are ``resx``, ``resy``, ``fov``, ``aperture_radius``, ``focus_distance`` and ``distance``.

A sketch of the parameters is given in this figure.

.. image:: resources/setup_lens_rays.png
  :width: 600


The challenge in the calibration is to find the parameters ``aperture_radis``, ``focus_distance`` and ``distance``. The ``fov`` indicates the field of view in the image plane in x direction in degrees.
This can be simply measured by a ruler. 
But since the ``fov`` also depends on the ``distance``, it is intertwisted with the other parameters. The ``aperture_radius`` is the radius of the aperture which describes how large the light cone 
is going to be. Note, this is a abstract, conceptualized projector so the aperture radius is not the physical aperture of a lens, but rather a parameter that describes the light cone of the projector.

The following config files generates the traces of singles rays through a cylindrical vial filled with a medium. 


.. raw:: html

   <details>
   <summary><a>Config file lens projector (click to expand)</a></summary>

.. code-block:: json

    {
        "vial": {
            "type": "cylindrical",
            "r_int": 6,
            "r_ext": 7,
            "ior": 1.5,
            "medium": {
                "ior": 1.5,
                "phase": {
                    "type": "rayleigh"
                },
                "extinction": 0.1,
                "albedo": 0.0
            }
        },
        "projector": {
            "type": "lens",
            "n_patterns": 400,
            "resx": 740,
            "resy": 700,
            "fov": 5.58,
            "aperture_radius": 4.0,
            "focus_distance": 152.0,
            "motion": "circular",
            "distance": 150
        },
        "sensor": {
            "type": "dda",
            "scalex": 15.2,
            "scaley": 15.2,
            "scalez": 15.2,
            "film": {
                "type": "vfilm",
                "resx": 1000,
                "resy": 1000,
                "resz": 1
            }
        },
        "target": {
            "filename": "cylinder.ply",
            "size": 1000
        },
        "psf_analysis": [
            {
                "x": 370,
                "y": 350,
                "index_pattern": 0,
                "intensity": 1
            },
            {
                "x": 0,
                "y": 350,
                "index_pattern": 0,
                "intensity": 1
            },
            {
                "x": 739,
                "y": 350,
                "index_pattern": 0,
                "intensity": 1
            }
        ],
        "spp_ref": 10000
    }

.. raw:: html

   </details>


Running ``drtvam this_config.json`` will generate the traces of the rays through the vial.

<insert picture of generated image>


In experiment we capture similar traces through a glass vial filled with a medium. To make the trace visible we use fluorescent dye in the medium.
It is important to determine the pixel size of the experimental camera in the focal plane (your imaging system might be not telecentric).
Further, the projected pixels in the real setup should hit the vial as close as possible to the vertical end of the vial. Otherwise there is geometric distortion in the image because of the refractive 
index mismatch between the medium and the air.

An experimental capture image could look like this

<insert picture of setup>


With the following helper script, we can overlay the experimental image with the simulated traces. By running ``drtvam`` and adapting the parameters, we can find the best fit of the simulated traces to the experimental image.



Calibration of a ``collimated`` projector
-----------------------------------------
The calibration of a collimated projector is trivial as the only required property is the ``pixel_size`` of the projector in image plane. 
This can be easily measured with a detector or ruler.


Calibration of a ``telecentric`` projector
------------------------------------------
The calibration of a telecentric projector is more work than the ``collimated`` projector, but less than the ``lens`` projector. 
Additionally to the ``pixel_size``, the ``distance``, ``aperture_radius`` and ``focus_distance`` are required. These can be easily inferred from
an experimental capture image from top (or bottom) through a vial filled with a medium.
