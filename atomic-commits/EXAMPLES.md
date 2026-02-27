# Dependency Analysis Examples

## Example 1: Independent Changes

**Scenario**: You have changes in three files with no dependencies between them.

```
Changed files:
  README.md          — Fixed a typo
  app/config.py      — Updated a default timeout value
  tests/test_auth.py — Added a missing test case
```

**Analysis**: All three are self-contained. No file depends on changes in another.

**Commit order**: Any order works. Group by topic:

```
1. Fix typo in README — README.md
2. Update default timeout value — app/config.py
3. Add missing auth test case — tests/test_auth.py
```

## Example 2: Schema Change with Dependent Code

**Scenario**: You added a column to a database model and updated code that uses it.

```
Changed files:
  app/models/user.py       — Added `last_login_at` column
  app/services/auth.py     — Sets `last_login_at` on login
  app/api/users.py         — Returns `last_login_at` in response
  migrations/003_add_col.py — Migration for the new column
```

**Analysis**:
- `models/user.py` + `migrations/003_add_col.py` are the foundation — everything else depends on the column existing
- `auth.py` and `api/users.py` both depend on the model change but are independent of each other

**Commit order**:

```
1. Add last_login_at column to User model — app/models/user.py, migrations/003_add_col.py
2. Set last_login_at on user login — app/services/auth.py
3. Return last_login_at in user API response — app/api/users.py
```

## Example 3: Unrelated Fix Mixed with Feature Work

**Scenario**: While working on a feature, you also fixed a bug you noticed.

```
Changed files:
  app/utils/format.py      — Fixed off-by-one error in date formatting (bug fix)
  app/services/reports.py   — New report generation feature
  app/api/reports.py        — New API endpoint for reports
  tests/test_reports.py     — Tests for the new feature
```

**Analysis**:
- The `format.py` fix is completely independent
- The report files all relate to the same feature and depend on each other

**Commit order**: Unrelated fix first, then the feature:

```
1. Fix off-by-one in date formatting — app/utils/format.py
2. Add report generation service — app/services/reports.py
3. Add reports API endpoint and tests — app/api/reports.py, tests/test_reports.py
```

## Example 4: Refactoring Then Using the Refactored Code

**Scenario**: You extracted a utility function, then used it in new code.

```
Changed files:
  app/lib/validation.py    — Extracted `validate_email()` from inline code
  app/services/signup.py   — Removed inline validation, now calls `validate_email()`
  app/services/invite.py   — New feature that also uses `validate_email()`
```

**Analysis**:
- `validation.py` + `signup.py` must go together (extracting the function and updating the caller is one atomic change)
- `invite.py` depends on `validate_email()` existing

**Commit order**:

```
1. Extract email validation into shared utility — app/lib/validation.py, app/services/signup.py
2. Add invite service using shared email validation — app/services/invite.py
```
