from djangosaber.cache.threaded import DictCachedMixin
from djangosaber.saber import Traverse
import operator

from cachetools import cachedmethod

class TraverseCached(Traverse, DictCachedMixin):
    @cachedmethod(operator.attrgetter('_cache'))
    def lookup(self, key, rel_id, id):
        return super(TraverseCached, self).lookup(key, rel_id, id)

class DictTraverse(Traverse):
    def __getitem__(self, key):
        return dict.__getitem__(self, key)
