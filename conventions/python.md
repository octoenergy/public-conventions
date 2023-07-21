# Python

These are a series of conventions (to follow) and anti-patterns (to avoid) for
writing Python application code. They are intended to be an aid to code-review
in that common comments can reference a single detailed explanation.

- [Make function signatures explicit](#make-function-signatures-explicit)
- [Import modules, not objects](#import-modules-not-objects)
- [Favour singular nouns for class names](#favour-singular-nouns-for-class-names)
- [Name private things with a leading underscore](#name-private-things-with-a-leading-underscore)
- [Avoid naming collisions with a trailing underscore](#avoid-naming-collisions-with-a-trailing-underscore)
- [Convenience imports](#convenience-imports)
- [Application logic in interface layer](#application-logic-in-interface-layer)
- [Catching exceptions](#catching-exceptions)
- [Don't do nothing silently](#dont-do-nothing-silently)
- [Docstrings](#docstrings)
- [Docstrings vs comments](#docstrings-vs-comments)
- [Prefer American English for naming things](#prefer-american-english-for-naming-things)
- [Timeouts for HTTP requests](#timeouts-for-http-requests)
- [Use immutable types when modification is not required](#use-immutable-types-when-modification-is-not-required)
- [Favour attrs over dataclasses](#favour-attrs-over-dataclasses)

## Make function signatures explicit

Specify all the parameters you expect your function to take whenever possible.
Avoid `*args` and `**kwargs` (otherwise known as
[var-positional and var-keyword parameters](https://docs.python.org/3/glossary.html#term-parameter))
without good reason. Code with loosely defined function signatures can be
difficult to work with, as it's unclear what variables are entering the
function.

```python
def do_something(**kwargs):  # Don't do this
    ...
```

Be explicit instead:

```python
def do_something(foo: int, bar: str):
    ...
```

This includes functions that wrap lower level functionality, such as model
creation methods:

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

Of course, there are plenty of good use cases for `**kwargs`, such as making
Celery tasks backward compatible, or in class based views, but they come with a
cost, so use them sparingly.

### Using `**kwargs` in functions with many parameters

A particularly tempting use of `**kwargs` is when a function is passing a large
number of parameters around, for example:

```python
def main():
    do_something(
        one=1, two=2, three=3, four=4, five=5, six=6, seven=7, eight=8, nine=9, ten=10
    )


def do_something(**kwargs):  # Don't do this.
    _validate(**kwargs)
    _execute(**kwargs)
```

This isn't a good use of dynamic parameters, as it makes the code even harder to
work with.

At a minimum, specify the parameters explicitly. However, many parameterized
functions are a smell, so you could also consider fixing the underlying problem
through refactoring. One option is the
[Introduce Parameter Object](https://sourcemaking.com/refactoring/introduce-parameter-object)
technique, which introduces a dedicated class to pass the data.

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
works well with `mock.patch.object` to fake/stub/mock _direct_ collaborators of
the system-under-test. Using the more general `mock.patch` often leads to
accidental integration tests as an indirect collaborator (several calls away) is
patched.

E.g.:

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

Avoiding object imports isn't a hard and fast rule. Sometimes it can
significantly impair readability. This is particularly the case with commonly
used objects in the standard library. Some examples where you should import the
object instead:

```python
from decimal import Decimal
from typing import Optional, Tuple, Dict
from collections import defaultdict
```

## Favour singular nouns for class names

Try to use singular nouns as the names of Python classes. This tends to result
in more readable code, especially when dealing with collections of instances.

This applies to enums, too: for example, favour `Weekday` over `Weekdays`, as
it's grammatically correct to say 'this object is a weekday', not 'this object
is a weekdays'.

### Example

Consider a class named with a _plural_ noun: `UserDetails`. Naming a list of
these is awkward:

```python
user_details_list: list[UserDetails] = get_user_details_list(account)
```

A singular noun such as `UserProfile` is better, as we can just use the plural
form for the collection:

```python
user_profiles: list[UserProfile] = get_user_profiles(account)
```

### Tips for finding a singular noun when you have a plural

- As an alternative to `Options`, `Details` or `Preferences`, you can use
  `Profile` or `Specification` instead.
- An easy tweak is to add a noun that describes a collection (such as `Set` or
  `Batch`) to the end of a class name. For example, `EventBatch` is better than
  `Events`.
- [Look at a thesaurus](https://www.thesaurus.com/) - maybe there is already a
  singular form that you can use.

## Name private things with a leading underscore

When a function, class, method, module or module-level-variable should be
treated as _private_, prefix its name with an underscore. For example:

- A function or variable named `_foo` should not be used outside the module it's
  declared in.
- A class named `_Foo` should not be used outside the module it's declared in.
- A method named `_foo` should not be used except in the class it's declared on,
  or its subclasses.
- A module named `_foo.py` should not be imported directly except by its
  siblings or direct parent package (although see
  [the guidance on convenience imports](#convenience-imports) for some
  restrictions on this).

## Avoid name collisions by using a trailing underscore

Sometimes we really want to use a variable name that's already taken by built-in
or a library import.

An example is the word "property", which can mean at least two things:

- An instance of the `Property` class representing a real estate property in
  Kraken.
- [A Python property](https://docs.python.org/3/library/functions.html#property),
  with the decorator `@property` squatting most namespaces.

A trailing underscore prevents the name collision:

```python
property_ = account.default_current_property()
if not property_:
    raise payments_comms.UnableToNotifyCustomer("No property found for account")
```

```python
for transaction_ in invoice_queries.transactions(invoice):
    # We only need to record VAT lines for charges and credits.
    if not isinstance(transaction_, models.BillableItem):
        continue
```

Note that asking function callers to use underscore-suffixed kwargs might be a
bit too much. Better to find a different argument name. That is, instead of:

```python
def date_to_string(date_: Optional[date]) -> str:
    return date_.isoformat() if date_ else ""
```

prefer:

```python
def date_to_string(date_to_format: Optional[date]) -> str:
    return date_to_format.isoformat() if date_to_format else ""
```

## Convenience imports

A useful pattern is to import the "public" objects from a package into its
`__init__.py` module to make life easier for calling code. This does need to be
done with care though - here's a few guidelines:

### Establish a canonical import path by prefixing private module names with underscores

One danger of a convenience import is that it can present two different ways to
access an object, e.g.: `mypackage.something` versus `mypackage.foo.something`.

To avoid this, prefix modules that are accessible from a convenience import with
an underscore, to indicate that they are _private_ and shouldn't be imported
directly by callers external to the parent package, e.g.:

```txt
mypackage/
    __init__.py  # Public API
    _foo.py
    _bar.py
```

Note: you should only use this if all the modules in the package are private
(see below).

### Don't use convenience imports in packages with public children

Avoid using convenience imports in the `__init__.py` of any package containing
publicly-importable modules or subpackages (i.e. ones that aren't prefixed with
an underscore). This results in unnecessary imports when the public children are
imported, increasing bootstrap times and the chance of circular import problems.

For example, don't do this:

```txt
mypackage/
   __init__.py  # imports from _foo.py
   _foo.py
   bar.py
```

This is because when we import `mypackage.bar`, we are forced to import from
`_foo.py` too.

### Don't use wildcard imports

Don't use wildcard imports (i.e. `from somewhere import *`), even if each
imported module specifies an `__all__` variable.

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

- Wildcard imports can make it harder for maintainers to find where
  functionality lives.
- Wildcard imports can confuse static analysis tools like mypy.
- If submodules don't specify an `__all__` variable, a large number of objects
  can be inadvertently imported into the `__init__.py` module, leading to a
  danger of name collisions.

Fundamentally, it's better to be explicit (even if it is more verbose).

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

The role of interface layers is simply to translate transport-layer requests
(like HTTP requests) into domain requests. And similarly, translate domain
responses into transport responses (e.g. convert an application exception into a
HTTP error response).

A useful thought exercise to go through when adding code to a view is to imagine
needing to expose the same functionality via a REST API or a management command.
Would anything need duplicating from the view code? If so, then this tells you
that there's logic in the view layer that needs extracting.

## Catching exceptions

Don't use bare `except:` clauses; always specify the exception types that should
be caught.

Don't catch
[`BaseException`](https://docs.python.org/3.10/library/exceptions.html#BaseException)
(as this can block keyboard interrupts and system exits).

Further, only catch the
[`Exception`](https://docs.python.org/3.10/library/exceptions.html#Exception)
type in these cases:

1. **If you are re-raising the exception.** This is appropriate when you want to
   log the exception (to Sentry normally) but allow somewhere further up the
   call chain to handle it.

   ```py
   def do_the_thing():
       try:
           do_the_subthing()
       except Exception:
           # This is unexpected so let's log to Sentry.
           logger.exception("Unable to do the subthing")

           # Re-raise the exception so somewhere higher up in the call chain can
           # handle it.
           raise
   ```

2. **If you are re-raising a different exception.** This is appropriate if you
   want to ensure all errors from some component are converted into an
   `UnableTo`-style domain exception so callers don't have to worry about other
   types. Since we have a [convention to distinguish between anticipated and
   unanticipated exceptions][unanticipated], this would normally indicate
   something unanticipated has happened in your component and should be logged
   to Sentry for further investigation.

   ```py
   def do_the_thing():
       try:
           do_the_subthing()
       except Exception as e:
           # This is unexpected so let's log to Sentry.
           logger.exception("Unable to do the subthing")

           # Convert into a specific exception so callers of this function don't
           # have to worry about catching Exception.
           raise UnableToDoTheThing(...) from e
   ```

   Remember to chain the exceptions (using `raise ... from ...`) so it's clear
   the one exception lead to the other. This can be thought of as an "isolation
   point".

[unanticipated]: https://github.com/octoenergy/coding-conventions/blob/master/conventions/application.md#distinguish-between-anticipated-and-unanticipated-exceptions

3. **If you want to provide a better experience for the end user than the
   default exception handler.** E.g. it often makes sense to catch `Exception`
   in HTTP views so you can show a more meaningful error to the end user (than
   "Internal server error"). When doing this, the exception should always be
   logged to Sentry for further investigation. E.g

   ```py
   class MyView(generic.FormView):
       def form_valid(self, form):
           try:
               usecase.perform_action()
           except Exception:
               # This is unanticipated so let's log to Sentry...
               logger.exception("Unable to perform action")

               # ...and show a friendly message to the end user.
               msg = (
                   "Something went wrong when processing your submission. "
                   "We're going to look into it."
               )
               form.add_error(None, msg)
               return self.form_invalid(form)
   ```

## Don't do nothing silently

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
couldn't be taken. E.g.:

```python
def do_something(*args, **kwargs):
    if thing_done_already():
        raise ThingAlreadyDone
    if thing_not_ready():
        raise ThingNotReady
    ...
```

Let the calling code decide how to handle cases where the action has already
happened or the pre-conditions aren't met. The calling code is usually in the
best place to decide if doing nothing is the right action.

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

This practice does mean using lots of custom exception classes (which some
people are afraid of) - but that is okay.

## Docstrings

The first sentence of a function's docstring should complete this sentence:

> This function will ...

which helps enforce an imperative mood.

It's conventional (but not mandatory) to start docstrings with "test" for
predicates (boolean-returning) functions and "return" for query functions.

Further:

- Use a newline character after the initial `"""` and before the final `"""` and
  ensure the sentence ends with a period.

- In general, prefer type annotations to documenting parameter and return-value
  types in the docstring as this gives `mypy` a chance to catch possible type
  errors.

- But do document exceptions that a function can raise (as these can't be
  indicated using type annotations). Use this format (that PyCharm recognises):

```py
  """
  Do something with foo.

  :raises FooError: if the foo is bad
  """
```

For example:

```py
def is_meal_tasty(meal: Meal) -> bool:
    """
    Test if the passed meal is tasty or not.
    """
    ...
```

Related:
[PEP 257 - Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)

## Docstrings vs. comments

There is a difference:

- **Docstrings** are written between triple quotes within the function/class
  block. They explain what the function does and are written for people who
  might want to _use_ that function/class but are not interested in the
  implementation details.

- In contrast, **comments** are written `# like this` and are written for people
  who want to understand the implementation so they can _change_ or _extend_ it.
  They will commonly explain _why_ something has been implemented the way it
  has.

It sometimes makes sense to use both next to each other, e.g.:

```python
def do_that_thing():
    """
    Perform some action and return some thing.
    """
    # This has been implemented this way because of these crazy reasons.
```

Related reading:

- http://stackoverflow.com/questions/19074745/python-docstrings-descriptions-vs-comments

## Prefer American English for naming things

When naming objects like modules, classes, functions and variables, prefer
American English. For example, use `serializers.py` (US spelling) instead of
`serialisers.py` (UK spelling). This ensures the names in our codebase match
those in the wider Python ecosystem.

## Timeouts for HTTP Requests

Use the _requests_ library for making HTTP calls.

Consider using one of our helper classes like `HTTPClient` or `JSONClient` from
`octoenergy/services/services_base.py`. These classes wrap _requests_.

When communicating with an external dependency, include a timeout unless you
have a very good reason not to.

An example for HTTP requests:

```python3
requests.get(
    "https://my-external-service/",
    timeout=10
)
```

If you don't include a timeout, you risking leaving an end user waiting for an
unacceptable length of time, or having a worker process blocked doing nothing
useful.

The
[requests library documentation](https://requests.readthedocs.io/en/master/user/quickstart/#timeouts)
has this to say about timeouts:

> Nearly all production code should use this parameter in nearly all requests.
> Failure to do so can cause your program to hang indefinitely.

## Use immutable types when modification is not required

If you don't expect your data to be changed, consider making them
[immutable](https://en.wikipedia.org/wiki/Immutable_object).

For example, this might mean:

- Instead of `@attrs.define` use `@attrs.frozen`.
- Instead of `set` use `frozenset`.
- Instead of `list[object]` use `tuple[object, ...]` or
  `collections.abc.Sequence[object]`.

By reducing what data may vary, this approach can:

- Make code easier for developers to reason about.
- Let Mypy trust that data doesn't change, and better enable polymorphism.
  ([Immutable collections are covariant](https://mypy.readthedocs.io/en/stable/generics.html#variance-of-generic-types),
  where most mutable containers are invariant.)

Immutable types also have the advantage of being
[hashable](https://docs.python.org/3/glossary.html#term-hashable), so it's
possible to store them in sets or use them as keys in dictionaries.

### Immutable containers with mutable data

Be cautious when immutable containers (tuples, frozen `dataclasses` etc) contain
mutable data. You will not gain the full advantages of immutability. For
example, the outer container will not be hashable because it will still be
possible to modify the inner data.

It is recommended to use immutable structures
[all the way down](https://en.wikipedia.org/wiki/Turtles_all_the_way_down).

So, when you see something like this:

```python
@attrs.frozen
class Example:
    things: list[str]
```

It might be safer to change it to something like this:

```python
@attrs.frozen
class Example:
    things: tuple[str, ...]
```

## Favour attrs over dataclasses

When faced with a choice between using [`attrs`](https://www.attrs.org/) and
[`dataclasses`](https://docs.python.org/3/library/dataclasses.html), choose
`attrs`.

There are a number of advantages:

- The `attrs` library has a mostly-compatible superset of the functionality in
  `dataclasses`.
  - In other words,
    [`attrs` has more features](https://www.attrs.org/en/23.1.0/why.html#data-classes).
- It calls `super` in the generated `__init__` method: `dataclasses` lack of
  this has caused outages in the past!
- It uses less memory because it uses
  [`__slots__`](https://docs.python.org/3/reference/datamodel.html#slots) by
  default.
- It has a faster development iteration time, as a result of not being tied to
  Python's release schedule.
- Our codebase will be more consistent for only using one of these two very
  similar libraries.

### Use the new `attrs` naming scheme

Old versions of `attrs` had a
[cutesy naming convention which has now been deprecated](https://www.attrs.org/en/23.1.0/names.html).

The quickest way to check is by the imports. The new version imports `attrs`,
not `attr`.

The new API looks like this:

```python
import attrs

@attrs.define  # Note: this is mutable, but @attrs.frozen is often preferable.
class MyClass:
    value: int
```

The old API looked like this:

```python
import attr

@attr.s
class MyClass:
    value: int
```

### Further reading

- ["Why not data classes"](https://www.attrs.org/en/stable/why.html#data-classes)
  from attrs' docs.
