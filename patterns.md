# Architecture patterns

## Django

### Serialize template context

Don't pass any "rich" objects into the template context. Instead, serialize
domain objects to Python primitives beforehand.

#### Why?

- Having rich objects in the template is an enabler for undesirable behaviour:

  1. It encourages adding application-logic-rich methods to models, just so that
     functionality is available in templates (see [Why your Django models are fat](https://codeinthehole.com/lists/why-your-models-are-fat/)). 
     This is particularly prevalent for list views.

  2. It makes it easy to trigger hundreds of SQL queries for a single HTTP
     request, especially in a list view where the template loops over a
     `Queryset` and calls methods on each model instance. Serializing in the
     view ensures all SQL queries are performed before template rendering.

- It makes it easy to convert a Django HTML view into a JSON API view as the
  view is already serializing domain objects into JSON -- you just need to remove
  the template-rendering part. This dovetails in with our long-term strategy of
  embracing more React apps backed by JSON APIs for user interfaces.

- It makes it easier to cache data as all the database querying is done in one
  place.

- It makes it easier to compute global or queryset-level variables in one place.

#### How? 

Use `Serializer` classes from the Django-Rest-Framework to serialize rich
objects into dictionaries before rendering templates.

Example for a list-view using an embedded serializer.

```python
from django.views import generic
from rest_framework import serializers

class Teams(generic.ListView):
    template_name = "teams.html"
    model = models.Team
    context_object_name = "teams"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Serialize the queryset and remove object_list from the ctx so the 
        # Queryset instance is not included in the template context.
        context[self.context_object_name] = self.get_serialized_queryset(context.pop('object_list'))

        return context

    def get_serialized_queryset(self, queryset):
        return self.TemplateSerializer(instance=queryset, many=True).data

    class TemplateSerializer(serializers.Serializer):
        # Obj attributes just need same name
        pk = serializers.IntegerField()
        name = serializers.CharField()

        # Read fields off related objects using `source`
        leader_pk = serializers.IntegerField(source='leader.pk')
        leader_name = serializers.CharField(source='leader.get_full_name')

        # Call a model method using `source`
        num_users = serializers.CharField(source='get_num_users')

        # Call a method on this serializer (looks for method prefixed `get_`)
        call_weight = serializers.SerializerMethodField()

        # Use format=None to get datetime instances instead of strings
        created_at = serializers.DateTimeField(format=None)

        def get_call_weight(self, obj):
            pass
```

You don't have to embed the serializer class - reusable serializers can also be
used.

When serializing a collection of different domain objects (eg for a detail or
template view), pass them to the serializer as a dict:

```python
from django.views import generic
from rest_framework import serializers
from . import forms

class SwitchBrand(generic.FormView):
    template_name = "switch-brand.html"
    form_class = forms.Confirm

    def dispatch(self, request, *args, **kwargs):
        self.account = shortcuts.get_object_or_404(models.Account, number=kwargs['account_number'])
        self.target_brand = shortcuts.get_object_or_404(data_models.Brand, code=kwargs['brand_code'])
        return super().dispatch(request, *args, **kwargs)

    class _TemplateContext(serializers.Serializer):
        account_number = serializers.CharField(source='account.number')
        current_brand_name = serializers.CharField(source='account.portfolio.brand.name')
        target_brand_name = serializers.CharField(source='target_brand.name')
        electricity_agreements = serializers.SerializerMethodField()
        gas_agreements = serializers.SerializerMethodField()

        def get_electricity_agreements(self, obj):
            agreements = obj['account'].get_active_electricity_agreements()
            return [
                {
                    'mpan': agreement.meter_point.mpan,
                    'tariff_code': agreement.tariff.code,
                } for agreement in agreements
            ]

        def get_gas_agreements(self, obj):
            agreements = obj['account'].get_active_gas_agreements()
            return [
                {
                    'mprn': agreement.meter_point.mprn,
                    'tariff_code': agreement.tariff.code,
                } for agreement in agreements
            ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Pass the account and target brand to the serializer in a dict.
        extra = self._TemplateContext(
            instance=dict(account=self.account, target_brand=self.target_brand)).data
        ctx.update(extra)

        return ctx

    def form_valid(self, form):
        ...
```
The key point for using `Serializer`s is that the data being serialized must be
passed as a single object. Hence when there's a collection of different objects,
we pass a dictionary containing them all.



