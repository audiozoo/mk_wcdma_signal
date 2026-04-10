# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git & GitHub Workflow

This project uses Git for version control with all work pushed to GitHub (`audiozoo/mk_wcdma_signal`). The goal is that **no work is ever lost** and we can always revert to a known-good state.

### Commit and push after every meaningful unit of work

This is non-negotiable. After completing any meaningful unit of work — a new file, a new feature, a bug fix, or a significant edit — commit and push immediately. Do not batch up unrelated changes into a single commit.

### Commit message format

- Use short, descriptive imperative subject lines (e.g. `Add WCDMA channel model`, `Fix spreading factor calculation`)
- Keep the subject line under 72 characters
- Add a blank line and a brief body only when the change needs context that the diff alone does not convey

### Workflow for every change

```bash
git add <specific files>
git commit -m "Short imperative description"
git push origin main
```

Always stage specific files rather than `git add -A` to avoid accidentally committing generated or sensitive files.

### Why this matters

Pushing to GitHub after each meaningful unit of work means:
- The project is always backed up remotely
- Any mistake can be reverted with a single command
- The full history of the project is preserved and readable

### Reverting

To undo the last pushed commit while keeping the changes locally:

```bash
git revert HEAD
git push origin main
```
