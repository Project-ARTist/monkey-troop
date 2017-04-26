from typing import List

from model.ITask import ITask

__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


class Task(ITask):
    def __init__(self, package_name: str, categories: List[str]):
        self.package = package_name
        self.categories = categories

    def get_categories(self) -> List[str]:
        return self.categories

    def get_package(self) -> str:
        return self.package
