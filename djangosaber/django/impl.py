from djangosaber.util import key

import six
import logging
logging.basicConfig(level=logging.debug)

# logger = logging.getLogger(__file__)
# logger.setLevel(logging.debug)

class OrmMixin(object):
    _memory = None

    def objects(self):
        return self

    def all(self):
        return self

    def first(self):
        return self[0]

    @property
    def pk(self):
        return self.id

    def values_list(self, *args, **kwargs):
        keys = list(args) or self._memory.fields[self._name].values().keys()
        flat = kwargs.get('flat', False)
        if flat:
            return list(map(lambda x: getattr(x, keys[0]), self))
        return list(map(lambda x: {k:getattr(x, k) for k in keys}, self))

class Iterse(OrmMixin, list):

    def __init__(self, data, model=None):
        super(Iterse, self).__init__(data)
        self.model = model

    def __hash__(self):
        return id(self)

class Traverse(OrmMixin, object):

    def __init__(self, data, name=None, model=None):
        for k,v in six.iteritems(data):
            setattr(self, k, v)
        self._name = name
        self.model = model

    def __hash__(self):
        return id(self)

    def lookup(self, key, rel_id, id, index_key=None, index_val=None):
        #logging.debug("lookup: %s, %s, %s, %s, %s"%(key,rel_id,id, index_key, index_val))
        if not self._memory.is_indexed:
            return [k for k in self._memory.data[key] if getattr(k, rel_id) == id]
        else:
            return self.index_lookup(index_key or key, id, key, rel_id=rel_id)

    def index_lookup(self, tbl, id, rel_key, rel_id=''):
        #logging.debug("index.lookup: %s, %s, %s"%(tbl,id,rel_key))
        if rel_key is None or rel_id in ['id', 'pk']:
            return self._memory.index.get(key(tbl, str(id)))
        return Iterse(self._memory.index.get(key(tbl, str(id), rel_key), []))

