from argparse import ArgumentParser
from multiprocessing import Pipe
from os import makedirs, path
from sys import argv
from time import sleep

import shutil
from typing import List

from DeviceWorker import DeviceWorker
from ReportWriter import ReportWriter
from evaluations.Evaluations import Evaluations
from model.TaskWorker import TaskWorker
from utils import shellutils
from utils.filesystem_config import FilesystemConfig

__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


# constants
PARCEL_NUM_PROCESSED = 'processed'
PARCEL_NUM_SUCCEEDED = 'succeeded'
SEPARATOR = '::'


def wait_for_workers(workers: List[TaskWorker]) -> None:
    """
    Blocks until all provides workers finished execution.
    :param workers: the workers to wait for
    """
    for p in workers:
        print('Joining ' + p.name)
        p.join()


def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('evaluation',
                        metavar='<EVALUATION>',
                        action='store',
                        help='The evaluation that will be invoked.')

    parser.add_argument('package-list',
                        metavar='<PACKAGE_LIST>',
                        action='store',
                        help='Package File which contains a categorized package list. '
                             'Relative to the current package list search folder')

    parser.add_argument('-a', '--apk-folder',
                        action='store',
                        help='Folder for app APKs.')
    parser.add_argument('-o', '--out-folder',
                        action='store',
                        help='Output folder for, e.g., results.')
    parser.add_argument('-t', '--tmp-folder',
                        action='store',
                        help='Folder to store data temporarily.')
    parser.add_argument('-l', '--list-folder',
                        action='store',
                        help='Search folder for package lists.')

    return parser


def main() -> None:
    # parsing general arguments
    parser = create_parser()
    args = parser.parse_args()

    evaluation_name = args.evaluation
    apk = args.apk_folder
    out = args.out_folder
    tmp = args.tmp_folder
    lists = args.list_folder

    # initialize singleton
    fsm_args = dict()
    if apk is not None:
        fsm_args['apk'] = apk
    if out is not None:
        fsm_args['out'] = out
    if tmp is not None:
        fsm_args['tmp'] = tmp
    if lists is not None:
        fsm_args['lists'] = lists
    fsm = FilesystemConfig(**fsm_args)

    # set dir values to the updated value
    # apk_dir = fsm.get_apk_dir()
    out_dir = fsm.get_out_dir()
    # tmp_dir = fsm.get_tmp_dir()
    report_dir = fsm.get_report_dir()
    result_dir = fsm.get_result_dir()
    # lists = fsm.get_lists_dir()

    # finding the right evaluation

    if len(argv) < 2:
        print('Did not provide evaluation name.')
        exit(-1)

    # ~ strategy pattern
    try:
        evaluator = Evaluations.MAP[evaluation_name]
        if evaluator is None:
            raise KeyError
    except KeyError as no_such_evaluator:
        print('No such evaluator: ' + evaluation_name)
        exit(-1)
        return  # ide workaround

    # initialization (e.g. eval-specific input parsing)
    evaluator.init()

    # preparing the queue

    analyzer = evaluator.get_analyzer([ReportWriter.KEY_PKG, ReportWriter.KEY_CATS],
                                      [ReportWriter.KEY_SUCC, ReportWriter.KEY_WORKER, ReportWriter.KEY_TIMESTAMP])
    tested = [app_row[ReportWriter.KEY_PKG] for app_row in analyzer.get_tested()]
    # if unfinished_runs_exist(evaluation_name):
    #     cont = input("Evaluation was finished prematurely the last time. Do you want to proceed? (y/n)").lower()
    #     if cont == 'y' or cont == 'yes':
    #         # restore state if present (do not count from 0)
    #         (tested, succeeded) = read_progress(get_save_path(evaluation_name))
    #     else:
    #         if cont != 'n' and cont != 'no':
    #             print('No valid answer given. Treated as no.')
    #         print('Deleting saved progress.')
    #         remove(get_save_path(evaluation_name))

    skip = []
    if len(tested) > 0:
        sure = False
        while not sure:
            cont = input("Evaluation was finished prematurely the last time. Do you want to proceed? (y/n)").lower()
            # continue
            if cont == 'y' or cont == 'yes':
                print('Proceeding with evaluation.')
                print('Current state:')
                analyzer.api_summary()
                skip = tested
                sure = True
            # do not continue
            else:
                if cont != 'n' and cont != 'no':
                    print('No valid answer given. Treated as no.')
                print('Do not proceed with evaluation.')

                delete = input(
                    'Are you sure you want to delete all persisted data from the last evaluation? (y/n)').lower()
                if delete == 'y' or delete == 'yes':
                    # delete data from last evaluation
                    shutil.rmtree(out_dir)
                    sure = True

    # ensure 'out' directories exist
    makedirs(report_dir, exist_ok=True)
    makedirs(result_dir, exist_ok=True)

    tasks = evaluator.create_task_queue(skip)

    # should be reliable since no one touched the queue yet
    # task_num = tasks.qsize()

    # preparing the devices

    devices = shellutils.list_devices()

    if devices is None:
        print('No devices available.')
        exit(0)

    device_workers = list()
    device_worker_connections = dict()

    helper_workers = list()
    helper_worker_connections = dict()

    # preparing the reporter process
    reporter_pipe_worker, reporter_pipe_main = Pipe(True)
    reporter = ReportWriter(name='ReportWriter', control_channel=reporter_pipe_worker,
                            known_subtasks=evaluator.get_subtask_ids_ordered(),
                            analyzer=analyzer, eval_name=evaluation_name)
    report_queue = reporter.get_task_queue()
    helper_workers.append(reporter)
    helper_worker_connections[reporter] = reporter_pipe_main
    reporter.start()

    # try: handle interrupts and errors
    try:
        # preparing and starting the device workers

        # we have an early bail-out in case there are no devices
        # noinspection PyTypeChecker
        for device in devices:
            recv, send = Pipe(False)
            worker = evaluator.create_device_worker(recv, tasks, device, report_queue)
            device_workers.append(worker)
            device_worker_connections[worker] = send
            worker.start()
            print('started ' + device)

        # wait for workers to finish
        waited_rounds = 0
        while not tasks.empty():
            waited_rounds += 1
            sleep(5)
            if waited_rounds % 10 == 0:
                print('main process: queue not empty, sleeping')

        # signalling the reporter is should stop the next time its queue gets empty

        # give the workers a chance to finish the last task and send a report before telling the
        # reporter to finish the report queue and exit
        wait_for_workers(device_workers)

        # now signal the reporter to stop after finishing the current queue
        reporter_pipe_main.send(ReportWriter.msg_producers_done)
        # and wait for it to finish
        wait_for_workers([reporter])
        print('Evaluation completed.')


    except KeyboardInterrupt as abort:
        print('Keyboard interrupt.')
    except Exception as e:
        print('Encountered exception ' + str(e))
        # fallthrough to termination

    # depending on whether we aborted or succeeded, device workers might be running or not,
    # so we just terminate all of them
    print('Terminating worker processes that are possibly still running.')

    # merge worker lists and connection dicts
    all_workers = device_workers + helper_workers
    all_connections = device_worker_connections.copy()
    all_connections.update(helper_worker_connections)

    for worker in all_workers:
        if worker.is_alive():
            all_connections[worker].send(DeviceWorker.msg_terminate)
    wait_for_workers(all_workers)

    print('Evaluation finished.')

    analyzer.api_summary()

    # some threads (e.g. daemon threads of queue) need some time to finish before we finish the main process.
    sleep(2)


if __name__ == '__main__':
    main()
