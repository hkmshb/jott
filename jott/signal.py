class SignalHandler:
    '''Wrapper for a signal handler method that allows blocking the handler
    for incoming signals. To be used as function decorator.

    The method will be replaced by a BoundSignalHandler object that supports
    a 'blocked()' method which returns a context manager to temporarily block
    a callback.

    Intended to be used as::

        class Foo():
            @SignalHandler
            def on_changed(self):
                ...

            def update(self):
                with self.on_changed.blocked():
                    # do something that results in a "changed" signal
    '''

    def __init__(self, func):
        self._func = func

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            name = '_bound_' + self._func.__name__
            if not hasattr(instance, name) \
                or getattr(instance, name) is None:
                bound_obj = BoundSignalHandler(instance, self._func)
                setattr(instance, name, bound_obj)
            return getattr(instance, name)


class BoundSignalHandler:

    def __init__(self, instance, func):
        self._instance = instance
        self._func = func
        self._blocked = 0

    def __call__(self, *args, **kwargs):
        if self._blocked == 0:
            return self._func(self._instance, *args, **kwargs)

    def _block(self):
        self._blocked += 1

    def _unblock(self):
        if self._blocked > 0:
            self._blocked -= 1

    def blocked(self):
        '''Returns a context manager that can be used to temporarily block a
        callback.
        '''
        return SignalHandlerBlockContextManager(self)


class SignalHandlerBlockContextManager:

    def __init__(self, handler):
        self.handler = handler

    def __enter__(self):
        self.handler._block()

    def __exit__(self, *exc_info):
        self.handler._unblock()
