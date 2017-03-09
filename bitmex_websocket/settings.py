from __future__ import absolute_import
import os
import sys
from bitmex_websocket.utils.dotdict import dotdict
import bitmex_websocket._settings_base as baseSettings
from imp import reload


def import_path(fullpath):
    """
    Import a file with full path specification. Allows one to
    import from anywhere, something __import__ does not do.
    """
    path, filename = os.path.split(fullpath)
    filename, ext = os.path.splitext(filename)
    sys.path.insert(0, path)
    module = __import__(filename)
    reload(module)  # Might be out of date
    del sys.path[0]
    return module

# Assemble settings.
settings = {}
settings.update(vars(baseSettings))

if os.environ.get('RUN_ENV') != 'test':
    userSettings = import_path(os.path.join('..', 'settings'))
    settings.update(vars(userSettings))

# Main export
settings = dotdict(settings)
