from version import __version__

# TODO: The intended behavior is to be able to import models directly, i.e. `import models.EmptyModel`. This cannot be
#   done without needing to install every model package. Possible solution is to restructure every model into its own
#   module. Another (current) solution is to check if the package is installed before import. See `set_model()` in
#   api/app.py.

import importlib.util

from .base import EmptyModel

model_dict = {
    'empty': EmptyModel
}

if importlib.util.find_spec('onconet') is not None:
    from .mirai import MiraiModelWrapper
    from .density import DensityModel
    model_dict['mirai'] = MiraiModelWrapper
    model_dict['density'] = DensityModel

if importlib.util.find_spec('sybil') is not None:
    from .sybil import SybilModel
    model_dict['sybil'] = SybilModel

__all__ = ['__version__', 'model_dict']
