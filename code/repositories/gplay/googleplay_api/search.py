#!/usr/bin/python

from repositories.gplay.googleplay_api.googleplay_api.config import ANDROID_ID
from repositories.gplay.googleplay_api.googleplay_api.googleplay import GooglePlayAPI
from repositories.gplay.googleplay_api.googleplay_api.helpers import print_header_line, print_result_line

# Do not remove
GOOGLE_LOGIN = GOOGLE_PASSWORD = AUTH_TOKEN = None

import sys

if (len(sys.argv) < 2):
    print("Usage: %s request [nb_results] [offset]" % sys.argv[0])
    print("Search for an app.")
    print("If request contains a space, don't forget to surround it with \"\"")
    sys.exit(0)

request = sys.argv[1]
nb_res = None
offset = None

if (len(sys.argv) >= 3):
    nb_res = int(sys.argv[2])

if (len(sys.argv) >= 4):
    offset = int(sys.argv[3])

api = GooglePlayAPI(ANDROID_ID)
api.login(GOOGLE_LOGIN, GOOGLE_PASSWORD, AUTH_TOKEN)

try:
    message = api.search(request, nb_res, offset)
except:
    print("Error: something went wrong. Maybe the nb_res you specified was too big?")
    sys.exit(1)

print_header_line()
doc = message.doc[0]
for c in doc.child:
    print_result_line(c)

