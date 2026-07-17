from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

SECRET_KEY = 'test-secret-key-for-testing-only'
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
