import logging
import os
import alog

################################################################################
# Connection/Auth
################################################################################

# API URL.
BASE_URL = "https://www.bitmex.com/api/v1/"

# The BitMEX API requires permanent API keys. Go to
# https://testnet.bitmex.com/api/apiKeys to fill these out.
BITMEX_API_KEY = os.environ.get('BITMEX_API_KEY')
BITMEX_API_SECRET = os.environ.get('BITMEX_API_SECRET')

LOG_LEVEL = os.environ.get('LOG_LEVEL')

if LOG_LEVEL is None:
    LOG_LEVEL = logging.INFO

LOG_LEVEL = logging.getLevelName(LOG_LEVEL)

alog.debug(LOG_LEVEL)

alog.set_level(LOG_LEVEL)
