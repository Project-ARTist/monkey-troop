from multiprocessing import Queue

from DeviceWorker import DeviceWorker
from evaluations.Task import Task
from model.IAppRepository import IAppRepository
from utils.shellutils import adb_install, adb_shell, adb_uninstall

__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


class TraceLoggingWorker(DeviceWorker):

    def __init__(self, group=None, target: str=None, name: str="DeviceProcess", args=(), kwargs={}, control_channel=None,
                 queue: Queue=None, report_queue: Queue=None, device_id: str=None,
                 app_repo: IAppRepository=None, artist_package: str='saarland.cispa.artist.artistgui',
                 artist_activity: str='ArtistMainActivity'):
        super(TraceLoggingWorker, self).__init__(group, target, name, args, kwargs, control_channel, queue, report_queue,
                                                 device_id, artist_package, artist_activity)

        if app_repo is None:
            raise AssertionError('App repository is not available. Abort.')
        self.repo = app_repo

    def process(self, task: Task) -> None:
        # local import to avoid circular dependency
        from evaluations.trace_logging.TraceLoggingEvaluator import TraceLoggingEvaluator

        app = task.package
        seed = self.generate_monkey_seed()
        self.start_task(task)

        try:
            # check if app is available
            self.start_subtask(TraceLoggingEvaluator.SUBTASK_TEST_AVAILABLE)
            app_path = self.repo.get_app(app)
            app_available = app_path is not None
            self.conclude_subtask(app_available)
            if not app_available:
                self.log('App not downloaded. Abort.')
                return

            # install app for the first time
            self.start_subtask(TraceLoggingEvaluator.SUBTASK_INSTALL_APP_1)
            (success2, out2) = adb_install(app_path, device=self.device_id)
            self.log(out2)
            self.conclude_subtask(success2, include_logcat=True)
            if not success2:
                return

            # test uninstrumented app. We are interested in whether apps might be broken already BEFORE we instrument
            self.start_subtask(TraceLoggingEvaluator.SUBTASK_TEST_UNINSTRUMENTED)
            success3 = self.monkey_test(app, seed)
            self.conclude_subtask(success3, include_logcat=True)
            if not success3:
                return

            # clean (re)installation of app
            self.start_subtask(TraceLoggingEvaluator.SUBTASK_INSTALL_APP_2)
            (success4, out4) = adb_install(app_path, device=self.device_id)
            self.log(out4)
            self.conclude_subtask(success4, include_logcat=True)
            if not success4:
                return

            # instrument app
            self.start_subtask(TraceLoggingEvaluator.SUBTASK_INSTRUMENT)
            success5 = self.instrument(app)
            self.conclude_subtask(success5, include_logcat=True)
            if not success5:
                return

            # test instrumented app again with the same seed
            self.start_subtask(TraceLoggingEvaluator.SUBTASK_TEST_INSTRUMENTED)
            success6 = self.monkey_test(app, seed)
            self.conclude_subtask(success6, include_logcat=True)

        # always cleanup no matter where we finish
        finally:
            self.cleanup(task)

    # best effort cleanup since we do not know what apps and data are still on the device
    def cleanup(self, task: Task) -> None:

        from evaluations.trace_logging.TraceLoggingEvaluator import TraceLoggingEvaluator
        self.start_subtask(TraceLoggingEvaluator.SUBTASK_CLEANUP)

        app_package = task.package
        self.log('Clean up for task ' + app_package)

        artist_succ, artist_out = adb_shell('am force-stop ' + self.artist_package, device=self.device_id)
        self.log(('un' if not artist_succ else '') + 'successfully stopped ARTistGUI')
        self.log(artist_out)

        app_succ, app_out = adb_uninstall(app_package, device=self.device_id)
        self.log(('un' if not app_succ else '') + 'successfully deinstalled ' + app_package + ': ')
        self.log(app_out)

        # delete all result files
        del_succ, del_out = adb_shell('rm ' + self.instrumentation_result_path() + '*', device=self.device_id)
        self.log(('un' if not del_succ else '') + 'successfully removed result files: ')
        self.log(del_out)

        # TODO in order to reliably report whether cleaning up worked,
        # we need to find out what needs to be cleaned up and then check if it worked.
        # Either we remember it during the processing or simply probe whether an app is installed or a file is present
        self.conclude_subtask(True, include_logcat=True)