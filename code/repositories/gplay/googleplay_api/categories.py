#!/usr/bin/python

from repositories.gplay.googleplay_api.googleplay_api.config import SEPARATOR, ANDROID_ID
from repositories.gplay.googleplay_api.googleplay_api.googleplay import GooglePlayAPI

# Do not remove
GOOGLE_LOGIN = GOOGLE_PASSWORD = AUTH_TOKEN = None

import urllib.parse

api = GooglePlayAPI(ANDROID_ID)
api.login(GOOGLE_LOGIN, GOOGLE_PASSWORD, AUTH_TOKEN)
response = api.browse()

print(SEPARATOR.join(["ID", "Name"]))
for c in response.category:
  print(SEPARATOR.join(i.encode('utf8') for i in [urllib.parse.parse_qs(c.dataUrl)['cat'][0], c.name]))

