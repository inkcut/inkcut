# -*- coding: utf-8 -*-
"""
Copyright (c) 2017-2018, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import os
import sys
import logging
import platform
import traceback


from logging.handlers import RotatingFileHandler


def init_logging():
    """ Configures logging to .config/inkcut/logs within the user's home
    directory. Logging is now initialized before any external dependencies
    are imported so any missing or incorrect libraries are correctly caught
    and reported as errors in the log.

    """
    log_dir = os.path.expanduser('~/.config/inkcut/logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_filename = os.path.join(log_dir, 'inkcut.txt')
    log_format = '%(asctime)-15s | %(levelname)-7s | %(name)s | %(message)s'

    try:
        # This can be missing on python 2 so catch it if it is
        import faulthandler
        if 'INKCUT_DEBUG' in os.environ:
            crashlog = sys.stderr
        else:
            crashlog = open(os.path.join(log_dir, 'crash.txt'), 'a+')
        faulthandler.enable(crashlog)
    except Exception as e:
        print("Warning: faulthandler could not be enabled: {}".format(e))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    formatter = logging.Formatter(log_format)

    # Log to stdout
    stream = logging.StreamHandler(sys.stdout)
    stream.setLevel(logging.DEBUG)
    stream.setFormatter(formatter)

    # Log to rotating handler
    disk = RotatingFileHandler(
        log_filename,
        maxBytes=1024*1024*10,  # 10 MB
        backupCount=10,
    )
    disk.setLevel(logging.DEBUG)
    disk.setFormatter(formatter)

    root.addHandler(disk)
    root.addHandler(stream)
    print("Logging to {}".format(log_filename))


def log_debug_info(log):
    try:
        from inkcut import version
        log.info('Version: {}'.format(version))
        log.info('Python: {}'.format(sys.version))
        log.info('System: {}'.format(platform.uname()))
        log.info('Executable: {}'.format(sys.executable))
        log.info('Args: {}'.format(sys.argv))
        from qtpy import QT_VERSION
        log.info('Qt: {} Api:'.format(QT_VERSION))
    except Exception as e:
        log.exception(e)


def main():
    """ Setup logging then load and run the Inkcut application. If any errors
    occur that aren't handled by the application ensure they get logged.

    """
    init_logging()
    log = logging.getLogger('inkcut')
    log.info('='*40)
    log.info('Inkcut launched')
    log_debug_info(log)
    log.info('='*40)

    try:
        from inkcut.core.workbench import InkcutWorkbench
        workbench = InkcutWorkbench()
        workbench.run()
        log.info('='*40)
        log.info('Inkcut exited cleanly')
        log.info('='*40)
    except Exception as e:
        log.error(traceback.format_exc())
        raise


if __name__ == '__main__':
    main()

