# Learning Journal: Secure CI Workflow

**Author:** Dhananjay Gupta
**Project:** https://github.com/dhananjaygupta1312-arch/Secure-CI-Workflow
**Period:** November 2026

This journal records what I did, what broke, how I fixed it, and what I learned while building a DevSecOps pipeline: a Flask app, GitHub Actions CI, and four security scanners. I included the exact error messages because the mistakes taught me the most.

---

## Project at a glance

| Item | Detail |
|---|---|
| Goal | Build a CI pipeline that tests code and fails on security findings, with before/after proof |
| Stack | Python, Flask, pytest, GitHub Actions, WSL2 Ubuntu, VS Code |
| Scanners | Semgrep (SAST), pip-audit (SCA), Gitleaks (secrets), CycloneDX (SBOM) |
| Two code states | Tag `v0-vulnerable` (planted flaws) and `main` (fixed) |
| Planted flaws | SQL injection, unsafe `yaml.load`, hardcoded secret, debug mode, old dependencies |

## Timeline summary

| Stage | What happened |
|---|---|
| 1 | Set up WSL2, VS Code, Git, GitHub CLI |
| 2 | Built the vulnerable app, tests, and first workflow |
| 3 | CI failed: Python 3.9 not found on Ubuntu 26.04 |
| 4 | CI failed: `ModuleNotFoundError: No module named 'app'` |
| 5 | Git trouble: diverged history, rebase conflict, detached HEAD |
| 6 | Ran scanners, collected "before" evidence |
| 7 | Fixed the code, turned the pipeline into an enforcing gate |
| 8 | Added `run_all.sh`, wrote docs, tested the gate on a throwaway branch |

---

## Entry 1: Environment setup

**Goal:** Get Linux, Git, VS Code, and GitHub working together.

**What I did**
- Installed WSL2 with Ubuntu and VS Code with the WSL extension
- Configured Git with my name, email, and `main` as the default branch
- Logged in to GitHub with `gh auth login`
- Created the repo and a Python virtual environment

**What I learned**
- Develop inside the Linux filesystem (`~/projects`), not on `/mnt/c/`, because the Windows drive is slow and causes line-ending issues.
- The CI runner is Linux, so developing on Linux avoids "works on my machine" surprises.
- A virtual environment keeps this project's packages separate from the rest of the system.
- The green **WSL: Ubuntu** box in VS Code confirms the editor is connected to Linux.

---

## Entry 2: Building the vulnerable app

**Goal:** Create a deliberately flawed app so the scanners have something to find.

**What I did**
- Wrote `app/app.py` with four planted flaws: SQL built by string formatting, `yaml.load` on request data, a hardcoded secret, and `debug=True`
- Pinned old dependency versions in `requirements.txt` so pip-audit would find CVEs
- Wrote one pytest test for `/health`
- Created the first workflow (tests only)

**What I learned**
- Each flaw maps to a real category: injection, unsafe deserialization, sensitive data exposure, security misconfiguration, and vulnerable components (OWASP Top 10).
- The test passes even though the app is insecure. Functional tests do not measure security.

---

## Entry 3: CI failure, Python version not found

**Date:** 01/11/2026

**Error**
```
Error: The version '3.9' with architecture 'x64' was not found for Ubuntu 26.04.
```

**What happened**
The `security` job failed at `setup-python`, so every later step (Semgrep, pip-audit, Gitleaks, SBOM) was skipped and showed as grey circles.

**Cause**
`ubuntu-latest` had moved to Ubuntu 26.04, and no prebuilt Python 3.9 existed for that image.

**Fix**
Changed `runs-on: ubuntu-latest` to `runs-on: ubuntu-24.04` in both jobs.

**What I learned**
- `ubuntu-latest` is a moving target. Pinning the runner makes the pipeline reproducible.
- When an early step fails, all later steps are skipped, so look for the first red step.
- Python 3.9 is end-of-life, so it may not stay available on hosted runners.

---

## Entry 4: CI failure, tests cannot import the app

**Date:** 01/11/2026

**Error**
```
tests/test_app.py:1: from app.app import app
ModuleNotFoundError: No module named 'app'
```

**What happened**
After the runner fix, `setup-python` and `pip install` passed and the `security` job went green. The `test` job still failed.

**Cause**
`pytest.ini` (with `pythonpath = .`) was inside the `app/` folder. Pytest only reads it from the folder it runs in or a parent, so it was ignored.

**Fix**
```bash
git mv app/pytest.ini pytest.ini
```
and changed the CI step to `python -m pytest -v --junitxml=test-results.xml`.

**What I learned**
- A correct config file in the wrong folder is silently ignored.
- `python -m pytest` adds the current folder to `sys.path`, while plain `pytest` does not. This explains why imports can work in one and fail in the other.
- Empty files like `app/__init__.py` are easy to forget to commit.

---

## Entry 5: Git history problems

**Goal:** Push the fix to GitHub.

I hit three separate Git problems in a row.

### 5a. Diverged history
```
Your branch and 'origin/main' have diverged, and have 2 and 3 different commits each, respectively.
! [rejected]  main -> main (non-fast-forward)
```
- **Cause:** I edited the workflow on github.com and also committed locally.
- **Fix:** `git pull --rebase origin main`, then `git push`.
- **Learned:** Always `git pull` before starting work. Never use `git push --force` just to silence the error, because it can erase someone else's commits.

### 5b. Merge conflict during rebase
```
CONFLICT (content): Merge conflict in .github/workflows/Secure-CI.yml
error: could not apply 89c7db9... moved pytest in root
```
- **Cause:** Both sides changed the same workflow file.
- **Fix:** Opened the file, kept `ubuntu-24.04` and `python -m pytest`, deleted every `<<<<<<<`, `=======`, `>>>>>>>` marker, then `git add` and `git rebase --continue`.
- **Learned:** During a rebase, "HEAD" is the remote side and the lower block is my commit. Conflict markers must be removed completely. `git rebase --abort` is the safe escape hatch.

### 5c. Detached HEAD
```
[detached HEAD a4830da] Add before-fix evidence
fatal: You are not currently on a branch.
```
- **Cause:** The rebase was left unfinished, so HEAD pointed at a commit instead of a branch.
- **Fix:** Finish the rebase (`git add .`, `git rebase --continue`), or save the commit with `git branch rescue-work`, switch to `main`, and merge it.
- **Learned:** A commit made in detached HEAD is not attached to any branch and can be lost. `git status` explains the state clearly if I read it first.

---

## Entry 6: Running the scanners and collecting "before" evidence

**What I did**
- Installed Semgrep, pip-audit, CycloneDX, pip-licenses, and the Gitleaks binary
- Ran each scanner locally and in CI
- Tagged the vulnerable state: `git tag v0-vulnerable`
- Saved outputs to `evidence/before/` and `sbom/sbom-before.json`

**Surprising result**
```
INF 8 commits scanned.
INF no leaks found
```
Gitleaks did not detect `SuperSecretPassword123!`.

**What I learned**
- Secret scanners match known token formats (such as specific API key patterns). A generic password is easy to miss.
- "No findings" does not mean "safe". Every scanner has blind spots, so using several tools and reviewing results matters.
- Scanner categories are different jobs: SAST reads my code, SCA checks my libraries, secret scanning checks for leaked credentials, and the SBOM lists everything I depend on.

**Numbers for the report**
- Semgrep findings: [N]
- pip-audit CVEs: [N]
- Gitleaks findings: 0

---

## Entry 7: Fixing the vulnerabilities and enforcing the gate

**What I did**
- Replaced string-built SQL with a parameterized query
- Replaced `yaml.load` with `yaml.safe_load`
- Read the key from `os.environ`
- Set `debug=False`
- Upgraded dependencies
- Updated the workflow: Python 3.12, removed every `|| true` and `continue-on-error`, used `semgrep --error`
- Added `if: always()` to scanner steps so all scanners run even when one fails

**What I learned**
- `|| true` is what turns a scanner from a report into a gate. Removing it makes findings fail the build.
- A secret deleted from code is still in Git history. The real fix is to **rotate** the secret, since it must be treated as compromised.
- Making changes on a branch and opening a pull request lets the pipeline check them before merge.
- Failing on every low-severity finding can cause alert fatigue, so teams often fail only on high severity.

---

## Entry 8: Automation script, docs, and the failing-PR test

**Date:** around 14/11/2026

**What I did**
- Wrote `run_all.sh` to run tests, Semgrep, pip-audit, Gitleaks, and the SBOM in one command, printing `RESULT: PASS` or `RESULT: FAIL`
- Created the setup guide, technical report, and README
- Created the throwaway branch `test/reintroduce-flaw` to prove the pipeline blocks a regression

**Errors**
```
fatal: The current branch test/reintroduce-flaw has no upstream branch.
nothing added to commit but untracked files present
```

**Cause**
- A new local branch has no remote counterpart until I push it with `-u`.
- The commit said "nothing added" because `run_all.sh` was already committed. Only `docs/` and `evidence/latest/` were untracked. Because the commands were chained with `&&`, the push never ran.
- More importantly, I was on the **throwaway branch** while trying to commit real project files.

**Fix**
- Run `git branch --show-current` before every commit.
- Switch to `main` to commit docs and scripts. Untracked files travel with me when switching branches.
- Add generated output (`evidence/latest/`) to `.gitignore`.
- Push the test branch only when I want the failing-PR demo: `git push -u origin test/reintroduce-flaw`, then `gh pr create --fill`.

**What I learned**
- `&&` stops the chain at the first failure, which is useful but can hide the fact that a later command never ran.
- Throwaway branches are for experiments only. Real work belongs on `main` or a proper feature branch.
- Generated files do not belong in version control.

---

## Mistakes and lessons table

| Mistake | Error | Lesson |
|---|---|---|
| Used `ubuntu-latest` | Python 3.9 not found on Ubuntu 26.04 | Pin runner and tool versions |
| `pytest.ini` inside `app/` | `ModuleNotFoundError: No module named 'app'` | Config file location matters |
| Edited on GitHub and locally | Non-fast-forward rejection | `git pull` before working |
| Left a rebase unfinished | Detached HEAD | Read `git status`, finish or abort the rebase |
| Trusted a clean Gitleaks run | Generic password undetected | Scanners have blind spots |
| Committed on a throwaway branch | "no upstream branch" | Check the branch before committing |

## Concepts I can now explain

- **CI/CD and GitHub Actions:** workflows, events, jobs, steps, runners, artifacts
- **SAST vs SCA:** analyzing my own code versus checking third-party libraries for known CVEs
- **CVE and CVSS:** the vulnerability ID and its severity score
- **SBOM:** a standard inventory of all components, useful when a new CVE is announced
- **Shift-left security:** catching problems at review time instead of in production
- **False positives:** findings that are not real problems, which need human review
- **Quality gate:** a check that blocks a merge when it fails
- **Git rebase vs merge:** replaying my commits on top of the remote ones versus joining the histories

## Commands I now use confidently

| Command | Purpose |
|---|---|
| `git status` | See what state I am in |
| `git branch --show-current` | Confirm my branch |
| `git pull --rebase origin main` | Combine remote and local commits cleanly |
| `git rebase --continue` / `--abort` | Finish or undo a rebase |
| `git tag v0-vulnerable` | Bookmark the vulnerable state |
| `git push -u origin <branch>` | Push a new branch and link it |
| `gh pr create --fill` | Open a pull request from the terminal |
| `python -m pytest -v` | Run tests with correct import paths |
| `./run_all.sh` | Run every check at once |

## Open questions

- When is merge better than rebase?
- How should a team decide which severity levels fail the build?
- How do I write a custom Semgrep rule or Gitleaks pattern for my own secret format?
- How do DAST tools like OWASP ZAP complement what I built?

## Final reflection

**Most important thing I learned:** Security is not the same as passing tests. Automated scanners catch what tests cannot, but each scanner has blind spots, so no single tool is proof of safety.

**Hardest problem:** The Git history issues (diverged branches, rebase conflict, detached HEAD). They looked frightening, but each had a calm, recoverable fix once I read the message and checked `git status`.

**What I would do differently:** Pin versions from the start, pull before every session, check my branch before committing, and save screenshots as I go instead of at the end.

**What I would add next:** Dependabot, Trivy container scanning, OWASP ZAP (DAST), branch protection requiring passing checks, pinning Actions to commit SHAs, and a custom Gitleaks rule for generic passwords.

---
