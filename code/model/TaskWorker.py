from multiprocessing import Process
from queue import Empty
from multiprocessing import Queue
from time import time

from model.ITask import ITask


__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


class TaskWorker(Process):
    # control channel messages:

    msg_terminate = 'TERMINATE'

    class TerminationSignal(Exception):
        pass

    def __init__(self, group=None, target=None, name: str = "DeviceProcess", args=(), kwargs={},
                 control_channel=None, queue: Queue = None, report_queue: Queue = None, worker_id=None):
        super(TaskWorker, self).__init__(group, target, name, args, kwargs)

        # identifying string for this worker
        self.id = worker_id

        # currently recv only pipe
        if control_channel is None:
            raise AssertionError('No control channel provided.')
        self.control_channel = control_channel

        if queue is None:
            raise AssertionError('No queue provided.')
        self.tasks = queue

        # can be none
        self.report_queue = report_queue

        self.log_prefix = name

        # logging and reporting state
        self.current_task = None
        self.current_subtask = None
        self.worker_log = list()
        self.subtask_log = dict()
        self.subtask_success = dict()

    def log(self, s: str) -> None:
        if self.current_subtask is not None:
            self.subtask_log[self.current_subtask].append(s)
        else:
            self.worker_log.append(s)

    def reset_task_state(self) -> None:
        self.current_task = None
        self.current_subtask = None
        self.subtask_success = dict()
        self.subtask_log = dict()

    def start_task(self, task) -> None:
        self.reset_task_state()
        self.current_task = task

    def start_subtask(self, subtask: str) -> None:
        self.current_subtask = subtask
        self.subtask_log[subtask] = list()

    def conclude_subtask(self, success: bool) -> None:
        self.subtask_success[self.current_subtask] = success

    def send_report(self) -> None:
        # not all workers have a report queue
        if self.report_queue is not None:
            timestamp = int(time())

            # local import to avoid circular dependency
            from ReportWriter import ReportTask
            report = ReportTask(self.current_task, self.worker_log, self.subtask_success, self.subtask_log, timestamp,
                                self.id)
            self.report_queue.put(report)

    def run(self) -> None:
        super(TaskWorker, self).run()

        try:
            while self.keepalive_condition():
                try:
                    self.handle_messages()
                except TaskWorker.TerminationSignal as terminate:
                    self.log('Received termination signal via message. Finishing.')
                    break

                try:
                    task = self.tasks.get(block=True, timeout=1)
                except Empty as empty:
                    self.log('Queue is empty. Continuing to re-evaluate keepalive condition.')
                    continue

                # if not self.tasks.valid(task):
                #    self.log('Ignoring malformed task: ' + repr(task))


                try:
                    # do the actual work
                    self.process(task)
                except KeyboardInterrupt as abort:
                    self.log('Keyboard interrupt. Finishing.')
                    break
                except Exception as generic_exception:
                    self.log('Error: Aborting task due to exception: ' + str(generic_exception))
                    # fallthrough to send an (incomplete) report
                self.send_report()
                # implicit continue here

            self.log("queue is empty, finishing process.")
        except KeyboardInterrupt as abort:
            self.log('Keyboard interrupt. Finishing.')

    def get_task_queue(self) -> Queue:
        return self.tasks

    def not_implemented(self, msg: str) -> None:
        self.log(msg)
        raise NotImplementedError(msg)

    def handle_messages(self) -> None:
        """
        Handle messages from the control channel.
        """

        while self.control_channel.poll():
            msg = self.control_channel.recv()
            self.handle_single_message(msg)

    def handle_single_message(self, msg: str) -> None:
        """
        Handle a single message received via the control channel.
        This method is meant to be overwritten in case own control messages are introduced. 
        In this case, either calling super or reimplementing the handling of the termination message is required.
        :param msg: the control message string
        """

        # exit gracefully if termination signal from main process is obtained
        if msg == TaskWorker.msg_terminate:
            self.log('Received termination signal. Exiting.')
            raise TaskWorker.TerminationSignal

    ### interface

    def keepalive_condition(self) -> bool:
        self.not_implemented('keepalive_condition is not implemented yet.')
        return False

    def process(self, task: ITask) -> None:
        self.not_implemented('run is not implemented yet.')
