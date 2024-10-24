import functools
from typing import Optional, Type

import flax.linen as nn
import jax.numpy as jnp
from tensorflow_probability.substrates import jax as tfp

tfd = tfp.distributions

from supe.distributions.tanh_transformed import TanhTransformedDistribution


class Normal(nn.Module):
    base_cls: Type[nn.Module]
    action_dim: int
    log_std_min: Optional[float] = -20
    log_std_max: Optional[float] = 2
    state_dependent_std: bool = True
    squash_tanh: bool = False
    default_init: nn.initializers.Initializer = nn.initializers.xavier_uniform

    @nn.compact
    def __call__(self, inputs, temperature=1.0, *args, **kwargs) -> tfd.Distribution:
        x = self.base_cls()(inputs, *args, **kwargs)

        means = nn.Dense(
            self.action_dim, kernel_init=self.default_init(), name="OutputDenseMean"
        )(x)

        if self.state_dependent_std:
            log_stds = nn.Dense(
                self.action_dim,
                kernel_init=self.default_init(),
                name="OutputDenseLogStd",
            )(x)
        else:
            log_stds = self.param(
                "OutpuLogStd", nn.initializers.zeros, (self.action_dim,), jnp.float32
            )

        log_stds = jnp.clip(log_stds, self.log_std_min, self.log_std_max)

        distribution = tfd.MultivariateNormalDiag(
            loc=means, scale_diag=jnp.exp(log_stds) * temperature
        )

        if self.squash_tanh:
            return TanhTransformedDistribution(distribution)
        else:
            return distribution


TanhNormal = functools.partial(Normal, squash_tanh=True)