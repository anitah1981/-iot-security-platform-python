# Admin and beta users: plan, role, and free full access

## 1. Set your test account to Business plan

Run (from project root, with MONGO_URI in .env):

```
python scripts/set_user_plan.py YOUR_EMAIL@example.com --plan business
```

Replace with the email you use to log in. You will then have Business features: audit logs, alert exports, higher device limit, etc.

## 2. Make a user an admin

Admins can unlock locked accounts and use network monitoring enable/disable. Set by email:

```
python scripts/set_user_plan.py THEIR_EMAIL@example.com --role admin
```

Combine with plan: `--plan business --role admin`

## 3. Give initial users full service for free (testing, no platform change)

Use **plan_override**: the app already uses it for feature checks. Set it to business so a user gets full access without Stripe:

```
python scripts/set_user_plan.py beta_user@example.com --plan-override business
```

Their stored plan can stay free; get_effective_plan() returns business. No change to the rest of the platform; you control who gets it by running the script for specific emails. To remove later: set plan_override to null in DB or add a script option.

## Script: scripts/set_user_plan.py

- Requires MONGO_URI in .env (production or Atlas).
- Args: email (required), --plan free|pro|business, --role consumer|user|business|admin, --plan-override pro|business.

Examples: --plan business (your test); --role admin (admin); --plan-override business (free full access for beta).
