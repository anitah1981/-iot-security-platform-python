# Keeping Local and Live (Your Domain) in Sync

This doc explains how to ensure the app you run **locally** is the same version that runs on **your domain** (and what goes live).

---

## Single source of truth

- **One repo:** This GitHub repo (`-iot-security-platform-python`).
- **One branch for live:** `main`. What is on `main` is what **should** be deployed to your domain.
- **Deployment:** Railway (or your host) is connected to this repo and deploys from `main`. When you push to `main`, a new build runs and that code goes live on your domain.

So: **local `main` = what you work on → push → same code runs on your domain.** There is no separate “production” codebase; consistency comes from always going through Git and deploying from `main`.

---

## Workflow that keeps things consistent

### 1. Work only on `main` (or merge into `main` before going live)

- Check your branch: `git branch` (you should see `* main`).
- If you use a feature branch, merge it into `main` when it’s ready; only `main` is deployed to your domain.

### 2. Pull before you start work

- So your local code matches what’s on GitHub (and what’s live after the last deploy):
  ```bash
  git pull origin main
  ```
- Then run the app locally and make your changes.

### 3. Run and test locally

- From project root: `python -m uvicorn main:app --host 127.0.0.1 --port 8000`
- Test at `http://127.0.0.1:8000`. This is the same codebase that will go live after you push.

### 4. When you’re happy: commit and push to `main`

- Commit: `git add -A` then `git commit -m "Your message"`
- Push: `git push origin main`
- Railway will pick up the push (if auto-deploy is on) and deploy. Your domain will then run this new version.

### 5. Confirm deployment

- In Railway: **Deployments** tab — check that the latest deployment is from your latest commit.
- Open your domain in the browser and confirm the changes are there.

---

## Quick checklist before “go live”

Use this when you want to be sure what you’re about to push is what will go live:

| Check | Command / action |
|-------|-------------------|
| Current branch is `main` | `git branch` → `* main` |
| Local is up to date with GitHub | `git pull origin main` (no new commits from others, or merge them) |
| No uncommitted changes you forgot | `git status` → commit and push any changes you want live |
| Railway deploys from `main` | Railway → Project → Settings: “Deploy from GitHub” / “Branch: main” |

After you push, the version running on your domain will match your local `main` once the deploy finishes.

---

## If you use a different host (not Railway)

Same idea:

- Connect the host to this GitHub repo.
- Set the deploy branch to `main`.
- Every push to `main` triggers a new build; that build is what runs on your domain. No separate “production” copy — one repo, one branch, one pipeline.

---

## Summary

- **Local app** = same repo, branch `main`. You run it to develop and test.
- **Live app (your domain)** = Railway (or host) deploys from `main` on every push.
- **Consistency:** Always work from and push to `main`; pull before work; push when ready. That way the version you’re working on is the one connected to your domain and the one that goes live.
