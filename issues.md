# Lab 5: Static Code Analysis - Issue Table

**File analysed:** `billing_system.py`

## Score Summary

Output of `python static_summary.py`.

| Tool | Before | Target | After |
|------|--------|--------|-------|
| Pylint | 4.43/10 | > 9.5 | |
| Bandit (High / Medium / Low) | 1 / 1 / 3 | 0 / 0 / 0 | |
| Flake8 | 36 issues | 0 | |

Raw output (before):

```
File:    billing_system.py
Pylint:  4.43/10   (target > 9.5)
Bandit:  High=1  Medium=1  Low=3   (target all 0)
Flake8:  36 issues   (target 0)
```

---

## 1. Bandit (Security) - fix commit #1

| # | Issue ID | Type | Severity | Line(s) | Description | Fix Approach | 
|---|----------|------|----------|---------|-------------|--------------|
| 1 | B413 | Security | High | 8 | `from Crypto.Cipher import AES` uses the deprecated pyCrypto-style import | Switch to the maintained `cryptography` library (e.g. AES-GCM via `cryptography.hazmat`) and update `encryptCard` accordingly | |
| 2 | B702 | Security | Medium | 86 | Mako `Template` renders `${user}` and `${amount}` without escaping, so it is open to XSS | Escape variables with the `h` filter (`${user \| h}`) or use `default_filters=['h']` | |
| 3 | B105 | Security | Low | 14 | Hardcoded secret `WEBHOOK_SECRET` | Read from an environment variable (`os.environ.get`) and fail clearly if missing | |
| 4 | B311 | Security | Low | 67 | `random.choice` used for coupon codes, not cryptographically secure | Use `secrets.choice` instead of `random.choice` | |
| 5 | B101 | Security | Low | 85 | `assert amount >= 0` is stripped when Python runs with `-O` | Replace with an explicit `if amount < 0: raise ValueError(...)` | |
| 6 | (not flagged) | Security | n/a | 15 | Hardcoded `CARD_KEY` is also a secret in source code, though Bandit did not flag it | Load from an environment variable, same as `WEBHOOK_SECRET` | |

---

## 2. Pylint (Quality) - fix commit #2

Target: score above **9.5**. Baseline: **4.43/10**.

| # | Issue ID | Type | Severity | Line(s) | Description | Fix Approach | 
|---|----------|------|----------|---------|-------------|--------------|
| 1 | E0601 | Bug | High | 63 | `refund` used before assignment | Initialise `refund` before the `try` block, or restructure so every path assigns it | |
| 2 | W0134 / W0150 | Bug | High | 63 | `return` inside `finally` shadows the return value and can swallow exceptions | Move the `return` out of `finally`; keep only cleanup code there | |
| 3 | C0103 | Convention | Low | 24, 27, 35, 40, 43, 50, 58, 66, 69, 72, 76, 80, 84 | 13 functions use camelCase instead of snake_case (`isTrialOver`, `applyCoupon`, etc.) | Rename to snake_case and update every call site, including the main block near line 107 | |
| 4 | C0114 / C0116 | Convention | Low | 1, 20, 24, 27, 35, 40, 43, 50, 58, 66, 69, 72, 76, 80, 84, 88 | Missing module docstring and function docstrings | Add a short one-line docstring to the module and each function | |
| 5 | C0301 | Convention | Low | 86, 96, 98, 100 | Lines longer than 100 characters | Break the lines (also resolves the related Flake8 E501 items) | |
| 6 | W0611 | Warning | Low | 1 | Unused imports `os`, `sys` | Remove them, or keep `os` if used for env variables in the Bandit fixes | |
| 7 | C0410 | Convention | Low | 1 | Multiple imports on one line | One import per line | |
| 8 | C0121 | Convention | Low | 29 | `coupon == None` | Use `coupon is None` | |
| 9 | R1735 | Refactor | Low | 16 | `dict()` call | Use a `{}` literal | |
| 10 | R1734 | Refactor | Low | 21 | `list()` call | Use a `[]` literal | |
| 11 | R1718 | Refactor | Low | 70 | Set can be built with a set comprehension | Rewrite as a `{...}` comprehension | |
| 12 | C0206 | Convention | Low | 70 | Iterating dict keys then indexing | Iterate with `.items()` | |
| 13 | W1406 | Warning | Low | 86 | Redundant `u""` string prefix | Remove the `u` | |
| 14 | I1101 | Info | Info | 81 | `lxml.etree` members cannot be introspected | Optional: add `--extension-pkg-allow-list=lxml` or ignore | |

---

## 3. Flake8 (Style) - fix commit #3

Target: **0 issues**. Baseline: **36 issues**.

| # | Issue ID | Type | Count | Line(s) | Description | Fix Approach 
|---|----------|------|-------|---------|-------------|--------------
| 1 | E302 | Style | 15 | 20, 24, 27, 35, 40, 43, 50, 58, 66, 69, 72, 76, 80, 84, 88 | Expected 2 blank lines before a function | Add a second blank line before each function | |
| 2 | E501 | Style | 16 | 21, 67, 70, 77, 86, 91, 92, 93, 94, 95, 96, 98, 100, 101, 103, 104 | Line longer than 79 characters | Wrap long lines using parentheses or intermediate variables | |
| 3 | F401 | Bug-risk | 2 | 1 | `os` and `sys` imported but unused | Remove (overlaps with Pylint W0611) | |
| 4 | E401 | Style | 1 | 1 | Multiple imports on one line | Split into separate lines (overlaps with Pylint C0410) | |
| 5 | E711 | Style | 1 | 29 | Comparison to `None` with `==` | Use `is None` (overlaps with Pylint C0121) | |
| 6 | E305 | Style | 1 | 107 | Expected 2 blank lines after the last function | Add a second blank line before the main block | |
| | | | **36** | | **Total** | | |

---

## 4. Overlaps (one fix clears several reports)

| Fix | Clears |
|-----|--------|
| Remove unused `os`/`sys` imports | Pylint W0611, Flake8 F401 |
| Split imports onto separate lines | Pylint C0410, Flake8 E401 |
| `== None` to `is None` | Pylint C0121, Flake8 E711 |
| Wrap long lines | Pylint C0301, Flake8 E501 |

