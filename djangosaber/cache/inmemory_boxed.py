import datetime
import functools
import logging
import hashlib
import math

CACHED = {}

def bucket(time):
    now = datetime.datetime.now()
    cur_second_today = now.hour*60*60 + now.minute*60 + now.second
    return str(int(math.floor(cur_second_today/time)))

def expire_stale_caches(time):
    cur_key = bucket(time)
    for key in list(CACHED.keys()):
        if key != cur_key:
            try:
                del CACHED[key]
            except KeyError:
                pass

def get_cache(key, time):
    try:
        return CACHED.get(bucket(time)).get(key)
    except AttributeError:
        return None

def set_cache(key, value, time):
    # TODO: finer expiration methods
    expire_stale_caches(time)

    CACHED.setdefault(bucket(time), {})[key] = value


def cachedfn(f, time=120):
    def _(*args, **kwargs):
        key = hashlib.sha256('%s%s%s' % (f.__name__, str(args), str(kwargs))).hexdigest()
        value = get_cache(key, time)
        if value is None:
            value = f(*args, **kwargs)
            set_cache(key, value, time)
        return value
    return _

def cached(time=120):
    """ Write and read to a timed-bucket. """
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            key = hashlib.sha256('%s%s%s' % (function.__name__, str(args), str(kwargs))).hexdigest()
            value = get_cache(key, time)
            if value is None:
                value = function(*args, **kwargs)
                set_cache(key, value, time)
            return value
        return wrapper
    return decorator
