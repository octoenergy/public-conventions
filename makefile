# Run all checks run in CI.
ci: test markdownlint spell_check prettier_check

test:
	pytest -v .circleci/

markdownlint:
	docker run --rm -v $$(pwd):/work tmknom/markdownlint:0.33.0 -- .

spell_check:
	docker run --rm -ti -v $$(pwd):/workdir tmaier/markdown-spellcheck:latest --report --ignore-numbers --ignore-acronyms  "**/*.md"

prettier_check:
	prettier --check --parser=markdown .

install:
	pip install pytest==8.3.4

server:
	grip
