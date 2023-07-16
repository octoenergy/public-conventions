# Application

- [Publishing events](#events)
- [Logging exceptions](#logging-exceptions)
- [Distinguish between anticipated and unanticipated exceptions](#distinguish-exceptions)
- [Exception imports](#exception-imports)
- [Celery tasks](#celery-tasks)
- [Keyword-arg only functions](#kwarg-only-functions)
- [Minimise system clock calls](#system-clock)
- [Modelling periods of time](#time-periods)

## <a name="events">Publishing events</a>

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
        "foo": foo,
        "bar": bar,
    },
    meta={"result": result},
)
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

## <a name="logging-exceptions">Logging exceptions</a>

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

## <a name="distinguish-exceptions">Distinguish between anticipated and unanticipated exceptions</a>

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

## <a name="exception-imports">Exception imports</a>

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

## <a name="celery-tasks">Celery tasks</a>

Care is required when changing Celery task signatures as publishers and
consumers get deployed at different times. It's important that changes to how an
event is published don't cause consumers to crash.

To protect against this, Celery tasks should be defined like this:

```python
@app.task(queue=settings.MY_QUEUE)
def my_task(*, foo, bar, **kwargs):
    ...
```

and called like this:

```python
my_task.apply_async(kwargs={"foo": 1, "bar": 2})
```

Things to note:

1. The task is declared with a specific queue. It's easier to troubleshoot queue
   issues if tasks are categorised like this. Note that the queue is specified when
   we declare the task, not when we trigger the task, as we want each specific task
   to be added to the same queue.
2. The task is called using `kwargs`, not `args` - and the task declaration uses a
   leading `*` to enforce this.
3. The task signature ends with `**kwargs` to capture any additional arguments. This
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

## <a name="kwarg-only-functions">Keyword-only functions</a>

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

## <a name="system-clock">Minimise system clock calls</a>

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

## <a name="time-periods">Modelling periods of time</a>

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
