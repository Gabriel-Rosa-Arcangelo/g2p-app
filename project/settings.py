from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-nde*ndrnzj5=w4d0qy0=59g8m64328cnd0m4g041^q5zvz_k-%'

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '192.168.2.6.nip.io']


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'channels',
    'captcha',
    'project',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

RECAPTCHA = 'recaptcha.fields.ReCaptchaField'

RECAPTCHA_PUBLIC_KEY = '6LfQ81QpAAAAACi9JhuTsqA-Oe2__8RD2v05AZuH'
RECAPTCHA_PRIVATE_KEY = '6LfQ81QpAAAAAHAJRr-9etoCaZmqWNXegB80YXq5'
SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']


SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'project.urls'

#FIREFOX WEBDRIVER_PATH
WEBDRIVER_PATH = os.path.join(BASE_DIR, 'geckodriver')
#print(WEBDRIVER_PATH)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-GB'

TIME_ZONE = 'Europe/London'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'

LOGIN_REDIRECT_URL = '/accounts/home/'
LOGOUT_REDIRECT_URL = '/accounts/login'

ACCOUNT_SIGNUP_REDIRECT_URL = '/accounts/profile_picture'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'eurofinsbrasil20@gmail.com'
EMAIL_HOST_PASSWORD = 'uhhv iihk hgbv bjme'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

ACCOUNT_EMAIL_VERIFICATION = "optional"
EMAIL_VERIFICATION = 'mandatory'

SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

#email : eurofinscatg@gmail.com
#senha : eurofinscatg2024

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
