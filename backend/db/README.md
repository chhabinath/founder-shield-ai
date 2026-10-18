# Database & migrations

> **Status:** reviewable migrations, **not yet applied to any live
> database** (no Supabase project/credentials connected in this phase).

## Backends

The backend selects persistence via `DATABASE_BACKEND`:

- `memory` (default) - in-memory repositories for local dev/tests. No
  credentials required. Data is non-persistent.
- `supabase` - Supabase Postgres. Required in production (enforced by
  config validation). A Supabase-backed repository implementation is added
  behind the existing repository interfaces once credentials exist.

## Applying migrations (when a Supabase project is available)

Order matters: `0001_initial.sql` then `0002_rls_policies.sql`.

Apply via the Supabase SQL editor or CLI (do not run destructive migrations
against an existing production database):

```bash
# Example only - requires a configured project.
supabase db execute --file db/migrations/0001_initial.sql
supabase db execute --file db/migrations/0002_rls_policies.sql
```

## Row-Level Security

Every table is owner-scoped by `owner_id = auth.uid()`. RLS is a
defense-in-depth layer in ADDITION to application-level ownership checks in
the repository/service code. RLS must never be disabled for convenience.

## Data minimization & retention

- No raw audio is stored. `interview_records.answer_text` holds redacted
  content only.
- Redacted interview records are retained for `INTERVIEW_RETENTION_DAYS`
  (default 30). Owners may delete their data at any time; deletes cascade
  to dependent rows via `on delete cascade`.

## Verification status

These policies are **unverified against a live database**. When a project
is connected, verify: (1) RLS blocks cross-owner selects, (2) inserts with a
mismatched owner_id are rejected, (3) cascade deletes behave as intended.
