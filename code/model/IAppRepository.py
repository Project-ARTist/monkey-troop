from typing import Union


__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


class IAppRepository(object):

    # change type in case another type is used to represent paths in this class
    Path = Union[str, None]

    def get_app(self, package_name: str) -> Path:
        raise AssertionError('IAppRepository: get_app not implemented')

    def get_app_version(self, package_name: str, version: str) -> Path:
        raise AssertionError('IAppRepository: get_app_version not implemented')
