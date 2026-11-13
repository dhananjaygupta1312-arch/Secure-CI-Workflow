# Secure CI Workflow

![Secure CI](https://github.com/dhananjaygupta1312-arch/Secure-CI-Workflow/actions/workflows/Secure-CI.yml/badge.svg)

A DevSecOps project that shows how a GitHub Actions pipeline can catch security problems **before** code is merged. A deliberately vulnerable Flask app is scanned with four automated tools, fixed, and then protected by a pipeline that fails the build if the flaws come back.


---

## What the pipeline does

On every push and pull request, GitHub Actions runs:

| Stage | Tool | What it checks |
|---|---|---|
| Unit tests | pytest | App behaves correctly |
| SAST (static code analysis) | Semgrep | Insecure code patterns (SQL injection, unsafe YAML, debug mode) |
| SCA (dependency scan) | pip-audit | Known CVEs in third-party libraries |
| Secret scanning | Gitleaks | Leaked keys and tokens in files and Git history |
| SBOM (dependency inventory) | CycloneDX | Machine-readable list of every dependency |

Reports are saved as downloadable artifacts on each run.

```
code push -> tests -> SAST -> SCA -> secrets -> SBOM -> artifacts
                         \_____ any finding = build fails _____/
```

---

## Before and after

| Finding | Tool | Severity | Before | After | Fix |
|---|---|---|---|---|---|
| SQL injection | Semgrep | High | Found | Gone | Parameterized query |
| Unsafe `yaml.load` | Semgrep | High | Found | Gone | `yaml.safe_load` |
| Flask debug mode on | Semgrep | Medium | Found | Gone | `debug=False` |
| Hardcoded secret | Gitleaks | High | Not detected (see note) | Removed | Read from environment variable |
| Vulnerable dependencies | pip-audit | Varies | **N** CVEs | **0** | Upgraded packages |

> Fill in the real numbers from `evidence/before/` and `evidence/after/`.
>
> **Note:** Gitleaks reported "no leaks found" on the generic string used as the fake secret. Secret scanners match known token formats, so they miss plain passwords. This is a limitation discussed in the technical report.

---

## Repository layout

```
Secure-CI-Workflow/
├── app/
│   ├── __init__.py
│   ├── app.py                 # Flask app (vulnerable on tag v0-vulnerable, fixed on main)
│   └── requirements.txt
├── tests/
│   └── test_app.py
├── .github/workflows/
│   └── Secure-CI.yml          # the CI pipeline
├── docs/
│   ├── setup-guide.md
│   └── technical-report.md
├── evidence/
│   ├── before/                # scan outputs on the vulnerable version
│   └── after/                 # scan outputs on the fixed version
├── sbom/
│   ├── sbom-before.json
│   └── sbom-after.json
├── journal/
│   └── learning-journal.md
├── pytest.ini                 # must be in the project root
├── run_all.sh                 # runs every check locally
└── README.md
```

---

## Quick start

Requires Linux or WSL2 (Ubuntu), Git, and Python 3.12.

```bash
git clone https://github.com/dhananjaygupta1312-arch/Secure-CI-Workflow.git
cd Secure-CI-Workflow
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt pytest semgrep pip-audit cyclonedx-bom
python -m pytest -v
```

Run every check at once:

```bash
chmod +x run_all.sh
./run_all.sh
```

- On the vulnerable version (`git checkout v0-vulnerable`) it prints `RESULT: FAIL`.
- On the fixed version (`main`) it prints `RESULT: PASS`.

Full instructions: [docs/setup-guide.md](docs/setup-guide.md)

---

## Reproduce the "before" state

```bash
git checkout v0-vulnerable
./run_all.sh evidence/demo-before
git checkout main
```

---

## Documentation

- [Setup guide](docs/setup-guide.md)
- [Technical report](docs/technical-report.md)
- [Learning journal](journal/learning-journal.md)
- [Evidence before the fix](evidence/before/)
- [Evidence after the fix](evidence/after/)

---

## Limitations

- Scanners do not find logic or authorization bugs.
- Tools can raise false positives and need human review.
- A secret removed from code stays in Git history until it is **rotated**.
- Gitleaks missed a generic password because it relies on known token patterns.

---

*This project is for learning. The vulnerable code is intentional. Do not deploy it.*
