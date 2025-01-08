# Contributing

You're welcome to suggest changes if you spot a broken link or typo. Clone the
repo or use the GitHub UI to make a pull request.

## Installation

Several tests are run on changes in CI. To replicate these tests locally, you'll
need to install some tools. None are essential but they will detect possible
problems before CI does.

### Prettier

Ensure [Prettier](https://prettier.io/) version 3.2.5 is installed. It can be installed with:

    npm install -g prettier@3.2.5

Verify the installed version is correct with:

    prettier --version

Once installed, ensure your editor runs Prettier on a pre-save hook:

- [PyCharm instructions](https://www.jetbrains.com/help/pycharm/prettier.html)
- [VSCode instructions](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
- [Vim instructions](https://prettier.io/docs/en/vim.html)

### Docker

Ensure you have Docker installed. Mac users can [install from Homebrew](https://formulae.brew.sh/formula/docker).

### Python tooling

Ensure you have a Python 3.11 virtual environment created for this project and
Python packages have been installed with `make install`.

There are various ways of doing
this - here is one that uses `pyenv` and `pyenv-virtualenvwrapper`:

```sh
pyenv local 3.11.4  # Match the version in `.circleci/config.yml`
mkvirtualenv conventions
make install
```

## Development

### Formatting

Markdown should be formatted with Prettier using the configuration in
`.prettierrc.yaml`. Verify this with:

```sh
make prettier_check
```

### Linting

Markdown should conform to the Markdownlint rules declared in
`.markdownlint.yaml`. Verify this with:

```sh
make markdownlint
```

### Spelling

Markdown must pass a spell-check. Verify this with:

```sh
make spell_check
```

Spelling exceptions are held in `.spelling`.

### Commit messages

Git commit subjects must:

- Be no longer than 70 characters.
- Start with a capital letter.
- Not end with a full stop.

Further, PR branches should rebase off `main` to incorporate upstream
changes; don't merge `main` into your branch.

These rules are checked using Pytest in CI. Verify conformance with:

```sh
make test
```

### Preview rendered pages

You can use [`grip`](https://github.com/joeyespo/grip) to render Github-flavour
markdown files. Install with:

```sh
brew install grip
```

While working on docs, run a local, auto-reloading server with:

```sh
make server
```
