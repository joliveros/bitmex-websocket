from __future__ import absolute_import
import os
import sys
from bitmex_websocket.utils.dotdict import dotdict
import bitmex_websocket._settings_base as baseSettings
from imp import reload


def import_path(fullpath):
    '''
    Import a file with full path specification. Allows one to
    import from anywhere, something __import__ does not do.
    '''
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
BITMEX_API_KEY = os.environ.get('BITMEX_API_KEY')
if BITMEX_API_KEY:
    settings['BITMEX_API_KEY'] = BITMEX_API_KEY
print("BITMEX_API_KEY: %s" % (BITMEX_API_KEY))
BITMEX_API_SECRET = os.environ.get('BITMEX_API_SECRET')
if BITMEX_API_SECRET:
    settings['BITMEX_API_SECRET'] = BITMEX_API_SECRET

# Main export
settings = dotdict(settings)
