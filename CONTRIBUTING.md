# Contributing

Markdown code in this repo must pass several static analysis tests, which are
detailed below. Note that you can run:

```sh
make ci
```

to run these checks before pushing to Github.

## Git commit subjects

Git commit subjects must:

- Be no longer than 70 characters;
- Start with a capital letter;
- Not end with a full stop;

Further, pull request branches should rebase off `main` to incorporate upstream
changes; don't merge `main` into your branch.

These rules are checked using Pytest in CI.

## Linting

Markdown files are linted by
[`markdownlint-cli`](https://github.com/igorshubovych/markdownlint-cli).

To run the linting locally run:

    docker run -i --rm -v `pwd`:/work tmknom/markdownlint:0.33.0

or, if installed on your host OS, run:

    markdownlint .

or:

    make markdownlint

Configuration for the enforced rules is in `.markdownlint.yaml`.

Many linting issues can be fixed by running:

    markdownlint --fix .

## Preview rendered pages

You can use [`grip`](https://github.com/joeyespo/grip) to render Github-flavour
markdown files. Install with:

    brew install grip

While working on docs, run a local, auto-reloading server with:

    make server
