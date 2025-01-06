# Contributing

You're welcome to suggest changes if you spot a broken link or typo. Clone the repo or use the GitHub UI to make a PR.

## Installation

You'll need a few tools to make and test your changes before pushing them to a PR.

### Prettier

All Markdown should be formatted with [Prettier](https://prettier.io/) version 3.1
Install with:

```sh
npm install -g prettier@3.1
```

Once installed, ensure your editor runs Prettier on a pre-save hook:

- [PyCharm instructions](https://www.jetbrains.com/help/pycharm/prettier.html)
- [VSCode instructions](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
- [Vim instructions](https://prettier.io/docs/en/vim.html)

Prettier conformance is checked in CI and configured via `.prettierrc.yaml` and
`.prettierignore`.

### Docker

### Pytest

## Development

### Run CI tests locally

If your changes include Markdown, be aware that Markdown code in this repo must pass several static analysis tests. Before pushing to GitHub, run

```sh
make ci
```

to run these checks.

### Git commit subjects

Git commit subjects must:

- Be no longer than 70 characters.
- Start with a capital letter.
- Not end with a full stop.

Further, PR branches should rebase off `main` to incorporate upstream
changes; don't merge `main` into your branch.

These rules are checked using Pytest in CI.

### Spelling

Pull requests must pass a spell-check before merge. This is done using the
[`tmaier/markdown-spellcheck`](https://hub.docker.com/r/tmaier/markdown-spellcheck)
Docker image.

To run the spell-test locally run:

```sh
make spell_check
```

or:

```sh
docker run --rm -ti -v $(pwd):/workdir tmaier/markdown-spellcheck:latest \
    --report --ignore-numbers --ignore-acronyms "**/*.md"
```

Add exceptions to the custom dictionary in `.spelling`.

### Linting

Markdown files are linted by
[`markdownlint-cli`](https://github.com/igorshubovych/markdownlint-cli).

To run the linting locally run:

```sh
docker run -i --rm -v `pwd`:/work tmknom/markdownlint:0.33.0
```

or, if installed on your host OS, run:

```sh
markdownlint .
```

or:

```sh
make markdownlint
```

Configuration for the enforced rules is in `.markdownlint.yaml`.

Many linting issues can be fixed by running:

```sh
markdownlint --fix .
```

## Preview rendered pages

You can use [`grip`](https://github.com/joeyespo/grip) to render Github-flavour
markdown files. Install with:

```sh
brew install grip
```

While working on docs, run a local, auto-reloading server with:

```sh
make server
```
