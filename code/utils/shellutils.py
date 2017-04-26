from subprocess import CalledProcessError, check_output, STDOUT
from typing import Union, Tuple, List


__author__ = 'Oliver Schranz <oliver.schranz@cispa.saarland>'


def adb_install(packagePath: str, string_out: bool = True, reinstall: bool = True, device: Union[str, None] = None) \
        -> Tuple[bool, str]:
    """
    Install an application on a specific device.
    :param packagePath: full path to the android apk package
    :param string_out: whether the collected output should be decoded to a regular string
    :param reinstall: whether to force reinstall with the -r flag
    :param device: the device to run the command on or None to use the one connected device
    :return: a tuple of the success flag and the collected log output of the execution
    """
    command = 'adb ' \
              + (('-s ' + device + ' ') if device is not None else '') \
              + 'install ' \
              + ('-r ' if reinstall else ' ') \
              + packagePath
    return shell(command, string_out=string_out)


def adb_uninstall(packageName: str, string_out: bool=True, device: Union[str, None]=None) -> Tuple[bool, str]:
    """
       Uninstall an application on a specific device.
       :param packagePath: full path to the android apk package
       :param string_out: whether the collected output should be decoded to a regular string
       :param device: the device to run the command on or None to use the one connected device
       :return: a tuple of the success flag and the collected log output of the execution
       """
    command = 'adb' \
              + ((' -s ' + device + '') if device is not None else '') \
              + ' uninstall ' \
              + packageName
    return shell(command, string_out=string_out)


def adb_shell(command: str, string_out: bool=True, device: Union[str, None]=None) -> Tuple[bool, str]:
    """
    Issue shell commands on specific devices.
    :param command: the command to execute
    :param string_out: whether the collected output should be decoded to a regular string
    :param device: the device to run the command on or None to use the one connected device
    :return: a tuple of the success flag and the collected log output of the execution
    """
    cmd = 'adb' \
          + ((' -s ' + device) if device is not None else '') \
          + ' shell ' \
          + command
    return shell(cmd, string_out=string_out)


def adb_pull(filepath: str, destination: str, string_out: bool=True, device: Union[str, None]=None) -> Tuple[bool, str]:
    """
    Pull a file from a specific device.
    :param filepath: the path of the file on the device
    :param destination: the host path to store the file to
    :param string_out: whether the collected output should be decoded to a regular string
    :param device: the device to run the command on or None to use the one connected device
    :return: a tuple of the success flag and the collected log output of the execution
    """

    cmd = 'adb' \
          + ((' -s ' + device) if device is not None else '') \
          + ' pull ' \
          + filepath + ' ' + destination
    return shell(cmd, string_out=string_out)


def adb_logcat_clear(device: Union[str, None]=None) -> Tuple[bool, str]:
    """
    Clear logcat.
    :param device: the device to run the command on or None to use the one connected device
    :return: a tuple of the success flag and the collected log output of the execution
    """
    device_str = ' -s ' + device + ' ' if device is not None else ' '
    return shell('adb' + device_str + 'logcat -c')


def adb_logcat_dump(device: Union[str, None]=None) -> Tuple[bool, str]:
    """
    Dump the current content of logcat since the last clear.
    :param device: the device to run the command on or None to use the one connected device
    :return: a tuple of the success flag and the collected log output of the execution
    """
    device_str = ' -s ' + device + ' ' if device is not None else ' '
    return shell('adb' + device_str + 'logcat -d')


def list_devices() -> Union[List[str], None]:
    """
    List all devices currently available via adb
    :return: list of available device identifiers for success or None for failure
    """
    devices = list()
    succ, out = shell("adb devices")
    if not succ:
        return None
    lines = out.split('\n')[1:]  # ignore first line
    for line in lines:
        splitted = line.split('\t')
        if len(splitted) != 2:
            continue
        if splitted[1].strip().lower() == 'device':
            device = splitted[0].strip()
            devices.append(device)
        else:
            print('ignoring : ' + line)
    return devices


def shell(command: str, string_out: bool=True) -> Tuple[bool, str]:
    """
    Executes a shell command.
    :param command: the command to execute
    :param string_out: whether the collected output should be decoded to a regular string
    :return: a tuple of the success flag and the collected log output of the execution
    """
    # print('COMMAND: ' + command)
    try:
        out = check_output(command.split(" "), stderr=STDOUT)
        resultcode = 0
    except CalledProcessError as e:
        out = e.output
        resultcode = e.returncode

    return resultcode == 0, out if not string_out else out.decode()
