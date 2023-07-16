# Python

These are a series of conventions (to follow) and anti-patterns (to avoid) for
writing Python and Django application code. They are intended to be an aid to
code-review in that common comments can reference a single detailed explanation.

- [Wrap with parens not backslashes](#wrapping)
- [Make function signatures explicit](#make-function-signatures-explicit)
- [Import modules, not objects](#import-modules-not-objects)
- [Convenience imports](#convenience-imports)
- [Application logic in interface layer](#application-logic-in-interface-layer)
- [Don't do nothing silently](#dont-do-nothing-silently)
- [Docstrings vs comments](#docstrings)
- [Prefer American English for naming modules and objects](#naming-language)

## <a name="wrapping">Wrap with parens not backslashes</a>

That is, prefer:

```python
from path.to.some.module import thing1, thing2, thing3, thing4
```

over:

```python
from path.to.some.module import thing1, thing2, thing3, thing4
```

## Make function signatures explicit

Specify all the parameters you expect your function to take whenever possible. Avoid `*args` and `**kwargs`
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

Of course, there are plenty of good use cases for `**kwargs`, such as making Celery tasks backward
compatible, or in class based views, but they come with a cost, so use them sparingly.

### Using `**kwargs` in functions with many parameters

A particularly tempting use of `**kwargs` is when a function is passing a large number of parameters around,
for example:

```python
def main():
    do_something(
        one=1, two=2, three=3, four=4, five=5, six=6, seven=7, eight=8, nine=9, ten=10
    )


def do_something(**kwargs):  # Don't do this.
    _validate(**kwargs)
    _execute(**kwargs)
```

This isn't a good use of dynamic parameters, as it makes the code even harder to work with.

At a minimum, specify the parameters explicitly. However, many parametered functions are a smell, so you could
also consider fixing the underlying problem through refactoring. One option is the
[Introduce Parameter Object](https://sourcemaking.com/refactoring/introduce-parameter-object) technique, which
introduces a dedicated class to pass the data.

## Import modules, not objects

Usually, you should import modules rather than their objects. Instead of:

```python
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
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


@mock.patch.object(somemodule, "collaborator")
def test_a_single_unit(collaborator):
    somemodule.somefunction(1)
    collaborator.assert_called_with(value=1)
```

Remember, in the long term, slow integration tests will rot your test suite.
Fast isolated unit tests keep things healthy.

### When to import objects directly

Avoiding object imports isn't a hard and fast rule. Sometimes it can significantly
impair readability. This is particularly the case with commonly used objects
in the standard library. Some examples where you should import the object instead:

```python
from decimal import Decimal
from typing import Optional, Tuple, Dict
from collections import defaultdict
```

## Convenience imports

A useful pattern is to import the "public" objects from a package into its
`__init__.py` module to make life easier for calling code. This does need to be
done with care though - here's a few guidelines:

### Establish a canonical import path by prefixing private module names with underscores

One danger of a convenience import is that it can present two different ways to access an object, e.g.:
`mypackage.something` versus `mypackage.foo.something`.

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

### Don't use wildcard imports

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

### Only use convenience imports in leaf-node packages

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

### Don't expose modules as public objects in `__init__.py`

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

## Application logic in interface layer

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

## <a name="dont-do-nothing-silently">Don't do nothing silently</a>

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

## <a name="docstrings">Docstrings vs. comments</a>

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

## <a name="naming-language">Prefer American English for naming modules and objects</a>

When naming objects like modules, classes, functions and variables, prefer American English. Eg, use serializers.py instead of serialisers.py. This ensures the names in our codebase match those in the wider ecosystem.

UK spellings are fine in comments or docstrings.
