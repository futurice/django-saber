from django.apps import apps

from collections import defaultdict
import operator
import six

import os, logging, datetime
# logging.basicConfig(level=logging.DEBUG)

def key(table, id='', relation=''):
    # logging.debug("key: {} {} {}".format(table, id, relation))
    return '.'.join([table, id, relation]).rstrip('.')

class Memory(object):
    def __init__(self, controllers=[]):
        self._controllers = controllers

    def initialize(self, data=None, exclude=[]):
        self.classes = self.model_classes()
        self.fields = self.model_fields()
        self.data = data or self.populate(exclude=exclude)
        self.index = defaultdict(dict)
        self.creating_index = False
        self.is_indexed = False
        Traverse._memory = self
        Iterse._memory = self

    def fmt(self, model, data):
        cls = self.model_classes()[model._meta.model_name]
        return Iterse([cls(k, name=model._meta.model_name, model=cls) for k in data], model)

    def populate(self, exclude=[]):
        r = {}
        for model in apps.get_models():
            if model._meta.model_name in exclude:
                continue
            r[model._meta.model_name] = self.fmt(model, model.objects.all().values())
        return r

    def create_index(self, tbl, field_name, relation):
        self.creating_index = True

        for k, v in enumerate(self.data[tbl]):
            pk = getattr(v, 'id')
            self.index.setdefault(key(tbl, str(pk)), k)
            rel_ids = []

            try:
                rel_data = getattr(v, relation, getattr(v, field_name))
            except KeyError as e:
                #logging.debug("Could not find relation: %s => %s"%(key(tbl,relation), e))
                continue

            if rel_data:
                if isinstance(rel_data, dict):
                    rel_data = [rel_data]
                rel_ids = map(operator.attrgetter('id'), rel_data)
            self.index[key(tbl, str(pk), relation)] = rel_ids
        self.creating_index = False

    def create_indexes(self, exclude=[]):
        """
        Create an index for data-lookups, stored as a map of keys to values.
        - direct lookups store the list index value
        - related lookups give the database ID
        """
        for name, fields in six.iteritems(self.fields):
            if name in exclude:
                continue
            # TODO: table index .get(pk=x) lookup
            self.index.setdefault(name, {})
            # relation indexes
            for field_name, data in six.iteritems(fields):
                if data['tbl']:
                    self.create_index(name, field_name, data['tbl'])
        self.is_indexed = True
    
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

    def objects(self):
        return self

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

class Traverse(OrmMixin, dict):

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

    def rel_alias_reverse(self, tbl, key):
        #logging.debug("rel_alias_reverse: %s, %s"%(tbl,key))
        for fieldname, v in six.iteritems(self._memory.fields[tbl]):
            if v['tbl'] == key:
                return v['rel_id'] if v['rel_id'] else fieldname
        raise Exception("Unknown reverse alias")

    def lookup(self, key, rel_id, id):
        #logging.debug("lookup: %s, %s, %s"%(key,rel_id,id))
        if not self._memory.is_indexed:
            return [k for k in self._memory.data[key] if k[rel_id] == id]
        else:
            return self.index_lookup(key, id, rel_id)

    def get_many_relation(self, key):
        #logging.debug("get_many_relation: %s"%key)
        orig_key = key
        key = self.rel_alias(self._name, key)
        key = key.replace('_set', '')
        my_id = self['id']
        if '_set' in orig_key:
            # TODO: this is a get_reverse_relation
            rel_id = '%s'%self._name
            vals = self.lookup(rel_id, key, my_id)
        else:
            rel_id = '%s_id'%self.rel_alias_reverse(key, self._name)
            vals = self.lookup(key, rel_id, my_id)

        return Iterse(vals)

    def get_relation(self, key):
        #logging.debug("get_relation: %s"%key)
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
        id = self['id']

        if not self._memory.is_indexed:
            return Iterse([k for k in self._memory.data[rel_key] if k[rel_id] == id])
        else:
            return self.index_lookup(self._name, id, rel_key)

    def index_lookup(self, tbl, id, rel_key):
        #logging.debug("index.lookup: %s, %s, %s"%(tbl,id,rel_key))
        rel_key_orig = rel_key
        if rel_key in ['id','pk']:
            rel_id = self._memory.index.get(key(tbl, str(id)))
            return self._memory.data[tbl][rel_id]
        rel_ids = self._memory.index.get(key(tbl, str(id), rel_key), [])
        #logging.debug("rel_ids: %s"%rel_ids)
        indexes = [self._memory.index[key(rel_key, str(k))] for k in rel_ids]
        return Iterse(self._memory.data[rel_key][k] for k in indexes)

    def __getattr__(self, key):
        #logging.debug("__getattr__: %s, %s"%(self._name, key))
        if '_set' in key:
            return self.get_many_relation(key)
        if '%s_id'%key in self:
            return self.get_relation(key)
        try:
            return self[key]
        except KeyError as e:
            if key in self._memory.fields.get(self._name, {}):
                return self.get_reverse_relation(key)
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, key))

