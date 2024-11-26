.. _plugin_doc:

Plugin documentation
====================

Dr.TVAM extends the Mitsuba 3 framework with a few *plugins* that are specific
to the TVAM problem setting. In particular, we use custom plugins to define the
printing medium and its container, the projection system and its motion, the
volumetric sensor, and the integrator that computes the absorption map. Other
parts of Dr.TVAM directly use Mitsuba 3 plugins without modifications. In
particular we use the `shape
<https://mitsuba.readthedocs.io/en/stable/src/generated/plugins_shapes.html>`_
and `BSDF
<https://mitsuba.readthedocs.io/en/stable/src/generated/plugins_bsdfs.html>`_
plugins as they are to define the different surfaces and materials in the
printing setup. Please refer to the Mitsuba 3 documentation for more information
on these plugins.

For the custom plugins, we provide a detailed reference in the following
sections.

Plugins
-------

.. toctree::
    :maxdepth: 1

    plugin_reference/container
    plugin_reference/projector
    plugin_reference/sensor
    plugin_reference/integrator
    plugin_reference/loss
    plugin_reference/optimizer

