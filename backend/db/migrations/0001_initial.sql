-- FounderShield AI - initial schema (Phase 02)
-- Reviewable migration. NOT yet applied to any live database.
-- Target: Supabase Postgres. Ownership via Supabase auth.users(id).

create extension if not exists "pgcrypto";

-- Interview sessions -----------------------------------------------------
create table if not exists interview_sessions (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users (id) on delete cascade,
    status text not null default 'CREATED'
        check (status in ('CREATED','IN_PROGRESS','READY_FOR_BRIEF',
                          'REVIEW_REQUIRED','APPROVED','EXPORTED','CANCELLED')),
    locale text not null default 'en',
    provider text not null default 'mock',
    question_count int not null default 0,
    paused boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create index if not exists idx_sessions_owner on interview_sessions (owner_id);

-- Interview records (REDACTED answer text only; no raw audio) ------------
create table if not exists interview_records (
    id uuid primary key default gen_random_uuid(),
    session_id uuid not null references interview_sessions (id) on delete cascade,
    owner_id uuid not null references auth.users (id) on delete cascade,
    question_key text not null,
    question_text text not null,
    answer_text text not null,          -- redacted content only
    source text not null default 'founder'
        check (source in ('founder','ai_suggestion')),
    is_dont_know boolean not null default false,
    created_at timestamptz not null default now()
);
create index if not exists idx_records_session on interview_records (session_id);
create index if not exists idx_records_owner on interview_records (owner_id);

-- Problem briefs ---------------------------------------------------------
create table if not exists problem_briefs (
    id uuid primary key default gen_random_uuid(),
    session_id uuid not null references interview_sessions (id) on delete cascade,
    owner_id uuid not null references auth.users (id) on delete cascade,
    current_version_id uuid,            -- FK added after brief_versions exists
    status text not null default 'draft',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create index if not exists idx_briefs_owner on problem_briefs (owner_id);

-- Immutable brief versions ----------------------------------------------
create table if not exists brief_versions (
    id uuid primary key default gen_random_uuid(),
    brief_id uuid not null references problem_briefs (id) on delete cascade,
    owner_id uuid not null references auth.users (id) on delete cascade,
    version_number int not null,
    content jsonb not null,
    content_hash text not null,
    created_by text not null default 'founder'
        check (created_by in ('founder','ai')),
    created_at timestamptz not null default now(),
    unique (brief_id, version_number)
);
create index if not exists idx_versions_brief on brief_versions (brief_id);
create index if not exists idx_versions_owner on brief_versions (owner_id);

alter table problem_briefs
    add constraint fk_briefs_current_version
    foreign key (current_version_id) references brief_versions (id)
    deferrable initially deferred;

-- Approvals (bind to one immutable version) ------------------------------
create table if not exists approval_records (
    id uuid primary key default gen_random_uuid(),
    brief_version_id uuid not null references brief_versions (id) on delete cascade,
    owner_id uuid not null references auth.users (id) on delete cascade,
    approved_content_hash text not null,
    destination text,
    status text not null default 'active'
        check (status in ('active','invalidated')),
    approved_at timestamptz not null default now(),
    invalidated_at timestamptz
);
create index if not exists idx_approvals_version on approval_records (brief_version_id);
create index if not exists idx_approvals_owner on approval_records (owner_id);

-- Audit events (no sensitive payloads) -----------------------------------
create table if not exists audit_events (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users (id) on delete cascade,
    session_id uuid references interview_sessions (id) on delete set null,
    event_type text not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);
create index if not exists idx_audit_owner on audit_events (owner_id);
