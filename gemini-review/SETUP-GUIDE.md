# 🤖 Gemini Code Review — Setup Guide

> Share this with your team to get automated AI code reviews on every PR.

---

## What You Get

| Workflow | Trigger | What It Does |
|----------|---------|-------------|
| **gemini-code-review.yml** | Every PR | Reviews all code for 6 checks: logical errors, loops, logging, SQL audit, flowcharts, summary |
| **gemini-security-review.yml** | PR touches auth/API/DB files | Deep security scan (OWASP-style) |
| **gemini-sql-audit.yml** | Every Monday (scheduled) | Counts all PostgreSQL procedures, creates GitHub Issue report |

### Supported Stack
- **Python** (Django, Flask, FastAPI)
- **PHP** (Laravel, plain PHP)
- **Node.js** (Express, NestJS, vanilla)
- **React** (JSX/TSX)
- **PostgreSQL** (functions, procedures, triggers)

---

## Setup (5 minutes)

### Option A: One-Command Setup

```bash
# Clone or download the gemini-review files, then:
chmod +x setup-gemini-review.sh
./setup-gemini-review.sh
```

The script will walk you through everything interactively.

### Option B: Manual Setup

#### Step 1 — Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click **"Create API Key"**
3. Copy the key (starts with `AIza...`)

#### Step 2 — Add the Secret to GitHub

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Name: `GEMINI_API_KEY`
4. Value: paste your API key
5. Click **"Add secret"**

> **Note:** `GITHUB_TOKEN` is provided automatically by GitHub Actions — you do NOT need to create it.

#### Step 3 — Copy the Workflow Files

Place these files in your repository:

```
your-repo/
├── .github/
│   └── workflows/
│       ├── gemini-code-review.yml       ← Main review (all PRs)
│       ├── gemini-security-review.yml   ← Security scan (auth/DB changes)
│       └── gemini-sql-audit.yml         ← Weekly SQL audit
├── docs/
│   └── styleguide.md                    ← Coding standards Gemini enforces
└── setup-gemini-review.sh               ← Setup script (optional)
```

#### Step 4 — Push & Test

```bash
git add .github/ docs/
git commit -m "[CHORE] Add Gemini code review workflows"
git push origin main
```

Now open a PR with any Python/PHP/JS/SQL changes and Gemini will post a review comment automatically.

#### Step 5 — Create Labels (Optional)

The SQL audit workflow creates issues with labels. Create them in your repo:

| Label | Color | Purpose |
|-------|-------|---------|
| `sql-audit` | `#0E8A16` | Weekly SQL audit reports |
| `automated` | `#1D76DB` | Auto-generated issues |
| `security` | `#D93F0B` | Security findings |
| `gemini-review` | `#7057FF` | Gemini review tags |

Or run: `./setup-gemini-review.sh` which creates them for you.

---

## What Each Check Does

### 1. Logical Errors
Gemini scans for bugs, off-by-one errors, null pointer risks, race conditions, incorrect boolean logic, wrong operators, and unreachable code. Each issue gets a severity rating and suggested fix.

### 2. Loop Analysis
Finds all loops (for, while, foreach, map, reduce, recursion) and flags potential infinite loops, O(n²)+ nested complexity, missing break conditions, and large dataset iteration without pagination.

### 3. Logging Audit
Enforces the team's logging standard: **every function must have logging**. Flags missing logging, wrong log levels, and sensitive data being logged (passwords, tokens, PII).

### 4. Flowchart Generation
Generates a **Mermaid flowchart** showing the PR's control flow — decision points, loops, error paths, and external calls (DB, API). Rendered directly in the GitHub comment.

### 5. PostgreSQL Procedure Count
Counts and catalogs all stored procedures, functions, and triggers in the PR's SQL files. Flags missing security context, injection risks, and missing error handling.

### 6. Overall Summary
Provides a severity breakdown and a merge recommendation: ✅ Approve / ⚠️ Approve with comments / ❌ Request changes, plus the top 3 things to fix.

---

## Security Review (Bonus)

When a PR touches auth, API, or database files, the security workflow runs automatically and checks for:

- Broken authentication & authorization
- SQL injection, XSS, command injection
- API security (rate limiting, CORS, validation)
- Database security (RLS, parameterization)
- Hardcoded secrets & insecure config

---

## Weekly SQL Audit

Every Monday at 07:00 UTC, the audit scans ALL `.sql` and `.pgsql` files in the repo and creates a GitHub Issue with:

- Full procedure/function/trigger inventory table
- Complexity analysis (top 10 most complex)
- Issues found (security, style, best practices)
- Actionable recommendations

To run it manually: go to **Actions** → **Gemini SQL Audit (Weekly)** → **Run workflow**.

---

## Configuration

### Change the Gemini Model

Edit the `GEMINI_MODEL` env variable in `gemini-code-review.yml`:

```yaml
env:
  GEMINI_MODEL: "gemini-2.5-pro"  # Change this
```

### Change Review Branches

Edit the `branches` list in each workflow:

```yaml
on:
  pull_request:
    branches: [main, develop, staging]  # Add or remove branches
```

### Change the SQL Audit Schedule

Edit the `cron` in `gemini-sql-audit.yml`:

```yaml
on:
  schedule:
    - cron: "0 7 * * 1"   # Mon 7am UTC — change as needed
```

### Increase File Limit

Edit `MAX_FILES` in `gemini-code-review.yml` (default: 50 files per PR).

---

## Costs

Gemini API pricing (as of 2025):
- **Gemini 2.5 Pro**: check [Google AI pricing](https://ai.google.dev/pricing)
- A typical PR review with ~20 files costs approximately $0.01 – $0.05
- The weekly SQL audit costs approximately $0.02 – $0.10 depending on repo size
- Free tier includes 50 requests/day which covers most small teams

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Workflow doesn't trigger | Check branch names match your PR's base branch |
| "Bad credentials" error | Verify `GEMINI_API_KEY` secret is set correctly |
| Review comment is empty | Check Actions log for Gemini API errors |
| Too many files error | Increase `MAX_FILES` or split your PR |
| SQL audit issue not created | Ensure the repo has Issues enabled and labels exist |
| Security review doesn't trigger | It only runs when auth/API/DB paths are changed |

---

## Team Onboarding Checklist

- [ ] API key created and added as `GEMINI_API_KEY` secret
- [ ] All 3 workflow files are in `.github/workflows/`
- [ ] `docs/styleguide.md` is committed
- [ ] Labels created (`sql-audit`, `automated`, `security`, `gemini-review`)
- [ ] Test PR opened and Gemini review posted successfully
- [ ] Team has read `docs/styleguide.md`
