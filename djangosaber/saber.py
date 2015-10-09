from django.apps import apps

import operator
import cachetools
from cachetools import LRUCache, cachedmethod

from djangosaber.cache import DictCachedMixin

class Memory(object):
    def __init__(self, controllers=[]):
        self._controllers = controllers

    def initialize(self, data=None):
        self.classes = self.model_classes()
        self.fields = self.model_fields()
        self.data = data or self.populate()
        Traverse._memory = self
        Iterse._memory = self

    def fmt(self, model, data):
        cls = self.model_classes()[model._meta.model_name]
        return Iterse([cls(k, name=model._meta.model_name, model=cls) for k in data], model)

    def populate(self):
        r = {}
        for model in apps.get_models():
            r[model._meta.model_name] = self.fmt(model, model.objects.all().values())
        return r
    
    def model_fields(self):
        r = {}
        for model in apps.get_models():
            rel = lambda k: k[0].related_model._meta.model_name if k[0].related_model else None
            rel_id = lambda k: k[0].field.attname if hasattr(k[0], 'field') else None
            name = lambda k: k[0].name
            r[model._meta.model_name] = {name(k):{'tbl':rel(k),'rel_id': rel_id(k)} for k in model._meta.get_fields_with_model()}
        return r

    def controllers(self, modules=[]):
        modules = modules or self._controllers
        r = {}
        for model in apps.get_models():
            r[model._meta.model_name] = []
            bases = model.__bases__
            for base in bases:
                if base.__module__ in modules:
                    r[model._meta.model_name].append(base)
        return r

    def model_classes(self):
        r = {}
        c = self.controllers()
        for model in apps.get_models():
            bases = (Traverse,) + tuple(c[model._meta.model_name])
            cls = type('Traverse_%s'%model._meta.model_name, bases, {})
            r[model._meta.model_name] = cls
        return r

class OrmMixin(object):
    _memory = None

    def all(self):
        return self

    def first(self):
        return self[0]

    @property
    def pk(self):
        return self['id']

    def values_list(self, *args, **kwargs):
        keys = list(args) or self._memory.fields[self._name].values().keys()
        flat = kwargs.get('flat', False)
        if flat:
            return map(lambda x: getattr(x, keys[0]), self)
        return map(lambda x: {k:getattr(x, k) for k in keys}, self)

class Iterse(OrmMixin, list):

    def __init__(self, data, model=None):
        super(Iterse, self).__init__(data)
        self.model = model

    def __hash__(self):
        return id(self)

def pred(rel_id, id):
    return lambda x: x[rel_id]==id

class Traverse(DictCachedMixin, OrmMixin, dict):

    def __init__(self, data, name=None, model=None):
        super(Traverse, self).__init__(data)
        self._name = name
        self.model = model

    def __hash__(self):
        return id(self)

    def rel_alias(self, tbl, key):
        if not self._name:
            return key
        alias = self._memory.fields[tbl].get(key)
        return alias['tbl'] if alias else key

    @cachedmethod(operator.attrgetter('_cache'))
    def lookup(self, key, rel_id, id):
        return list(filter(pred(rel_id, id), self._memory.data[key]))

    # 10-35% performance penalty with this method in place to support dict-lookups for DRF
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            if '%s_id'%key in self:
                return self.get_relation(key)
            raise

    def get_many_relation(self, key):
        key = self.rel_alias(self._name, key)
        key = key.replace('_set', '')
        my_id = self['id']
        rel_id = '%s_id'%self._name
        return Iterse(self.lookup(key, rel_id, my_id))

    def get_relation(self, key):
        x_id = '%s_id'%key
        key = self.rel_alias(self._name, key)
        value = self[x_id]
        values = self.lookup(key, 'id', value)
        if len(values) == 1:
            values = values[0]
        return values

    def get_reverse_relation(self, key):
        rel_key = self._memory.fields[self._name][key]['tbl']
        rel_id = self._memory.fields[self._name][key]['rel_id']
        my_id = self['id']
        return Iterse(filter(lambda x: x[rel_id]==my_id, self._memory.data[rel_key]))

    def __getattr__(self, key):
        if '_set' in key:
            return self.get_many_relation(key)
        if '%s_id'%key in self:
            return self.get_relation(key)
        try:
            return self[key]
        except KeyError:
            if key in self._memory.fields.get(self._name, {}):
                return self.get_reverse_relation(key)
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, key))
