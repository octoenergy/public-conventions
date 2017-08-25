# Python

These are a series of conventions (to use) and anti-patterns (to avoid) for
writing Python and Django application code. They are intended to be an aid to
code-review in that common comments can reference a single detailed explanation.

Django:

- [`CharField` choices](#charfield-choices)
- [Model field naming conventions](#model-field-naming-conventions)
- [Encapsulate model mutation](#encapsulate-model-mutation)
- [Group methods and properties on models](#group-methods-and-properties-on-models)
- [Don't rely on implicit ordering of querysets](#implicit-ordering)
- [Only use `.get` with unique fields](#uniqueness)
- [Be conservative with model `@property` methods](#property-methods)

Application:

- [Publishing events](#events)
- [Triggering Celery tasks](#celery-tasks)

General python:

- [Import modules, not objects](#import-modules-not-objects)
- [Application logic in interface layer](#application-logic-in-interface-layer)
- [Don't do nothing silently](#dont-do-nothing-silently)
- [Docstrings vs comments](#docstrings)

Testing:

- [Test folder structure](#test-folder-structure)
- [Test class structure ](#test-class-structure)
- [Test method structure ](#test-method-structure)


## Django


### `CharField` choices

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


### Model field naming conventions

`DateTimeField`s should generally have suffix `_at`. For example:

- `created_at`
- `sent_at`
- `period_starts_at`

There are some exceptions such as `available_from` and `available_to` but stick
with the convention unless you have a very good reason not to.

`DateField`s should have suffix `_date`:

- `billing_date`
- `supply_date`

This convention also applies to variable names.


### Encapsulate model mutation

Don't call a model's `save` method from anywhere but "mutator" methods on the
model itself. 

Similarly, avoid calling `SomeModel.objects.create` or even
`SomModel.related_objects.create` from outside of the model itself. Encapsulate
these in "factory" methods (classmethods for the `objects.create` call).

Doing this provides a useful overview of the lifecycle of a model as you
can see all the ways it can mutate in once place.

Also, this practice leads to better tests as you have a simple, readable method
to stub when testing units that call into the model layer.

Further reading:

- [Django models, encapsulation and data integrity](https://www.dabapps.com/blog/django-models-and-encapsulation/), by Tom Christie


### Group methods and properties on models

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

### <a name="uniqueness">Only use `.get` with unique fields</a>

Ensure calls to `.objects.get` and `.objects.get_or_create` use fields that have
a uniqueness constraint across them. If the fields aren't guaranteed to be
unique, use `.objects.filter`.

Don't do this:

```python
try:
    thing = Thing.objects.get(name=some_value)
except Thing.DoesNotExist:
    pass
else:
    thing.do_something()
```

unless the `name` field has a `unique=True`. Instead do this:

```python
things = Thing.objects.filter(name=some_value)
if things.count() == 1:
    things.first().do_something()
```

The same applies when looking up using more than one field.

This implies we never need to catch `MultipleObjectsReturned`.


### <a name="implicit-ordering">Don't rely on implicit ordering of querysets</a>

If you grab the `.first()` or `.last()` element of a queryset, ensure you
explicitly sort it with `.order_by()`. Don't rely on the default ordering set
in the `Meta` class of the model as this may change later on breaking your
assumptions.


### <a name="property-methods">Be conservative with model `@property` methods</a>

It's not always obvious when to decorate a model method as a property. Here
are some rules-of-thumb:

A property method should not trigger a database call. Don't do this:

```python
@property
def num_children(self):
    return self.kids.count()
```

Use a method instead.

Property methods should generally just derive a new value from the fields on
the model. A common use-case is predicates like:

```python
@property
def is_closed(self):
    return self.status == self.CLOSED
```


## Application

### <a name="events">Publishing events</a>

When publishing application events, the `params` should be things that are known
*before* the event, while `meta` should be things known *after* the event as
well as general contextual fields that aren't directly related to the event
itself (like a request user-agent).

Example:

```python
result = do_something(foo, bar)

events.publish(
    event=events.types.SOMETHING_WAS_DONE,
    params={
        'foo': foo,
        'bar': bar,
    },
    meta={
        'result': result
    })
```

### <a name="celery-tasks">Triggering Celery tasks</a>

Care is required when changing Celery task signatures as publishers and
consumers get deployed at different times. It's important that changes to how an
event is published don't cause consumers to crash.

To protect against this, we should do two things:

1. Celery tasks should always be called by passing kwargs (not args). Eg:

```python
some_tasks.apply_async(kwargs={'arg1': 1, 'arg2': 2}, queue="some-queue")
```

2. Task functions should accept `*args` and `**kwargs` in their signature to 
   allow them to handle changes in the published args without crashing
   immediately.

Together these two steps will provide some robustness to signature changes but
they are not watertight.

For frequently called tasks (that may be in-flight during a deployment), a
two-phase approach is required (similar to how backwards-incompatible database
migrations are handled).

First the consumer function needs to be updated to handle both the old and new way
of calling it (this may be to return new payloads to the queue if they can't be
handled). This then needs to be deployed.

Second, the publisher and consumer can be modified to use the new calling
args/kwargs. When this deploys, the older consumers should handle any published
events gracefully before they are terminated.


## Python 


### Import modules, not objects

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

Further, it fosters writing isolated unit tests in that it works well with
`mock.patch.object` to fake/stub/mock _direct_ collaborators of the
system-under-test. Using the more general `mock.patch` often leads to accidental integration tests 
as an indirect collaborator (several calls away) is patchd.


Eg:

```python
import mock
from somepackage import somemodule

@mock.patch.object(somemodule, 'collaborator')
def test_a_single_unit(collaborator):
    somemodule.somefunction(1)
    collaborator.assert_called_with(value=1)
```

Remember, in the long term, slow integration tests will rot your test suite.
Fast isolated unit tests keep things healthy. 

### Application logic in interface layer

Interface code like view modules and management command classes should contain
no application logic. It should all be extracted into other modules so other
"interfaces" can call it if they need to.

The role of interface layers is simply to translate transport-layer
requests (like HTTP requests) into domain requests. And similarly, translate domain
responses into transport responses (eg convert an application exception into a
HTTP error response).

A useful thought exercise to go through when adding code to a view is to imagine
needing to expose the same functionality via a REST API or a management command.
Would anything need duplicating from the view code? If so, then this tells you
that there's logic in the view layer that needs extracting.


### <a name="dont-do-nothing-silently">Don't do nothing silently</a>

Avoid this pattern:

```python

def do_something(*args, **kwargs):
    if thing_done_already():
        return
    if preconditions_not_met():
        return
    ...
```

where the function makes some defensive checks and returns without doing
anything if these fail. From the caller's point of view, it can't tell whether
the action was successful or not. This leads to subtle bugs.

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

Let the calling code decide how to handle cases where the action has
already happened or the pre-conditions aren't met. The calling code is usually
in the best place to decide if doing nothing is the right action.

If you _really_ doesn't matter if the action succeeds or fails from the caller's
point-of-view (a "fire-and-forget" action), then use a wrapper function that
delegates to the main function but swallows all exceptions:

```python

def do_something(*args, **kwargs):
    try:
        _do_something(*args, **kwargs)
    except (ThingsAlreadyDone, ThingNotReady):
        # Ignore these cases
        pass

def _do_something(*args, **kwargs):
    if thing_done_already():
        raise ThingAlreadyDone
    if thing_not_ready():
        raise ThingNotReady
    ...
```

This practice does mean using lots of custom exception classes (which some people are
afraid of) - but that is ok.


### <a name="docstrings">Docstrings vs. comments</a>

There is a difference:

* **Docstrings** are written between triple quotes within the function/class block. They explain
   what the function does and are written for people who might want to _use_ that
   function/class but are not interested in the implementation details.

* In contrast, **comments** are written as `# blah blah blah` and are written for
  people who want to understand the implementation so they can _change_ or _extend_ it.

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


## Testing

### <a name="test-folder-structure">Test folder structure</a>

Tests are organised by their type:

- `tests/unit/` - Isolated unit tests that test the behaviour of a single unit.
    Collaborators should be mocked.  No database or network access is permitted.

- `tests/integration/` - For testing several units and how they are plumbed
    together. These often require database access and use factories for set-up.
    These are best avoided in favour or isolated unit tests (to drive
    design) and end-to-end functional tests (to help us sleep better at night
    knowing things work as expected).

- `tests/functional/` - For end-to-end tests designed to check everything is
    plumbed together correctly. These should use webtest or Django's
    `call_command` function to trigger the test and only patch third party
    calls.


### <a name="test-class-structure">Test class structure</a>

The folder path of a test module should mirror the structure of the module it's testing. 
Eg `octoenergy/path/to/something.py` should have tests in
`tests/path/to/test_something.py`.

For each function/class being tested, use a test class to group its tests. Eg:

```python
from somewhere import some_function


class TestSomeFunction:

    def test_does_something_in_a_certain_way(self):
        ...

    def test_does_something_in_a_different_way(self):
        ...
```

Name the test methods so that they complete a sentence started by the test class
name. This is done in the above example to give:

- "test some_function does something in a certain way"
- "test some_function does something in a different way"

In this way, ensure the names accurately describe what the test is testing.


### <a name="test-method-structure">Test method structure</a>

A unit test has three steps:

- ARRANGE: put the world in the right state for the test
- ACT: call the unit under test (and possibly capture its output)
- ASSERT: assert that the right output was returned (or the right calls to
    collaborators were made).

To aid readability, organise your test methods in this way, adding a blank line
between each step. Trivial example:

```python
class TestSomeFunction:

    def test_does_something_in_a_certain_way(self):
        input = {'a': 100}

        output = some_function(input)

        assert output == 300 
```
This applies less to functional tests which can make many calls to the system.
