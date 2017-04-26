from typing import Union

from model.IAppRepository import IAppRepository
from repositories.FileBackedRepository import FileBackedRepository
from repositories.gplay.MonkeyLoader import MonkeyLoader

from os import path, rename


__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


class GPlayDownloaderRepository(FileBackedRepository):
    """
    App repository that downloads and cached apk files from the Google Play Store.
    """

    downloader = None

    def __init__(self):
        super().__init__()
        self.downloader = MonkeyLoader()

    # TODO detailed errors. Return values vs exceptions
    def get_app(self, package_name: str) -> IAppRepository.Path:
        """
        Returns either a cached or a freshly downloaded apk file.
        :param package_name: the package to return
        :return: apk path or None
        """
        filepath = super().get_app(package_name)
        if filepath is not None:
            return filepath

        # apk not yet available -> download it from Google Play
        apk_path = self.downloader.download_if_not_exist(package_name, self.root)

        if not path.exists(apk_path):
            return None

        intended_path = self.get_file_path(self.package_to_file(package_name, None))

        # we know that path to file matches, so only filename might be different
        if apk_path != intended_path:
            rename(apk_path, intended_path)
        return intended_path

