"""
A minimal reverse-mode automatic differentiation for NumPy arrays, so the
catalog's neural models (ledger RK200-RK425: transformers, temporal
convolutions, graph networks, diffusion and flow models, neural ODEs and
operators, deep hedging, RL agents) train without a deep-learning
framework. Research code only, like everything in research/catalog.

A `Tensor` wraps a float64 array, records the operation that produced it,
and `backward()` accumulates d(output)/d(leaf) into each leaf's `.grad`.
Broadcasting follows NumPy; gradients are summed back to each operand's
shape. The operation set is the one the catalog uses: arithmetic, matmul,
reductions, reshapes, indexing, concatenation, and the usual
nonlinearities. Complex-valued layers (Fourier neural operators) are built
from real DFT matrices, so nothing here needs complex numbers.

Pinned against central finite differences in
research/tests/test_catalog_autodiff.py.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from itertools import pairwise

import numpy as np

from engine.core.exceptions import ConfigurationError


def _unbroadcast(grad: np.ndarray, shape: tuple[int, ...]) -> np.ndarray:
    while grad.ndim > len(shape):
        grad = grad.sum(axis=0)
    for axis, size in enumerate(shape):
        if size == 1 and grad.shape[axis] != 1:
            grad = grad.sum(axis=axis, keepdims=True)
    return grad


class Tensor:
    """An array with a gradient tape."""

    __array_priority__ = 100  # numpy defers to Tensor's reflected operators

    def __init__(self, data, requires_grad: bool = False, _parents=(), _backward=None):
        self.data = np.asarray(data, dtype=float)
        self.requires_grad = requires_grad or any(p.requires_grad for p in _parents)
        self.grad: np.ndarray | None = None
        self._parents = _parents
        self._backward: Callable[[np.ndarray], None] | None = _backward

    # ---------------------------------------------------------------- plumbing
    @property
    def shape(self) -> tuple[int, ...]:
        return self.data.shape

    @property
    def ndim(self) -> int:
        return self.data.ndim

    def __len__(self) -> int:
        return len(self.data)

    def __repr__(self) -> str:
        return f"Tensor({self.data!r}, requires_grad={self.requires_grad})"

    def numpy(self) -> np.ndarray:
        return self.data

    def detach(self) -> Tensor:
        return Tensor(self.data.copy())

    def _accumulate(self, grad: np.ndarray) -> None:
        if not self.requires_grad:
            return
        grad = _unbroadcast(grad, self.data.shape)
        self.grad = grad.copy() if self.grad is None else self.grad + grad

    def backward(self, grad=None) -> None:
        """Accumulate gradients of this tensor into every leaf that requires them."""
        if not self.requires_grad:
            raise ConfigurationError("backward() on a tensor that does not require grad")
        order, seen = [], set()

        def visit(t: Tensor) -> None:
            if id(t) in seen:
                return
            seen.add(id(t))
            for p in t._parents:
                visit(p)
            order.append(t)

        visit(self)
        grads = {id(self): np.ones_like(self.data) if grad is None else np.asarray(grad, float)}
        for t in reversed(order):
            g = grads.pop(id(t), None)
            if g is None:
                continue
            if t._backward is None:  # a leaf
                t._accumulate(g)
            else:
                for p, pg in t._backward(g):
                    if p.requires_grad:
                        pg = _unbroadcast(pg, p.data.shape)
                        grads[id(p)] = grads[id(p)] + pg if id(p) in grads else pg

    # ---------------------------------------------------------------- arithmetic
    def __add__(self, other) -> Tensor:
        o = as_tensor(other)
        return Tensor(
            self.data + o.data, _parents=(self, o), _backward=lambda g: ((self, g), (o, g))
        )

    __radd__ = __add__

    def __neg__(self) -> Tensor:
        return Tensor(-self.data, _parents=(self,), _backward=lambda g: ((self, -g),))

    def __sub__(self, other) -> Tensor:
        return self + (-as_tensor(other))

    def __rsub__(self, other) -> Tensor:
        return as_tensor(other) + (-self)

    def __mul__(self, other) -> Tensor:
        o = as_tensor(other)
        return Tensor(
            self.data * o.data,
            _parents=(self, o),
            _backward=lambda g: ((self, g * o.data), (o, g * self.data)),
        )

    __rmul__ = __mul__

    def __truediv__(self, other) -> Tensor:
        o = as_tensor(other)
        return Tensor(
            self.data / o.data,
            _parents=(self, o),
            _backward=lambda g: ((self, g / o.data), (o, -g * self.data / o.data**2)),
        )

    def __rtruediv__(self, other) -> Tensor:
        return as_tensor(other) / self

    def __pow__(self, k: float) -> Tensor:
        if isinstance(k, Tensor):
            raise ConfigurationError("only constant exponents are supported")
        return Tensor(
            self.data**k,
            _parents=(self,),
            _backward=lambda g: ((self, g * k * self.data ** (k - 1)),),
        )

    def __matmul__(self, other) -> Tensor:
        o = as_tensor(other)

        def back(g):
            a, b = self.data, o.data
            if a.ndim == 1 and b.ndim == 1:
                return (self, g * b), (o, g * a)
            if a.ndim == 1:
                return (self, g @ np.swapaxes(b, -1, -2)), (o, np.outer(a, g))
            if b.ndim == 1:
                return (self, np.multiply.outer(g, b)), (o, np.swapaxes(a, -1, -2) @ g)
            ga = g @ np.swapaxes(b, -1, -2)
            gb = np.swapaxes(a, -1, -2) @ g
            return (self, ga), (o, gb)

        return Tensor(self.data @ o.data, _parents=(self, o), _backward=back)

    def __rmatmul__(self, other) -> Tensor:
        return as_tensor(other) @ self

    # ---------------------------------------------------------------- reductions and shape
    def sum(self, axis=None, keepdims: bool = False) -> Tensor:
        def back(g):
            if axis is not None and not keepdims:
                g = np.expand_dims(g, axis)
            return ((self, np.broadcast_to(g, self.data.shape)),)

        return Tensor(self.data.sum(axis=axis, keepdims=keepdims), _parents=(self,), _backward=back)

    def mean(self, axis=None, keepdims: bool = False) -> Tensor:
        n = self.data.size if axis is None else np.prod(np.take(self.data.shape, axis))
        return self.sum(axis=axis, keepdims=keepdims) / float(n)

    def reshape(self, *shape) -> Tensor:
        shape = shape[0] if len(shape) == 1 and isinstance(shape[0], tuple) else shape
        return Tensor(
            self.data.reshape(shape),
            _parents=(self,),
            _backward=lambda g: ((self, g.reshape(self.data.shape)),),
        )

    def transpose(self, *axes) -> Tensor:
        axes = axes or tuple(reversed(range(self.ndim)))
        inv = np.argsort(axes)
        return Tensor(
            self.data.transpose(axes),
            _parents=(self,),
            _backward=lambda g: ((self, g.transpose(inv)),),
        )

    @property
    def T(self) -> Tensor:
        return self.transpose()

    def __getitem__(self, idx) -> Tensor:
        def back(g):
            full = np.zeros_like(self.data)
            np.add.at(full, idx, g)
            return ((self, full),)

        return Tensor(self.data[idx], _parents=(self,), _backward=back)

    # ---------------------------------------------------------------- nonlinearities
    def _unary(self, value: np.ndarray, deriv: np.ndarray) -> Tensor:
        return Tensor(value, _parents=(self,), _backward=lambda g: ((self, g * deriv),))

    def exp(self) -> Tensor:
        v = np.exp(self.data)
        return self._unary(v, v)

    def log(self) -> Tensor:
        return self._unary(np.log(self.data), 1.0 / self.data)

    def tanh(self) -> Tensor:
        v = np.tanh(self.data)
        return self._unary(v, 1.0 - v**2)

    def sigmoid(self) -> Tensor:
        v = 1.0 / (1.0 + np.exp(-self.data))
        return self._unary(v, v * (1.0 - v))

    def relu(self) -> Tensor:
        return self._unary(np.maximum(self.data, 0.0), (self.data > 0).astype(float))

    def leaky_relu(self, slope: float = 0.01) -> Tensor:
        return self._unary(
            np.where(self.data > 0, self.data, slope * self.data),
            np.where(self.data > 0, 1.0, slope),
        )

    def softplus(self) -> Tensor:
        return self._unary(np.logaddexp(0.0, self.data), 1.0 / (1.0 + np.exp(-self.data)))

    def sqrt(self) -> Tensor:
        v = np.sqrt(self.data)
        return self._unary(v, 0.5 / v)

    def abs(self) -> Tensor:
        return self._unary(np.abs(self.data), np.sign(self.data))

    def sin(self) -> Tensor:
        return self._unary(np.sin(self.data), np.cos(self.data))

    def cos(self) -> Tensor:
        return self._unary(np.cos(self.data), -np.sin(self.data))

    def clip(self, lo: float, hi: float) -> Tensor:
        inside = ((self.data >= lo) & (self.data <= hi)).astype(float)
        return self._unary(np.clip(self.data, lo, hi), inside)


def as_tensor(x) -> Tensor:
    return x if isinstance(x, Tensor) else Tensor(x)


def param(shape, rng: np.random.Generator | None = None, scale: float | None = None) -> Tensor:
    """A trainable leaf with Glorot-uniform initialisation (zeros for 1-D biases)."""
    shape = (shape,) if isinstance(shape, int) else tuple(shape)
    if len(shape) == 1 and scale is None:
        return Tensor(np.zeros(shape), requires_grad=True)
    if rng is None:
        raise ConfigurationError("a weight tensor needs an rng")
    fan = shape[-2] + shape[-1] if len(shape) >= 2 else shape[0]
    lim = scale if scale is not None else np.sqrt(6.0 / fan)
    return Tensor(rng.uniform(-lim, lim, size=shape), requires_grad=True)


# ---------------------------------------------------------------- combinators
def concat(tensors: Iterable[Tensor], axis: int = -1) -> Tensor:
    ts = [as_tensor(t) for t in tensors]
    sizes = [t.data.shape[axis] for t in ts]
    cuts = np.cumsum(sizes)[:-1]

    def back(g):
        return tuple(zip(ts, np.split(g, cuts, axis=axis), strict=True))

    return Tensor(
        np.concatenate([t.data for t in ts], axis=axis), _parents=tuple(ts), _backward=back
    )


def stack(tensors: Iterable[Tensor], axis: int = 0) -> Tensor:
    ts = [as_tensor(t) for t in tensors]
    return concat([t.reshape(_expand(t.shape, axis)) for t in ts], axis=axis)


def _expand(shape: tuple[int, ...], axis: int) -> tuple[int, ...]:
    axis = axis if axis >= 0 else len(shape) + 1 + axis
    return (*shape[:axis], 1, *shape[axis:])


def where(mask: np.ndarray, a, b) -> Tensor:
    a, b = as_tensor(a), as_tensor(b)
    mask = np.asarray(mask, dtype=bool)
    return Tensor(
        np.where(mask, a.data, b.data),
        _parents=(a, b),
        _backward=lambda g: ((a, np.where(mask, g, 0.0)), (b, np.where(mask, 0.0, g))),
    )


def maximum(a, b) -> Tensor:
    a, b = as_tensor(a), as_tensor(b)
    return where(a.data >= b.data, a, b)


def softmax(x: Tensor, axis: int = -1) -> Tensor:
    shifted = x - Tensor(x.data.max(axis=axis, keepdims=True))
    e = shifted.exp()
    return e / e.sum(axis=axis, keepdims=True)


def log_softmax(x: Tensor, axis: int = -1) -> Tensor:
    shifted = x - Tensor(x.data.max(axis=axis, keepdims=True))
    return shifted - shifted.exp().sum(axis=axis, keepdims=True).log()


def logsumexp(x: Tensor, axis: int = -1) -> Tensor:
    m = Tensor(x.data.max(axis=axis, keepdims=True))
    return ((x - m).exp().sum(axis=axis, keepdims=True).log() + m).sum(axis=axis)


def shift(x: Tensor, k: int, axis: int = 0) -> Tensor:
    """Delay x by k steps along `axis`, filling with zeros (causal padding)."""
    if k == 0:
        return x
    pad_shape = list(x.shape)
    pad_shape[axis] = k
    idx = [slice(None)] * x.ndim
    idx[axis] = slice(0, x.shape[axis] - k)
    return concat([Tensor(np.zeros(pad_shape)), x[tuple(idx)]], axis=axis)


def causal_conv1d(
    x: Tensor, weight: Tensor, bias: Tensor | None = None, dilation: int = 1
) -> Tensor:
    """x (time, c_in), weight (kernel, c_in, c_out): y_t = sum_k x_{t - k d} W_k + b."""
    out = None
    for k in range(weight.shape[0]):
        term = shift(x, k * dilation, axis=0) @ weight[k]
        out = term if out is None else out + term
    return out if bias is None else out + bias


def dft_matrices(n: int, modes: int) -> tuple[np.ndarray, np.ndarray]:
    """Real and imaginary parts of the first `modes` rows of the n-point DFT."""
    t = np.arange(n)
    k = np.arange(modes)[:, None]
    ang = 2 * np.pi * k * t / n
    return np.cos(ang), -np.sin(ang)


# ---------------------------------------------------------------- losses and optimisation
def mse(pred: Tensor, target) -> Tensor:
    return ((pred - as_tensor(target)) ** 2).mean()


def bce_with_logits(logits: Tensor, target) -> Tensor:
    y = as_tensor(target)
    return (logits.softplus() - logits * y).mean()


class Adam:
    """Adam (Kingma & Ba 2015) over a list of leaf tensors."""

    def __init__(self, params: list[Tensor], lr: float = 1e-2, b1=0.9, b2=0.999, eps=1e-8):
        self.params, self.lr, self.b1, self.b2, self.eps = list(params), lr, b1, b2, eps
        self.m = [np.zeros_like(p.data) for p in self.params]
        self.v = [np.zeros_like(p.data) for p in self.params]
        self.t = 0

    def zero_grad(self) -> None:
        for p in self.params:
            p.grad = None

    def step(self) -> None:
        self.t += 1
        for i, p in enumerate(self.params):
            if p.grad is None:
                continue
            self.m[i] = self.b1 * self.m[i] + (1 - self.b1) * p.grad
            self.v[i] = self.b2 * self.v[i] + (1 - self.b2) * p.grad**2
            mh = self.m[i] / (1 - self.b1**self.t)
            vh = self.v[i] / (1 - self.b2**self.t)
            p.data -= self.lr * mh / (np.sqrt(vh) + self.eps)


def fit(
    loss_fn: Callable[[], Tensor], params: list[Tensor], steps: int, lr: float = 1e-2
) -> list[float]:
    """Run `steps` Adam updates on loss_fn(); returns the loss history."""
    opt, history = Adam(params, lr), []
    for _ in range(steps):
        opt.zero_grad()
        loss = loss_fn()
        loss.backward()
        opt.step()
        history.append(float(loss.data))
    return history


# ---------------------------------------------------------------- building blocks
class Dense:
    def __init__(self, n_in: int, n_out: int, rng: np.random.Generator) -> None:
        self.w, self.b = param((n_in, n_out), rng), param(n_out)

    def __call__(self, x: Tensor) -> Tensor:
        return x @ self.w + self.b

    @property
    def params(self) -> list[Tensor]:
        return [self.w, self.b]


class MLP:
    """Dense layers with a nonlinearity between them (none after the last)."""

    def __init__(self, sizes: list[int], rng: np.random.Generator, act: str = "tanh") -> None:
        self.layers = [Dense(a, b, rng) for a, b in pairwise(sizes)]
        self.act = act

    def __call__(self, x: Tensor) -> Tensor:
        for i, layer in enumerate(self.layers):
            x = layer(x)
            if i < len(self.layers) - 1:
                x = getattr(x, self.act)()
        return x

    @property
    def params(self) -> list[Tensor]:
        return [p for layer in self.layers for p in layer.params]


class LSTM:
    """A single-layer LSTM over a (time, features) sequence."""

    def __init__(self, n_in: int, n_hidden: int, rng: np.random.Generator) -> None:
        self.n = n_hidden
        self.w = param((n_in + n_hidden, 4 * n_hidden), rng)
        self.b = Tensor(np.r_[np.zeros(n_hidden), np.ones(n_hidden), np.zeros(2 * n_hidden)], True)

    def cell(self, x_t: Tensor, h: Tensor, c: Tensor) -> tuple[Tensor, Tensor]:
        """One step, for loops whose next input depends on the last output."""
        z = concat([x_t, h]) @ self.w + self.b  # works for one step (n,) or a batch (B, n)
        n = self.n
        i, f = z[..., :n].sigmoid(), z[..., n : 2 * n].sigmoid()
        o, g = z[..., 2 * n : 3 * n].sigmoid(), z[..., 3 * n :].tanh()
        c = f * c + i * g
        return o * c.tanh(), c

    def zero_state(self, batch: int | None = None) -> tuple[Tensor, Tensor]:
        shape = (self.n,) if batch is None else (batch, self.n)
        return Tensor(np.zeros(shape)), Tensor(np.zeros(shape))

    def __call__(self, x: Tensor) -> Tensor:
        h, c = self.zero_state()
        outs = []
        for t in range(x.shape[0]):
            h, c = self.cell(x[t], h, c)
            outs.append(h)
        return stack(outs, axis=0)

    @property
    def params(self) -> list[Tensor]:
        return [self.w, self.b]


def numerical_grad(f: Callable[[], float], x: Tensor, eps: float = 1e-6) -> np.ndarray:
    """Central finite differences of scalar f() with respect to x.data."""
    g = np.zeros_like(x.data)
    it = np.nditer(x.data, flags=["multi_index"])
    for _ in it:
        i = it.multi_index
        old = x.data[i]
        x.data[i] = old + eps
        up = f()
        x.data[i] = old - eps
        down = f()
        x.data[i] = old
        g[i] = (up - down) / (2 * eps)
    return g
