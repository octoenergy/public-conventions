# Testing

- [Test folder structure](#test-folder-structure)
- [Test module names for unit and integration tests](#test-module-names-unit)
- [Test module names for functional tests](#test-module-names-functional)
- [Test class structure](#test-class-structure)
- [Isolation](#test-isolation)
- [Freeze or inject time for tests](#freezing-time)
- [Unit test method structure](#test-method-structure)
- [Functional test method structure](#functional-test-method-structure)
- [Don't use numbered variables](#numbered-variables)###



## Test folder structure

Tests are organised by their type:

- `tests/unit/` - Isolated unit tests that test the behaviour of a single unit.
  Collaborators should be mocked. No database or network access is permitted.

- `tests/integration/` - For testing several units and how they are plumbed
  together. These often require database access and use factories for set-up.
  These are best avoided in favour or isolated unit tests (to drive
  design) and end-to-end functional tests (to help us sleep better at night
  knowing things work as expected).

- `tests/functional/` - For end-to-end tests designed to check everything is
  plumbed together correctly. These should use webtest or Django's
  `call_command` function to trigger the test and only patch third party
  calls.

## <a name="test-module-names-unit">Test module names for unit and integration tests</a>

The file path of a unit (or integration) test module should mirror the structure of the application module it's testing.

Eg `octoenergy/path/to/something.py` should have tests in
`tests/unit/path/to/test_something.py`.

## <a name="test-module-names-functional">Test module names for functional tests</a>

The file path of a functional test module should adopt the same naming as the
_use-case_ it is testing. Don't mirror the name of an application module.

Eg The "direct registration" journey should have functional tests in somewhere
like `tests/functional/consumersite/test_direct_registration.py`.

## <a name="test-class-structure">Test class structure</a>

For each object being tested, use a test class to group its tests. Eg:

```python
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

## <a name="test-isolation">Isolation</a>

Don't assume that tests that use the database are fully isolated from each other. Your
tests should not make assertions about the global state of the database.

For example, a test should not assert that there are only a certain number of model
instances in the database, as a transactional test (which does commit to the same DB)
running concurrently may have created some.

### Why aren't they isolated?

While in most cases tests _are_ isolated (i.e. they run in separate database transactions),
a few of our tests use the Pytest marker `transaction=true`. This causes them to use
`TransactionTestCase`, which, confusingly, doesn't run in a transaction. Because we
run our tests concurrently (using the `--numprocesses` flag), these
non-wrapped transactions are not isolated from other tests running at the same time.

## <a name="freezing-time">Freeze or inject time for tests</a>

Don't let tests or the system-under-test call the system clock unless it is
being explicitly controlled using a tool like [freezegun](https://github.com/spulec/freezegun).

This guards against a whole class of date-related test bugs which often manifest
themselves if your test-suite runs in the hours before or after midnight.
Typically these are caused by DST-offsets where a datetime in UTC has a different date to
one in the local timezone.

For unit tests, it's best to design functions and classes to have
dates/datetimes injected so freezegun isn't necessary.

For integration or functional tests, wrap the fixture creation and test
invocation in the freezegun decorator/context-manager to give tight control of what the system
clock calls will return.

Use this technique to control the context/environment in which a test
executes so that it behaves predictably whatever time of day the test suite is
run. Don't always pick a "safe" time for a test to run; use this technique to
test behaviour at trickier times such as midnight on DST-offset dates.

## <a name="test-method-structure">Unit test method structure</a>

A unit test has three steps:

- ARRANGE: put the world in the right state for the test
- ACT: call the unit under test (and possibly capture its output)
- ASSERT: check that the right output was returned (or the right calls to
  collaborators were made).

To aid readability, organise your test methods in this way, adding a blank line
between each step. Trivial example:

```python
class TestSomeFunction:
    def test_does_something_in_a_certain_way(self):
        input = {"a": 100}

        output = some_function(input)

        assert output == 300
```

This applies less to functional tests which can make many calls to the system.

## Functional test method structure

For functional tests, use comments and blank lines to ensure each step of the
test is easily understandable. Eg:

```python
def test_some_longwinded_process(support_client, factory):
    # Create an electricity-only account with one agreement
    account = factory.create_electricity_only_account()
    product = factory.create_green_product()
    agreement = factory.ElectricityAgreement(tariff__product=product, account=account)

    # Load account detail page and check the agreement is shown
    response = support_client.get("account", number=account.number)
    response.assert_status_ok()

    # Fill in form to revoke agreement
    ...

    # Check agreement has been revoked
    ...
```

You get the idea.

## <a name="numbered-variables">Don't use numbered variables</a>

Avoid numbering variables like so:

```py
def test_something(factory):
    account1 = factory.Account()
    account2 = factory.Account()
    ...
```

There's _always_ a better naming that avoids numeric suffixes and more
clearly expresses intent.

For instance, if you need more than one of something and it's not important
to distinguish between each instance, just use an iterable:

```py
def test_something(factory):
    accounts = [factory.Account(), factory.Account()]
    ...
    # some action happens to the accounts
    ...
    for account in accounts:
        assert account.action_happened  # some assertion on each item in iterable
```

If you do need to distinguish between the instances later on, then use
the distinguishing features to guide the naming of each variable. For example:

```py
def test_something(factory):
    withdrawn_account = factory.Account(status="WITHDRAWN")
    active_account = factory.Account(status="ACTIVE")
    accounts = [withdrawn_account, active_account]
    ...
    # some action happens to the accounts
    ...
    assert active_account.action_happened
```
