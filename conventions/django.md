# Django

- [`CharField` choices](#charfield-choices)
- [Class naming conventions](#class-naming-conventions)
- [Model field naming conventions](#model-field-naming-conventions)
- [Model method naming conventions](#model-method-naming-conventions)
- [Encapsulate model mutation](#encapsulate-model-mutation)
- [Group methods and properties on models](#group-methods-and-properties-on-models)
- [Create filter methods on querysets, not managers](#queryset-filters)
- [Use `.get` when expecting exactly one result](#uniqueness)
- [Don't rely on implicit ordering of querysets](#implicit-ordering)
- [Don't use audit fields for application logic](#audit-fields)
- [Ensure `updated_at` is set when calling `QuerySet.update`](#update-updated-at)
- [Be conservative with model `@property` methods](#property-methods)
- [Ensure `__str__` is unique](#unique-str)
- [Flash messages](#flash-messages)
- [Avoid model-forms](#model-forms)
- [Avoid field validators](#field-validators)
- [Avoid multiple domain calls from an interface component](#one-domain-call)
- [Check permissions in dispatch method](#check-permissions-in-dispatch)
- [Load resources in `setup` method](#load-in-setup)
- [DRF serializers](#drf-serializers)
- [Handling out-of-band form errors](#out-of-band-form-errors)
- [Use database constraints for enforcing data integrity](#integrity-at-the-database)
- [Use path converters in URLs instead of regular expressions](#url-path-converters)

## `CharField` choices

The values stored in the database should be:

- Uppercase and separated with underscores.
- Namespaced with a string prefix.

A human-readable version should also be added in the tuples provided to the field.

```python
class ChannelChoices(choices.TextChoices):
    TELESALES = "TELESALES", "Telesales"
    FIELD_SALES = "FIELD_SALES", "Field-sales"


...


class MyModel(models.Model):
    channel = models.CharField(max_length=128, choices=ChannelChoices.choices)
```

This is because the database value is a code or symbol intended to be used
within application logic but not shown to the end user - making it uppercase
makes this distinction clear. Using a human-readable version for the database
value can lead to bugs when a future maintainer wants to change the version
shown to the end user.

## Class naming conventions

Given we [import modules, not objects](python.md#import-modules-not-objects), there's no need to suffix
view/form/serializer classes names with `View`/`Form`/`Serializer`.

Within a calling module, it's nicer to have:

```python
from django.views import generic
from . import forms


class SetPassword(generic.FormView):
    form_class = forms.NewPassword
```

rather than:

```python
from django.views import generic
from . import forms


class SetPassword(generic.FormView):
    form_class = forms.NewPasswordForm
```

## Model field naming conventions

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

## Model method naming conventions

- For query methods (i.e. methods that look something up and return it), prefix with `get_`.

- For setter methods (i.e. methods that set fields and call save), prefix with `set_`.

- Prefer "latest" to "last" in method names as "latest" implies chronological order where the
  ordering is not explicit when using "last"; i.e.
  `get_latest_payment_schedule`. Similarly, prefer `earliest` to `first` in
  method names.

## Encapsulate model mutation

Don't call a model's `save` method from anywhere but "mutator" methods on the
model itself.

Similarly, avoid calling `SomeModel.objects.create` or even
`SomeModel.related_objects.create` from outside of the model itself. Encapsulate
these in "factory" methods (classmethods for the `objects.create` call).

Doing this provides a useful overview of the lifecycle of a model as you
can see all the ways it can mutate in one place.

Also, this practice leads to better tests as you have a simple, readable method
to stub when testing units that call into the model layer.

Further reading:

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
        self.name = ""
        self.save()

    def set_name(self, new_name):
        self.name = new_name
        self.save()

    # Queries

    def get_num_apples(self):
        return self.fruits.filter(type="APPLE").count()

    # Properties

    @property
    def is_called_dave(self):
        return self.name.lower() == "dave"
```

## <a name="queryset-filters">Create filter methods on querysets, not managers</a>

Django’s model managers and `QuerySet`s are similar, see the [docs](https://docs.djangoproject.com/en/stable/topics/db/managers/)
for an explanation of the differences. However, when creating methods that return a queryset we’re
better off creating these on a custom queryset class rather than a custom manager.

A manager method is only available on a manager or related-manager. So `Article.objects` or
`Author.articles`. They’re not available to querysets, which is what’s returned from a manager or
queryset method, so they cannot be chained. In the example below `my_custom_filter()` is a method
on a custom manager class, so an `AttributeError` is raised when attempting to call it from a
queryset, i.e. the return value of `.filter()`.

```pycon
>>> Article.objects.my_custom_filter().filter(is_published=True)
<QuerySet [<Article (1)>, <Article (2)>]>
>>> Article.objects.filter(is_published=True).my_custom_filter()
AttributeError: 'QuerySet' object has no attribute 'my_custom_filter'
```

Below is an example of creating a custom queryset class and using it as a model’s manager. This
allows us to call it on both the manager and queryset.

```python
class ArticleQuerySet(models.QuerySet):
    def my_custom_filter(self):
        return self.filter(headline__contains="Lennon")


# django-stubs needs the Manager to be declared outside of the Model class body
ArticleManager = models.Manager.from_queryset(ArticleQuerySet)


class Article(models.Model):
    objects = ArticleManager()
```

## <a name="uniqueness">Use `.get` when expecting exactly one record</a>

When expecting exactly one result, use `.objects.get`.

Be aware that `.get` can raise two types of exception: `ObjectDoesNotExist` and `MultipleObjectsReturned`. If you are
handling one of these, you should usually also handle the other.

Note: if there is a uniqueness constraint on the fields used for filtering the results, you do not need to catch
`MultipleObjectsReturned`, as the database will ensure that this cannot occur.

Do not use `.first` instead, unless also using `.order_by`, otherwise the database may return any of multiple matching
records. It is also vulnerable to a race condition when used with `.count()`.

Don't do this:

```py
things = Thing.objects.filter(name=some_value)
if things.count() == 1:
    things.first().do_something()
```

In the example above, an extra record with `name=some_value` could have been added between `.count` and `.first`,
resulting in a `MultipleObjectsReturned` exception that is unhandled. Similarly, the one record could have been deleted,
resulting in `.first` returning `None` and an `AttributeError` being raised when trying to call `None.do_something`.

Instead, do this:

```py
try:
    thing = Thing.objects.get(name=some_value)
except Thing.DoesNotExist:
    pass  # or handle appropriately
except Thing.MultipleObjectsReturned:
    pass  # or handle appropriately
```

The second example avoids a race condition and is also more efficient, as only a single database query is required.

## <a name="implicit-ordering">Don't rely on implicit ordering of querysets</a>

If you grab the `.first()` or `.last()` element of a queryset, ensure you
explicitly sort it with `.order_by()`. Don't rely on the default ordering set
in the `Meta` class of the model as this may change later on breaking your
assumptions.

When ordering querysets, ensure the fields you’re ordering by are covered by a
uniqueness constraint. Without this, the ordering of queryset may be
inconsistent when there are duplicate values in the ordering fields. In such
cases, the ordering will depend on the SQL [scan and join plan types and the
order on disk](https://www.postgresql.org/docs/current/queries-order.html).

If there’s no natural uniqueness constraint, append the table’s primary key to
order-by fields. For example, instead of `.order_by("date")`, use
`.order_by("date", "id")`.

## <a name="audit-fields">Don't use audit fields for application logic</a>

It's useful to add audit fields to models to capture datetimes when that database
record was created or updated:

```py
class SomeModel(models.Model):
    ...
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

But don't use these fields for application logic. If you need to use the
creation time of an object, add a separate field that must be explicitly set upon
creation. Why?

- Often the creation time of a domain object in the real world is different from
  the time when you inserted its record into the database (e.g. when backfilling).

- Fields with `auto_now_add=True` are harder to test as it's a pain to
  set the value when creating fixtures.

- Explicit is better than implicit.

These automatically set fields should only be used for audit and reporting
purposes.

## <a name="update-updated-at">Ensure `updated_at` is set when calling `QuerySet.update`</a>

A `models.DateTimeField(auto_now=True)` field, such as the audit field `updated_at`, will not automatically
be updated when calling `QuerySet.update` (for example, when we want to make an efficient bulk update).

https://docs.djangoproject.com/en/4.1/ref/models/querysets/#django.db.models.query.QuerySet.update

> Finally, realize that `update()` does an update at the SQL level and, thus, does not call any
> `save()` methods on your models, nor does it emit the `pre_save` or `post_save` signals (which are a consequence of calling `Model.save()`).

For this reason, it's important to explicitly set the `updated_at` field when calling `QuerySet.update`, so that we can be sure this field
is reliable/meaningful. e.g.

```py
Foo.objects.filter(...).update(..., updated_at=...)
```

## <a name="property-methods">Be conservative with model `@property` methods</a>

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

If in doubt, use a method not a property.

## <a name="unique-str">Ensure `__str__` is unique</a>

Ensure the string returned by a model's `__str__` method uniquely identifies
that instance.

This is important as Sentry (and other tools) often just print `repr(instance)`
of the instance (which prints the output from `__str__`). When debugging, it's
important to know exactly which instances are involved in an error, hence why
this string should uniquely identify a single model instance.

It's fine to use something like:

```py
def __str__(self):
    return f"#{self.id} ..."
```

## <a name="flash-messages">Effective flash messages</a>

Flash messages are those one-time messages shown to users after an action has
been performed. They are triggered using the `django.contrib.messages` package,
normally from within a view class/function.

Here's a few tips.

- Don't say "successfully" in flash messages (e.g. "The thing was updated
  successfully"). Prefer a more active tone (e.g. "The thing was updated").

- Don't include IDs that are meaningless to the end user (e.g. "Thing 1234 was
  updated").

- Consider including links to related resources that might be a common next step
  for the user. HTML can be included in flash messages

  ```python
  msg = (
      "<h4>Some heading</h4>"
      '<p>An action was performed. Now do you want to <a href="%s">do the next thing</a>.</p>'
  ) % next_thing_url
  messages.success(request, msg, extra_tags="safe")
  ```

Note the `safe` tag which allow HTML to be included in the message.

## <a name="model-forms">Avoid model forms</a>

[Django's model-forms](https://docs.djangoproject.com/en/2.1/topics/forms/modelforms/) are a useful crutch for rapidly building web projects.
However for a late-stage Django project (like ours), they are best avoided apart from the
most degenerate, simple scenarios.

Why? Because they conflate validation and persistence logic which, over time,
leads to hard-to-maintain code. As soon as you need to add more sophisticated
actions (than a simple DB write) to a successful form submission, model-forms
are the wrong choice. Once you start overriding `.save()`, you're on the path
to maintenance hell. Future maintainers will thank you if you ensure forms are
only responsible for validating dictionaries of data, nothing more,
single-responsibility principle and all that.

Instead, use plain subclasses of `form.Form` and Django's `fields_for_model`
function to extract the form fields you need. Handle the `form_valid` scenario
in the view with a single call into the domain layer to perform all necessary
actions.

One advantage of this is you can pluck form fields off several models to build a
sophisticated form, which allows views to be kept simple and thin (handling
multiple forms in the same view should be avoided).

Example:

```python
from django import forms
from myproject.someapp import models


class SampleForm(forms.Form):
    # Grab fields from two different models
    user_fields = forms.fields_for_model(models.User)
    profile_fields = forms.fields_for_model(models.Profile)

    name = user_fields["name"]
    age = profile_fields["age"]
```

The same principle applies to other ORM-constructs, like DRF's model
serializers, which trade-off good structure and long-term maintainability for
short-term development speed.

This is an important step in extricating a project from Django's tight grip,
moving towards treating Django as a library rather than framework.

## <a name="field-validators">Avoid field validators</a>

[Django's field validators](https://docs.djangoproject.com/en/4.0/ref/validators/) should not be used.
Like model forms, they can be useful in an early stage project, but are better avoided in a late-stage project like Kraken.
This is enforced by flake8 rule `K306`.

Why? They make it look like a field will always have its value validated when in practice it will not.

Example:

```python
from django.core import validators
from django.db import models


class SomeModel(models.Model):
    constrained_number = models.FloatField(
        default=0.5,
        validators=[
            validators.MinValueValidator(0.0),
            validators.MaxValueValidator(1.0),
        ],
    )
```

This looks like a field that cannot be set to values below 0 or above 1.
But the validation exists in code rather than the database, so it is possible to store values outside this range.

Django only runs field validators when calling `.full_clean()` on a Model.
This is done when using Django Admin to build forms or when using model forms.
Neither of these are the recommended method of creating forms in Kraken.
They are also not pulled into the form fields when we use `forms.fields_for_model`.
As such, field validators are not run automatically, while looking like they are.

Validation should instead be performed explicitly when validating input.
[Constraints](#integrity-at-the-database) should be used to provide data integrity in the database.
This makes it clear when validation is and isn't being run.

## <a name="one-domain-call">Avoid multiple domain calls from an interface component</a>

An interface component, like a view class/function or Celery task, should only make one
call into the domain layer (i.e. the packages in your codebase where application
logic lives).

Recall: the job of any interface component is this:

1. Translate requests from the language of the interface (i.e. HTTP requests or serialized Celery task payloads)
   into domain objects (e.g. `Account` instances)

2. Call into the domain layer of your application to fetch some query results or
   perform an action.

3. Translate any returned values (or exceptions) from the domain layer back into the
   language of the interface (e.g. into a 200 HTTP response for a successful query,
   or a 503 HTTP response if an action wasn't possible). Note, this step only
   applies to interfaces components that can _respond_ in some way - this
   doesn't apply to fire-and-forget Celery tasks where there's no results
   back-end.

This convention mandates that step 2 involves a single call into the domain
layer to keep the interface easy-to-maintain and to avoid leaking application
logic into the interface layer.

So avoid this kind of thing:

```python
class SomeView(generic.FormView):
    def form_valid(self, form):
        account = form.cleaned_data["account"]
        payment = form.cleaned_data["payment"]

        result = some_domain_module.do_something(account, payment)
        if result:
            some_other_domain_module.do_something_else(account)
        else:
            form.add_error(None, "Couldn't do something")
            return self.form_invalid(form)

        some_logging_module.log_event(account, payment)

        return shortcuts.redirect("success")
```

where the view class is making multiple calls into the domain layer.

Instead, encapsulate the domain functionality that the interface requires in a
single domain call:

```python
class SomeView(generic.FormView):
    def form_valid(self, form):
        try:
            some_domain_module.do_something(
                account=form.cleaned_data["account"],
                payment=form.cleaned_data["payment"],
            )
        except some_domain_module.UnableToDoSomething as e:
            # Here we assume the exception message is suitable for end-users.
            form.add_error(None, str(e))
            return self.form_invalid(form)

        return shortcuts.redirect("success")
```

Note the use of domain-specific exceptions to handle failure conditions.

Since fire-and-forget Celery tasks can't respond, their implementation should be
simple: just loading the appropriate domain objects and making a single call
into the domain layer. Something like:

```python
@app.task(queue=settings.SOME_QUEUE)
def perform_some_action(*, foo_id, bar_id, **kwargs):
    foo = Foo.objects.get(id=foo_id)
    bar = Bar.objects.get(id=bar_id)

    some_domain_module.perform_action(foo, bar)
```

## <a name="check-permissions-in-dispatch">Check permissions in `dispatch` method</a>

If using class-based views, perform all access-control and pre-condition checks
in the `dispatch` method (or the `get` method if a read-only view). Because:

- This method is expected to return a `HttpResponse` instance and so is a
  natural place to return a 403 if the requesting user does not have permission
  to access the requested object.

- This method is called for _all_ HTTP methods and avoids possible security
  holes if permissions are only checked in, say, the `get` method.

In particular, avoid checking permissions in other commonly subclassed methods
like `get_context_data` or `get_form_kwargs`.

When checking pre-conditions, avoid adding business logic to
[the `dispatch` method](https://docs.djangoproject.com/en/4.0/ref/class-based-views/base/#django.views.generic.base.View.dispatch).
Instead encapsulate the check as a function in the domain layer and call that
from `dispatch` - something like this:

```python
from django.views import generic
from django import http
from django.http import response

from project.interfaces import acl
from project.domain.frobs import checks


class ActOnFrob(generic.FormView):
    def dispatch(
        self, request: http.HttpRequest, *args, **kwargs
    ) -> response.HttpResponseBase:
        # Check if the request user is allowed to mutate the resource.
        if not acl.can_user_administer_frob(request.user, self.frob):
            return http.HttpResponseForbidden("...")

        # Check the pre-conditions for the resource to be mutated.
        if not checks.can_frob_be_mutated(self.frob):
            return http.HttpResponseForbidden("...")

        return super().dispatch(request, *args, **kwargs)
```

## <a name="load-in-setup">Load resources in `setup` method</a>

If using class-based views, perform all model loading in
[the `setup` method](https://docs.djangoproject.com/en/4.0/ref/class-based-views/base/#django.views.generic.base.View.setup)
(or the `get` method if a read-only view). This method should perform any
initialization prior to dispatching. Putting model loading in this view allows
the retrieved models to be used by any other method on the view class.

```python
from django.views import generic
from django import shortcuts, http

from project.data import models


class ActOnFrob(generic.FormView):
    def setup(self, request: http.HttpRequest, *args, **kwargs) -> None:
        super().setup(request, *args, **kwargs)

        # Load the resource specified in the URL.
        self.frob = shortcuts.get_object_or_404(models.Frob, id=kwargs["id"])
```

## DRF serializers

Serializers provided by Django-REST-Framework are useful, not just for writing
REST APIs. They can be used anywhere you want to clean and validate a nested
dictionary of data. Here are some conventions for writing effective serializers.

Be liberal in what is accepted in valid input.

- Allow optional fields to be omitted from the payload, or have `null` or `""`
  passed as their value.

- Convert inputs into normal forms (by e.g. stripping whitespace or upper-casing).

In contrast, be conservative in what is returned in the `validated_data` dict.
Ensure `validated_data` has a consistent data structure no matter what valid
input is used. Don't make calling code worry about whether a particular key _exists_ in the
dict.

In practice, this means:

- Optional fields where `None` is not a valid value have a default value set in
  the serializer field declaration.

- If optional string-based fields have `allow_null=True`, then convert any
  `None` values to the field default.

To that end, use this snippet at the end of your `validate` method to ensure
there are no missing keys in the `validated_data` dict and that `None` is only
included as a value in `validated_data` when it's a field's default.

```py
def validate(self, data):
    ...
    # Ensure validated data includes all fields and None is only used as a value when it's
    # the default value for a field.
    for field_name, field in self.fields.items():
        if field_name not in data:
            data[field_name] = field.initial
        elif data[field_name] is None and data[field_name] != field.initial:
            data[field_name] = field.initial

    return data

```

Misc:

- Ensure validation error messages end with a period.

## <a name="out-of-band-form-errors">Out-of-band form errors</a>

In a `FormView` sometimes an error occurs _after_ the initial payload has been
validated. For instance, a payment partner's API might respond with an error
when registering a new bankcard even though the submitted bankcard details
appeared to be valid. To handle this situation in a `FormView` subclass, use the
following pattern:

```py
from django.views import generic
from . import forms

class CreateSomething(generic.FormView):
    form_class = forms.Something

    ...

    def form_valid(self, form):
        try:
            thing = domain.create_a_thing(
                foo=form.cleaned_data['foo'],
                bar=form.cleaned_data['bar'],
            )
        except domain.UnableToCreateThing as e:
            # Handle *anticipated* exceptions; things we know might go wrong but
            # can't do much about (e.g. vendor errors). Here we assume the exception
            # message is suitable for end-users but often it needs some
            # adjusting.
            form.add_error(None, str(e))
            return self.form_invalid(form)
        except Exception as e
            # Optional handling of *unanticipated* errors. When this happens, we want to send
            # details of the error to Sentry so such errors can be investigated
            # and fixed. It's optional as we could omit this block and let the
            # exception percolate up to generate a 500 response which Sentry
            # will capture automatically. It's a bit friendlier to the user to
            # show them some custom copy rather than a generic 500 response.

            # Ensure your logger has the Raven handler so the exception is sent
            # to Sentry.
            logger.exception("Unable to create a thing")

            # Depending on context, it might not be appropriate to
            # show the exception message to the end-user. If possible, offer
            # some guidance on what the end-user should do next (e.g. contact
            # support, try again, etc). Ensure the tone is apologetic.
            msg = (
                "Really sorry, we weren't able to do the thing as an unanticipated "
                "error occurred. Error message: %s"
            ) % e
            form.add_error(None, msg)
            return self.form_invalid(form)
        else:
            # Handle successful creation...
            message.success(self.request, "Created the thing!")
            return http.HttpResponseFound(...)
```

## <a name="integrity-at-the-database">Use database constraints for enforcing data integrity</a>

Don't rely on the Python application for data integrity. Instead, use database
constraints to prevent the storage of corrupt data.

Application-level validations aimed at the user experience (such as form
validation) are acceptable as long as they aren't used as substitutes for data
integrity, but as an extra.

Some Django `QuerySet` methods such as `bulk_update()`, `bulk_create()`, and
`update()` don't call the model's `save()` method. If a model has validation
logic living in `save()`, it becomes susceptible to data inconsistencies.

The same risks apply to functions [encapsulating model mutations](#encapsulate-model-mutation)
and to other application-level validators, such as [model field validators](#field-validators).

When asserting data integrity is important, don't do this:

```python
def save(self, *args, **kwargs) -> None:
    if self.field_a is None and self.field_b is None:
        raise exceptions.ValidationError(
            "At least one of field_a or field_b must have a value."
        )
    return super().save(*args, **kwargs)
```

Assert it at the database level instead:

```python
class MyModel(models.Model):
    # model fields...

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~Q(field_a__isnull=True, field_b__isnull=True),
                name="at_least_one_of_field_a_or_field_b_not_null",
            )
        ]
```

## <a name="url-path-converters">Use path converters in URLs instead of regular expressions</a>

Where possible we prefer Django path converters to old style URLs.

The format is `<path-converter-name:variable_name>`, where `variable_name` is what gets
passed to the view kwargs. You can also just do `<variable_name>`, which matches any
string (excluding slashes).

Path converters define regular expressions and then convert the captured variable to a
Python object, so `<int:pk>` will pass an int to the view kwargs, while the old style
`(?P<pk>\d+)` passes a string.

New path converters can be created as per the
[Django docs](https://docs.djangoproject.com/en/2.1/topics/http/urls/#registering-custom-path-converters).
Examples can be seen in `octoenergy/interfaces/common/path_converters.py`.

You will also need to _register_ the path converter for the site on which you wish to
use it. This should be done by defining a `register` function in a `path_converters.py`
file, and then calling that from the base `urls.py`. For an example, see
`octoenergy/interfaces/supportsite/urls.py`.
