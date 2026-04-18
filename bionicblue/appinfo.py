"""General info for the app, including versioning."""

### standard library import
from collections import namedtuple



TITLE = "Bionic Blue"

ABBREVIATED_TITLE = "BB"

ORG_DIR_NAME = 'IndieSmiths'
APP_DIR_NAME = 'bionicblue'

### versioning

# release level meaning:
#
# '' (empty string) -> stable release
# 'a1', 'a2', etc. -> alpha release
# 'b1', 'b2', etc. -> beta release
# 'rc1', 'rc2', etc. -> release candidate

AppVersion = namedtuple("AppVersion", "major minor micro release_level")

APP_VERSION = AppVersion(0, 13, 0, 'rc1')

APP_VERSION_STRING = '.'.join(map(str, APP_VERSION[:3])) + APP_VERSION[3]
