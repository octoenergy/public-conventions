# Python

Contents:

- [`CharField` choices](#charfield-choices)
- [Model field naming conventions](#model-field-naming-conventions)


## `CharField` choices

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

## Model field naming conventions

`DateTimeField`s should generally have suffix `_at`. For example:

- `created_at`
- `sent_at`
- `period_starts_at`

There are some exceptions such as `available_from` and `available_to`.

`DateField`s should have suffix `_date`:

- `billing_date`
- `supply_date`


## Only mutate Django models with mutator methods

Don't call a model's `save` method from anywhere but "mutator" methods on the
model itself. 

See:

- [Django models, encapsulation and data integrity](https://www.dabapps.com/blog/django-models-and-encapsulation/), by Tom Christie
