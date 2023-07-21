import re
import subprocess

import pytest


@pytest.mark.parametrize(
    "subject, error_msg",
    [
        ("WIP: working on something", "is a WIP commit"),
        ("WIP", "is a WIP commit"),
        ("fixup! some other commit", "is a fix-up commit"),
        ("Do the thing.", "ends with a period"),
        ("do the thing", "isn't capitalised"),
        (
            "Do the things and include information that should really be in the commit body",
            "is too long",
        ),
        ("Deploy branch to test", "is a temporary commit"),
        ("Deploy to test", "is a temporary commit"),
        ("Deploy Celery branch to test", "is a temporary commit"),
        ("TEMP: Deploy to GE test", "is a temporary commit"),
        ("TMP Deploy to test", "is a temporary commit"),
        (
            "Merge branch 'main' into statements-variable-payment",
            "is an unnecessary merge commit ",
        ),
    ],
)
def test_commit_subject_validity(subject, error_msg):
    is_valid, _ = _is_commit_subject_valid(subject)
    assert is_valid is False, f"'{subject}' {error_msg}"


def _is_commit_subject_valid(subject):
    """
    Test if a commit subject is valid.

    See https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
    """
    if re.match(r"^wip([ :]|$)", subject.lower()):
        return False, "WIP commits should be rebased"

    if re.match(r"^fixup!", subject.lower()):
        return False, "Fix-up commits should be rebased"

    if re.match(r"^te?mp:?\s", subject.lower()):
        return False, "Temporary commits should be rebased"

    if re.search(r"\.$", subject):
        return False, "Commit subject should not end with a period"

    if re.search(r"^[a-z]", subject):
        return False, "Commit subject should be capitalised"

    if re.search(r"^deploy.*(branch)?.*to test", subject.lower()):
        return False, "Deploy-to-test commits should be removed before merge"

    if re.search(r"^Merge branch ", subject):
        return False, "Rebase PR branches off their target branch rather than adding merge commits"

    max_length = 70
    if len(subject) > max_length:
        return False, f"Commit subject should not be longer than {max_length} characters"

    return True, ""


def _pr_commits(target_branch: str):
    """
    Return a generator of commmit message SHAs and subjects for the commits in
    this branch.
    """
    # Need to run git fetch to ensure Circle's checkout is up-to-date.
    cmd = "git fetch"
    subprocess.run(cmd.split(), capture_output=True)

    cmd = f"git log {target_branch}.. --oneline"
    result = subprocess.run(cmd.split(), capture_output=True)
    output = result.stdout.decode("utf-8").strip()

    for line in output.split("\n"):
        parts = line.split(" ")
        yield parts[0], " ".join(parts[1:])


@pytest.mark.parametrize("sha,commit_subject", _pr_commits("origin/main"))
def test_branch_commit_subject(sha, commit_subject):
    is_valid, message = _is_commit_subject_valid(commit_subject)
    if not is_valid:
        pytest.fail(f"Commit {sha} '{commit_subject}' is invalid: {message}")
