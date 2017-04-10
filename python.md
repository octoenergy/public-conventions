# Python

## Code review comments

This section details common code-review comments.

- [`CharField` choices](#charfield-choices)

### `CharField` choices

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
