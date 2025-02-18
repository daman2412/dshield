import configparser
import json
import logging.config
import os

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, registry

__all_ = [
    # DATABASE SETTINGS
    'DATABASE_DEBUG_LOGGING',
    'DATABASE_ENGINE',
    'DATABASE_SESSION',
    'DATABASE_URL',

    # PLUGINS
    'PLUGINS',
]

config = configparser.ConfigParser()
config.read('settings.ini')

# TODO: Remvoe when everything gets rolled over
legacy_config = configparser.ConfigParser()
legacy_config.read('/etc/dshield.ini')

# APPLICATION
BASE_DIR = os.path.join(os.path.dirname(__file__))
LOCAL_IP = requests.get('https://www4.dshield.org/api/myip?json').json()['ip']
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} :: {asctime} :: <PID {process}:{processName}> :: {name} :: L:{lineno} :: {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': os.getenv('LOG_LEVEL', 'DEBUG'),
            'propagate': False,
        },
    },
}
logging.config.dictConfig(LOGGING)

# AUTH
DSHIELD_API_KEY = legacy_config.get(
    'DShield',
    'apikey',
    fallback=config.get("auth", "api_key", fallback=None)

)
DSHIELD_EMAIL = legacy_config.get(
    'DShield',
    'email',
    fallback=config.get("auth", "email", fallback=None)

)
DSHIELD_URL = config.get("auth", "url", fallback="https://www.dshield.org")
DSHIELD_USER_ID = legacy_config.get(
    'DShield',
    'userid',
    fallback=config.get("auth", "user_id", fallback=None)

)

# DATABASE SETTINGS
DATABASE_MAPPER_REGISTRY = registry()
DATABASE_BASE = DATABASE_MAPPER_REGISTRY.generate_base()
DATABASE_DEBUG_LOGGING = os.getenv('DATABASE_DEBUG_LOGGING', False)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+pysqlite:///:memory:')
DATABASE_ENGINE = create_engine(
    DATABASE_URL,
    echo=DATABASE_DEBUG_LOGGING,
    echo_pool=DATABASE_DEBUG_LOGGING,
    future=True
)
DATABASE_SESSION = Session(DATABASE_ENGINE)

# SSL certification key and certificate
PRIVATE_KEY = os.getenv('ISC_AGENT_PRIVATE_KEY_PATH', '~/dshield/etc/CA/keys/honeypot.key')
CERT_KEY = os.getenv('ISC_AGENT_CERT_KEY_PATH', '~/dshield/etc/CA/certs/honeypot.crt')

# PLUGINS
# Read from settings.ini file
PLUGINS = []
for k, v in config.items():
    protocol_dict = {}
    if not k.startswith('plugin'):
        continue
    _, protocol, name = k.split(":")
    protocol_dict['protocol'] = protocol
    protocol_dict['name'] = name
    for k1, v1 in v.items():
        v1 = json.loads(v1)
        protocol_dict[k1] = v1
    PLUGINS.append(protocol_dict)

# TODO: Temp solution to ensure at least http is started if no settings are given
if not PLUGINS:
    PLUGINS.append({"protocol": "tcp", "name": "http"})

