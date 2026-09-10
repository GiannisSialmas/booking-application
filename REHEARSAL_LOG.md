# Rehearsal Log

This repo is a rehearsal. It will be deleted once the booking service (and
eventually catalog/discovery) reach a good stopping point, and a **new,
clean repo** will be built from scratch using this document as a step-by-step
playbook — same order of operations, same decisions, but with every mistake
and gap discovered here already fixed from the start instead of stumbled
into mid-issue.

Each section below is a phase of work. Within each: what we actually did,
the decisions worth keeping, and — where relevant — a **Lesson** callout for
anything the clean repo should just do correctly from step one.

This file gets updated as the rehearsal continues. Treat it as a build log,
not a finished spec.

---

## Phase 0 — GitHub repo setup

- Deleted all default repo labels. Create labels only when an actual need
  for one shows up, not preemptively.
- One milestone per service (`Code bookings microservice`,
  `Code catalog microservice`, `Code discovery microservice`) — everything
  for that service goes in it, regardless of how foundational or advanced
  the work is. **Reversed a bad idea, not kept:** for a while there was a
  second "advanced" milestone per service, split off from a "basic" one,
  meant to separate foundational work from scenarios discovered later
  (event cancellation cascade, refunds — see Phase 8). That split added
  organizational overhead without real benefit — a milestone's job is
  "everything needed to call this service done," not a complexity
  gradient. Skip the split entirely; one milestone per service from the
  start.
- Created a GitHub Project ("Code the application") as the board.
- `gh` needed extra OAuth scopes (`project`, `read:project`) beyond the
  default `repo` scope to manage Projects — granted via
  `gh auth refresh -s project,read:project`.

**Workflow conventions adopted (apply from the start in the clean repo):**
- Branch per issue (`issue-N-<slug>`), squash-merge PRs. Squash was a
  deliberate choice for a solo-dev repo: one clean commit per issue on
  `main`, no merge-commit noise, no need for perfectly atomic in-branch
  commits before merging.
- No `ref: <issue-link>` line in PR bodies — dropped once
  `addCloseIssueReferences` became the standard way to link a PR to its
  issue (see the "Linked pull requests" note below). `ref:` was a
  plain-text workaround for a real problem (get *some* visible link
  without triggering auto-close); once the real closing-reference
  connection is created directly via the mutation, a text line asserting
  the same thing in the body is just redundant upkeep — the Development
  panel and the project board's "Linked pull requests" field already show
  it, on both the issue and the PR. The issue now auto-closes on merge
  (the manual-close discipline this bullet originally described is
  retired in favor of that).
- PRs always get `--assignee @me`. Issues get assigned only once actually
  being worked (i.e. the moment they move to "In Progress"), never
  bulk-assigned across the whole backlog.
- Move an issue's board Status to **In Progress** the moment work starts
  on it. GitHub's default project workflows only auto-move things to
  *Done* (on close/merge); nothing moves them to In Progress
  automatically.
- **PRs do not get their own board item at all — don't turn on the
  "Pull request linked to issue" default project workflow, and don't
  manually add a PR to the board either.** This was tried both ways in
  this rehearsal: first enabled (PRs auto-added as separate rows), briefly
  disabled, then re-enabled — and only dropped for good once the "Linked
  pull requests" field (see below) reliably showed the same information
  on the issue's own row. A separate PR row just duplicates that. The
  issue is the single unit of tracking; its Status/assignee are what
  matter, and its "Linked pull requests" field shows the PR without
  needing a row of its own.
- Scope-creep discipline: when something surfaces mid-issue that doesn't
  belong to that issue's stated scope, defer it into its own tracked issue
  (right milestone, right board status) rather than solving it inline or
  letting it get lost. Happened repeatedly: Postgres wiring pulled out of
  issue #1 into #3; the CI/Alembic-conflict concern spun into its own
  deferred issue (#16); the event-cancellation and refund scenarios spun
  into their own issues (#17, #18) in the same bookings milestone, instead
  of being bolted onto existing issues.

> **Lesson:** GitHub's "assignee" field only accepts real accounts with
> repo access — there's no way to add an AI assistant as a literal
> assignee/co-author on an issue or PR. The closest real equivalents:
> `--assignee @me` for the human, plus a `Co-Authored-By:` git trailer and
> a body footer on PRs (issues get an equivalent footer note, since they
> have no git-trailer mechanism).

**"Linked pull requests" board field — how it's actually populated, and
the workflow adopted going forward.** GitHub Projects has a native
"Linked pull requests" field on issue rows. It is populated *only* by a
genuine closing-reference connection — the same relationship a closing
keyword (`Fixes #N`/`Closes #N`) creates. A plain cross-reference (what
`ref:` produces) does not populate it, confirmed via the GraphQL API.
Editing an **already-merged** PR's body to retroactively add a closing
keyword does **not** retroactively create it either — the *keyword* path
only works while a PR is still open.

There is, however, a working API path that *does* work retroactively:
the `addCloseIssueReferences` GraphQL mutation (missed on the first,
narrower search of the mutation list — it doesn't contain "link" or
"connect" in its name). It creates the exact same closing-reference
connection a text keyword would, just without needing the keyword visibly
in the PR description, and it works even on already-merged/closed pairs
(confirmed by backfilling it onto issues #1-#5 against their respective
already-merged PRs). There's a matching `removeCloseIssueReferences` to
undo it. No mutation exists for a *non-closing* link — GitHub's only two
paths to this connection are a closing keyword or this mutation, both are
"closing" by name and by behavior, and the only true non-closing option is
manually clicking "Link a pull request" in the issue's Development
sidebar in the browser (no API equivalent for that one).

**Decided workflow (adopt from the start in the clean repo):** run
`addCloseIssueReferences` on every PR at the same moment it's opened —
same category of routine manual step as setting Status/assignee to In
Progress, not a one-off. This means every issue effectively becomes
closing-keyword-linked from the start (accepting that the issue will
auto-close whenever its linked PR merges, same as a text keyword would),
rather than relying on `ref:` plus a separate manual `gh issue close`.
This field populating reliably is also *why* PRs stopped getting their
own board item (previous bullet) — once the issue's own row shows the
linked PR, a duplicate row for the PR adds nothing.

> **Bug found and repeatedly confirmed while testing this (5 times, once
> per backfilled issue #1-#5):** creating this connection — whether by
> editing a PR body to add/remove a keyword, or by calling
> `addCloseIssueReferences` directly — flips the issue's board Status back
> to "In Progress", **even when the issue is already `CLOSED` and stays
> `CLOSED`** (confirmed via direct GraphQL query each time, not a caching
> artifact). This looks like the "Pull request linked to issue" board
> workflow re-firing on any new closing-reference connection, regardless
> of the issue's real state. **Always re-check and fix Status back to
> Done immediately after linking a PR to an already-closed issue** —
> treat this as a guaranteed side effect of the mutation, not a maybe, and
> build it into the routine from day one rather than discovering it by
> accident.

**Every commit and PR should carry attribution from the very first one:**
a `Co-Authored-By: Claude <...>` trailer on every commit message, and a
"🤖 Generated with Claude Code" footer on every PR body. In this rehearsal
that convention wasn't adopted until partway through — the early merged
PRs (#13, #14, #15) have no trailer at all; only #19 onward does. That's a
gap in this repo's history, not a deliberate choice. Apply it from commit
one in the clean repo instead of letting it start late.

---

## Phase 1 — README and repo scaffolding

- `README.md`: leads with *why the repo exists* — explicitly a
  platform/DevOps/SRE portfolio project, explicitly **not** a production
  application, even though it's shaped like a real one. Then a brief
  per-service breakdown (purpose/language/database), then how project
  management works (issues/milestones/projects).
- Service folders: `services/{booking,catalog,discovery}` — **no
  `-service` suffix**. (We initially used the suffix, then dropped it —
  start without it.)
- Each service starts as a bare hello-world in its actual language/runtime
  before any real logic, specifically to prove out the toolchain
  (build/run scripts, package manager, base image) in isolation first.
- `.gitignore` covering all three ecosystems' build artifacts up front.
- Deferred on purpose, not scaffolded early: `observability/`,
  `load-tests/`, `terraform/`, `argocd/`, `docs/adr/`. Empty placeholder
  folders for tiers of work not yet reached just look stale — add each
  when its actual work starts.

> **Lesson:** we scaffolded `docs/adr/` early, then explicitly removed it
> ("too official for such a project"). Skip ADRs for this kind of project
> from the start.

> **Lesson (version hygiene):** don't trust a training-data-era default
> for "the latest version" of anything — check. We initially wrote
> TypeScript `^5.7.0` (actual current at the time: `7.0.2`, a native
> rewrite) and Go `1.23` in `go.mod` (actual current: `1.27`). Verify real
> current versions for every language/runtime/major dependency before
> writing them down, especially in a fast-moving ecosystem.

---

## Phase 2 — Dockerizing a service (booking, as the template for the others)

- Multi-stage `Dockerfile` using `uv`, following Astral's own documented
  Docker pattern: the **builder** stage is based on the plain
  `python:X-slim` image (not `uv`'s own bundled Python image) with just the
  static `uv` binary copied in from `ghcr.io/astral-sh/uv:latest`. This
  decouples "which Python base image" from "which uv version" — you keep
  whatever canonical Python image you'd otherwise trust, and layer in `uv`
  as an independent, tiny, cached binary.
- `RUN --mount=type=cache,target=/root/.cache/uv` persists uv's package
  cache across builds without baking it into the image.
  `--mount=type=bind` exposes `uv.lock`/`pyproject.toml` to that one `RUN`
  step only (not a permanent `COPY`), which scopes that layer's
  cache-invalidation to just those two files — editing application code
  afterward doesn't force a redundant dependency reinstall. Same idea as
  the classic Node "`COPY package*.json`, `npm install`, then `COPY` the
  rest" pattern.
- Runtime stage: separate slim image, non-root `appuser`, only the built
  `.venv` copied in from the builder — `uv` itself never ships in the
  final image.
- `[tool.uv] package = false` in `pyproject.toml` — the service is an app,
  not a distributable package, so it doesn't need a `[build-system]`
  section or setuptools at all.
- `infra/compose/docker-compose.yml` + `.env.example` (`.env` itself
  gitignored) for local dev.

> **Lesson (scope discipline):** the very first version of this Dockerfile
> issue also tried to wire up a Postgres service in the same compose file.
> That got pulled back out — "Dockerfile + compose for one service" and
> "wire up its database connection" are two different issues. Keep them
> separate from the start.

> **Lesson (Postgres 18+ breaking change):** the official Postgres image
> changed its data-directory convention in v18 — mount the volume at
> `/var/lib/postgresql` (the parent directory), **not**
> `/var/lib/postgresql/data` like older guides show. Using the old path
> fails outright on container start with an explicit error message
> pointing this out.

> **Lesson (check before reaching for a container workaround):** before
> assuming a CLI tool must be avoided on the host because of the
> Docker-first/no-install policy, check whether it's already installed
> (`which <tool>`). The policy is about not *installing* new things
> without asking, not about refusing to use what's already there — `uv`
> was already on the host, and using it directly was faster and simpler
> than fighting container image variants to get the same result.

---

## Phase 3 — App config and database connection

- `pydantic-settings` `Settings` class, `@lru_cache`-wrapped
  `get_settings()` — the standard FastAPI-recommended singleton pattern so
  env vars aren't re-parsed on every dependency injection.
- **The app's only DB configuration is a single `DATABASE_URL` connection
  string**, supplied via `.env` — not assembled from separate
  `POSTGRES_USER`/`PASSWORD`/`DB` values. Those separate values *do* still
  exist, but only as the Postgres container's own bootstrap requirement
  (the official image demands them to initialize itself) — they're fixed
  local-dev constants hardcoded directly in `docker-compose.yml`, not
  treated as application config, and kept in sync by hand with the
  connection string in `.env.example`.
- SQLAlchemy `engine` created once at import time in `app/core/database.py`,
  with `pool_size`/`max_overflow` set **explicitly** even though the
  values match SQLAlchemy's own defaults — purely so the concurrency
  ceiling (5 warm connections, up to 10 more under burst, hard ceiling of
  15) is visible in code instead of hidden in library defaults.
- `get_db_session()` — a generator-based FastAPI dependency yielding a
  `Session` from a `SessionFactory` (a `sessionmaker`), with cleanup in a
  `finally` block.
- `GET /health` actually exercises the DB (`SELECT 1` through the real
  dependency) — `200` if reachable, `503` with a body if not. Not just
  "the process is up."

> **Lesson (FastAPI response-model quirk):** a route return-type
> annotation that mixes types, e.g. `dict[str, str] | JSONResponse`,
> breaks FastAPI's automatic response-model inference and crashes the app
> at startup. Fix: `response_model=None` on the route decorator whenever a
> route intentionally returns more than one response shape.

> **Lesson (ORM-level hooks aren't DB triggers):** `onupdate=func.now()`
> only fires when SQLAlchemy itself generates the `UPDATE` — it's an
> ORM-level hook, not a database trigger. A raw SQL statement or anything
> outside the ORM bypasses it silently. Worth knowing if anything is ever
> expected to write to these tables outside the app itself.

---

## Phase 4 — Schema and migrations

Five tables: `users`, `seat_inventory`, `bookings`, `booking_items`,
`payments`. SQLAlchemy 2.0 typed `Mapped`/`mapped_column` style throughout,
one `Base` shared by every model (needed so `Base.metadata` sees every
table at once — required for both Alembic autogenerate and for creating
the schema at all).

**Decisions worth keeping as-is:**
- Integer primary keys everywhere, not UUIDs. UUIDs cost index bloat and
  random insert order for tables that are purely internal; they'd only be
  justified for identifiers that cross a service/event boundary or get
  exposed publicly — neither applies to any of these five tables yet.
- `seat_inventory.event_id` is a plain indexed string, **not** a local
  foreign key — events belong to the Catalog service's own database, and a
  booking-service table can't have a real FK into another service's DB
  without coupling them at the data layer.
- `booking_items.price_cents` is a **snapshot** of what was actually
  charged, independent of `seat_inventory.price_cents` (the seat's
  *current* listed price, which can legitimately change over time). Needed
  for historical accuracy — if a cancelled seat gets resold to someone else
  at a different price, the original customer's record must still show
  what *they* paid.
- Deliberately **no unique constraint** on `booking_items.seat_inventory_id`
  — that would permanently block reselling a seat after its booking is
  cancelled. Double-booking prevention belongs in application-level
  concurrency control (an atomic conditional update at hold time), not a
  static schema constraint.
- `email: String(320)` — not an arbitrary number, it's RFC 5321's actual
  maximum email length (64-char local part + `@` + 255-char domain).
- Every model has a class docstring explaining its *business* role in
  plain language (not just field comments) — makes "why does this table
  exist" legible without needing external context.
- Alembic's `env.py` pulls `sqlalchemy.url` from the same
  `Settings`/`DATABASE_URL` the app itself uses, rather than a separately
  configured value in `alembic.ini` — one source of DB config, not two.
- `docker-entrypoint.sh` runs `alembic upgrade head` before `exec`-ing into
  uvicorn — migrations apply automatically on every container start.

> **Lesson (the `created_at`/`updated_at` rule):** apply timestamps by an
> actual rule, not ad hoc: `created_at` on every table, `updated_at` only
> on tables whose rows mutate after insert. We initially missed
> `updated_at` on `seat_inventory`, `payments`, and `users` — worth getting
> right the first time, since `seat_inventory` in particular is the *most*
> frequently mutated table in the whole schema (the hold/release/sold
> lifecycle) and not having an update timestamp there specifically hurts
> debugging concurrency issues later.

> **Lesson (native enum tradeoff):** SQLAlchemy's `Enum` type creates a
> real Postgres `ENUM` type. That's fine for a small number of stable
> values, but evolving it later is rigid — adding a value needs
> `ALTER TYPE ... ADD VALUE`, and there's no supported way to remove one
> without recreating the type. Go in aware of that tradeoff rather than
> assuming enum columns are cheap to change.

> **Big lesson — don't store a status value that's derivable from another
> column.** We originally modeled seat state as a 3-value enum
> (`available`/`held`/`sold`) plus `hold_expires_at`. `held` turned out to
> be fully redundant: it's just `status='available' AND hold_expires_at >=
> now()`, computed at query time. Collapsed to 2 values
> (`available`/`sold`). This isn't just a tidiness fix — it fixes a real
> correctness bug: storing `held` made seat availability depend on some
> sweep job eventually writing `status` back to `available` when a hold
> expired. If that job ever ran late (e.g. under exactly the load spikes
> this whole project exists to demonstrate handling), it would wrongly
> block a new hold on a seat that had already, logically, become
> available again. The fix belongs in the **acquisition query itself**:
> treat "held but past its expiry" as acquirable in the same atomic
> `UPDATE`, so a delayed sweep job is never a correctness dependency —
> only needed for side effects (marking the parent booking expired,
> emitting an event).

> **Lesson (inconsistent default enforcement, not yet fixed):**
> `created_at`/`updated_at` use a DB-side `server_default=func.now()`
> (safe regardless of what writes the row), but the status enum columns
> use a Python-side `default=...` (only applied when inserting through the
> ORM). A raw-SQL insert bypassing the ORM would hit a `NOT NULL`
> violation instead of getting a sensible default. Fix in the clean repo:
> use `server_default=` with an explicit SQL value for anything that needs
> to be safe regardless of what writes the row.

> **Lesson (generating migrations without touching production):**
> `alembic revision --autogenerate` diffs your models against *whatever
> database you point it at* — it never needs to be production. A fresh
> local Postgres brought to `head` is schema-identical to production
> (schema is fully determined by which migrations have run, not by which
> physical instance you're connected to). Production itself should only
> ever be migrated by an automated deploy pipeline, never manually by a
> developer with direct prod credentials.

> **Lesson (migration ordering and parallel-branch conflicts):** Alembic
> orders migrations purely by each file's own `revision`/`down_revision`
> pointers (a linked list/DAG) — never by filename, timestamp, or the
> "Create Date" comment. Two developers branching off the same head and
> each generating a migration creates two files pointing at the same
> parent; git merges both silently (different filenames, no textual
> conflict), and the fork only surfaces later as an Alembic "multiple
> heads" error, whenever someone next actually runs a migration. Deferred
> to its own tracked issue (#16) rather than solved immediately: a CI
> check failing the build on `alembic heads` reporting more than one
> revision, plus a broader "migration drift" check (fresh DB → `upgrade
> head` → `autogenerate` again → assert no diff). Still to investigate:
> how this interacts with GitHub merge queues.

> **Lesson (unshared migrations can be edited in place):** while a
> migration hasn't been merged/shared yet, it's fine (and preferable) to
> delete and regenerate it in place when the underlying models change,
> rather than stacking a second migration file for a change nobody else
> has built on top of.

---

## Phase 5 — Seed data

`scripts/seed.py` (a sibling of `app/`, not inside it — see the note on
directory layout below) seeds one sample event's seat map and one sample
user, idempotently (checked by natural key — `email` for the user,
`event_id` for the seats — safe to run repeatedly). Deliberately **not**
wired into `docker-entrypoint.sh` alongside migrations: seeding fake data
has no place auto-running on every container start beyond local dev,
unlike schema migrations which are needed in every environment.

> **The lesson this whole document exists to capture an example of:** the
> seed script's issue was scoped and titled around seeding a seat map —
> so that's all it did at first. The very next issue (implementing the
> hold endpoint) immediately needed a `User` row to satisfy a foreign key,
> and *nothing* in the original plan created one — there was no
> user-registration endpoint, no auth system, nothing. This was only
> caught because we hit the wall while building the next feature.
>
> **Do this instead in the clean repo:** when writing the seed
> script/step, provision every foreign-key dependency that *any* upcoming
> issue in the milestone will need, not just what the current issue's
> title literally says. Read ahead through the milestone's issue list
> before deciding the seed script's scope.

---

## Phase 6 — Directory layout principle

Established across `alembic/`, `scripts/`, and `tests/`: **`app/` contains
only the actual running application — nothing else.** Migrations tooling,
one-off scripts, and tests are all separate concerns and live as siblings
to `app/`, not nested inside it. `scripts/` originally started as
`app/seed.py` and was corrected once this principle was made explicit —
apply it from the start for every future tooling/test directory.

---

## Phase 7 — First real endpoint: `POST /bookings/hold`

- Request: `{user_id, seat_ids: [...]}`. Rejects duplicate seat IDs at
  validation time (Pydantic `field_validator`).
- **A single atomic bulk `UPDATE ... RETURNING`** acquires every requested
  seat in one statement:
  `WHERE id IN (...) AND status='available' AND (hold_expires_at IS NULL
  OR hold_expires_at < now())`. This is the SeatStatus lesson from Phase 4
  showing up directly in the query.
- **All-or-nothing**: if any requested seat isn't acquired, roll back the
  whole transaction and return `409` naming exactly which seat(s) failed —
  verified live that a mix of one available + one already-held seat leaves
  the available one completely untouched, not partially held.
- Extra guard: reject a hold spanning seats from more than one event.
- `Booking`/`BookingItem` rows are only created *after* every seat is
  confirmed acquired, with price snapshotted from the seat at that moment
  (ties back to the `price_cents` snapshot decision in Phase 4).
- `HOLD_DURATION_MINUTES` is a 12-factor env var on `Settings`, not
  hardcoded.

**A design gap surfaced and resolved before writing this endpoint:** no
user existed anywhere in the system yet (see Phase 5's lesson). Considered
two fixes: (1) accept an email and get-or-create a user inline in the hold
request, or (2) require an existing `user_id` and patch the seed script to
provision one. Went with (2) — keeps the hold endpoint's own scope
narrower, and the seed-script lesson above meant the real fix belonged
there anyway.

> **Correctness requirement identified for the *next* issue (confirm),
> not yet implemented as of this writing:** a hold can legitimately expire
> while the customer is on the payment provider's page (e.g. mid-Stripe-
> checkout). The confirm endpoint must **re-verify the hold is still valid
> for this specific booking** before trusting a successful payment
> callback — never treat "the payment provider said yes" as sufficient on
> its own. If the hold has lapsed (possibly to someone else already), the
> correct handling is to refund immediately and refuse to confirm, not to
> silently confirm a seat that may no longer be available. This is the
> "overselling under partial failure" scenario from the original design
> doc, and it's central to the whole reason this service exists — not an
> edge case to bolt on later. (Already written into the actual issue's
> description, not just this log.)

---

## Phase 8 — Scenarios discovered but deliberately deferred

While reasoning through the full booking lifecycle (hold → confirm →
cancel → expire), several real scenarios surfaced that clearly weren't
part of any issue already planned. Rather than solving them inline or
letting them get lost, each was written up and tracked as its own issue,
in the same bookings milestone as everything else (no separate
"basic"/"advanced" split — see the Phase 0 note on why that split was
tried and then reversed):

- **Organizer cancels an entire event** — a saga/cross-cutting operation
  across every booking tied to that event (refund, release seats, notify),
  triggered by an async event from the Catalog service, not a direct API
  call. Depends on the event bus (Kafka/NATS) existing, which it doesn't
  yet. → issue #17.
- **Refunds for already-confirmed bookings** — needs a
  `Payment.status -> REFUNDED` transition, a decision on the resulting
  `Booking` status, and a business decision on whether the seat goes back
  on sale (schema already supports the `REFUNDED` status value; no
  endpoint exists). → issue #18.
- **CI check for conflicting/multiple-head Alembic migrations** — see the
  migration-ordering lesson in Phase 4. → issue #16, no milestone (it's
  platform/CI work, not a booking-service scenario), added to the board so
  it isn't forgotten.

**Also decided, not yet implemented:** the original architecture doc's
justification for the Catalog service using MongoDB (polymorphic event
metadata across categories) doesn't actually require a separate database
technology — Postgres `JSONB` solves the same "no sparse null columns"
problem without the operational cost of running a second stateful
technology. Reconsidered in favor of two use cases chosen because they're
genuinely idiomatic Mongo fits rather than merely defensible ones:
1. **Venue seating-chart layout documents** — genuinely heterogeneous
   structure per section type (a "general admission" section is just a
   polygon + capacity, a "seated" section has rows/seats) and per shape
   kind (rect/arc/polygon each need different fields); the whole document
   is the natural unit of read/write (a seat-map UI fetches and renders it
   whole, never a fragment). Only shares a seat *label* back to Booking's
   `seat_inventory` — geometry and business/inventory state stay cleanly
   separated.
2. **Event reviews/ratings with threaded replies** — a common, legitimate
   real-world Mongo use case (naturally nested documents, no relational
   joins needed beyond "which event/user").

Core catalog data (events, venues, organizers, pricing tiers) goes back to
being relational — only these two things get Mongo collections when
Catalog work actually starts.

---

## Phase 9 — Testing

Decided to write tests **in parallel with each feature**, not deferred
entirely to one big "add a test suite" issue at the end (which is how the
original milestone had it scoped).

- Tests hit a **real** Postgres, never mocks — the whole point of the
  concurrency-critical logic (atomic seat acquisition) is meaningless
  against a mocked DB layer.
- Test isolation uses SQLAlchemy's SAVEPOINT-based "join a session to an
  external transaction" pattern
  (`Session(bind=connection, join_transaction_mode="create_savepoint")`).
  This is specifically necessary because the endpoint under test calls
  `db.commit()` itself — a naive "wrap the test in a transaction and roll
  back at the end" approach breaks the moment the code being tested
  commits. Verified by querying every table after the full suite ran: zero
  rows left behind, despite the tests exercising a real commit path.
- `pytest`/`httpx` live in a `dev` dependency group
  (`uv add --dev ...`), excluded from the production image
  (`uv sync --locked --no-dev` already does this). `tests/` is a sibling
  of `app/`, same principle as Phase 6.
- Run via `uv run pytest` on the host, pointed at the docker-compose
  Postgres's exposed port — same pattern already used for authoring
  Alembic migrations, rather than building dedicated Docker test-runner
  infrastructure before CI exists.

> **Lesson (don't run tests as a `docker build` step):** a `RUN pytest`
> layer executes in an isolated build sandbox with no access to sibling
> containers, so it can't reach a real Postgres the way `docker compose`
> can — and even for DB-less tests, baking test execution into the image
> build conflates "package an artifact" with "run CI," forces test-only
> dependencies into the build graph, and makes structured test output
> awkward to retrieve. The original design doc's own phrasing already had
> this right: "lint → **test** → build → scan → push" — test is its own
> pipeline step, before the image gets built, with the database provided
> as a real service container (GitHub Actions supports this natively).

**Open, not chased down:** a `StarletteDeprecationWarning` appeared
(`Using httpx with starlette.testclient is deprecated; install httpx2
instead`) — tests pass fine either way, but this reflects an ecosystem
change after this project's working knowledge. Worth resolving properly
in the clean repo rather than carrying the warning forward.

---

## Open items as of this writing

- Issue #7 (`confirm`) not yet implemented — carries the hold-revalidation
  requirement from Phase 7.
- Issues #8-#12 (cancel, get-bookings, hold-expiry sweep job, concurrency
  test, remaining test coverage) not yet started.
- CI pipeline doesn't exist yet (blocks issue #16's actual fix).
- Catalog and Discovery services are still hello-world only.
- The `httpx2` deprecation warning from Phase 9.
