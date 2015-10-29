import functools


def log_exceptions(logger):
    def decorator(f):
        """A decorator which will log stack traces for us. This is really useful
        for debugging exceptions that occur in background tasks."""
        @functools.wraps(f)
        def wrapped_with_logging(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                logger.exception(e)
                raise
        return wrapped_with_logging
    return decorator
