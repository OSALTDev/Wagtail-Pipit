#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Write local settings here, or override base settings
"""
from __future__ import absolute_import, unicode_literals

from typing import List, Set, Dict, Tuple, Optional

from pipit.settings.base import *  # NOQA

VS_CODE_REMOTE_DEBUG = get_env_bool("VS_CODE_REMOTE_DEBUG", default=False)
DEBUG = True
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG

DEBUG_TOOLBAR_PATCH_SETTINGS = False

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Add django debug toolbar when using local version
INSTALLED_APPS += ["debug_toolbar", "sslserver"]

MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

# Allow weak local passwords
AUTH_PASSWORD_VALIDATORS: List = []

INTERNAL_IPS = get_env("INTERNAL_IPS", default="").split(",")


# Allow django-debug-bar under docker
def show_toolbar(request):
    return True


DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": "pipit.settings.local.show_toolbar"}
