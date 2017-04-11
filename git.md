# Git

Contents:

- [Commit messages](#commit-messages)
- [Commit history](#commit-history)
- [Pull requests](#pull-requests)


## Commit messages

Commit messages should take this form:

> Capitalized, short (50 chars or less) summary
> 
> More detailed explanatory text, if necessary.  Wrap it to about 72
> characters or so.  In some contexts, the first line is treated as the
> subject of an email and the rest of the text as the body.  The blank
> line separating the summary from the body is critical (unless you omit
> the body entirely); tools like rebase can get confused if you run the
> two together.
> 
> Write your commit message in the imperative: "Fix bug" and not "Fixed bug"
> or "Fixes bug."  This convention matches up with commit messages generated
> by commands like git merge and git revert.
> 
> Further paragraphs come after blank lines.
> 
> - Bullet points are okay, too
> 
> - Typically a hyphen or asterisk is used for the bullet, followed by a
>   single space, with blank lines in between, but conventions vary here
> 
> - Use a hanging indent

(Taken from Tim Pope's [A note about git commit messages](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html))

Note especially:

- The short summary does not end with a full stop.

- The blank line between the first line and the detailed explanation.

Any non-trivial commit should have an explanation - one-liner commit messages
should be rare.


## Commit history

Ensure the codebase "makes sense" after each commit. Primarily that means the tests should
pass but also that the codebase isn't broken between commits. 

Avoid small "bug-fix" commits that should have been part of a previous commit.
Rebase/squash these commits before marking a pull request as ready for review.

It's fine to force-push PR branches, although coordinate with other
collaborators if multiple people are working on the same branch.


## Pull requests

Ensure the PR can be reviewed in chronological order, commit by commit (see
[commit history](#commit-history).

Avoid merge commits in PRs. Rebase against `origin/master` when you want to pull
changes from `master` into your branch.
