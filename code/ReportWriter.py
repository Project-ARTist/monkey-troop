from multiprocessing import Queue, Value
from csv import DictWriter
from os import path
from datetime import datetime
from typing import List, Tuple, Dict

from model.IResultAnalyzer import IResultAnalyzer
from model.ITask import ITask
from model.TaskWorker import TaskWorker
from utils.filesystem_config import FilesystemConfig


__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


class ReportTask(object):
    def __init__(self, completed_task: ITask, worker_log: List[str], success_dict: Dict[str, bool],
                 output_dict: Dict[str, str],
                 timestamp: int, worker = None):
        super(ReportTask, self).__init__()

        self.completed_task = completed_task
        self.worker_log = worker_log
        self.success_dict = success_dict
        self.output_dict = output_dict
        self.timestamp = timestamp
        self.worker = worker


# noinspection PyRedeclaration
class ReportWriter(TaskWorker):
    msg_producers_done = 'MSG_PRODUCERS_ARE_DONE'
    divider = '#' * 100
    queue_capacity = 1000

    # csv constants
    FILE_SUMMARY_SUFFIX = 'summary.csv'
    KEY_PKG = 'Package'
    KEY_CATS = 'Categories'
    KEY_WORKER = 'Worker'
    KEY_SUCC = 'Overall Success'
    KEY_TIMESTAMP = 'Timestamp'

    UNKNOWN_WORKER = 'Unknown Worker'
    CSV_IN_CELL_SEPARATOR = '::'

    def __init__(self, group=None, target=None, name: str = "DeviceProcess", args=(), kwargs={},  # process args
                 control_channel=None, known_subtasks: List[str] = list(),  # reporter specific args
                 analyzer: IResultAnalyzer = None, eval_name: str = '<Unknown Eval>'):

        # cache
        fsc = FilesystemConfig()
        self.reports_dir = fsc.get_report_dir()
        self.results_dir = fsc.get_result_dir()

        # this worker generates its own queue
        queue = Queue(ReportWriter.queue_capacity)
        super(ReportWriter, self).__init__(group, target, name, args, kwargs, control_channel, queue, None,
                                           "report_writer")

        self.known_subtasks = known_subtasks
        self.eval = eval_name
        if not analyzer:
            raise AssertionError('No analyzer provided.')
        self.analyzer = analyzer
        # unless this is set, the reporter keeps running even though the queue is currently empty
        self.exit_after_empty_queue = False

        # csv
        self.csv_keys = [ReportWriter.KEY_PKG, ReportWriter.KEY_CATS] + self.known_subtasks + [ReportWriter.KEY_SUCC] \
                        + [ReportWriter.KEY_WORKER] + [ReportWriter.KEY_TIMESTAMP]
        with open(self.get_summary_path(), 'a+') as csv_summary:
            csv_summary.write(('#' * 3) + ' ' + str(datetime.now().isoformat()) + '\n')  # log date
            header_writer = DictWriter(csv_summary, self.csv_keys, delimiter=';', quotechar='"')
            header_writer.writeheader()

        # values for statistics
        tested, outs, failures, successes = self.analyzer.get_all()
        self.tested = len(tested)
        self.outs = len(outs)
        self.fails = len(failures)
        self.successes = len(successes)

    # extending the message handling
    def handle_single_message(self, msg: str) -> None:
        super(ReportWriter, self).handle_single_message(msg)
        if msg == ReportWriter.msg_producers_done:
            self.log('Received message from main process: all workers done. Finish queue and exit')
            self.exit_after_empty_queue = True

    ### implementing the interface

    # as tasks are coming in infrequently and we do not know when the workers are done,
    # we have to wait until the main process terminates us
    def keepalive_condition(self) -> bool:
        return not (self.exit_after_empty_queue and self.tasks.empty())

    def process(self, task: ReportTask) -> None:
        self.log('processing report task')
        results = list()
        overall_success = True
        for subtask in self.known_subtasks:
            try:
                success = task.success_dict[subtask]
                overall_success &= success
            except KeyError as no_results_for_subtasks:
                success = False

            overall_success &= success

            try:
                output = task.output_dict[subtask]
            except KeyError as no_output_for_subtask:
                output = ['<< No output >>']

            results.append((subtask, success, output))

        self.write_report(task, overall_success, results, dump=True)

        result_row = self.update_result(task, overall_success, results)

        interpretation = self.analyzer.interpret(result_row)
        self.tested += 1
        if interpretation == IResultAnalyzer.OUT:
            self.outs += 1
        elif interpretation == IResultAnalyzer.FAIL:
            self.fails += 1
        elif interpretation == IResultAnalyzer.SUCCESS:
            self.successes += 1
        else:
            raise AssertionError('Unknown result interpretation: ' + interpretation)
        self.print_state()

    ### helper methods

    def report_file(self, name: str = None) -> str:
        return path.join(self.reports_dir, str(name) if name is not None else '')

    @staticmethod
    def format_timestamp(timestamp: int) -> str:
        return datetime.utcfromtimestamp(timestamp).strftime('%d.%m.%Y %H:%M:%S')

    def write_report(self, task: ReportTask, overall_success: bool, results: List[Tuple[str, bool, str]],
                     dump: bool = False) -> None:
        """
        Write a report file resembling the results of an app evaluation by one of the device workers.
        :param task: the task containing all information about the app evaluation
        :param overall_success: whether the evaluation succeeded for this app
        :param results: success flags and output for each subtask
        :param dump: whether report should also be dumped to the log
        """

        completed_task = task.completed_task
        id = completed_task.get_package()
        worker = task.worker
        timestamp = task.timestamp
        worker_log = task.worker_log

        self.log('Writing report for task ' + id)

        buffer = (ReportWriter.divider + '\n')
        buffer += (ReportWriter.divider + '\n')
        buffer += ('Task: ' + id + '\n')
        # add categories
        categories = completed_task.get_categories()
        if len(categories) > 0:
            buffer += 'Categories:'
        for cat in categories[:-1]:
            buffer += cat + ','
        buffer += categories[-1]

        buffer += ('Device: ' + (worker if worker is not None else ReportWriter.UNKNOWN_WORKER) + '\n')
        buffer += ('Timestamp: ' + self.format_timestamp(timestamp) + '\n')
        buffer += ('Overall success: ' + self.success_string(overall_success) + '\n')
        for (subtask, success, output) in results:
            buffer += (ReportWriter.divider + '\n')
            buffer += ('Subtask ' + subtask + ': ' + self.success_string(success) + '\n')
            buffer += ('Output:\n' + '\n'.join(output) + '\n')
        buffer += ('Worker log:' + '\n')
        for entry in worker_log:
            buffer += (entry + '\n')
        buffer += (ReportWriter.divider + '\n')

        # write report to filesystem
        with open(self.report_file(id), 'w') as report:
            report.write(buffer)

        # dump to log
        if dump:
            self.log('Dumping report for task ' + id)
            print(buffer)

    @staticmethod
    def success_string(success):
        return ('SUCCESS' if success else 'FAIL')

    # store result summary to csv file
    # def update_result(self, id, overall_success, results, timestamp, worker=None):
    # task, overall_success, results
    def update_result(self, task: ReportTask, overall_success: bool, results: List[Tuple[str, bool, str]]) -> Dict[
        str, str]:
        """
        Update the result csv file with a new row created from the provided app eval results.
        :param task: the task containing all information about the app evaluation
        :param overall_success: whether the evaluation succeeded for this app
        :param results: success flags and output for each subtask
        :return: the row dictionary that was appended to the result file
        """

        completed_task = task.completed_task
        id = completed_task.get_package()
        categories = completed_task.get_categories()
        worker = task.worker
        timestamp = task.timestamp

        categories_buffer = ''
        if len(categories) > 0:
            for cat in categories[:-1]:
                categories_buffer += cat + ReportWriter.CSV_IN_CELL_SEPARATOR
            categories_buffer += categories[-1]

        row_dict = dict()
        row_dict[ReportWriter.KEY_PKG] = id
        row_dict[ReportWriter.KEY_CATS] = categories_buffer
        row_dict[ReportWriter.KEY_WORKER] = worker if worker is not None else ReportWriter.UNKNOWN_WORKER
        row_dict[ReportWriter.KEY_TIMESTAMP] = self.format_timestamp(timestamp)
        for (subtask, success, output) in results:
            row_dict[subtask] = success
        row_dict[ReportWriter.KEY_SUCC] = overall_success
        with open(self.get_summary_path(), 'a') as result_csv:
            result_writer = DictWriter(result_csv, self.csv_keys, delimiter=';', quotechar='"')
            result_writer.writerow(row_dict)
        return row_dict

    def get_summary_path(self) -> str:
        return path.join(self.results_dir, self.eval + '_' + ReportWriter.FILE_SUMMARY_SUFFIX)

    # TODO use result analyzer
    def print_state(self) -> None:
        included = self.tested - self.outs
        print('tested: ' + str(self.tested) + ', out: ' + str(self.outs) + ', success: ' + str(self.successes) + '/'
              + str(included) + ': ' + (str(self.successes / included) if included > 0 else 0)) + '%'
