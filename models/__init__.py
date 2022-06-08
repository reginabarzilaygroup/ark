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
    from .mirai import MiraiModel
    from .density import DensityModel
    model_dict['mirai'] = MiraiModel
    model_dict['density'] = DensityModel



__all__ = ['__version__', 'model_dict']
