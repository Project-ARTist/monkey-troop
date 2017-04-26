from multiprocessing import Queue
from typing import List, Dict

from DeviceWorker import DeviceWorker
from model.IAppRepository import IAppRepository


__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


class IEvaluator(object):

    ASSUMPTION = -1
    REQUIRED = 0
    DONTCARE = 1

    def init(self) -> None:
        raise AssertionError('Evaluator: init not implemented')

    def create_task_queue(self, skip: int=0) -> Queue:
        raise AssertionError('Evaluator: create_task_queue not implemented')

    def create_device_worker(self, control_channel, queue: Queue, device: str, report_channel) -> DeviceWorker:
        raise AssertionError('Evaluator: create_device_worker not implemented')

    def get_eval_id(self) -> str:
        raise AssertionError('Evaluator: get_eval_id not implemented')

    def get_subtask_ids_ordered(self) -> List[str]:
        raise AssertionError('Evaluator: get_subtask_ids not implemented')

    def get_subtask_interpretation(self) -> Dict[str, int]:
        """
        Provides a mapping from subtask ids to their corresponding interpretations.
        The interpretations allows to reason about failed subtasks.
        If a subtask fails, there are 3 possibilities:
        * DONTCARE: it does not influence the overall success.
        * ASSUMPTION: if it fails, we remove the tested subject from our counting.
        * REQUIRED: we count a failure.
        :return: dictionary mapping from subtask ids to DONTCARE, ASSUMPTION or REQUIRED.
        """
        raise AssertionError('Evaluator: get_subtask_interpretation not implemented')

    def get_analyzer(self, fixed_fields_front: List[str], fixed_fields_back: List[str]):
        raise AssertionError('Evaluator: get_analyzer not implemented')

    def get_app_repository(self) -> IAppRepository:
        raise AssertionError('Evaluator: get_app_repository not implemented')