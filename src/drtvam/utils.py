import mitsuba as mi
import drjit as dr
import os
import numpy as np
import matplotlib.pyplot as plt

def iou_loss(pred, target, threshold=0.85):
    obj_mask = target.array > 0.
    thresholded = pred.array > threshold
    return mi.Float(dr.count(thresholded & obj_mask)) / dr.count(thresholded | obj_mask)

def reshape_grid(array, res):
    if len(array.shape) == 3:
        n, h, w = array.shape
        c = 1
    else:
        n, h, w, c = array.shape
    if np.log2(res) % 2 == 0:
        cols = rows = int(np.sqrt(res))
    else:
        rows = int(np.sqrt(res/2))
        cols = rows * 2

    return array.numpy().reshape((rows, cols, h, w, c)).swapaxes(1, 2).reshape((rows*h, cols*w, c))

def save_img(img, path):
    assert type(img) == mi.TensorXf
    if len(img.shape) == 2:
        bmp = mi.Bitmap(img[..., None])
    elif len(img.shape) == 3:
        bmp = mi.Bitmap(img)
    else:
        raise ValueError("Invalid image shape")
    bmp.write(path)

def save_vol(vol, path):
    assert type(vol) == mi.TensorXf
    if len(vol.shape) == 3:
        vol == vol[..., None]
    assert len(vol.shape) == 4

    bmp = mi.Bitmap(mi.TensorXf(reshape_grid(vol, vol.shape[0])))
    bmp.write(path)

def save_histogram(vol, target, filename):
    fig = plt.figure(figsize=(10, 5))
    obj_mask = target.numpy().flatten() > 0.

    voxels_final = vol.numpy().flatten()
    bins = np.linspace(0, 1, 500)
    plt.hist(voxels_final[obj_mask], bins=500, label="Object", alpha=0.55)
    plt.hist(voxels_final[~obj_mask], bins=500, label="Empty", alpha=0.55)

    plt.yscale('log')
    plt.ylabel("# Voxels")
    plt.xlabel("Received dose")
    plt.legend()
    plt.savefig(filename)

def discretize(scene, sensor=0):
    """
    Given a scene containing a target shape, this function converts
    it to a binary occupancy grid, to be used as the reference for optimization.
    """
    if isinstance(sensor, int):
        sensor = scene.sensors()[sensor]

    target_shape = None
    for shape in scene.shapes():
        if dr.hint(shape.id() == 'target', mode='scalar'):
            target_shape = shape
    if target_shape is None:
        raise ValueError("No target shape found in the scene")

    bbox = target_shape.bbox()

    res = sensor.resolution()
    voxel_size = sensor.bbox.extents() / mi.Vector3f(res.x, res.y, res.z)

    xx = dr.arange(mi.Float, res.x)
    yy = dr.arange(mi.Float, res.y)
    zz = dr.arange(mi.Float, res.z)
    z_idx, y_idx, x_idx = dr.meshgrid(zz, yy, xx, indexing='ij')

    pos = sensor.bbox.min + (0.5 + mi.Point3f(x_idx, y_idx, z_idx)) * voxel_size

    sampler = mi.load_dict({'type': 'independent'})
    sampler.seed(0, dr.width(pos))

    ray = mi.Ray3f(pos, mi.warp.square_to_uniform_sphere(sampler.next_2d()))
    active = dr.all((ray.o > bbox.min) & (ray.o < bbox.max))

    si = scene.ray_intersect(ray, active=active)

    inside = si.is_valid() & (si.shape == mi.ShapePtr(target_shape)) & (dr.dot(si.n, ray.d) > 0)

    voxels = dr.zeros(mi.TensorXf, shape=(res.z, res.y, res.x, 1))
    voxels.array[inside] = 1.0

    return voxels

def get_mesh_transform(filename, print_size, size=None):
    """
    Params
    ------

    filename: str
        Path to the mesh file

    print_size: mi.Point3f
        Size of the printable volume

    size: float
        Size of the object in the grid. If None, the object is scaled to fit the grid as tightly as possible.
    """
    ext = os.path.splitext(filename)[1][1:]
    if not ext in ['ply', 'obj']:
        raise ValueError(f"Unsupported extension: '{ext}', only PLY and OBJ meshes are supported.")

    shape = mi.load_dict({
            'type': ext,
            'filename': filename
    })
    params = mi.traverse(shape)
    bbox = shape.bbox()
    ext_max = dr.max(bbox.extents())
    if size is None:
        # Scale the object to fit the grid as tightly as possible
        # Align the largest dimension with the z-axis
        # This is because the printing volume is taller than it is wide because of refractions.
        axis_max = dr.select(bbox.extents() == ext_max, 1., 0.)

        if dr.any(axis_max != mi.ScalarVector3f(0, 0, 1)):
            rot_axis = dr.cross(axis_max, mi.ScalarVector3f(0, 0, 1))
            rot_mat = mi.ScalarTransform4f().rotate(rot_axis, 90.)
        else:
            rot_mat = mi.ScalarTransform4f(1.)

        # Find the enclosing circle of the object in the XY plane
        v = params['vertex_positions'].numpy().reshape((-1, 3))
        mask = (axis_max.numpy() != np.ones(3))
        v_2d = v[:, mask]
        import miniball
        mb = miniball.Miniball(v_2d)
        c = np.zeros(3)
        c[mask] = mb.center()
        c[~mask] = 0.5 * (bbox.min + bbox.max).numpy()[~mask]
        r = np.sqrt(mb.squared_radius())

        tr = mi.ScalarTransform4f().translate(-c)
        scale = mi.Point3f()
        scale.z = print_size.z / ext_max # Scale factor so the height fits on the DMD
        scale.xy = 0.5 * print_size.xy / r # Scale factor so the enclosing circle fits in the grid
        scale = mi.ScalarTransform4f().scale(dr.min(scale)[0])
        to_world = scale @ rot_mat @ tr
    else:
        if dr.any(size > print_size):
            raise ValueError("The size of the object is larger than the printable volume.")
        c = 0.5 * (bbox.min + bbox.max)
        to_world = mi.ScalarTransform4f().scale(size / ext_max) @ mi.ScalarTransform4f().translate(-c)

    return to_world

