# reads apps from an input list
# returns: (map: package->list(category), unique app count)
from os.path import join
from typing import List, Dict, Tuple

from utils.filesystem_config import FilesystemConfig

__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'

def read_apps(packages_file: str) -> Tuple[Dict[str, List[str]], int]:
    """
    Helper methods to read package names from list files.
    :param packages_file: the name of the list file. Search path is the current list directory. 
    :return: a tuple of the dictionary mapping from package names to categories, and the amount of unique apps
    """

    # realtive to search dir
    lists_dir = FilesystemConfig().get_lists_dir()
    packages_path = join(lists_dir, packages_file)

    # mapping: app -> list(category)
    app_dictionary = dict()
    # mock category for apps without a real category
    current_category = "<NO_CATEGORY>"
    # number of unique apps
    unique_count = 0
    with open(packages_path) as file:
        for line in file:
            stripped = str(line).strip()
            # drop lines that only contain whitespace and/or line breaks
            if not stripped:
                continue
            if stripped.startswith('~'):
                continue
            if stripped.startswith('#'):
                current_category = stripped.replace('#', '').strip()
            else:
                package_name = stripped

                # app not encountered yet
                if not package_name in app_dictionary.keys():
                    unique_count += 1
                    app_dictionary[package_name] = list()

                app_dictionary[package_name].append(current_category)
    return app_dictionary, unique_count
