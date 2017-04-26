#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from shutil import disk_usage

from repositories.gplay.MonkeyLoader import MonkeyLoaderConfig, MonkeyLoader
import argparse


__author__ = 'Sebastian Weisgerber <weisgerber@cs.uni-saarland.de>'


def terminate_if_disk_is_full(reserved_disk_space: int = MonkeyLoaderConfig.RESERVED_DISK_SPACE) -> None:
    disk_space = disk_usage('/home')
    print ('Disk Free: ' + str(disk_space.free) + ' of (' + str(disk_space.total) + ')')
    print ('Disk Used: ' + str(disk_space.used) + ' of (' + str(disk_space.total) + ')')

    if int(disk_space.free) < int(reserved_disk_space):
        print ('Terminating Programm, /home DiskFree: ' + str(disk_space.free) + ' of (' + str(
            disk_space.total) + ')')
        print('Terminating Programm, /home DiskFree: ' + str(disk_space.free) + ' of (' + str(
            disk_space.total) + ')')
        sys.exit(1)


def terminate_if_path_does_not_exist(path: str) -> None:
    if not os.path.exists(path):
        print('Path does not exist: ' + path)
        sys.exit(1)


def setup_args():
    parser = argparse.ArgumentParser(description='Downloads an APK from the playstore, based on '
                                                 'the package name, the package uses in the store.'
                                                 'Uses gplaycli for download, ')
    parser.add_argument('apk_name',
                        metavar='<APK NAME>',
                        action='store',
                        help='PlayStore URL: "https://play.google.com/store/apps/details'
                             '?id=com.google.android.apps.maps"'
                             'APKName: "com.google.android.apps.maps"')
    parser.add_argument('-a', '--apk_folder',
                        metavar='<APK_FOLDER>',
                        action='store',
                        help='Folder where APKs should get stored, if the apk exists, nothing is '
                             'downloaded')
    parser.add_argument('-t', '--alternative',
                        action='store_true',
                        help='Use the alternative downloader: googleplay-api')
    parser.add_argument('-l', '--legacy',
                        action='store_true',
                        help='Use the legacy downloader: google_play_crawler.jar')

    return parser.parse_args()


def main(commandline_args) -> None:
    """
    Stand Alone APK downloader tool.

    Uses MonkeyLoader for downloading

    :param commandline_args:
    :return:
    """
    downloader = MonkeyLoader()

    terminate_if_disk_is_full()

    package_name = commandline_args.apk_name
    apk_folder = commandline_args.apk_folder

    if (commandline_args.apk_folder is not None):
        terminate_if_path_does_not_exist(apk_folder)
        downloader.download_if_not_exist(package_name, apk_folder)
    else:
        downloader.download(package_name)


if __name__ == "__main__":

    commandline_args = setup_args()

    main(commandline_args)
