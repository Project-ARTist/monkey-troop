from typing import Dict, List, Union, Callable


__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


class IResultAnalyzer(object):

    FAIL = 'fail'
    OUT = 'out'
    SUCCESS = 'success'

    def is_success(self, summary_row: Dict[str, str]) -> bool:
        raise AssertionError('ResultAnalyzer: "is_success" not yet implemented!')

    def is_out(self, summary_row: Dict[str, str]) -> bool:
        raise AssertionError('ResultAnalyzer: "is_out" not yet implemented!')

    def is_failure(self, summary_row: Dict[str, str]) -> bool:
        raise AssertionError('ResultAnalyzer: "is_failure" not yet implemented!')

    def interpret(self, summary_row: Dict[str, str]) -> [str, None]:
        """
        Returns the interpretation of a summary row/
        :param summary_row: 
        :return: FAIL, OUT or SUCCESS for well-formed rows, None for headlines, comments and the like
        """
        raise AssertionError('ResultAnalyzer: "interpret" not yet implemented!')

    def get_all(self) -> List[Dict[str, str]]:
        """
        Returns all summary rows in a tuple
        :return: (tested, outs, failures, successes)  
        """
        raise AssertionError('ResultAnalyzer: "get_all" not yet implemented!')

    def get_tested(self) -> List[Dict[str, str]]:
        """z
        :return: all summary rows
        """
        raise AssertionError('ResultAnalyzer: "get_tested" not yet implemented!')

    def get_outs(self, csv_rows: Union[List[Dict[str, str]],None]=None) -> List[Dict[str, str]]:
        """
        Returns summary rows from apps that did not meet the assumptions
        :param csv_rows: 
        :return: list of all rows with a failed ASSUMPTION subtask
        """
        raise AssertionError('ResultAnalyzer: "get_outs" not yet implemented!')

    def get_fails(self, csv_rows: Union[List[Dict[str, str]], None]=None) -> List[Dict[str, str]]:
        """
        Returns summary rows from apps that failed
        :param csv_rows: 
        :return: list of all rows with a failed REQUIRED subtask
        """
        raise AssertionError('ResultAnalyzer: "get_fails" not yet implemented!')

    def get_successes(self, csv_rows: Union[List[Dict[str, str]], None]=None) -> List[Dict[str, str]]:
        """
        Returns summary rows from apps that successfully passed the evaluation. 
        :param csv_rows: 
        :return: list of all rows where all non-DONTCARE subtasks succeeded
        """
        raise AssertionError('ResultAnalyzer: "get_successes" not yet implemented!')

    def get_command_api(self) -> Dict[str, Callable[[], None]]:
        """
        Defines the public command API of this analyzer. 
        :return: a mapping from command strings to the corresponding api methods
        """
        raise AssertionError('ResultAnalyzer: "get_command_api" not yet implemented!')