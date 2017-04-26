from typing import List


__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


class ITask(object):
    def get_package(self) -> str:
        raise AssertionError('Task: get_package not implemented')

    def get_categories(self) -> List[str]:
        raise AssertionError('Task: get_category not implemented')

