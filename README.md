# pd-launchpad

Standardized project template for Product Direction's autonomous developer agent system. Clone this template when creating a new product repo — agents, skills, rules, commands, CI/CD, and Supabase coordination are pre-configured.

## Prerequisites

- Node.js 20+
- Supabase CLI (`npm install -g supabase`)
- Claude Code CLI
- Vercel CLI (`npm install -g vercel`)

## Bootstrap a New Project

The fastest way to create a new project from this template:

```bash
python scripts/bootstrap_project.py \
  --name "my-product" \
  --description "What this product does" \
  --dest "../my-product"
```

This will:
1. Copy all template files (excluding `node_modules/`, `.git/`, `package-lock.json`)
2. Replace all placeholders (`[PROJECT_NAME]`, `[PROJECT_DESCRIPTION]`, `[project-name]`)
3. Generate `.env` with Supabase credentials (from PD-OS config)
4. Register the project in Supabase `repos` table
5. `git init` + initial commit
6. `npm install`

Options: `--skip-npm`, `--skip-supabase`

## Manual Setup

If you prefer to set up manually:

```bash
# 1. Clone the template
git clone https://github.com/ignaciobassino/pd-launchpad.git my-project
cd my-project
rm -rf .git && git init

# 2. Replace placeholders (see table below)
# Search and replace all [PLACEHOLDER] values in CLAUDE.md and docs/

# 3. Configure environment
# Create .env with SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY

# 4. Install dependencies
npm install

# 5. Start development
npm run dev
```

## Placeholder Replacement

| Placeholder | Where | Replace With |
|-------------|-------|-------------|
| `[PROJECT_NAME]` | CLAUDE.md, docs/*.md, package.json | Your project name (kebab-case) |
| `[PROJECT_DESCRIPTION]` | CLAUDE.md | One-line project description |

## Agent System

This template includes a 4-agent development system:

| Agent | Role | Model |
|-------|------|-------|
| **architect** | Stack decisions, architecture, ADRs | opus |
| **developer** | TDD implementation (primary workhorse) | sonnet |
| **reviewer** | Two-stage code review (read-only) | sonnet |
| **qa** | Test execution, acceptance validation | sonnet |

Agents are coordinated via Supabase `work_items` and triggered by specs from PD-OS.

## File Structure

```
├── CLAUDE.md                      # Project constitution
├── .claude/
│   ├── agents/                    # 4 agent definitions
│   ├── skills/                    # 7 production-ready skills
│   ├── commands/                  # 4 slash commands (/review, /qa, /ship, /status)
│   └── rules/                     # 4 behavioral rules (always active)
├── docs/
│   ├── specs/                     # PM specs land here (from PD-OS)
│   ├── architecture.md            # Filled by architect agent
│   ├── plan.md                    # Filled by plan-from-spec skill
│   └── delivery-reports/          # Task completion reports
├── src/                           # Application code
├── tests/
│   ├── unit/                      # Vitest tests
│   └── e2e/                       # Playwright tests
├── .github/workflows/             # CI + preview deploy
├── scripts/
│   └── supabase_client.py         # Work item CRUD
├── package.json                   # Base dependencies
└── tsconfig.json                  # TypeScript strict mode
```

## Commands

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start Next.js dev server |
| `npm run test` | Run all tests |
| `npm run test:unit` | Run unit tests (Vitest) |
| `npm run test:e2e` | Run e2e tests (Playwright) |
| `npm run lint` | Lint code |
| `npm run type-check` | TypeScript type checking |
| `/review` | Two-stage code review |
| `/qa` | Full test suite |
| `/ship` | Production deploy (human gates) |
| `/status` | Show Supabase work items |
