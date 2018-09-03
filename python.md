# Python

These are a series of conventions (to use) and anti-patterns (to avoid) for
writing Python and Django application code. They are intended to be an aid to
code-review in that common comments can reference a single detailed explanation.

Django:

- [`CharField` choices](#charfield-choices)
- [Model field naming conventions](#model-field-naming-conventions)
- [Class naming conventions](#class-naming-conventions)
- [Encapsulate model mutation](#encapsulate-model-mutation)
- [Group methods and properties on models](#group-methods-and-properties-on-models)
- [Don't rely on implicit ordering of querysets](#implicit-ordering)
- [Create filter methods on querysets, not managers](#queryset-filters)
- [Only use `.get` with unique fields](#uniqueness)
- [Be conservative with model `@property` methods](#property-methods)
- [Ensure `__str__` is unique](#unique-str)
- [Flash messages](#flash-messages)

Application:

- [Publishing events](#events)
- [Logging exceptions](#logging-exceptions)
- [Triggering Celery tasks](#celery-tasks)
- [Keyword-arg only functions](#kwarg-only-functions)
- [Minimise system clock calls](#system-clock)

General python:

- [Wrap with parens not backslashes](#wrapping)
- [Import modules, not objects](#import-modules-not-objects)
- [Application logic in interface layer](#application-logic-in-interface-layer)
- [Don't do nothing silently](#dont-do-nothing-silently)
- [Docstrings vs comments](#docstrings)

Testing:

- [Test folder structure](#test-folder-structure)
- [Test class structure ](#test-class-structure)
- [Unit test method structure ](#test-method-structure)
- [Functional test method structure ](#functional-test-method-structure)


## Django


### `CharField` choices

The values stored in the database should be uppercase and separated with
underscores. A human-readable version should also be added in the tuples
provided to the field.

```
TELESALES, FIELD_SALES = "TELESALES", "FIELD_SALES"
CHANNEL_CHOICES = (
    (TELESALES, "Telesales"),
    (FIELD_SALES, "Field-sales"),
)
channel = models.CharField(max_length=128, choices=CHANNEL_CHOICES)
```

This is because the database value is a code or symbol intended to be used
within application logic but not shown to the end user - making it uppercase
makes this distinction clear.  Using a human-readable version for the database
value can lead to bugs when a future maintainer wants to change the version
shown to the end user.


### Class naming conventions

Given we [import modules, not objects](#import-modules-not-objects), there's no need to suffix
view/form/serializer classes names with `View`/`Form`/`Serializer`.

Within a calling module, it's nicer to have:

```
from django.views import generic
from . import forms

class SetPassword(generic.FormView):
    form_class = forms.NewPassword
```

rather than:

```
from django.views import generic
from . import forms

class SetPassword(generic.FormView):
    form_class = forms.NewPasswordForm
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

```
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

### <a name="queryset-filters">Create filter methods on querysets, not managers</a>

Django’s model manager and queryset are similar, see the [docs](https://docs.djangoproject.com/en/stable/topics/db/managers/)
for an explanation of the differences. However, when creating methods that return a queryset we’re
better off creating these on a custom queryset class rather than a custom manager.

A manager method is only available on a manager or related-manager. So `Article.objects` or
`Author.articles`. They’re not available to querysets, which is what’s returned from a manager or
queryset method, so they cannot be chained. In the example below `my_custom_filter()` is a method
on a custom manager class, so an `AttributeError` is raised when attempting to call it from a
queryset, i.e. the return value of `.filter()`.

```
>>> Article.objects.my_custom_filter().filter(is_published=True)
<QuerySet [<Article (1)>, <Article (2)>]>
>>> Article.objects.filter(is_published=True).my_custom_filter()
AttributeError: 'QuerySet' object has no attribute 'my_custom_filter'
```

Below is an example of creating a custom queryset class and using it as a model’s manager. This
allows us to call it on both the manager and queryset.

```
class ArticleQuerySet(models.QuerySet):

    def my_custom_filter(self):
        return self.filter(headline__contains='Lennon')


class Article(models.Model):

    objects = ArticleQuerySet.as_manager()
```

### <a name="uniqueness">Only use `.get` with unique fields</a>

Ensure calls to `.objects.get` and `.objects.get_or_create` use fields that have
a uniqueness constraint across them. If the fields aren't guaranteed to be
unique, use `.objects.filter`.

Don't do this:

```
try:
    thing = Thing.objects.get(name=some_value)
except Thing.DoesNotExist:
    pass
else:
    thing.do_something()
```

unless the `name` field has a `unique=True`. Instead do this:

```
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

```
@property
def num_children(self):
    return self.kids.count()
```

Use a method instead.

Property methods should generally just derive a new value from the fields on
the model. A common use-case is predicates like:

```
@property
def is_closed(self):
    return self.status == self.CLOSED
```


### <a name="unique-str">Ensure `__str__` is unique</a>

Ensure the string returned by a model's `__str__` method uniquely identifies
that instance.

This is important as Sentry (and other tools) often just print `repr(instance)`
of the instance (which prints the output from `__str__`). When debugging, it's
important to know exactly which instances are involved in an error, hence why
this string should uniquely identify a single model instance.


### <a name="flash-messages">Effective flash messages</a>

Flash messages are those one-time messages shown to users after an action has
been performed. They are triggered using the `django.contrib.messages` package,
normally from within a view class/function.

Here's a few tips.

- Don't say "successfully" in flash messages (eg "The thing was updated
  successfully"). Prefer a more active tone (eg "The thing was updated").

- Don't include IDs that are meaningless to the end user (eg "Thing 1234 was
  updated").

- Consider including links to related resources that might be a common next step
  for the user. HTML can be included in flash messages

  ```
  msg = (
      '<h4>Some heading</h4>'
      '<p>An action was performed. Now do you want to <a href="%s">do the next thing</a>.</p>'
  ) % next_thing_url
  messages.success(request, msg, extra_tags='safe')
  ```

  Note the `safe` tag which allow HTML to be included in the message.



## Application

### <a name="events">Publishing events</a>

When publishing application events, the `params` should be things that are known
*before* the event, while `meta` should be things known *after* the event as
well as general contextual fields that aren't directly related to the event
itself (like a request user-agent).

Example:

```
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

### <a name="logging-exceptions">Logging exceptions</a>

Use `logger.exception` in `except` blocks but pass a useful message - don't just
pass on the caught exception's message. Don't even format the exception's
message into the logged message - Sentry will pick up the original exception
automatically.

Doing this enables Sentry to group the logged errors together rather than
treating each logged exception as a new error.
See [Sentry's docs](https://docs.sentry.io/clients/python/integrations/logging/#usage) for further info.

Don't do this:

```
try:
    do_something()
except UnableToDoSomething as e:
    logger.exception(str(e))
```

or this:

```
try:
    do_something()
except UnableToDoSomething as e:
    logger.exception("Unable to do something: %s" % e)
```

Instead, do this:

```
try:
    do_something()
except UnableToDoSomething:
    logger.exception("Unable to do something")
```

If you do need to format data into the message string, don't use the `%`
operator. Instead, pass the parameters as args:
https://docs.sentry.io/clients/python/integrations/logging/#usage

```
try:
    do_something(arg=x)
except UnableToDoSomething:
    logger.exception("Unable to do something with arg %s", x)
```


### <a name="celery-tasks">Triggering Celery tasks</a>

Care is required when changing Celery task signatures as publishers and
consumers get deployed at different times. It's important that changes to how an
event is published don't cause consumers to crash.

To protect against this, we should do two things:

1. Celery tasks should always be called by passing kwargs (not args). Eg:

```
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

### <a name="kwarg-only-functions">Keyword-only functions</a>

Python 3 supports keyword-only arguments where callers of a function HAVE to
pass kwargs (positional args get a `TypeError`). Syntax:

```py
    def f(*, name, age):
        ...
```

In general, prefer calling functions with kwargs where it's not immediately
obvious what the positional args are (ie most of the time). This
improves readability and makes collaborator tests clearer (ie writing the
`collabator.assert_called_with(...)` assertion).

Further, _always_ use keyword-only args for "public" domain functions (ie
those which are called from the interface layer or from packages within the
domain layer).

### <a name="system-clock">Minimise system clock calls</a>

Avoids calls to the system clock in the domain layer of the application. That
is, calls to `localtime.now()`, `localtime.today()` etc. Think of such calls
like network or database calls.

Instead, prefer computing relevant datetimes or dates at the interface layer and
passing them in. This won't always be possible but often is.

Why?

1. This makes testing easier as you don't need to mock a system call.  Your
   functions will be purer with controlled inputs and outputs. 

2. It also avoids issues where Celery tasks are publishing on one day but get
   executed on another. It removes an assumption from the code. 

## Python 


### <a name="wrapping">Wrap with parens not backslashes</a>

That is, prefer:

```
from path.to.some.module import (
    thing1, thing2, thing3, thing4)
```

over:

```
from path.to.some.module import \
    thing1, thing2, thing3, thing4
```

### Import modules, not objects

Usually, you should import modules rather than their objects. Instead of:

```
from django.http import (
    HttpResponse, HttpResponseRedirect, HttpResponseBadRequest)
from django.shortcuts import render, get_object_or_404
```

prefer:

```
from django import http, shortcuts
```

This keeps the module namespace cleaner and less likely to have accidental
collisions. It also usually makes the module more concise and readable.

Further, it fosters writing simpler isolated unit tests in that import modules
works well with `mock.patch.object` to fake/stub/mock _direct_ collaborators of the
system-under-test. Using the more general `mock.patch` often leads to accidental integration tests
as an indirect collaborator (several calls away) is patched.

Eg:

```
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

```
from decimal import Decimal
from typing import Optional, Tuple, Dict
from collections import defaultdict
```

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

```

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

```

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

```

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

* In contrast, **comments** are written `# like this` and are written for
  people who want to understand the implementation so they can _change_ or _extend_ it. They will commonly
  explain _why_ something has been implemented the way it has.

It sometimes makes sense to use both next to each other, eg:

```
def do_that_thing():
    """
    Perform some action and return some thing
    """
    # This has been implemented this way because of these crazy reasons.
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

The folder path of a unit (or integration) test module should mirror the structure of the module it's testing.
Eg `octoenergy/path/to/something.py` should have tests in
`tests/unit/path/to/test_something.py`.

For each function/class being tested, use a test class to group its tests. Eg:

```
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

Using this technique, ensure the names accurately describe what the test is testing.

This is less important for functional tests which don't call into a single
object's API.


### <a name="test-method-structure">Unit test method structure</a>

A unit test has three steps:

- ARRANGE: put the world in the right state for the test
- ACT: call the unit under test (and possibly capture its output)
- ASSERT: check that the right output was returned (or the right calls to
    collaborators were made).

To aid readability, organise your test methods in this way, adding a blank line
between each step. Trivial example:

```
class TestSomeFunction:

    def test_does_something_in_a_certain_way(self):
        input = {'a': 100}

        output = some_function(input)

        assert output == 300
```
This applies less to functional tests which can make many calls to the system.


### <a name="functional-test-method-structure">Functional test method structure</a>

For functional tests, use comments and blank lines to ensure each step of the
test is easily understandable. Eg:

```
def test_some_longwinded_process(support_client, factory):
    # Create an electricity-only account with one agreement
    account = factory.create_electricity_only_account()
    product = factory.create_green_product()
    agreement = factory.ElectricityAgreement(tariff__product=product, account=account)

    # Load account detail page and check the agreement is shown
    response = support_client.get('account', number=account.number)
    response.assert_status_ok()

    # Fill in form to revoke agreement
    ...

    # Check agreemnt has been revoked
    ...
```

You get the idea.
