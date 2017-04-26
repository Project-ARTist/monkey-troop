from typing import Union

from model.IAppRepository import IAppRepository

from os import path

from utils.filesystem_config import FilesystemConfig


__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


class FileBackedRepository(IAppRepository):
    """
    Simple implementation of an AppRepository that manages a directory of apk files.
    Version-awareness is not supported.
    """

    def __init__(self):
        self.root = FilesystemConfig().get_apk_dir()

    def get_app(self, package_name: str) -> IAppRepository.Path:
        """
        :param package_name
        :return: path to apk file or None
        """
        filename = FileBackedRepository.package_to_file(package_name, None)
        filepath = self.get_file_path(filename)
        if not path.exists(filepath):
            return None
        return filepath

    def get_app_version(self, package_name: str, version: str) -> IAppRepository.Path:
        """
        :param package_name
        :param version
        :return: path to apk file or None
        """

        # TODO log fallback
        return self.get_app(package_name)

    @staticmethod
    def package_to_file(package_name: str, version: Union[str, None]) -> IAppRepository.Path:
        """
        Maps a package name and version to a filename for lookup.

        :param package_name
        :param version
        :return: filename
        """

        # this implementation is not version-aware
        return package_name

    def get_file_path(self, filename: str) -> IAppRepository.Path:
        """
        :param filename
        :return: full path to filename
        """

        return path.join(self.root, filename + ".apk")
