# Python

These are a series of conventions (to follow) and anti-patterns (to avoid) for
writing Python and Django application code. They are intended to be an aid to
code-review in that common comments can reference a single detailed explanation.

Application:

- [Publishing events](#events)
- [Logging exceptions](#logging-exceptions)
- [Distinguish between anticipated and unanticipated exceptions](#distinguish-exceptions)
- [Exception imports](#exception-imports)
- [Celery tasks](#celery-tasks)
- [Keyword-arg only functions](#kwarg-only-functions)
- [Minimise system clock calls](#system-clock)
- [Modelling periods of time](#time-periods)

General Python:

- [Wrap with parens not backslashes](#wrapping)
- [Make function signatures explicit](#make-function-signatures-explicit)
- [Import modules, not objects](#import-modules-not-objects)
- [Convenience imports](#convenience-imports)
- [Application logic in interface layer](#application-logic-in-interface-layer)
- [Don't do nothing silently](#dont-do-nothing-silently)
- [Docstrings vs comments](#docstrings)
- [Prefer American English for naming modules and objects](#naming-language)

## Application

### <a name="events">Publishing events</a>

When publishing application events, the `params` should be things that are known
_before_ the event, while `meta` should be things known _after_ the event as
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

Prefer passing IDs of model instances rather than the instances of themselves.
Eg, prefer `params={'bill_id': bill.id}` to `params={'bill': bill}`.

Also, call `.isoformat()` on any dates or datetimes as that gives a more useful
string.

Prefer using the [reverse domain name notation](https://en.wikipedia.org/wiki/Reverse_domain_name_notation) naming convention for event type constants. This can aid performing queries in our logging platform.

Example:

```
COMMS_MESSAGE_SEND_SUCCESS = "comms.message.send-success"
COMMS_MESSAGE_SEND_ERROR = "comms.message.send-error"
```

Which then makes it easy to perform these three such queries.

```
# Only successful send message events
json.event:"comms.message.send-success"

# Only error send message events
json.event:"comms.message.send-error"

# All send message events (i.e. both success and error)
json.event:"comms.message.send-*"
```

### <a name="logging-exceptions">Logging exceptions</a>

Use `logger.exception` in `except` blocks but pass a useful message - don't just
pass on the caught exception's message. Don't even format the exception's
message into the logged message - Sentry will pick up the original exception
automatically.

Doing this enables Sentry to group the logged errors together rather than
treating each logged exception as a new error.
See [Sentry's docs](https://docs.sentry.io/clients/python/integrations/logging/#usage) for further info.

Don't do this:

```python
try:
    do_something()
except UnableToDoSomething as e:
    logger.exception(str(e))
```

or this:

```python
try:
    do_something()
except UnableToDoSomething as e:
    logger.exception("Unable to do something: %s" % e)
```

Instead, do this:

```python
try:
    do_something()
except UnableToDoSomething:
    logger.exception("Unable to do something")
```

If you do need to format data into the message string, don't use the `%`
operator. Instead, pass the parameters as args:
<https://docs.sentry.io/clients/python/integrations/logging/#usage>

```python
try:
    do_something(arg=x)
except UnableToDoSomething:
    logger.exception("Unable to do something with arg %s", x)
```

### <a name="distinguish-exceptions">Distinguish between anticipated and unanticipated exceptions</a>

When calling functions that can raise exceptions, ensure your handling
distinguishes between _anticipated_ and _unanticipated_ exceptions. It generally
makes sense to use separate exception classes for anticipated exceptions and to
log any other exceptions to Sentry:

For example:

```py
try:
    some_usecase.do_something()
except some_usecase.UnableToDoSomething:
    # We know about this failure condition. No code change is required so we
    # don't log the error to Sentry.
    pass
except Exception:
    # This is *unanticipated* so we log the exception to Sentry as some change is
    # required to handle this more gracefully.
    logger.exception("Unable to do something")
```

The rule of thumb is that anything logged to Sentry requires a code change to
fix it. If nothing can be done (ie a vendor time-out), publish an application
event instead.

### <a name="exception-imports">Exception imports</a>

Ensure exception classes are importable from the same location as functionality that
raise them.

For example, prefer:

```py
from octoenergy.domain import operations

try:
    operations.do_the_thing()
except operations.UnableToDoTheThing as e:
    ...
```

where the `UnableToDoTheThing` exception is importable from the `operations`
module, just like the `do_the_thing` function which can raise it.

This is simpler (ie fewer imports) and reads better than when the exception class lives elsewhere:

```py
from octoenergy.domain import operations
from octoenergy.somewhere.other import exceptions

try:
    operations.do_the_thing()
except exceptions.UnableToDoTheThing as e:
    ...
```

In general, be wary of re-using the same exception type for different use-cases;
this can lead to ambiguity and bugs. Furthermore, it rarely makes sense to have
`exceptions.py` modules of exception classes used in many places. In general,
prefer to define exception types in the same module as where they are raised.

### <a name="celery-tasks">Celery tasks</a>

Care is required when changing Celery task signatures as publishers and
consumers get deployed at different times. It's important that changes to how an
event is published don't cause consumers to crash.

To protect against this, Celery tasks should be defined like this:

```python
@app.task(queue=settings.MY_QUEUE)
def my_task(*, foo, bar, **kwargs):
    ...
````

and called like this:

```python
my_task.apply_async(kwargs={'foo': 1, 'bar': 2})
```

Things to note:

1. The task is declared with a specific queue. It's easier to troubleshoot queue
   issues if tasks are categorised like this. Note that the queue is specified when
   we declare the task, not when we trigger the task, as we want each specific task
   to be added to the same queue.
2. The task is called using `kwargs`, not `args` - and the task declaration uses a
   leading `*` to enforce this.
3. The task signature ends with ``**kwargs`` to capture any additional arguments. This
   simplifies the future addition of arguments, as older workers can still handle newer
   tasks without crashing.

These steps provide some robustness to signature changes but
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

### <a name="kwarg-only-functions">Keyword-only functions</a>

Python 3 supports keyword-only arguments where callers of a function HAVE to
pass kwargs (positional args get a `TypeError`). Syntax:

```python
    def f(*, name, age):
        ...
```

In general, prefer calling functions with kwargs where it's not immediately
obvious what the positional args are (ie most of the time). This
improves readability and makes collaborator tests clearer (i.e. writing the
`collaborator.assert_called_with(...)` assertion).

Further, _always_ use keyword-only args for "public" domain functions (ie
those which are called from the interface layer or from packages within the
domain layer).

### <a name="system-clock">Minimise system clock calls</a>

Avoid calls to the system clock in the domain layer of the application. That
is, calls to `localtime.now()`, `localtime.today()` etc. Think of such calls
like network or database calls.

Instead, prefer computing relevant datetimes or dates at the interface layer and
passing them in. This won't always be possible but often is.

Why?

1. This makes testing easier as you don't need to mock a system call. Your
   functions will be purer with controlled inputs and outputs.

2. It also avoids issues where Celery tasks are publishing on one day but get
   executed on another. It removes an assumption from the code.

Avoid the pattern of using a default of `None` for a date/datetime parameter
then calling the system clock to populate it if no value is explicitly passed.
Instead of:

```py
def some_function(*, base_date=None):
    if base_date is None:
        base_date = datetime.date.today()
    ...
```

prefer the more explicit:

```py
def some_function(*, base_date):
```

which forces callers to compute the date they want to use for the function.
As suggested above, such system-clock calls should be reserved for the interface
layer of your application and the value passed though into the
business-logic/domain layers.

### <a name="time-periods">Modelling periods of time</a>

It's common for domain objects to model some period of time that defines when an
object is "active" or "valid". When faced with this challenge, prefer to use
_datetime_ fields where the upper bound is nullable and exclusive. Eg:

```python
class SomeModel(models.Model):
    ...
    active_from = models.DateTimeField()
    active_to = models.DateTimeField(null=True)
```

Specifically, try and avoid using `datetime.date` fields as these are more error-prone
due to implicit conversion of datetimes and complications from daylight-savings
time.

Further, whether using `date`s or `datetime`s, allowing the upper bound to be
exclusive allows zero-length periods to be modelled, which is often required
(even if it isn't obvious that will be the case at first).

Don't follow this rule dogmatically: there will be cases where the appropriate
domain concept is a date instead of a datetime, but in general, prefer to model
with datetimes.

## Python

### <a name="wrapping">Wrap with parens not backslashes</a>

That is, prefer:

```python
from path.to.some.module import (
    thing1, thing2, thing3, thing4)
```

over:

```python
from path.to.some.module import \
    thing1, thing2, thing3, thing4
```

### Make function signatures explicit

Specify all the parameters you expect your function to take whenever possible. Avoid ``*args`` and ``**kwargs``
(otherwise known as [var-positional and var-keyword parameters](https://docs.python.org/3/glossary.html#term-parameter))
without good reason. Code with loosely defined function signatures can be difficult to work with, as it's unclear
what variables are entering the function.

```python
def do_something(**kwargs):  # Don't do this
   ...
```

Be explicit instead:

```python
def do_something(foo: int, bar: str):
   ...
```

This includes functions that wrap lower level functionality, such as model creation methods:

```python
class MyModel(models.Model):
    ...

    @classmethod
    def new(cls, **kwargs):  # Don't do this.
        return cls.objects.create(**kwargs)
```

Instead, do this:

```python
class MyModel(models.Model):
    ...

    @classmethod
    def new(cls, foo: int, bar: str):
        return cls.objects.create(foo=foo, bar=bar)
```

Of course, there are plenty of good use cases for ``**kwargs``, such as making Celery tasks backward
compatible, or in class based views, but they come with a cost, so use them sparingly.

#### Using ``**kwargs`` in functions with many parameters

A particularly tempting use of ``**kwargs`` is when a function is passing a large number of parameters around,
for example:

```python
def main():
    do_something(one=1, two=2, three=3, four=4, five=5, six=6, seven=7, eight=8, nine=9, ten=10)

def do_something(**kwargs):  # Don't do this.
   _validate(**kwargs)
   _execute(**kwargs)
```

This isn't a good use of dynamic parameters, as it makes the code even harder to work with.

At a minimum, specify the parameters explicitly. However, many parametered functions are a smell, so you could
also consider fixing the underlying problem through refactoring. One option is the
[Introduce Parameter Object](https://sourcemaking.com/refactoring/introduce-parameter-object) technique, which
introduces a dedicated class to pass the data.

### Import modules, not objects

Usually, you should import modules rather than their objects. Instead of:

```python
from django.http import (
    HttpResponse, HttpResponseRedirect, HttpResponseBadRequest)
from django.shortcuts import render, get_object_or_404
```

prefer:

```python
from django import http, shortcuts
```

This keeps the module namespace cleaner and less likely to have accidental
collisions. It also usually makes the module more concise and readable.

Further, it fosters writing simpler isolated unit tests in that import modules
works well with `mock.patch.object` to fake/stub/mock _direct_ collaborators of the
system-under-test. Using the more general `mock.patch` often leads to accidental integration tests
as an indirect collaborator (several calls away) is patched.

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

#### When to import objects directly

Avoiding object imports isn't a hard and fast rule. Sometimes it can significantly
impair readability. This is particularly the case with commonly used objects
in the standard library. Some examples where you should import the object instead:

```python
from decimal import Decimal
from typing import Optional, Tuple, Dict
from collections import defaultdict
```

### Convenience imports

A useful pattern is to import the "public" objects from a package into its
`__init__.py` module to make life easier for calling code. This does need to be
done with care though - here's a few guidelines:

#### Establish a canonical import path by prefixing private module names with underscores

One danger of a convenience import is that it can present two different ways to access an object, e.g.:
`mypackage.something` versus  `mypackage.foo.something`.

To avoid this, prefix modules that are accessible from a convenience import with an underscore, to indicate that they
are _private_ and shouldn't be imported directly by callers external to the parent package, e.g.:

```txt
mypackage/
    __init__.py  # Public API
    _foo.py
    _bar.py
```

It's okay for private and public modules to coexist in the same package, as long as the public modules aren't used in
convenience imports. For example, in the following structure we might expect calling code to access `mypackage.blue` and
`mypackage.bar.green`, but not `mypackage._foo.blue` or `mypackage.green`.

```txt
mypackage/
    __init__.py
    _foo.py  # Defines blue
    bar.py  # Defines green
```

#### Don't use wildcard imports

Don't use wildcard imports (ie `from somewhere import *`), even if each imported
module specifies an `__all__` variable.

Instead of:

```py
# hallandoates/__init__.py
from ._problems import *
from ._features import *
```

prefer:

```py
# hallandoates/__init__.py
from ._problems import ICantGoForThat, NoCanDo
from ._features import man_eater, rich_girl, shes_gone
```

Why?

- Wildcard imports can make it harder for maintainers to find where functionality lives.
- Wildcard imports can confuse static analysis tools like mypy.
- If submodules don't specify an `__all__` variable, a large number of objects
  can be inadvertently imported into the `__init__.py` module, leading to a danger of name collisions.

Fundamentally, it's better to be explicit (even if it is more verbose).

#### Only use convenience imports in leaf-node packages

Don't structure packages like this:

```txt
foo/
    bar/
        waldo/
            __init__.py
            thud.py
        __init__.py  # imports from _bar.py and _qux.py
        _bar.py
        _qux.py
```

where a non-leaf-node package, `foo.bar` has convenience imports in its
`__init__.py` module. Doing this means imports from subpackages like `foo.bar.waldo.thud`
will unnecessarily import everything in `waldo`'s `__init__.py` module. This is
wasteful and increases the change of circular import problems.

Only use convenience imports in leaf-node packages; that is, packages with no
subpackages.

#### Don't expose modules as public objects in `__init__.py`

If your package structure looks like:

```txt
foo/
    bar/
        __init__.py
        bar.py
        qux.py
```

don't do this:

```py
# foo/bar/__init__.py
import bar, qux
```

where the modules `bar` and `qux` have been imported.

It's better for callers to import modules using their explicit path rather than
this kind of trickery.

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

If it _really_ doesn't matter if the action succeeds or fails from the caller's
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

- **Docstrings** are written between triple quotes within the function/class block. They explain
   what the function does and are written for people who might want to _use_ that
   function/class but are not interested in the implementation details.

- In contrast, **comments** are written `# like this` and are written for
  people who want to understand the implementation so they can _change_ or _extend_ it. They will commonly
  explain _why_ something has been implemented the way it has.

It sometimes makes sense to use both next to each other, eg:

```python
def do_that_thing():
    """
    Perform some action and return some thing
    """
    # This has been implemented this way because of these crazy reasons.
```

Related reading:

- <http://stackoverflow.com/questions/19074745/python-docstrings-descriptions-vs-comments>

### <a name="naming-language">Prefer American English for naming modules and objects</a>

When naming objects like modules, classes, functions and variables, prefer American English. Eg, use serializers.py instead of serialisers.py. This ensures the names in our codebase match those in the wider ecosystem.

UK spellings are fine in comments or docstrings.
