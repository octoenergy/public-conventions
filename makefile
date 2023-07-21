ci: test markdownlint

test:
	pytest -v .circleci/

markdownlint:
	markdownlint .
