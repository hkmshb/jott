"""Defines the base class for errors in jott.
"""
import sys
import logging

log = logging.getLogger('jott')


def get_error_msg(error):
    """Returns the message to show for an error.

    :param error: error object or string
    :returns: 2-tuple of: message string and a boolean indicating whether
              a traceback should be shown or not
    """
    if isinstance(error, Error):
        # expected error
        return error.msg, False
    elif isinstance(error, EnvironmentError):
        # normal error e.g. OSError, IOError
        msg = error.strerror
        if hasattr(error, 'filename') and error.filename:
            msg += ': ' + error.filename
        return msg, False
    else:
        # unexpected error
        msg = _('Looks like you found a bug')
        return msg, True


def log_error(error, debug=None):
    """Log error and traceback.

    :param error: error as understood by 'get_error_msg()'
    :param debug: optional debug message, defaults to the error itself
    """
    msg, show_trace = get_error_msg(error)
    if debug is None:
        debug = msg
    if show_trace:
        # unexpected error - will be logged with traceback
        log.exception(debug)
    else:
        # expected error - log trace to debug
        log.debug(debug, exc_info=1)
        log.error(msg)


def _run_error_dialog(error):
    raise NotImplementedError()


def show_error(error):
    """Show an error by calling 'log_error()' and when running interactive
    also calling ErrorDialog.

    :param error: the error object.
    """
    log_error(error)
    _run_error_dialog(error)


def exception_handler(debug):
    """Like 'show_error()' but with debug message instead of the actual error.
    Intended to be used in 'except' blocks as a catch-all for both intended and
    unintended errors.

    :param debug: debug message for logging
    """
    # we use debug as log message, rather than the error itself
    # the error itself shows up in the traceback anyway
    exc_info = sys.exc_info()
    error = exc_info[1]
    del exc_info    # recommended by manual

    log_error(error, debug=debug)
    _run_error_dialog(error)


class Error(Exception):
    """Base class for all errors in jott.

    This class is intended for application and usage errors, these will be
    caught in the user interface and presented as error dialogs.

    In contrast an Exception that does not derive from this base class will
    result in a "You found a bug" dialog. Do not use this class e.g. to catch
    programming errors.

    Subclasses should define two attributes. The first is 'msg', which is the
    short description of the error. Typically this gives the specific input /
    page / ... which caused the error. The other attribute is 'description'
    which can be less specific but should explain the error in a user friendly
    way.
    """
    description = ''
    msg = '<Unknown Error>'

    def __init__(self, msg, description=None):
        self.msg = msg
        if description:
            self.description = description
            # else class attribute is used

    def __repr__(self):
        return "<{}: {}>".format(
            self.__class__.__name__,
            self.msg
        )

    def __str__(self):
        msg = '' + self.msg.strip()
        if self.description:
            msg += '\n\n' + self.description.strip() + '\n'
        return msg
