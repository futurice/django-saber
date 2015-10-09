django-saber
==============
* [django-saber](https://github.com/futurice/django-saber) [![Build Status](https://travis-ci.org/futurice/django-saber.svg?branch=master)](https://travis-ci.org/futurice/django-saber)

Saber provides a drop-in replacement for the Django ORM for dealing with a defined database set. All Model attributes, methods and relations will work seamlessly -- faster.

Why
---

This library helped reduce the generation of an expensive report from 200 seconds to 1 second, by changing a prefetched queryset with an in-memory data representation.

* When you need to calculate a dataset in (near) real-time
* For read-only views

Usage
-----

Your Django project should separate concerns; that is, separate Models (fields) and Controllers (logic). This allows Saber to use the same logic.

``` eg.
class ThinController(object):
 def name_rhymes_with_orange(self): pass
  
class Thin(ThinController, models.Model):
 name = models.CharField(max_length=255)
```

To mimic Models, provide the module that has the model Controllers. By default, memory.initialize() will load the full database into memory.

```
memory = Memory(controllers=['test_project.controllers'])
memory.initialize()
database = Traverse(memory.data)
database.thin.all() 
database.thin[0].name
database.thin[0].name_rhymes_with_orange()
```

License
-------

BSD-3 see LICENSE
