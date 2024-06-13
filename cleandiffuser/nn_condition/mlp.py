from typing import List

import torch
import torch.nn as nn

from cleandiffuser.utils import at_least_ndim, Mlp
from cleandiffuser.nn_condition import IdentityCondition, get_mask


class LinearCondition(IdentityCondition):
    """
    MLP condition is a simple multi-layer perceptron to process the input condition.

    Input:
        - condition: (b, ..., in_dim)
        - mask :     (b, ) or None, None means no mask
        - dropout:   float, probability of condition dropout

    Output:
        - condition: (b, ..., out_dim)
    """

    def __init__(self, in_dim: int, out_dim: int, dropout: float = 0.25):
        super().__init__(dropout)
        self.affine = nn.Linear(in_dim, out_dim)

    def forward(self, condition: torch.Tensor, mask: torch.Tensor = None):
        mask = at_least_ndim(get_mask(
            mask, (condition.shape[0],), self.dropout, self.training, condition.device), condition.dim())
        return self.affine(condition) * mask


class MLPCondition(IdentityCondition):
    """
    MLP condition is a simple multi-layer perceptron to process the input condition.

    Input:
        - condition: (b, *cond_in_shape)
        - mask :     (b, ) or None, None means no mask

    Output:
        - condition: (b, *cond_out_shape)
    """

    def __init__(self, in_dim: int, out_dim: int, hidden_dims: List[int], 
                 act=nn.LeakyReLU(), dropout: float = 0.25):
        super().__init__(dropout)
        hidden_dims = [hidden_dims, ] if isinstance(hidden_dims, int) else hidden_dims
        self.mlp = Mlp(
            in_dim, hidden_dims, out_dim, act)

    def forward(self, condition: torch.Tensor, mask: torch.Tensor = None):
        mask = at_least_ndim(get_mask(
            mask, (condition.shape[0],), self.dropout, self.training, condition.device), condition.dim())
        return self.mlp(condition) * mask


class MLPSieveObsCondition(IdentityCondition):
    def __init__(self, o_dim: int, emb_dim: int = 128, hidden_dim: int = 512, dropout: float = 0.25):
        super().__init__(dropout)
        hidden_dims = [hidden_dim, ]
        self.mlp = Mlp(
            o_dim, hidden_dims, emb_dim, nn.LeakyReLU())

    def forward(self, obs: torch.Tensor, mask: torch.Tensor = None):
        mask = at_least_ndim(get_mask(
            mask, (obs.shape[0],), self.dropout, self.training, obs.device), 2)
        embs = self.mlp(obs)  # (b, history_len, emb_dim)
        return torch.flatten(embs, 1) * mask
