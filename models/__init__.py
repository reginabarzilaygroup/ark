from version import __version__
from .base import EmptyModel
from .mirai import MiraiModel

model_dict = {
    'empty': EmptyModel,
    'mirai': MiraiModel
}
