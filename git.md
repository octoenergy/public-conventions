# Git

This is a guide to how to use `git` at Octopus Energy.

Contents:

- [Commit messages](#commit-messages)
- [Commit granularity](#commit-granularity)
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

(Taken from Tim Pope's seminal [A note about git commit messages](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html).)

Note especially:

- The short summary does not end with a full stop.

- The blank line between the first line and the detailed explanation.

Only truly trivial changes should have a one-line commit message. All others
should include some detail on what problem is being fixed and how the commit fixes
it. To this end, consider using a 
[commit message template](http://codeinthehole.com/tips/a-useful-template-for-commit-messages/).


## Commit granularity

Ensure the codebase "makes sense" after each commit. Primarily that means the tests should
pass but also that the codebase isn't broken (in some sense) between commits. 

Avoid small "bug-fix", "linting" or "address code review comments" commits that
should have been part of a previous commit. Rebase/squash these commits to give
a clean history before requesting code review for a pull-request.

Of course, rebasing an already-pushed branch means a force-push is required to
push to Github. This is fine when you're the only person working on the branch
but, when there's more than one person working on the branch, make sure you talk
to each before force-pushing to avoid clobbering each other's work.


## Pull requests

Strive for PRs that can be reviewed in chronological order, commit by commit (see
[commit granularity](#commit-granularity)).

Avoid merge commits in PR branches by rebasing against `origin/master`
when you want to pull changes from `master` into your branch.

Further reading:

- [Advanced pull-request crafting](https://codeinthehole.com/tips/advanced-pull-request-crafting/)
