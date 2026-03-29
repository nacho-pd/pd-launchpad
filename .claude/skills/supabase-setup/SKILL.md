---
name: supabase-setup
description: "Supabase schema design, migrations, RLS policies, and auth configuration"
---

# Supabase Setup

Designs and implements the full Supabase backend: schema, migrations, Row Level Security
policies, authentication configuration, and seed data. All changes go through migrations —
the database is never modified directly.

---

## 1. Input

| Input | Source | Required |
|---|---|---|
| Data model | `docs/architecture.md` (entities, relationships) | Yes |
| Spec requirements | `docs/specs/<feature>.md` (data/auth needs) | Yes |
| Existing migrations | `supabase/migrations/` directory | No |
| Auth requirements | Spec (login methods, roles, permissions) | Yes |
| Seed data needs | Development/testing requirements | No |
| Performance requirements | NFRs from spec (query latency, data volume) | No |

### Pre-Requisites

Before running this skill:
- Supabase CLI is installed (`supabase --version`)
- Supabase project is initialized (`supabase init` has been run)
- Local Supabase is running (`supabase start`) or remote project is linked
- `docs/architecture.md` contains at least an entity list with relationships

---

## 2. Thinking Frameworks

### 2.1 Migration Workflow

Migrations are the ONLY way to modify the database schema. This ensures reproducibility
across environments (local, preview, staging, production).

**Rules:**
1. Never modify the database directly via the Supabase dashboard or `psql` in production.
2. Migrations are numbered sequentially: `YYYYMMDDHHMMSS_description.sql`
3. Each migration must be idempotent where possible (use `IF NOT EXISTS`, `IF EXISTS`).
4. Every migration should be reversible — include a rollback comment block.
5. One migration per logical change (don't mix unrelated schema changes).
6. Test migrations locally before applying to remote.

**Creating a migration:**
```bash
supabase migration new <description>
# Creates: supabase/migrations/<timestamp>_<description>.sql
```

**Applying migrations:**
```bash
# Local
supabase db reset  # Drops and recreates from all migrations

# Remote
supabase db push   # Applies pending migrations to linked project
```

### 2.2 Schema Design Principles

**Normalize first, denormalize with evidence:**
- Start with 3NF (Third Normal Form) — no data duplication.
- Denormalize only when you have measured query performance issues.
- Document every denormalization decision with the query it optimizes.

**Primary keys:**
- Use `uuid` for all primary keys (never serial/integer).
- Generate with `gen_random_uuid()` (built into PostgreSQL 13+).
- UUIDs prevent enumeration attacks and simplify distributed systems.

**Timestamps:**
- Every table gets `created_at` and `updated_at` columns.
- Use `timestamptz` (timestamp with time zone), never `timestamp`.
- Default `created_at` to `now()`.
- Use a trigger for `updated_at` auto-update.

**Naming conventions:**
- Tables: `snake_case`, plural (`users`, `projects`, `team_members`)
- Columns: `snake_case` (`first_name`, `created_at`)
- Foreign keys: `<referenced_table_singular>_id` (`user_id`, `project_id`)
- Indexes: `idx_<table>_<columns>` (`idx_projects_user_id`)
- Constraints: `<table>_<column>_<type>` (`projects_name_unique`)

**Standard columns template:**
```sql
CREATE TABLE IF NOT EXISTS public.example (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  -- domain columns here --
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);
```

**Updated_at trigger (create once, reuse):**
```sql
-- Include this in the first migration, reuse for all tables
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to each table:
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.example
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();
```

### 2.3 RLS Policy Design

Row Level Security is the primary access control mechanism in Supabase. Every table
that stores user data MUST have RLS enabled.

**Principle: Deny by default, grant minimum necessary.**

```sql
-- Step 1: Enable RLS (denies all access by default)
ALTER TABLE public.example ENABLE ROW LEVEL SECURITY;

-- Step 2: Grant specific access via policies
CREATE POLICY "Users can read own data"
  ON public.example
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own data"
  ON public.example
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own data"
  ON public.example
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own data"
  ON public.example
  FOR DELETE
  USING (auth.uid() = user_id);
```

**Common RLS patterns:**

**1. Owner-only access (most common):**
```sql
-- User can only see/modify their own rows
USING (auth.uid() = user_id)
```

**2. Team-based access:**
```sql
-- User can see rows belonging to their team
USING (
  team_id IN (
    SELECT team_id FROM public.team_members
    WHERE user_id = auth.uid()
  )
)
```

**3. Role-based access:**
```sql
-- Only admins can delete
CREATE POLICY "Admins can delete"
  ON public.example
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.team_members
      WHERE user_id = auth.uid()
        AND team_id = example.team_id
        AND role = 'admin'
    )
  )
```

**4. Public read, authenticated write:**
```sql
-- Anyone can read (including anonymous)
CREATE POLICY "Public read"
  ON public.example
  FOR SELECT
  USING (true);

-- Only authenticated users can write
CREATE POLICY "Authenticated insert"
  ON public.example
  FOR INSERT
  WITH CHECK (auth.uid() IS NOT NULL);
```

**5. Service role bypass (for server-side operations):**
```sql
-- RLS is automatically bypassed when using the service_role key
-- No policy needed — but NEVER expose service_role key to the client
```

**RLS testing:**
```sql
-- Test as anonymous user
SET request.jwt.claim.sub = '';
SET role TO anon;
SELECT * FROM public.example;  -- Should return empty or public rows only

-- Test as authenticated user
SET request.jwt.claim.sub = '<user-uuid>';
SET role TO authenticated;
SELECT * FROM public.example;  -- Should return only user's rows

-- Reset
RESET role;
```

### 2.4 Auth Patterns

**Supabase Auth for user management:**
- Email/password login (default)
- Magic link (passwordless email)
- OAuth providers (Google, GitHub, etc.)
- Phone/SMS OTP

**Auth configuration in migrations:**
```sql
-- User profiles table (extends auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
  id          uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name   text,
  avatar_url  text,
  role        text NOT NULL DEFAULT 'member' CHECK (role IN ('member', 'admin', 'owner')),
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name, avatar_url)
  VALUES (
    NEW.id,
    NEW.raw_user_meta_data->>'full_name',
    NEW.raw_user_meta_data->>'avatar_url'
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();
```

### 2.5 Seed Data Patterns

**Rules for seed data:**
1. Development seeds are separate from production seeds.
2. Seed scripts must be idempotent (safe to run multiple times).
3. Use `ON CONFLICT DO NOTHING` or `INSERT ... WHERE NOT EXISTS`.
4. Never seed sensitive data (passwords, tokens) — use dummy values.
5. Seed data should exercise all RLS policies (create users with different roles).

**Seed file structure:**
```
supabase/
  seed.sql              # Development seed data (runs on `supabase db reset`)
  migrations/
    20260101000000_initial_schema.sql
    20260101000001_rls_policies.sql
    20260101000002_auth_setup.sql
```

**Idempotent seed example:**
```sql
-- supabase/seed.sql

-- Create test users (these are created in auth.users by Supabase CLI)
-- For local dev, use supabase/config.toml to configure test users

-- Seed data for development
INSERT INTO public.projects (id, name, user_id, description)
VALUES
  ('a0000000-0000-0000-0000-000000000001', 'Demo Project',
   'b0000000-0000-0000-0000-000000000001', 'A sample project for development'),
  ('a0000000-0000-0000-0000-000000000002', 'Test Project',
   'b0000000-0000-0000-0000-000000000001', 'Another sample project')
ON CONFLICT (id) DO NOTHING;
```

### 2.6 Index Strategy

**Create indexes for:**
- Foreign key columns (PostgreSQL does NOT auto-index FKs)
- Columns used in WHERE clauses frequently
- Columns used in ORDER BY
- Columns used in RLS policy conditions

**Do NOT index:**
- Small tables (<1000 rows)
- Columns with low cardinality (boolean, enum with few values)
- Columns rarely queried

```sql
-- Foreign key index (always create these)
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects (user_id);

-- Composite index for common query pattern
CREATE INDEX IF NOT EXISTS idx_tasks_project_status
  ON public.tasks (project_id, status);

-- Partial index for active records
CREATE INDEX IF NOT EXISTS idx_tasks_active
  ON public.tasks (project_id)
  WHERE status != 'archived';
```

---

## 3. Expected Output

The skill produces the following files:

| File | Purpose |
|---|---|
| `supabase/migrations/<timestamp>_initial_schema.sql` | Table definitions, indexes, triggers |
| `supabase/migrations/<timestamp>_rls_policies.sql` | All RLS policies |
| `supabase/migrations/<timestamp>_auth_setup.sql` | Profile table, auth triggers |
| `supabase/seed.sql` | Development seed data |
| `docs/architecture.md` (updated) | Schema documentation section added |

### Migration File Template

```sql
-- Migration: <description>
-- Created: <ISO date>
-- Purpose: <what this migration does and why>

-- =============================================================================
-- UP
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.projects (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text NOT NULL,
  description text,
  user_id     uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  status      text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
  settings    jsonb DEFAULT '{}'::jsonb,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_name_user
  ON public.projects (user_id, lower(name));

-- Triggers
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.projects
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();

-- =============================================================================
-- ROLLBACK (run manually if needed)
-- =============================================================================
-- DROP TRIGGER IF EXISTS set_updated_at ON public.projects;
-- DROP INDEX IF EXISTS idx_projects_name_user;
-- DROP INDEX IF EXISTS idx_projects_user_id;
-- DROP TABLE IF EXISTS public.projects;
```

### Schema Documentation Template (for architecture.md)

```markdown
## Database Schema

### Entity Relationship Diagram

<ASCII diagram or link to generated diagram>

### Tables

#### projects
| Column | Type | Nullable | Default | Description |
|---|---|---|---|---|
| id | uuid | NO | gen_random_uuid() | Primary key |
| name | text | NO | — | Project name |
| user_id | uuid | NO | — | FK to auth.users |
| status | text | NO | 'active' | active, archived, deleted |
| created_at | timestamptz | NO | now() | — |
| updated_at | timestamptz | NO | now() | Auto-updated via trigger |

**RLS Policies:**
- SELECT: Owner only (`auth.uid() = user_id`)
- INSERT: Authenticated users (`auth.uid() = user_id`)
- UPDATE: Owner only
- DELETE: Owner only (soft delete preferred)

**Indexes:**
- `idx_projects_user_id` on (user_id)
- `idx_projects_name_user` unique on (user_id, lower(name))
```

---

## 4. Review / Rubric

### Schema Quality Checklist

| Criterion | Pass/Fail |
|---|---|
| All tables have `id uuid PRIMARY KEY DEFAULT gen_random_uuid()` | |
| All tables have `created_at` and `updated_at` with timestamptz | |
| All tables have `updated_at` trigger | |
| All foreign keys have corresponding indexes | |
| All tables have RLS enabled | |
| RLS policies follow least-privilege (deny by default) | |
| RLS policies cover all operations (SELECT, INSERT, UPDATE, DELETE) | |
| No table allows unrestricted public write access | |
| Migrations are numbered sequentially with descriptive names | |
| Migrations use `IF NOT EXISTS` / `IF EXISTS` for idempotency | |
| Migrations include rollback comments | |
| Seed data is idempotent (uses ON CONFLICT or WHERE NOT EXISTS) | |
| Seed data creates users with different roles for RLS testing | |
| Schema is documented in architecture.md | |
| Connection verified after setup (test query succeeds) | |
| No raw SQL injection vulnerabilities in stored procedures | |

### Common Mistakes to Avoid

- Forgetting to enable RLS on a new table (data is publicly accessible)
- Using `timestamp` instead of `timestamptz` (timezone bugs)
- Missing index on foreign key columns (slow JOINs)
- Overly permissive RLS policies (using `true` for write operations)
- Hardcoding user IDs in seed data that don't exist in auth.users
- Creating circular foreign key dependencies
- Using `SECURITY DEFINER` on functions without careful review (bypasses RLS)
- Mixing schema changes and data migrations in the same file

---

## 5. Skill Definition (Orchestration)

### Sub-Tasks

```yaml
tasks:
  - id: ss-01
    name: read-data-model
    action: "Read docs/architecture.md for entity definitions and relationships"
    output: "Entity list with attributes and relationships"

  - id: ss-02
    name: read-spec-requirements
    action: "Read spec for data requirements, auth needs, and access patterns"
    output: "Data requirements, auth requirements, query patterns"

  - id: ss-03
    name: read-existing-migrations
    action: "Read supabase/migrations/ to understand current schema state"
    output: "Current schema state, migration count"

  - id: ss-04
    name: design-schema
    action: "Design tables, columns, types, relationships, and indexes based on data model"
    depends_on: [ss-01, ss-02, ss-03]
    output: "Schema design document (tables, columns, types, constraints, indexes)"

  - id: ss-05
    name: create-initial-migration
    action: "Write the SQL migration file for table creation"
    depends_on: [ss-04]
    output: "supabase/migrations/<timestamp>_initial_schema.sql"

  - id: ss-06
    name: create-updated-at-function
    action: "Create the handle_updated_at() trigger function if it doesn't exist"
    depends_on: [ss-03]
    output: "Trigger function SQL (included in initial migration or separate)"

  - id: ss-07
    name: design-rls-policies
    action: "Design RLS policies per table based on auth requirements"
    depends_on: [ss-02, ss-04]
    output: "RLS policy design (table, operation, condition)"

  - id: ss-08
    name: create-rls-migration
    action: "Write the SQL migration file for RLS policies"
    depends_on: [ss-07]
    output: "supabase/migrations/<timestamp>_rls_policies.sql"

  - id: ss-09
    name: configure-auth
    action: "Design auth setup: profiles table, signup trigger, role management"
    depends_on: [ss-02, ss-04]
    output: "Auth configuration SQL"

  - id: ss-10
    name: create-auth-migration
    action: "Write the SQL migration file for auth setup"
    depends_on: [ss-09]
    output: "supabase/migrations/<timestamp>_auth_setup.sql"

  - id: ss-11
    name: create-seed-data
    action: "Write idempotent seed data for development and testing"
    depends_on: [ss-04, ss-07]
    output: "supabase/seed.sql"

  - id: ss-12
    name: apply-migrations-local
    action: "Run `supabase db reset` to apply all migrations to local database"
    depends_on: [ss-05, ss-08, ss-10, ss-11]
    output: "Migration application result (success/failure)"

  - id: ss-13
    name: verify-rls-policies
    action: "Test RLS policies with anon and authenticated roles"
    depends_on: [ss-12]
    output: "RLS verification results per table and role"

  - id: ss-14
    name: test-auth-flow
    action: "Verify auth trigger fires on user creation, profile is created"
    depends_on: [ss-12]
    output: "Auth flow test results"

  - id: ss-15
    name: document-schema
    action: "Add schema documentation section to docs/architecture.md"
    depends_on: [ss-04, ss-07]
    output: "Updated architecture.md with schema section"

  - id: ss-16
    name: verify-connection
    action: "Test database connection from the application (import Supabase client, run a query)"
    depends_on: [ss-12]
    output: "Connection verification result"
```

### Execution Flow

```
ss-01 (data model) ──┐
ss-02 (spec)       ──┤──> ss-04 (design schema) ──> ss-05 (schema migration)
ss-03 (existing)   ──┘         |                      |
                               |                 ss-06 (updated_at fn)
                               |
                          ss-07 (design RLS) ──> ss-08 (RLS migration)
                               |
                          ss-09 (auth config) ──> ss-10 (auth migration)
                               |
                          ss-11 (seed data)
                               |
                               v
                    ss-12 (apply migrations locally)
                         |         |         |
                    ss-13 (verify  ss-14    ss-16
                     RLS)      (test auth) (verify conn)
                         |
                    ss-15 (document schema)
```

---

## 6. HITL Build

### Agent Autonomy

The Supabase setup agent creates all migration files and seed data autonomously,
then applies them to the LOCAL Supabase instance only.

**Autonomous actions:**
- Read data model and spec requirements
- Design schema with tables, columns, types, relationships, indexes
- Write migration SQL files
- Design and write RLS policies
- Configure auth triggers
- Write seed data
- Apply migrations to LOCAL Supabase (`supabase db reset`)
- Verify RLS policies locally
- Test auth flow locally
- Document schema in architecture.md
- Verify application can connect

**Escalation triggers (agent stops and asks for help):**
- Complex multi-tenant requirements — tenant isolation strategy needs human decision
- Custom auth flows (SAML, custom JWT claims) — security implications require review
- Performance concerns with RLS — complex policies may impact query performance
- Existing production data — migrations must be carefully reviewed for data safety
- Cross-database dependencies — integration with external databases needs planning
- Compliance requirements (HIPAA, SOC2) — data handling rules need expert input
- Schema changes to tables with >100k rows — may need online migration strategy

### Safety Constraints

- The agent MUST NOT run `supabase db push` (remote deployment) without human approval
- The agent MUST NOT modify existing migration files (create new ones instead)
- The agent MUST NOT use `SECURITY DEFINER` on functions without documenting the reason
- The agent MUST NOT store sensitive data (passwords, API keys) in seed files
- The agent MUST NOT disable RLS on any table, even temporarily
- The agent MUST NOT grant superuser or service_role privileges in RLS policies
- The agent MUST include rollback comments in every migration

---

## 7. HITL Review

### Full Review Required

This skill requires **FULL human review** before applying to any remote environment.
Database schema changes are difficult to reverse in production.

### Review Presentation

The agent presents the following for human review:

**1. Schema diagram:**
```
auth.users
  |
  |-- 1:1 --> profiles (id = auth.users.id)
  |
  |-- 1:N --> projects (user_id)
                |
                |-- 1:N --> tasks (project_id)
                |
                |-- N:M --> team_members (project_id, user_id)
```

**2. RLS policy summary:**
```
| Table        | SELECT        | INSERT         | UPDATE        | DELETE        |
|-------------|---------------|----------------|---------------|---------------|
| profiles    | Own only      | Auto (trigger) | Own only      | None          |
| projects    | Owner + team  | Authenticated  | Owner only    | Owner only    |
| tasks       | Team members  | Team members   | Team members  | Project owner |
| team_members| Team members  | Project owner  | Project owner | Project owner |
```

**3. Migration file list:**
```
supabase/migrations/
  20260329000000_initial_schema.sql     (tables, indexes, triggers)
  20260329000001_rls_policies.sql       (all RLS policies)
  20260329000002_auth_setup.sql         (profiles, signup trigger)
supabase/seed.sql                       (dev seed data)
```

**4. Verification results:**
- Local migrations applied: PASS/FAIL
- RLS tests: PASS/FAIL per table
- Auth trigger: PASS/FAIL
- App connection: PASS/FAIL

### Approval Flow

```
Agent creates migrations + policies (local only)
  |
  v
Agent runs local verification (supabase db reset + tests)
  |
  v
Agent presents schema diagram + RLS summary + verification results
  |
  v
Human reviews
  |-- Requests changes --> Agent modifies migrations and re-tests locally
  |-- Approves
  v
Agent runs `supabase db push` to apply to remote
  |
  v
Agent verifies remote connection
  |
  v
Done
```

### Post-Approval Checklist

After human approves and remote deployment succeeds:

- [ ] Verify remote connection from deployed application
- [ ] Confirm RLS policies work on remote (test with real auth tokens)
- [ ] Update architecture.md with final schema documentation
- [ ] Notify team of schema changes (new tables, changed columns)
- [ ] If applicable, update TypeScript types (`supabase gen types typescript`)
- [ ] Archive any replaced migration strategies in git history
