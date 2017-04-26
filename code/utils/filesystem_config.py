from os import makedirs
from os.path import realpath, dirname, join, isabs, exists

from utils.singleton import Singleton


__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


class FilesystemConfig(object, metaclass=Singleton):

    # defaults for relative paths
    DEFAULT_APK = 'apk'
    DEFAULT_OUT = 'out'
    DEFAULT_LISTS = 'lists'
    DEFAULT_REPORT = 'reports'
    DEFAULT_RESULT = 'results'

    # defaults for absolute paths
    DEFAULT_TMP = '/tmp'

    def __init__(self, apk: str=DEFAULT_APK, out: str=DEFAULT_OUT, tmp: str=DEFAULT_TMP, lists: str=DEFAULT_LISTS)\
            -> None:
        """
        Initializes the singleton instance with either provided or default values. 
        Note that due to the singleton nature, this method is only invoked exactly once and for subsequent
        object 'generations', the original instance is returned.
        
        This in particular means that the first invocation of FilesystemConfig() triggers the __init__ function
        while subsequent calls silently return the singleton object, ignoring all the provided arguments.
        
        :param apk: dir for apk storage
        :param out: dir for outputs, such as reports and results
        :param tmp: dir for temporary files
        :param lists: search dir for package list files
        """

        # root/code/utils/filesystem_config.py
        filepath = realpath(__file__)

        # root/code/utils/filesystem_config.py -> root
        self.root = dirname(dirname(dirname(filepath)))

        self.apk = self.__prepare_path(apk)
        self.out = self.__prepare_path(out)
        self.tmp = self.__prepare_path(tmp)
        self.lists = self.__prepare_path(lists)

        self.report = join(self.out, FilesystemConfig.DEFAULT_REPORT)
        self.result = join(self.out, FilesystemConfig.DEFAULT_RESULT)

    def __prepare_path(self, path: str) -> str:
        assert path is not None
        if not isabs(path):
            path = join(self.root, path)
            path = realpath(path)

        if not exists(path):
            makedirs(path, exist_ok=True)

        return path

    def get_root_dir(self) -> str:
        return self.root

    def get_apk_dir(self) -> str:
        return self.apk

    def get_out_dir(self) -> str:
        return self.out

    def get_report_dir(self) -> str:
        return self.report

    def get_result_dir(self) -> str:
        return self.result

    def get_tmp_dir(self) -> str:
        return self.tmp

    def get_lists_dir(self) -> str:
        return self.lists


