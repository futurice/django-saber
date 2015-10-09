from cachetools import LRUCache

import threading
_thread_locals = threading.local()

def threaded_cache(name='_cache'):
    if not hasattr(_thread_locals, name):
        set_cache(name)
    return getattr(_thread_locals, name)

def get_cache():
    return LRUCache(maxsize=20000)

def set_cache(name):
    setattr(_thread_locals, name, get_cache())

class ObjectCachedMixin(object):
    @property
    def _cache(self):
        return threaded_cache()

class DictCachedMixin(dict):
    @property
    def _cache(self):
        return threaded_cache()
