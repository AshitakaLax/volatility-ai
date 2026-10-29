"""research/catalog/autodiff.py -- gradients against finite differences."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import (
    LSTM,
    MLP,
    Adam,
    Tensor,
    bce_with_logits,
    causal_conv1d,
    concat,
    dft_matrices,
    fit,
    log_softmax,
    logsumexp,
    maximum,
    mse,
    numerical_grad,
    param,
    shift,
    softmax,
    stack,
    where,
)


def _check(build, *shapes, seed=0, tol=1e-5):
    rng = np.random.default_rng(seed)
    xs = [Tensor(rng.normal(size=s) + 0.1, requires_grad=True) for s in shapes]
    out = build(*xs)
    out.backward()
    for x in xs:
        num = numerical_grad(lambda: float(build(*xs).data), x)
        assert x.grad == pytest.approx(num, abs=tol, rel=tol)


def test_arithmetic_and_broadcasting_gradients():
    _check(lambda a, b: ((a * b + a / (b.abs() + 1.0)) ** 2).sum(), (3, 4), (4,))
    _check(lambda a, b: (a - 2.0 * b).mean() + (3.0 - a).sum(), (2, 3), (2, 1))
    _check(lambda a: (1.0 / (a.abs() + 0.5)).sum(), (5,))


def test_matmul_shapes_including_vectors_and_batches():
    _check(lambda a, b: (a @ b).tanh().sum(), (3, 4), (4, 2))
    _check(lambda a, b: (a @ b).sum(), (4,), (4, 3))
    _check(lambda a, b: (a @ b).sum(), (3, 4), (4,))
    _check(lambda a, b: (a @ b) * 1.0, (4,), (4,))
    _check(lambda a, b: (a @ b).sigmoid().sum(), (2, 3, 4), (4, 5))


def test_nonlinearities_reductions_and_indexing():
    _check(lambda a: (a.exp() + a.softplus() + a.sin() * a.cos()).sum(), (3,))
    _check(lambda a: (a.abs() + 1.0).log().sum() + (a.abs() + 1.0).sqrt().sum(), (4,))
    _check(lambda a: a.reshape(2, 6).transpose().sum(axis=0).sum(), (3, 4))
    _check(lambda a: (a[1:, ::2] ** 2).sum() + a[0, 1], (3, 4))
    _check(lambda a: a.mean(axis=1, keepdims=True).sum() + a.sum(axis=0).sum(), (3, 4))
    _check(lambda a: a.leaky_relu(0.1).sum() + a.relu().sum() + a.clip(-0.5, 0.5).sum(), (6,))


def test_combinators_softmax_and_losses():
    _check(lambda a, b: (concat([a, b], axis=0) ** 2).sum(), (2, 3), (1, 3))
    _check(lambda a, b: stack([a, b], axis=1).tanh().sum(), (3,), (3,))
    _check(lambda a: (softmax(a, axis=1) * Tensor([[1.0, 2.0, 3.0]])).sum(), (2, 3))
    _check(lambda a: log_softmax(a)[..., 0].sum() + logsumexp(a).sum(), (2, 3))
    _check(lambda a, b: where(a.data > 0, a, b).sum() + maximum(a, b).sum(), (5,), (5,))
    _check(lambda a: mse(a, np.ones(4)) + bce_with_logits(a, np.array([0, 1, 1, 0.0])), (4,))
    _check(lambda a: shift(a, 2).sum() * 1.0 + (shift(a, 1) * a).sum(), (5, 2))


def test_causal_convolution_is_causal_and_differentiable():
    rng = np.random.default_rng(1)
    x, w = Tensor(rng.normal(size=(8, 2))), Tensor(rng.normal(size=(3, 2, 4)))
    y = causal_conv1d(x, w, dilation=2).data
    x2 = x.data.copy()
    x2[5:] += 10.0  # the future cannot move the past
    assert causal_conv1d(Tensor(x2), w, dilation=2).data[:5] == pytest.approx(y[:5])
    _check(lambda a, b: causal_conv1d(a, b, dilation=2).tanh().sum(), (6, 2), (2, 2, 3))


def test_dft_matrices_match_numpy_fft():
    x = np.random.default_rng(2).normal(size=16)
    re, im = dft_matrices(16, 5)
    f = np.fft.rfft(x)[:5]
    assert re @ x == pytest.approx(f.real) and im @ x == pytest.approx(f.imag)


def test_layers_train_and_lstm_gradients_check():
    rng = np.random.default_rng(3)
    x = rng.normal(size=(64, 2))
    y = (np.sin(x[:, :1]) + 0.5 * x[:, 1:]) ** 2
    net = MLP([2, 16, 1], rng)
    hist = fit(lambda: mse(net(Tensor(x)), y), net.params, steps=400, lr=0.02)
    assert hist[-1] < 0.2 * hist[0]
    lstm = LSTM(2, 3, rng)
    seq = Tensor(rng.normal(size=(4, 2)))
    out = lstm(seq)
    out.sum().backward()
    num = numerical_grad(lambda: float(lstm(seq).sum().data), lstm.w)
    assert lstm.w.grad == pytest.approx(num, abs=1e-5)


def test_adam_minimises_a_quadratic_and_errors_are_explicit():
    p = param((3,), np.random.default_rng(4), scale=1.0)
    opt = Adam([p], lr=0.1)
    for _ in range(300):
        opt.zero_grad()
        ((p - 2.0) ** 2).sum().backward()
        opt.step()
    assert p.data == pytest.approx(2.0, abs=1e-3)
    with pytest.raises(ConfigurationError):
        Tensor([1.0]).backward()
    with pytest.raises(ConfigurationError):
        Tensor([1.0], requires_grad=True) ** Tensor([2.0])
