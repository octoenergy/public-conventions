# Architecture patterns

## Django

### Serialize template context

Don't pass any "rich" objects into the template context. Instead serialize
domain objects to Python primitives beforehand.

Why?

- Having rich objects in the template is an enabler for undesirable behaviour:

  1. It encourages adding application-logic-rich methods to models, just so that
     functionality is available in templates (see [Why your Django models are fat](https://codeinthehole.com/lists/why-your-models-are-fat/)). 
     This is particularly prevalent for list views.

  2. It makes it easy to trigger hundreds of SQL queries for a single HTTP
     request, especially in a list view where the template loops over a
     `Queryset` and calls methods on each model instance.

- It makes it easy to convert a Django HTML view into a JSON API view as the
  view is already converting domain objects into JSON, you just need to remove
  the template-rendering part. This dovetails in with our long-term strategy of
  embracing more React apps backed by JSON APIs for user interfaces.

- It makes it easier to cache data as all the database querying is done in one
  place.

- It makes it easier to compute global or queryset-level variables in one place.

How? 

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
        # Serialise the queryset and remove object_list from the ctx.
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
