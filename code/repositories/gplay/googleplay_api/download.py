#!/usr/bin/python

from repositories.gplay.googleplay_api.googleplay_api.config import ANDROID_ID
from repositories.gplay.googleplay_api.googleplay_api.googleplay import GooglePlayAPI
from repositories.gplay.googleplay_api.googleplay_api.helpers import sizeof_fmt

# Do not remove
GOOGLE_LOGIN = GOOGLE_PASSWORD = AUTH_TOKEN = None

import sys

if (len(sys.argv) < 2):
    print("Usage: %s packagename [filename]")
    print("Download an app.")
    print("If filename is not present, will write to packagename.apk.")
    sys.exit(0)

packagename = sys.argv[1]

if (len(sys.argv) == 3):
    filename = sys.argv[2]
else:
    filename = packagename + ".apk"

# Connect
api = GooglePlayAPI(ANDROID_ID)
api.login(GOOGLE_LOGIN, GOOGLE_PASSWORD, AUTH_TOKEN)

# Get the version code and the offer type from the app details
m = api.details(packagename)
doc = m.docV2
vc = doc.details.appDetails.versionCode
ot = doc.offer[0].offerType

# Download
print("Downloading %s..." % sizeof_fmt(doc.details.appDetails.installationSize), end=' ')
data = api.download(packagename, vc, ot)
open(filename, "wb").write(data)
print("Done")

