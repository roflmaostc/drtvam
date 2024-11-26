import mitsuba as mi
mi.set_variant('cuda_ad_mono', 'cuda_ad_rgb')
import drjit as dr
import pytest
from drtvam.utils import iou_loss

def test_iou():
    target = mi.TensorXf([1,1,0,0], shape=(2,2))

    pred = dr.ones(mi.TensorXf, shape=(2,2))
    assert dr.all(iou_loss(pred, target) == 0.5)

    pred = dr.zeros(mi.TensorXf, shape=(2,2))
    assert dr.all(iou_loss(pred, target) == 0.)

    pred = mi.TensorXf([1,0,0,0], shape=(2,2))
    assert dr.all(iou_loss(pred, target) == 0.5)

    pred = mi.TensorXf([1,1,1,0], shape=(2,2))
    assert dr.all(iou_loss(pred, target) == 2/3)

    pred = mi.TensorXf([0.6, 0.6, 0.6,0], shape=(2,2))
    assert dr.all(iou_loss(pred, target) == 0.)

    pred = mi.TensorXf([0.6, 0.6, 0.6,0], shape=(2,2))
    assert dr.all(iou_loss(pred, target, threshold=0.5) == 2/3)

