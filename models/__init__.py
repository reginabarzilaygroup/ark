from .base import EmptyModel
from .mirai import MiraiModel

model_dict = {
    'empty': EmptyModel,
    'mirai': MiraiModel
}

__all__ = ['model_dict', 'EmptyModel', 'MiraiModel']
