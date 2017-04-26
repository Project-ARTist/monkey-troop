# -*- coding: utf-8 -*-
import os

from repositories.gplay.googleplay_api.googleplay_api.googleplay import GooglePlayAPI
from repositories.gplay.googleplay_api.googleplay_api.helpers import sizeof_fmt

__author__ = 'Sebastian Weisgerber <weisgerber@cs.uni-saarland.de>'

# Do not remove
GOOGLE_LOGIN = GOOGLE_PASSWORD = AUTH_TOKEN = None
from repositories.gplay.googleplay_api.googleplay_api.config import *


class MonkeyLoaderConfig:
    RESERVED_DISK_SPACE = int(5000000000)

    DOWNLOADER_BASE_FOLDER = 'repositories/gplay'

    APK_FILE_ENDING = '.apk'


class GooglePlayApi:
    def __init__(self):
        print('> Starting GooglePlayApi')
        pass

    def download(self, package_name: str) -> str:
        print('> downloading: ' + package_name + ' [GooglePlayApi]')

        global ANDROID_ID, GOOGLE_LOGIN, GOOGLE_PASSWORD, AUTH_TOKEN

        apk_filename = get_apk_filename(package_name)

        api_handle = GooglePlayAPI(ANDROID_ID)
        api_handle.login(GOOGLE_LOGIN, GOOGLE_PASSWORD, AUTH_TOKEN)

        # Get the version code and the offer type from the app details
        app_details = api_handle.details(package_name)
        app_details_docv2 = app_details.docV2
        app_version_code = app_details_docv2.details.appDetails.versionCode
        app_offer_type = app_details_docv2.offer[0].offerType

        # Download
        print("Downloading %s..." % sizeof_fmt(app_details_docv2.details.appDetails.installationSize), end=' ')

        apk_download_data = api_handle.download(package_name, app_version_code, app_offer_type)

        self.save_downloaded_apk(apk_download_data, apk_filename)

        print('> downloading: ' + package_name + ' [GooglePlayApi] DONE')
        return apk_filename

    def save_downloaded_apk(self, apk_download_data, apk_filename):
        opened_apk_file = open(apk_filename, "wb")
        opened_apk_file.write(apk_download_data)
        opened_apk_file.close()


def get_apk_filename(package_name: str) -> str:
    return str(package_name + MonkeyLoaderConfig.APK_FILE_ENDING)


class MonkeyLoader:
    """
    Facade class for APK download from Google's Play Store

    Using the downloaders:
    - https://github.com/egirault/googleplay-api (default)

    """

    downloaders = list()

    def __init__(self):
        self.downloaders.append(GooglePlayApi())

    def __str__(self):
        to_string = "class MonkeyLoader"
        return to_string

    def download_if_not_exist(self, package_name: str, apk_folder: str) -> str:
        """
        Downloads the package from one of the configured downloaders.
        Check if the application is already in the APK folder.

        :param package_name:
        :param apk_folder:
        :return:
        """
        apk_name = get_apk_filename(package_name)
        path_to_apk = os.path.join(apk_folder, apk_name)
        if (os.path.exists(path_to_apk)):
            print('File exists, Not Downloading: ' + path_to_apk)
            return path_to_apk
        else:
            self.download(package_name, path_to_apk)
            return path_to_apk

    def download(self, package_name: str, path_to_apk: str=None) -> str:
        """
        Downloads the package from one of the configured downloaders.
        Does not check if the application is already in the APK folder.

        :param package_name:
        :param path_to_apk:
        :return:
        """

        if (path_to_apk == None):
            path_to_apk = os.getcwd() + '/' + get_apk_filename(package_name)

        for downloader in self.downloaders:
            apk_file = downloader.download(package_name)
            if (apk_file != None and path_to_apk != None):
                try:
                    os.rename(apk_file, path_to_apk)
                    break
                except OSError:
                    print('>> Could NOT move APK to: ' + path_to_apk)
            if (os.path.exists(apk_file)):
                print('APK Found: ' + apk_file)
                break

        return path_to_apk
