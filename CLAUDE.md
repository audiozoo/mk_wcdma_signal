# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git & GitHub Workflow

This project uses Git for version control with all work pushed to GitHub (`audiozoo/mk_wcdma_signal`) so that progress is never lost and changes can be reverted at any time.

### Commit and push regularly
After completing any meaningful unit of work (new file, feature, fix, or significant edit), commit and push immediately. Do not batch up large amounts of unrelated changes into a single commit.

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

### Reverting
To undo the last pushed commit while keeping the changes locally:
```bash
git revert HEAD
git push origin main
```
