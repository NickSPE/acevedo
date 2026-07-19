import os

os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing-only')
os.environ.setdefault('DB_NAME', 'test_db')
os.environ.setdefault('DB_USER', 'test_user')
os.environ.setdefault('DB_PASSWORD', 'test_pass')
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')

from . import settings

for key, value in settings.__dict__.items():
    if not key.startswith('__'):
        globals()[key] = value

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

SECRET_KEY = 'test-secret-key-for-testing-only'
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
