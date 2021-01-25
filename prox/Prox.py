import torch

class Prox:
    r"""
    Proximal operator base class

    Prox is currently supported to be called on a torch.Tensor

    .. math::
       Prox_f(v) = \arg \min_x \frac{1}{2} \| x - v \|_2^2 + f(x)

    Args:

    """

    def __init__(self):
        #sigpy has size/shape input parameter, but I don't see why we would need it?: Maybe for now we do not need it: we do not.
        pass

    def __call__(self, v):
        #sigpy also has alpha value, maybe add that here after implementing basic functionality
        if v.dtype == torch.cfloat or v.dtype == torch.cdouble:
            return self._complex(v) * self._apply(v.abs())
        return self._apply(v)

    def __repr__(self):
        return f'<{self.__class__.__name__} Prox'

    def _complex(self, v):
        '''
        Backprop .backward() currently not implemented for .angle() and .exp()
        Current solution: calculate angle as torch.atan(a.imag/a.real) and use cos + i sin
        formulation to avoid .angle() and .exp()
        '''
        angle = torch.atan(v.imag/v.real)
        exp = torch.complex(torch.cos(angle), torch.sin(angle))
        return exp

class L1Regularizer(Prox):
    r"""
    Proximal operator for L1 regularizer, using soft thresholding

    .. math::
        \arg \min_x \frac{1}{2} \| x - v \|_2^2 + \lambda \| Tx \|_1

    Args:
        Lambda (float): regularization parameter.
        T (LinearMap): optional, unitary LinearMap
    """

    def __init__(self, Lambda, T=None):
        super().__init__()
        self.Lambda = float(Lambda)
        if T is not None:
            assert('unitary' in T.property)
        self.T = T

    def _apply(self, v):
        # Closed form solution from
        # https://archive.siam.org/books/mo25/mo25_ch6.pdf
        thresh = torch.nn.Softshrink(self.Lambda)
        if self.T is not None:
            v = self.T(v)
        x = thresh(v)
        return x

class L2Regularizer(Prox):
    r"""
    Proximal operator for L2 regularizer

    .. math::
        \arg \min_x \frac{1}{2} \| x - v \|_2^2 + \lambda \| x \|_2

    Args:
        Lambda (float): regularization parameter.
    """
    def __init__(self, Lambda):
        super().__init__()
        self.Lambda = float(Lambda)

    def _apply(self, v):
        # Closed form solution from
        # https://archive.siam.org/books/mo25/mo25_ch6.pdf
        scale = 1.0 - self.Lambda / torch.max(torch.Tensor([self.Lambda]), torch.linalg.norm(v))
        x = torch.mul(scale, v)
        return x

class SquaredL2Regularizer(Prox):

    r"""
    Proximal operator for Squared L2 regularizer

    .. math::
        \arg \min_x \frac{1}{2} \| x - v \|_2^2 + \lambda \| x \|_2^2

    Args:
        Lambda (float): regularization parameter.
    """

    def __init__(self, Lambda):
        super().__init__()
        self.Lambda = float(Lambda)

    def _apply(self, v):
        x =  torch.div(v, 1 + 2*self.Lambda)
        return x

class BoxConstraint(Prox):

    r"""
    Proximal operator for Box Constraint

    .. math::
        \arg \min_{x} \in [lower, upper]} \frac{1}{2} \| x - v \|_2^2

    Args:
        Lambda (float): regularization parameter.
        lower (scalar): minimum value
        upper (scalar): maximum value
    """

    def __init__(self, Lambda, lower, upper):
        super().__init__()
        self.l = lower
        self.u = upper
        self.Lambda = float(Lambda)

    def _apply(self, v):
        x = torch.clamp(v, self.l, self.u)
        return x

