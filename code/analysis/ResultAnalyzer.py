from os import path
from csv import DictReader
from typing import List, Dict, Union, Callable, Tuple

from ReportWriter import ReportWriter
from model.IEvaluator import IEvaluator
from model.IResultAnalyzer import IResultAnalyzer
from utils.filesystem_config import FilesystemConfig

__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


class ResultAnalyzer(IResultAnalyzer):
    RESULTS_SUMMARY = 'summary.csv'

    CMD_SUMMARY = 'summary'
    CMD_SUCC = 'successes'
    CMD_FAILS = 'fails'
    CMD_OUTS = 'outs'
    CMD_CHECK = 'check'

    LOG_TAG = "ResultAnalyzer"

    def __init__(self, evaluator: IEvaluator, fixed_fields_front: List[str], fixed_fields_back: List[str]):

        self.fsm = FilesystemConfig()

        self.summary_file = path.join(self.fsm.get_result_dir(),
                                      evaluator.get_eval_id() + "_" + ResultAnalyzer.RESULTS_SUMMARY)
        print(self.summary_file)

        self.evaluator = evaluator

        # caching
        self.subtasks = evaluator.get_subtask_ids_ordered()
        self.interpretations = evaluator.get_subtask_interpretation()
        self.required_subtasks = [subtask for subtask in self.subtasks
                                  if self.interpretations[subtask] == IEvaluator.REQUIRED]
        self.assumed_subtasks = [subtask for subtask in self.subtasks
                                 if self.interpretations[subtask] == IEvaluator.ASSUMPTION]
        self.dontcare_subtasks = [subtask for subtask in self.subtasks
                                  if self.interpretations[subtask] == IEvaluator.DONTCARE]

        self.fixed_fields_front = fixed_fields_front
        self.fixed_fields_back = fixed_fields_back
        self.ordered_fieldnames = self.fixed_fields_front + self.subtasks + self.fixed_fields_back

    ### interface

    def is_success(self, summary_row: Dict[str, str]) -> bool:
        return self.interpret(summary_row) == IResultAnalyzer.SUCCESS

    def is_out(self, summary_row: Dict[str, str]) -> bool:
        return self.interpret(summary_row) == IResultAnalyzer.OUT

    def is_failure(self, summary_row: Dict[str, str]) -> bool:
        return self.interpret(summary_row) == IResultAnalyzer.FAIL

    def interpret(self, summary_row: Dict[str, str]) -> Union[str, None]:

        for subtask in self.subtasks:

            # sanity check
            if subtask not in self.interpretations.keys():
                self.log('Error! No interpretation available for subtask ' + subtask)
                exit(-1)

            interpretation = self.interpretations[subtask]
            subtask_result = summary_row[subtask]
            if not self.is_app_row(summary_row):
                # invalid
                return None
            subtask_success = (subtask_result == 'True')
            # sanity check
            if not subtask_success and subtask_result != 'False':
                self.log('Unexpected value for subtask ' + subtask + ': ' + subtask_result)
                self.log(str(summary_row))
                exit(-1)

            if interpretation == IEvaluator.DONTCARE:
                continue
            if not subtask_success:
                if interpretation == IEvaluator.REQUIRED:
                    # count as fail
                    return IResultAnalyzer.FAIL
                elif interpretation == IEvaluator.ASSUMPTION:
                    # remove from counting
                    return IResultAnalyzer.OUT
                else:
                    self.log('Error! Unexpected interpretation for subtask ' + subtask + ': ' + str(interpretation))
                    exit(-1)
        # no fails (that we care about) occurred
        return IResultAnalyzer.SUCCESS

    #
    def get_all(self) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
        # if this method ever gets too slow because the data is too big: implement in one interation
        tested = self.get_tested()
        outs = self.get_outs(csv_rows=tested)
        fails = self.get_fails(csv_rows=tested)
        successes = self.get_successes(csv_rows=tested)
        return tested, outs, fails, successes

    def get_tested(self) -> List[Dict[str, str]]:
        # filter out non-data rows (comments, headlines, ...)
        return self.find_matching_entries(lambda row: self.interpret(row) is not None)

    def get_outs(self, csv_rows: Union[List[Dict[str, str]], None]=None) -> List[Dict[str, str]]:
        if not csv_rows:
            csv_rows = self.get_app_rows()
        return self.find_matching_entries(lambda x: self.is_out(x), csv_rows=csv_rows)

    def get_fails(self, csv_rows: Union[List[Dict[str, str]]]=None) -> List[Dict[str, str]]:
        if not csv_rows:
            csv_rows = self.get_app_rows()
        return self.find_matching_entries(lambda x: self.is_failure(x), csv_rows=csv_rows)

    # returns summary rows from apps that succeeded
    def get_successes(self, csv_rows: Union[List[Dict[str, str]], None]=None) -> List[Dict[str, str]]:
        if not csv_rows:
            csv_rows = self.get_app_rows()
        return self.find_matching_entries(lambda x: self.is_success(x), csv_rows=csv_rows)

    def get_command_api(self) -> Dict[str, Callable[[], None]]:
        return {
            ResultAnalyzer.CMD_SUMMARY: self.api_summary,
            ResultAnalyzer.CMD_CHECK: self.api_check,
            ResultAnalyzer.CMD_SUCC: self.get_successes,
            ResultAnalyzer.CMD_FAILS: self.api_failures,
            ResultAnalyzer.CMD_OUTS: self.get_outs
        }

    ### API implementation ###

    def api_summary(self) -> None:
        """
        API method to print a summary of the current evaluation results.
        """

        # category -> (tests, outs, fails, successes)
        results = dict()

        # use list since tuples do not support item assignment
        overall = [0, 0, 0, 0]

        for row in self.get_app_rows():
            # app = row[ReportWriter.KEY_PKG]
            categories = row[ReportWriter.KEY_CATS].strip().split(ReportWriter.CSV_IN_CELL_SEPARATOR)
            for cat in categories:
                if cat not in results.keys():
                    # use list since tuples do not support item assignment
                    results[cat] = [0, 0, 0, 0]

                # increase number of tests
                results[cat][0] += 1
                overall[0] += 1

                # None not possible since we iterate over checked app rows
                interpretation = self.interpret(row)
                if interpretation == IResultAnalyzer.OUT:
                    results[cat][1] += 1
                    overall[1] += 1
                    continue
                if interpretation == IResultAnalyzer.FAIL:
                    results[cat][2] += 1
                    overall[2] += 1
                    continue
                if interpretation == IResultAnalyzer.SUCCESS:
                    results[cat][3] += 1
                    overall[3] += 1
                    continue
                raise AssertionError('Unknown interpretation: ' + interpretation)

        for cat in sorted(results.keys()):
            tests, outs, fails, successes = results[cat]
            included = tests - outs
            percentage = (successes / included) * 100 if included > 0 else 0
            self.log('Category ' + cat + ': Tested: ' + str(tests) + ', removed: ' + str(outs)
                     + ', success: ' + str(successes) + '/' + str(included) + ' = ' + str(percentage) + '%')

        overall_tests = overall[0]
        overall_outs = overall[1]
        overall_successes = overall[3]
        overall_included = overall_tests - overall_outs
        overall_percentage = (overall_successes / overall_included) * 100 if overall_included > 0 else 0
        self.log('Overall: Tested: ' + str(overall_tests) + ', removed: ' + str(overall_outs)
                 + ', success: ' + str(overall_successes) + '/' + str(overall_included) + ' = ' + str(
            overall_percentage) + '%')

    def api_successes(self, dump: bool=False) -> None:
        """
        API method to display all apps that were successfully tested. 
        """
        successes = self.get_successes()
        if dump:
            for row in successes:
                self.log(row[ReportWriter.KEY_PKG])

        self.log('Found ' + str(len(successes)) + ' successes.')

    def api_failures(self, dump: bool=False) -> None:
        """
        API method to display all apps that were successfully tested. 
        """
        failures = self.get_fails()
        if dump:
            for row in failures:
                self.log(row[ReportWriter.KEY_PKG])

        self.log('Found ' + str(len(failures)) + ' failures.')

    def api_outs(self, dump: bool=False) -> None:
        """
        API method to display all apps that were removed from the evaluation because they failed for reasons beyond our 
        control. 
        """
        outs = self.get_outs()
        if dump:
            for row in outs:
                self.log(row[ReportWriter.KEY_PKG])

        self.log('Found ' + str(len(outs)) + ' outs.')

    # API for command CMD_CHECK
    # check results for inconsistencies
    def api_check(self) -> None:
        """
        API method to check the current evaluation resilts for inconsistencies, such as duplicate app packages.
        """

        row_dict = self.get_app_rows()

        # count occurences of package names
        packages_counter = dict()  # mapping: package -> occurence
        for row in row_dict:

            for fieldname in row.keys():
                # check for unknown fieldname
                if not fieldname in self.fixed_fields_front + self.subtasks + self.fixed_fields_back:
                    self.log('Warning: Found unknown field: ' + fieldname)

            # remove header lines and comments
            if row[ReportWriter.KEY_TIMESTAMP] is None or row[ReportWriter.KEY_TIMESTAMP] == ReportWriter.KEY_TIMESTAMP:
                # self.log('Skipping entry: ' + str(row))
                continue
            package_name = row[ReportWriter.KEY_PKG]
            if package_name in packages_counter.keys():
                packages_counter[package_name] += 1
            else:
                packages_counter[package_name] = 1

        # find and print duplicates
        duplicates = [(package, count) for (package, count) in packages_counter.items() if count > 1]
        if len(duplicates) > 0:
            self.log(str(len(duplicates)) + ' duplicates:')
            for pkg, count in duplicates:
                self.log(pkg + ': ' + str(count))
        else:
            self.log('No duplicates.')

            ### helper methods ###

    def log(self, s: str) -> None:
        print(ResultAnalyzer.LOG_TAG + ": " + str(s))

    def read_csv_dict(self) -> List[Dict[str, str]]:
        """
        Reads a csv into a list of row dictionaries. The keys are the ordered fieldnames (package, subtask, ...)saved 
        in the analyzer. Also contains entries such as header lines and empty lines.
        :return: list of dictionaries mapping from fieldnames to values
        """
        result = []

        if path.isfile(self.summary_file):
            with open(self.summary_file, 'r') as result_csv:
                csv_reader = DictReader(result_csv, delimiter=';', fieldnames=self.ordered_fieldnames)
                for row in csv_reader:
                    result.append(row)
        return result

    def find_matching_entries(self, condition: Callable[[Dict[str, str]], bool],
                              csv_rows: Union[List[Dict[str, str]], None]=None) -> List[Dict[str, str]]:
        """
        Scans the provided csv_rows for entries matching the provided condition. 
        :param condition: function mapping rows to booleans
        :param csv_rows: the rows of a read csv result file. Falls back to the current results if no rows are provided.
        :return: list of row dicts meeting the provided condition
        """
        results = []
        if csv_rows is None:
            csv_rows = self.read_csv_dict()

        # noinspection PyTypeChecker
        for row in csv_rows:
            if condition(row):
                results.append(row)
        return results

    # get all app entries from the summary csv, omitting categories and empty lines
    def get_app_rows(self) -> List[Dict[str, str]]:
        """
        Reads all app rows from the summary csv, omitting categories and empty lines.
        :return: list of row dicts
        """
        return self.find_matching_entries(ResultAnalyzer.is_app_row)

    # True if a given row is an app testing result, False otherwise (categories, header lines)
    @staticmethod
    def is_app_row(row: Dict[str, str]) -> bool:
        """
        Checks whether a csv row is an app entry.
        :param row: the csv row dict to check
        :return: true if app row, false if other (e.g., category, empty)
        """
        return row[ReportWriter.KEY_TIMESTAMP] is not None \
               and row[ReportWriter.KEY_TIMESTAMP] != ReportWriter.KEY_TIMESTAMP
