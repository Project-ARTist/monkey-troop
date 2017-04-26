from argparse import ArgumentParser
from multiprocessing import Queue
from typing import List, Dict

from DeviceWorker import DeviceWorker
from analysis.ResultAnalyzer import ResultAnalyzer
from evaluations.Task import Task
from evaluations.common import read_apps
from evaluations.trace_logging.TraceLoggingWorker import TraceLoggingWorker
from model.IAppRepository import IAppRepository
from model.IEvaluator import IEvaluator
from repositories.gplay.GPlayDownloaderRepository import GPlayDownloaderRepository

__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


class TraceLoggingEvaluator(IEvaluator):
    # id used to choose this evaluator
    EVAL_ID = 'trace_logging'

    # subtask ids
    SUBTASK_TEST_AVAILABLE = 'test_app_availability'
    SUBTASK_INSTALL_APP_1 = 'install_app_1'
    SUBTASK_TEST_UNINSTRUMENTED = 'test_app_uninstrumented'
    SUBTASK_INSTALL_APP_2 = 'install_app_2'
    SUBTASK_INSTRUMENT = 'instrument_app'
    SUBTASK_TEST_INSTRUMENTED = 'test_app_instrumented'
    SUBTASK_CLEANUP = 'cleanup'

    # subtask to interpretation map
    SUBTASKS_INTERPRETATION = {
        # detect whether eligible for testing
        SUBTASK_TEST_AVAILABLE: IEvaluator.ASSUMPTION,
        SUBTASK_INSTALL_APP_1: IEvaluator.ASSUMPTION,
        SUBTASK_TEST_UNINSTRUMENTED: IEvaluator.ASSUMPTION,
        SUBTASK_INSTALL_APP_2: IEvaluator.ASSUMPTION,
        # do the actual testing
        SUBTASK_INSTRUMENT: IEvaluator.REQUIRED,
        SUBTASK_TEST_INSTRUMENTED: IEvaluator.REQUIRED,
        # try to clean up
        SUBTASK_CLEANUP: IEvaluator.DONTCARE
    }

    # identifiers for arguments
    ARG_PKG_LIST = 'package_list'
    ARG_APK_FOLDER = 'apk_folder'
    ARG_REVERSE = 'reverse'

    # parcel
    SEPARATOR = '::'

    def __init__(self):
        self.package_list = None
        self.reverse = False

    def init(self) -> None:
        parser = self.create_parser()

        # we only care for the recognized args
        args = parser.parse_known_args()[0]

        if args.evaluation != TraceLoggingEvaluator.EVAL_ID:
            print('Error! Wrong evaluation provided. Expected "' + TraceLoggingEvaluator.EVAL_ID + '"')
            exit(-1)

        self.package_list = args.package_list
        self.reverse = args.reverse

    def create_parser(self) -> ArgumentParser:
        parser = ArgumentParser()

        parser.add_argument('evaluation',
                            metavar='<EVALUATION>',
                            action='store',
                            help='The evaluation that will be invoked. Should be "' + TraceLoggingEvaluator.EVAL_ID + '"')

        parser.add_argument(TraceLoggingEvaluator.ARG_PKG_LIST,
                            metavar='<PACKAGE_LIST>',
                            action='store',
                            help='Package File which contains a categorized package list.')

        parser.add_argument('-r', '--reverse',
                            action='store_true',
                            help='Activating this flag leads to a reverse processing of the package list')
        return parser

    def create_task_queue(self, skip: int=0) -> Queue:

        app_dict, num_apps = read_apps(self.package_list)
        queue = Queue(num_apps)

        for app,categories in app_dict.items():
            if app in skip:
                print('Skipping already processed app ' + app)
                continue
            queue.put(Task(app, categories))
        return queue

    def create_device_worker(self, control_channel, queue: Queue, device_id: str, report_queue, process_args=(),
                             process_kwargs={}) -> DeviceWorker:
        process_name = 'device_' + device_id
        repo = self.get_app_repository()
        return TraceLoggingWorker(name=process_name, args=process_args, kwargs=process_kwargs,
                             control_channel=control_channel, queue=queue, device_id=device_id, report_queue=report_queue,
                             app_repo=repo)

    def get_eval_id(self) -> str:
        return TraceLoggingEvaluator.EVAL_ID

    def get_subtask_ids_ordered(self) -> List[str]:
        # the ordering matters
        return [TraceLoggingEvaluator.SUBTASK_TEST_AVAILABLE,
                TraceLoggingEvaluator.SUBTASK_INSTALL_APP_1,
                TraceLoggingEvaluator.SUBTASK_TEST_UNINSTRUMENTED,
                TraceLoggingEvaluator.SUBTASK_INSTALL_APP_2,
                TraceLoggingEvaluator.SUBTASK_INSTRUMENT,
                TraceLoggingEvaluator.SUBTASK_TEST_INSTRUMENTED,
                TraceLoggingEvaluator.SUBTASK_CLEANUP]

    def get_subtask_interpretation(self) -> Dict[str, int]:
        return TraceLoggingEvaluator.SUBTASKS_INTERPRETATION

    def get_analyzer(self, fixed_fields_front: List[str], fixed_fields_back: List[str]) -> ResultAnalyzer:
        # no specialized analyzer needed currently: return default one
        return ResultAnalyzer(self, fixed_fields_front, fixed_fields_back)

    def get_app_repository(self) -> IAppRepository:
        return GPlayDownloaderRepository()


