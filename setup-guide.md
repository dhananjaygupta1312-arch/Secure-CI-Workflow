# Setup Guide

This guide takes you from a blank machine to running the full test and security pipeline, locally and on GitHub Actions. It assumes **Windows with WSL2 (Ubuntu)**. On Mac or Linux, skip section 1.

Commands marked 🐧 run in the Ubuntu terminal. Commands marked 🪟 run in Windows PowerShell.

---

## 1. Prerequisites

| Tool | Purpose | Check |
|---|---|---|
| WSL2 + Ubuntu (Windows only) | Linux environment matching CI | `wsl -l -v` shows VERSION 2 |
| Git | Version control | `git --version` |
| Python 3.12 | Runs the fixed app and scanners | `python3 --version` |
| VS Code + WSL extension | Editor | Bottom-left shows **WSL: Ubuntu** |
| GitHub account + GitHub CLI (`gh`) | Hosting and CI | `gh auth status` |

### Install WSL2 (Windows only)
🪟 PowerShell as Administrator:
```powershell
wsl --install -d Ubuntu
```
Restart when asked, then create a Linux username and password.

### Install Linux tools
🐧
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-venv python3-pip curl gh
```

### Configure Git and log in to GitHub
🐧
```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
git config --global core.autocrlf input
gh auth login
gh auth status
```
For `gh auth login` choose GitHub.com, then HTTPS, then log in with a web browser.

---

## 2. Clone the repository

Keep the project inside the Linux filesystem (`~/projects`), not under `/mnt/c/`, which is slow and causes line-ending problems.

🐧
```bash
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/dhananjaygupta1312-arch/Secure-CI-Workflow.git
cd Secure-CI-Workflow
```

---

## 3. Create the Python environment

🐧
```bash
python3 -m venv .venv
source .venv/bin/activate
```
Your prompt should now start with `(.venv)`. Re-run the `source` line in every new terminal.

If your system Python is not 3.12, install `uv` and let it fetch the right version:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
uv venv --python 3.12 .venv
source .venv/bin/activate
```

### Install dependencies
```bash
pip install -r app/requirements.txt pytest
pip install semgrep pip-audit cyclonedx-bom pip-licenses
```

### Install Gitleaks (separate binary)
Find the current version at https://github.com/gitleaks/gitleaks/releases, then replace `X.Y.Z`:
```bash
cd /tmp
curl -sSL -o gitleaks.tar.gz https://github.com/gitleaks/gitleaks/releases/download/vX.Y.Z/gitleaks_X.Y.Z_linux_x64.tar.gz
tar -xzf gitleaks.tar.gz gitleaks
sudo mv gitleaks /usr/local/bin/
cd ~/projects/Secure-CI-Workflow
gitleaks version
```

---

## 4. Open in VS Code

🐧
```bash
code .
```
Confirm the green **WSL: Ubuntu** box at bottom-left. Then press `Ctrl+Shift+P`, choose **Python: Select Interpreter**, and pick `.venv/bin/python`. Open the terminal with `` Ctrl+` ``.

---

## 5. Run the tests

🐧
```bash
python -m pytest -v
```
Expected: `1 passed`.

`pytest.ini` must sit in the **project root** (beside `app/` and `tests/`). Pytest ignores it if it is inside `app/`.

---

## 6. Run each security scanner

| Scanner | Command | What it checks |
|---|---|---|
| Semgrep (SAST) | `semgrep scan --config auto --error app/` | Insecure code patterns |
| pip-audit (SCA) | `pip-audit -r app/requirements.txt` | Known CVEs in dependencies |
| Gitleaks (secrets) | `gitleaks detect --source . -v` | Secrets in files and Git history |
| CycloneDX (SBOM) | `cyclonedx-py requirements app/requirements.txt -o sbom/sbom.json` | Dependency inventory |
| pip-licenses | `pip-licenses --format=markdown --with-urls` | Package, version, license table |

Semgrep needs internet access to download its rules. Flag names can differ between versions, so run `<tool> --help` if one errors.

### Run everything at once
```bash
chmod +x run_all.sh
./run_all.sh
```
It prints `RESULT: PASS` when all checks are clean and `RESULT: FAIL` otherwise. Pass a folder name to save reports elsewhere: `./run_all.sh evidence/demo-after`.

---

## 7. Reproduce the "before" and "after" states

```bash
git checkout v0-vulnerable        # deliberately vulnerable version (uses old pinned dependencies)
./run_all.sh evidence/demo-before # expect RESULT: FAIL
git checkout main                 # fixed version
./run_all.sh evidence/demo-after  # expect RESULT: PASS
```

The vulnerable tag uses old pinned packages that may not install on Python 3.12. For that tag, create a Python 3.9 environment:
```bash
uv venv --python 3.9 .venv-old
source .venv-old/bin/activate
pip install -r app/requirements.txt pytest
```
Switch back with `deactivate`, then `source .venv/bin/activate`.

---

## 8. Use GitHub Actions

The pipeline is defined in `.github/workflows/Secure-CI.yml` and runs automatically on every push and pull request.

1. Push a commit: `git add . && git commit -m "message" && git push`
2. Open the repo on github.com and click the **Actions** tab.
3. Click the latest run, then click a job (`test` or `security`) to read its log.
4. A green check means all steps passed. A red X means a step failed; expand it to read the error.
5. Scroll to **Artifacts** at the bottom of the run page and download `test-results` and `security-reports`.

### Important workflow settings
- `runs-on: ubuntu-24.04` is pinned because `ubuntu-latest` can change and break the Python setup.
- Scanner steps have no `|| true`, so findings fail the job. That is intentional.
- `fetch-depth: 0` makes Gitleaks scan the full history.

---

## 9. Daily workflow

```bash
cd ~/projects/Secure-CI-Workflow
git pull                          # always pull first
source .venv/bin/activate
# edit files
python -m pytest -v
./run_all.sh
git add .
git commit -m "describe the change"
git push
```

Make changes on a branch and open a pull request so the pipeline can check them before merge:
```bash
git checkout -b my-change
git push -u origin my-change
gh pr create --fill
```

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `The version '3.9' ... was not found for Ubuntu 26.04` | `ubuntu-latest` moved to a newer image | Set `runs-on: ubuntu-24.04`, or use a newer Python |
| `ModuleNotFoundError: No module named 'app'` | `pytest.ini` not in project root, or `app/__init__.py` missing | `git mv app/pytest.ini pytest.ini`, `touch app/__init__.py`, and use `python -m pytest` |
| `! [rejected] main -> main (non-fast-forward)` | Local and remote history diverged | `git pull --rebase origin main`, then `git push` |
| `CONFLICT (content): Merge conflict in ...` | Same file edited in two places | Edit the file, delete the `<<<<<<<`, `=======`, `>>>>>>>` lines, then `git add .` and `git rebase --continue` |
| `You are not currently on a branch` (detached HEAD) | Unfinished rebase, or a tag/commit was checked out | Finish with `git rebase --continue`, or `git branch rescue-work && git switch main && git merge rescue-work` |
| `pip install` fails on old pinned versions | Old packages do not support Python 3.12 | Use a Python 3.9 environment for `v0-vulnerable` |
| Gitleaks finds nothing for a fake password | Scanners match known token patterns only | Expected. Use a realistic token format for demos |
| Gitleaks flags a secret in old commits on `main` | Secret remains in Git history | Rotate the secret, add the fingerprint to `.gitleaksignore`, and explain it in the report |
| Semgrep cannot download rules | No internet access | Check the network, or show saved output from `evidence/` |
| `git push` asks for a password repeatedly | Not logged in | Run `gh auth login` again |
| `code .` not found | VS Code not on PATH | Reinstall VS Code on Windows with "Add to PATH", restart Ubuntu |
| Venv packages not found in VS Code | Wrong interpreter selected | Select `.venv/bin/python` again |
| Slow file access | Project is under `/mnt/c/` | Move it to `~/projects` |
| Packages not found after reopening terminal | Venv not activated | `source .venv/bin/activate` |

---

## 11. Verify your setup

- [ ] `python -m pytest -v` shows `1 passed`
- [ ] `./run_all.sh` prints `RESULT: PASS` on `main`
- [ ] The Actions tab shows a green run
- [ ] You can download the `security-reports` artifact
- [ ] A fresh clone in `/tmp` works by following only this guide

Fresh-clone test:
```bash
cd /tmp && git clone https://github.com/dhananjaygupta1312-arch/Secure-CI-Workflow.git test-clone
cd test-clone && cat docs/setup-guide.md
```
