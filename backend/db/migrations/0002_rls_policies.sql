-- FounderShield AI - Row-Level Security policies (Phase 02)
-- Reviewable migration. NOT yet applied to any live database.
-- Each table is owner-scoped: a row is visible/mutable only when its
-- owner_id equals auth.uid(). RLS is a defense-in-depth layer in ADDITION
-- to application-level ownership checks. Do NOT disable RLS for convenience.

alter table interview_sessions enable row level security;
alter table interview_records  enable row level security;
alter table problem_briefs      enable row level security;
alter table brief_versions      enable row level security;
alter table approval_records    enable row level security;
alter table audit_events        enable row level security;

-- Helper: policies below assume Supabase sets auth.uid() to the caller.

-- interview_sessions
create policy sessions_select on interview_sessions
    for select using (owner_id = auth.uid());
create policy sessions_insert on interview_sessions
    for insert with check (owner_id = auth.uid());
create policy sessions_update on interview_sessions
    for update using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy sessions_delete on interview_sessions
    for delete using (owner_id = auth.uid());

-- interview_records
create policy records_select on interview_records
    for select using (owner_id = auth.uid());
create policy records_insert on interview_records
    for insert with check (owner_id = auth.uid());
create policy records_delete on interview_records
    for delete using (owner_id = auth.uid());

-- problem_briefs
create policy briefs_select on problem_briefs
    for select using (owner_id = auth.uid());
create policy briefs_insert on problem_briefs
    for insert with check (owner_id = auth.uid());
create policy briefs_update on problem_briefs
    for update using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy briefs_delete on problem_briefs
    for delete using (owner_id = auth.uid());

-- brief_versions (immutable: select + insert only, no update policy)
create policy versions_select on brief_versions
    for select using (owner_id = auth.uid());
create policy versions_insert on brief_versions
    for insert with check (owner_id = auth.uid());
create policy versions_delete on brief_versions
    for delete using (owner_id = auth.uid());

-- approval_records
create policy approvals_select on approval_records
    for select using (owner_id = auth.uid());
create policy approvals_insert on approval_records
    for insert with check (owner_id = auth.uid());
create policy approvals_update on approval_records
    for update using (owner_id = auth.uid()) with check (owner_id = auth.uid());

-- audit_events (append + read own; no update/delete)
create policy audit_select on audit_events
    for select using (owner_id = auth.uid());
create policy audit_insert on audit_events
    for insert with check (owner_id = auth.uid());
