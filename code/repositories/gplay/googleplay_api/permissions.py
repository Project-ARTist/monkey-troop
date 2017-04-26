#!/usr/bin/python

# Do not remove
from repositories.gplay.googleplay_api.googleplay_api.config import ANDROID_ID
from repositories.gplay.googleplay_api.googleplay_api.googleplay import GooglePlayAPI

GOOGLE_LOGIN = GOOGLE_PASSWORD = AUTH_TOKEN = None

import sys

if (len(sys.argv) < 2):
    print("Usage: %s packagename1 [packagename2 [...]]" % sys.argv[0])
    print("Display permissions required to install the specified app(s).")
    sys.exit(0)

packagenames = sys.argv[1:]

api = GooglePlayAPI(ANDROID_ID)
api.login(GOOGLE_LOGIN, GOOGLE_PASSWORD, AUTH_TOKEN)

# Only one app
if (len(packagenames) == 1):
    response = api.details(packagenames[0])
    print("\n".join(i.encode('utf8') for i in response.docV2.details.appDetails.permission))

else: # More than one app
    response = api.bulkDetails(packagenames)

    for entry in response.entry:
        if (not not entry.ListFields()): # if the entry is not empty
            print(entry.doc.docid + ":")
            print("\n".join("    "+i.encode('utf8') for i in entry.doc.details.appDetails.permission))
            print()

