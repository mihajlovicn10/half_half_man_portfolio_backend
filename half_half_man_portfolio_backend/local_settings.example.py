# Copy this file to local_settings.py and fill in your values.
# local_settings.py is in .gitignore and will not be committed.

SECRET_KEY = 'your-secret-key-here'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'half_half_man_portfolio_backend',
        'USER': 'postgres',
        'PASSWORD': 'your-password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
