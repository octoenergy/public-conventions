# Python

Contents:

- [`CharField` choices](#charfield-choices)
- [Model field naming conventions](#model-field-naming-conventions)
- [Encapsulate model mutation](#encapsulate-model-mutation)
- [Group methods and properties on models](#group-methods-and-properties-on-models)
- [Import modules, not objects](#import-modules-not-objects)
- [Application logic in interface layer](#application-logic-in-interface-layer)
- [Don't do nothing silently](#dont-do-nothing-silently)
- [Docstrings vs comments](#docstrings)


## `CharField` choices

The values stored in the database should be uppercase and separated with
underscores. A human-readable version should also be added in the tuples
provided to the field.

```python
TELESALES, FIELD_SALES = "TELESALES", "FIELD_SALES"
CHANNEL_CHOICES = (
    (TELESALES, "Telesales"),
    (FIELD_SALES, "Field-sales"),
)
channel = models.CharField(max_length=128, choices=CHANNEL_CHOICES)
```

## Model field naming conventions

`DateTimeField`s should generally have suffix `_at`. For example:

- `created_at`
- `sent_at`
- `period_starts_at`

There are some exceptions such as `available_from` and `available_to`.

`DateField`s should have suffix `_date`:

- `billing_date`
- `supply_date`

This convention also applies to variable names.


## Encapsulate model mutation

Don't call a model's `save` method from anywhere but "mutator" methods on the
model itself. This provides a useful overview of the lifecycle of a model as you
can see all the ways it can mutate in once place.

Similarly, avoid calling `SomeModel.objects.create` or even
`SomModel.related_objects.create` from outside of the model itself. Encapsulate
these in "factory" methods (classmethods for the `objects.create` call).

Inspiration:

- [Django models, encapsulation and data integrity](https://www.dabapps.com/blog/django-models-and-encapsulation/), by Tom Christie


## Group methods and properties on models

To keep models well organised and easy to understand, group their methods and
properties into these groups using a comment:

- Factories 
- Mutators
- Queries 
- Properties

Contrived example:

```python
class SomeModel(models.Model):
    name = models.CharField(max_length=255)

    # Factories

    @classmethod
    def new(cls, name):
        return cls.objects.create(name=name)

    # Mutators

    def anonymise(self):
        self.name = ''
        self.save()

    def update_name(self, new_name):
        self.name = new_name
        self.save()

    # Queries

    def num_apples(self):
        return self.fruits.filter(type="APPLE").count()


    # Properties

    @property
    def is_call_dave(self):
        return self.name.lower() == "dave"
```


## Import modules, not objects

Instead of:

```python
from django.http import (
    HttpResponse, HttpResponseRedirect, HttpResponseBadRequest)
from django.shortcuts import render, get_object_or_404
```

prefer:

```python
from django import http, shortcuts
```

This keeps the module namespace cleaner and less like to have accidental
collisions. It also makes the module more concise and readable.

## Application logic in interface layer

Interface code like view modules and management command classes should contain
no application logic. It should all be extracted into other modules so other
"interfaces" can call it if they need to.

The role of interface layers is simply to translate transport-layer
requests (like HTTP requests) into domain requests. And similarly, translate domain
responses into transport responses (eg convert an application exception into a
error HTTP response).

A useful thought exercise to go through when adding code to a view is to imagine
needing to expose the same functionality via a REST API or a management command.
Would anything need duplicating from the view code? If so, then this tells you
that there's logic in the view layer that needs extracting.

## <a name="dont-do-nothing-silently">Don't do nothing silently</a>

Avoid this pattern:

```python

def do_something(*args, **kwargs):
    if thing_done_already():
        return
    if thing_not_ready():
        return
    ...
```

where the function checks some condition and returns without doing anything.
From the caller's point of view, it can't tell whether the action was successful
or not.

It's much better to be explicit and use exceptions to indicate that an action
couldn't be taken. Eg:

```python

def do_something(*args, **kwargs):
    if thing_done_already():
        raise ThingAlreadyDone
    if thing_not_ready():
        raise ThingNotReady
    ...
```

Let the calling code decide if how to handle the situation where the action has
already happened or it pre-conditions aren't met. 

This does mean using lots of custom exception classes - but that is ok.


## <a name="docstrings">Docstrings vs. comments</a>

There is a difference:

* *Docstrings* are written between triple quotes within the function/class block. They explain
   what the function does and are written for people who might want to _use_ that
   function/class but are not interested in the implementation details.

* In contrast, *comments* are written as `# blah blah blah` and are written for
  people who want to _change_ or _extend_ the implementation.

It sometimes makes sense to use both next to each other, eg:

```python
def do_that_thing():
    """
    Perform some action and return some thing
    """
    # This has been implemented this way because of these crazy reason.
```

Related reading:

- http://stackoverflow.com/questions/19074745/python-docstrings-descriptions-vs-comments
