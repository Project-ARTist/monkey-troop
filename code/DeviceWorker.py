from random import getrandbits
from time import sleep
from traceback import format_exception
from os import path
from typing import Union

from model.TaskWorker import TaskWorker
from utils.filesystem_config import FilesystemConfig

from utils.shellutils import adb_shell, shell, adb_pull, adb_logcat_dump, adb_logcat_clear


__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


# abstract class
class DeviceWorker(TaskWorker):

    EXT_STORAGE_DATA = '/storage/emulated/0/Android/data'
    LOGCAT_HEADER = 'LOGCAT DUMP:\n'

    def __init__(self, group=None, target=None, name="DeviceProcess", args=(), kwargs={},
                 control_channel=None, queue=None, report_queue=None, device_id = None,
                 artist_package='saarland.cispa.artist.artistgui', artist_activity='ArtistMainActivity'):
        super(DeviceWorker, self).__init__(group, target, name, args, kwargs,
                                           control_channel, queue, report_queue, device_id)

        if device_id is None:
            raise AssertionError('Missing device id')

        self.device_id = device_id

        # TODO check that device is reachable

        self.artist_package = artist_package
        self.artist_activity = artist_activity

    # do not quit unless there are no more tasks
    def keepalive_condition(self) -> bool:
        return not self.tasks.empty()

    ### logcat dumping

    # clear logcat so a later dump only captures the relevant entries
    def start_subtask(self, subtask: str) -> None:
        super(DeviceWorker, self).start_subtask(subtask)
        adb_logcat_clear(device=self.device_id)

    # add logcat dumping
    def conclude_subtask(self, success, include_logcat=False) -> None:
        # before concluding subtask, add logcat dump to the log
        if include_logcat:
            log = self.subtask_log[self.current_subtask]
            try:
                succ, dump = adb_logcat_dump(device=self.device_id)
            except Exception as e:
                self.log('exception caught during logcat dumping:')
                self.log(str(e))
                succ = False
                dump = ''
            log.append(DeviceWorker.LOGCAT_HEADER)
            if succ:
                log.append(dump)
            else:
                log.append('<could not dump logcat>')
        super(DeviceWorker, self).conclude_subtask(success)

    ### on-device testing utils

    def generate_monkey_seed(self) -> int:
        """
        Generate a random seed for the monkey.
        This is useful if tests need to be reproducible since the seed is used to seed the ransomness generator. 
        :return: a random 32 bit seed
        """
        return getrandbits(32)

    def monkey_test(self, app: str, seed: Union[int, None]=None) -> bool:
        """
        Test an application on the device using the monkey UI exercising tool.
        The test can be repeated by using the same seed.
        :param app: the app under test
        :param seed: the seed to be used by the monkey
        :return: whether the test succeeded or crashed
        """
        self.log('Starting monkey test for ' + app)
        events = 500
        try:
            cmd = 'monkey' \
                  + ' -p ' \
                  + str(app) \
                  + ((' -s ' + str(seed)) if seed is not None else '') \
                  + ' -v' \
                  + ' --kill-process-after-error' \
                  + ' ' + str(events)  # provide the number of events the monkey should generate
            (success, out) = adb_shell(cmd, device=self.device_id)
            self.log(out)
            return success
        except Exception as e:
            self.log('Encountered exception during monkey testing: ')
            self.log(''.join(format_exception(None, e, e.__traceback__)))
            return False

    def instrument(self, app: str) -> bool:
        """
        Trigger on-device recompilation of an application using an installed ARTist version.
        :param app: the app to be instrumented
        :return: success or failure
        """
        activity = self.artist_package + '/.' + self.artist_activity
        self.log('Starting ARTistGUI to instrument ' + app)
        (start_success, start_out) = adb_shell('am start -n ' + activity +
                                              ' --es INTENT_EXTRA_PACKAGE ' + app, device=self.device_id)

        self.log(start_out)
        if not start_success:
            self.log('Could not start ARTistGUI')
            return False

        # path where ARTistGUI stores the instrumentation result file to
        result_path = self.instrumentation_result_path(app)

        # roughly how long to wait before considering it a fail
        wait_seconds = 1800  # 30 minutes

        instrumentation_success = False

        # busy wait
        self.log('Starting busy wait: checking ' + result_path + ' until results appear or timeout occurs.')
        ls = 'ls ' + result_path
        for i in range(0, wait_seconds):
            # check if file exists
            (exists, ls_out) = adb_shell(ls, device=self.device_id)

            # not yet done
            if (not exists) and 'No such file or directory' in ls_out:
                if i % 10 == 0:
                    self.log(str(i).zfill(4) + ' - ' + app + ' - waiting for instrumentation to finish.')
                sleep(1)
            # unexpected error, should only occur during debugging (wrong permission etc)
            elif not exists:
                self.log('ls command failed. Abort.')
                instrumentation_success = False  # making it explicit
                self.log(ls_out)
                break
            else:
                self.log('Found instrumentation result file')

                tmp_result = path.join(FilesystemConfig().get_tmp_dir(), 'ARTIST_RESULT')
                # (pulled, pulled_out) = shell('adb pull ' + result_path + ' ' + tmp_result)
                (pulled, pulled_out) = adb_pull(result_path, tmp_result, device=self.device_id)
                self.log('Pulling instrumentation result file from device '
                         + ('succeeded' if pulled else 'failed') + ':')
                self.log(pulled_out)

                if not pulled:
                    instrumentation_success = False
                    break

                with open(tmp_result, 'r') as result:
                    result_line = result.readline().strip()
                    self.log('Read "' + result_line + '" from result file.')
                    if result_line == 'true':
                        self.log('Result file: compilation succeeded!')
                        instrumentation_success = True
                    else:
                        self.log('Result file: compilation failed!')
                        instrumentation_success = False

                # cleanup result file but do not abort if it does not work, just log
                (cleanup, cleanup_out) = shell('rm ' + tmp_result)
                self.log('Cleaning the result file ' + ('succeeded' if cleanup else 'failed') + '.')
                self.log(cleanup_out)
                break

        self.log('Stopping ARTistGUI')
        (stop_success, stop_log) = adb_shell('am force-stop ' + self.artist_package, device=self.device_id)
        self.log(stop_log)
        if not stop_success:
            self.log('Stopping ARTistGUI failed.')
            # TODO reinstall? what if reinstall fails??

        return instrumentation_success

    def instrumentation_result_path(self, app=None):
        """
        Encapsulates the path of the file on the device where ARTistGUI writes down whether the instrumentation 
        succeeded or failed. 
        :param app: the app for which the result file path will be returned
        :return: the device file path for the instrumentation result file
        """
        artist_ext_dir = path.join(DeviceWorker.EXT_STORAGE_DATA, self.artist_package, "files", 'ArtistResults')
        return path.join(artist_ext_dir, (str(app) if app is not None else ''))

    ### interface left to implement

    # def process(self, task) from TaskWorker

    def cleanup(self, task):
        self.not_implemented('cleanup is not implemented yet.')




