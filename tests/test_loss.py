import mitsuba as mi
import pytest

from drtvam.loss import *

def test_l2():
    # Binary mask and sum reduction
    target = mi.TensorXf([1,1,0,0], shape=(2,2,1))
    loss_fn = L2Loss({'reduction': 'sum'})

    pred = mi.TensorXf([1,2,3,4], shape=(2,2,1))
    dr.enable_grad(pred)
    loss = loss_fn(pred, target)
    assert loss == 26

    dr.backward(loss)
    assert dr.all(pred.grad.array == mi.Float([0,2,6,8]))

    # Binary mask and mean reduction
    loss_fn = L2Loss({'reduction': 'mean'})

    pred = mi.TensorXf([1,2,3,4], shape=(2,2,1))
    dr.enable_grad(pred)
    loss = loss_fn(pred, target)
    assert loss == 6.5

    dr.backward(loss)
    assert dr.all(pred.grad.array == mi.Float([0,0.5,1.5,2]))

    # Greyscale mask and sum reduction
    loss_fn = L2Loss({'reduction': 'sum'})
    target = mi.TensorXf([0.2, 0.8, 0.5, 0.], shape=(2,2,1))
    pred = mi.TensorXf([1., 1., 1., 1.], shape=(2,2,1))
    dr.enable_grad(pred)
    loss = loss_fn(pred, target)
    assert dr.allclose(loss,  0.8**2 + 0.2**2 + 0.5**2 + 1.)
    dr.backward(loss)
    assert dr.allclose(pred.grad.array, mi.Float([1.6, 0.4, 1., 2.]))


    # Surface-aware target and sum reduction
    target = mi.TensorXf([0.2, 0.8], shape=(1,1,2))
    pred = mi.TensorXf([0.4, 0.3], shape=(1,1,2))
    dr.enable_grad(pred)
    loss = loss_fn(pred, target)
    assert dr.allclose(loss, 0.2 * 0.6**2 + 0.8 * 0.3**2)
    dr.backward(loss)
    assert dr.allclose(pred.grad.array, mi.Float([-2*0.2*0.6, 2*0.8*0.3]))


@pytest.mark.parametrize("variant", ["cuda_ad_mono", "llvm_ad_mono"])
def test_thresholded(variant):
    mi.set_variant(variant)
    target = mi.TensorXf([1,1,0,0], shape=(2,2))
    loss_fn = ThresholdedLoss({'K': 2, 'tl': 0.9, 'tu': 0.95, 'reduction': 'sum'})

    pred = mi.TensorXf([0.5, 0.97, 0.92, 0.5], shape=(2,2,1))
    dr.enable_grad(pred)
    loss = loss_fn(pred, target)
    assert dr.allclose(loss, 0.45**2 + 0.02**2)
    dr.backward(loss)
    assert dr.allclose(pred.grad.array, mi.Float([-0.9, 0., 0.04, 0.]))

    loss_fn = ThresholdedLoss({'K': 2, 'tl': 0.9, 'tu': 0.95, 'reduction': 'mean'})

    pred = mi.TensorXf([0.5, 0.97, 0.92, 0.5], shape=(2,2,1))
    dr.enable_grad(pred)
    loss = loss_fn(pred, target)
    assert dr.allclose(loss, (0.45**2 + 0.02**2) / 4)
    dr.backward(loss)
    assert dr.allclose(pred.grad.array, mi.Float([-0.225, 0., 0.01, 0.]))

    loss_fn = ThresholdedLoss({'K': 1, 'tl': 0.9, 'tu': 0.95, 'reduction': 'sum'})

    pred = mi.TensorXf([0.5, 1.1, 0.92, 0.5], shape=(2,2,1))
    dr.enable_grad(pred)
    loss = loss_fn(pred, target)
    assert dr.allclose(loss, 0.57)
    dr.backward(loss)
    assert dr.allclose(pred.grad.array, mi.Float([-1, 1., 1., 0.]))

    loss_fn = ThresholdedLoss({'K': 2, 'tl': 0.4, 'tu': 0.95, 'reduction': 'sum'})

    pred = mi.TensorXf([0.5, 0.97, 0.92, 0.5], shape=(2,2,1))
    dr.enable_grad(pred)
    loss = loss_fn(pred, target)
    assert dr.allclose(loss, 0.45**2 + 0.52**2 + 0.1**2)
    dr.backward(loss)
    assert dr.allclose(pred.grad.array, mi.Float([-0.9, 0., 1.04, 0.2]))

    loss_fn = ThresholdedLoss({'K': 2, 'tl': 0.9, 'tu': 0.99, 'reduction': 'sum'})

    pred = mi.TensorXf([0.5, 0.97, 0.92, 0.5], shape=(2,2,1))
    dr.enable_grad(pred)
    loss = loss_fn(pred, target)
    assert dr.allclose(loss, 0.49**2 + 0.02**2 + 0.02**2)
    dr.backward(loss)
    assert dr.allclose(pred.grad.array, mi.Float([-0.98, -0.04, 0.04, 0.]))

    # Surface-aware target and sum reduction
    loss_fn = ThresholdedLoss({'K': 2, 'tl': 0.9, 'tu': 0.95, 'reduction': 'sum'})
    target = mi.TensorXf([0.2, 0.8, 2, 2], shape=(2,1,2))
    pred = mi.TensorXf([0.2, 0.1, 0.96, 0.92], shape=(2,1,2))
    dr.enable_grad(pred)
    loss = loss_fn(pred, target)
    assert dr.allclose(loss, 0.2 * 0.75**2 + 0.5 * 0.02**2)
    dr.backward(loss)
    assert dr.allclose(pred.grad.array, mi.Float([-2*0.2*0.75, 0., 0., 2*0.5*0.02]))

