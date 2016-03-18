from djangosaber.cache.threaded import DictCachedMixin
from djangosaber.saber import Traverse
import operator

from cachetools import cachedmethod

class TraverseCached(Traverse, DictCachedMixin):
    @cachedmethod(operator.attrgetter('_cache'))
    def lookup(self, key, rel_id, id):
        return list(filter(pred(rel_id, id), self._memory.data[key]))

class DictTraverse(Traverse):
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            if '%s_id'%key in self:
                return self.get_relation(key)
            raise
