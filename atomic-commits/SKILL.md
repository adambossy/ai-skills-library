---
name: atomic-commits
description: Make clean, atomic git commits that always leave the repository in a working state. Use when the user has multiple unstaged changes and wants to commit them as a well-ordered series of small, focused commits.
---

# Atomic Commits

Analyze unstaged changes, identify dependency relationships, and create a well-ordered series of small, focused commits that each leave the repository in a working state.

## Quick Start

1. **Assess** — Review all staged and unstaged changes
2. **Analyze** — Map dependency relationships between changes
3. **Plan** — Propose a commit sequence (get user approval)
4. **Execute** — Create commits one at a time, verifying after each
5. **Verify** — Show the final commit log

## Workflow

### 1. Assess the Current State

```bash
git status --porcelain
git diff --stat
git diff --cached --stat
```

If there are no changes, stop — nothing to commit.

### 2. Analyze Changes and Plan Commit Order

Read the actual diffs to understand what changed:

```bash
git diff
git diff --cached
```

Map the dependency relationships between all changed files:

- **Self-contained** — Can be committed independently
- **Dependent** — Requires other changes to be committed first (e.g., a new import used in another file, a schema change needed by a query)
- **Logically related** — Part of the same feature, fix, or refactoring

### 3. Plan the Commit Sequence

Apply these ordering rules:

1. **Standalone changes first.** If file A can be committed independently but file B depends on changes in file A, commit A before B.
2. **Each commit must be functional.** Code should work after every commit. Changes that depend on each other must be in the same commit.
3. **Group related commits sequentially.** If commits B and C relate to a feature but commit A is an unrelated fix, order them A → B → C so history reads cleanly by topic.
4. **Smaller is better.** When in doubt, prefer more smaller commits over fewer large ones. Five small commits are better than one large commit with the same changes.

Present the plan to the user before executing:

```
Planned commits:
1. <short description> — <files>
2. <short description> — <files>
...
```

Wait for approval before proceeding.

### 4. Execute Commits

For each planned commit:

1. **Stage specific files only** — Use `git add <file>...`. Never use `git add -A` or `git add .`.
2. **Write a concise message** — Imperative mood, first line under 72 characters.
3. **Commit with HEREDOC** for clean formatting:
   ```bash
   git add <files> && git commit -m "$(cat <<'EOF'
   <commit message>

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   ```
4. **Verify** the commit succeeded (`git status --porcelain`) before moving on.

### 5. Final Verification

```bash
git log --oneline -<N>
```

Show the user the commit log so they can review.

## Rules

- **Never `git add -A` or `git add .`** — Always stage specific files by name.
- **Never `--no-verify`** — If a hook fails, fix the issue and retry.
- **Never amend** unless the user explicitly asks — always create new commits.
- **Never commit secrets** — Warn the user if `.env`, credentials, or token files appear in the changeset.
- **One change is fine** — If there's only one logical change, a single commit is correct. Don't split artificially.
- **Partial staging** — If only some hunks in a file belong to a commit and this can't be handled non-interactively, tell the user and ask them to stage those hunks manually.

## Dependency Analysis Examples

See [EXAMPLES.md](EXAMPLES.md) for walkthroughs of common scenarios.
