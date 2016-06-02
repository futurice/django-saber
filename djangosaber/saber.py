from __future__ import absolute_import
from django.apps import apps

from collections import defaultdict
import operator
import six
import copy

import os, logging, datetime
logging.basicConfig(level=logging.DEBUG)

from djangosaber.util import key
from djangosaber.django.impl import Traverse, Iterse

def rel(model):
    return model.related_model._meta.model_name if model.related_model else None

def rel_id(model):
    return model.field.attname if hasattr(model, 'field') else None

def fk(self, a, pk, to):
    return Iterse(self.lookup(rel_id, key, my_id))

def get_fields_with_model(model):
    return [(f, f.model if f.model != model else None) for f in model._meta.get_fields()]

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

    def relational_methods(self, cls, name):
        for k,v in six.iteritems(self.model_rels()[name]):
            if not v['rel_id'] and not v['tbl']:
                continue
            if v['rel_id'] is None: # FK
                def _(key, rel_id, field, name):
                    @property
                    def _fk(self):
                        fk_id = getattr(self, '%s_id'%field)
                        if fk_id:
                            kw = {'key': key, 'rel_id': rel_id, 'id': fk_id}
                            rs = self.lookup(**kw)
                            # TODO: reverse FK scenario ended up here?
                            if isinstance(rs, list) and len(rs) == 1:
                                return rs[0]
                            return rs
                        return None
                    return _fk
                setattr(cls, k, _(key=v['tbl'], rel_id='id', field=k, name=name))
            else: # reverse FK
                def _(key, rel_id, field, name):
                    @property
                    def _fk(self):
                        fk_id = getattr(self, 'id')
                        kw = {'key': key, 'rel_id': rel_id, 'id': fk_id, 'index_key': name}
                        return Iterse(self.lookup(**kw))
                    return _fk
                # unless related_name=X set, then k is related field name
                if v['rel_id'] is None:
                    rel_id = '%s_id'%k
                else:
                    rel_id = v['rel_id']
                setattr(cls, k, _(key=v['tbl'], rel_id=rel_id, field=k, name=name))
                # TODO: _set needs to be without @property
                setattr(cls, '%s_set'%k, getattr(cls, k))

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

    def update_index(self, idx, v, tbl, field_name, relation):
        pk = getattr(v, 'id')
        self.index.setdefault(key(tbl, str(pk)), v)
        rel_data = []

        try:
            rel_data = getattr(v, relation, getattr(v, field_name))
        except KeyError as e:
            #logging.debug("Could not find relation: %s => %s"%(key(tbl,relation), e))
            return

        self.index[key(tbl, str(pk), relation)] = rel_data

    def create_index(self, tbl, field_name, relation):
        self.creating_index = True
        for k, v in enumerate(self.data[tbl]):
            self.update_index(k, v, tbl, field_name, relation)
        self.creating_index = False

    def create_indexes(self, exclude=[]):
        for name, fields in six.iteritems(self.fields):
            if name in exclude:
                continue
            # relation indexes
            for field_name, data in six.iteritems(fields):
                if data['tbl'] and data['tbl'] not in exclude:
                    self.create_index(name, field_name, data['tbl'])
        self.is_indexed = True
    
    def model_fields(self):
        r = {}
        for model in apps.get_models():
            rel = lambda k: k[0].related_model._meta.model_name if k[0].related_model else None
            rel_id = lambda k: k[0].field.attname if hasattr(k[0], 'field') else None
            name = lambda k: k[0].name
            r[model._meta.model_name] = {name(k):{'tbl':rel(k),'rel_id': rel_id(k)} for k in get_fields_with_model(model)}
        return r

    def model_rels(self):
        """
        rel_id = None|attrName
        - reverse FKs attrName on related table
        - None means FK is on this table
        rel = related table
        """
        r = {}
        for model in apps.get_models():
            r.setdefault(model._meta.model_name, {})
            for k in get_fields_with_model(model):
                if rel(k[0]) or rel_id(k[0]):
                    r[model._meta.model_name][k[0].name] = {'tbl':rel(k[0]),'rel_id': rel_id(k[0])}
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

    CLASSES = {}
    def model_classes(self):
        if self.CLASSES:
            return self.CLASSES
        r = {}
        c = self.controllers()
        for model in apps.get_models():
            bases = (Traverse,) + tuple(c[model._meta.model_name])
            cls = type('Traverse_%s'%model._meta.model_name, bases, {})

            # attach fk-methods to not need __getattr__
            self.relational_methods(cls, model._meta.model_name)

            r[model._meta.model_name] = cls
        self.CLASSES = r
        return r
