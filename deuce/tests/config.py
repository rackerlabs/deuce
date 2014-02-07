# Server Specific Configurations
server = {
    'port': '8080',
    'host': '0.0.0.0'
}

# Pecan Application Configurations
app = {
    'root': 'deuce.controllers.root.RootController',
    'modules': ['deuce'],
    'static_root': '%(confdir)s/../../public',
    'template_path': '%(confdir)s/../../deuce/templates',
    'debug': True,
    'errors': {
        404: '/error/404',
        '__force_dict__': True
    }
}

logging = {
    'loggers': {
        'root': {'level': 'INFO', 'handlers': ['console']},
        'deuce': {'level': 'DEBUG', 'handlers': ['console']},
        'py.warnings': {'handlers': ['console']},
        '__force_dict__': True
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'formatters': {
        'simple': {
            'format': ('%(asctime)s %(levelname)-5.5s [%(name)s]'
                       '[%(threadName)s] %(message)s')
        }
    }
}

import os

if not os.path.exists('/tmp/block_storage'):
    os.mkdir('/tmp/block_storage')

block_storage_driver = {
    'driver': 'deuce.drivers.storage.blocks.disk.DiskStorageDriver',
    'options': {
        'path': '/tmp/block_storage'
    }
}

metadata_driver = {
    'driver': 'deuce.metadata.driver.SqliteStorageDriver',
    'options': {
        'path': '/tmp/vaultmeta.db'
    }
}
