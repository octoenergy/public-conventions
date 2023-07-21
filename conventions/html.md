# HTML and Django templates

Contents:

- [Prefer object properties to hard-coded comparisons](#prefer-object-properties-to-hard-coded-comparisons)

## Prefer object properties to hard-coded comparisons

Instead of:

```
{% if obj.channel == "FIELD_SALES" %}
    ...
{% endif %}
```

add a property to the model/class to allow:

```
{% if obj.is_field_sales %}
    ...
{% endif %}
```
