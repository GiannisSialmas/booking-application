# Event Ticketing Platform

## Why This Repo Exists

This repository implements an event ticketing platform — the kind of system that sells seats to concerts, conferences, sports matches, and theater shows. **It is not a production application.** No real events, seats, or payments are ever processed here.

The application exists purely as a vehicle to practice and showcase **platform engineering, DevOps, and SRE skills**: containerization, CI/CD, GitOps, observability, autoscaling, chaos engineering, and load testing. The domain was chosen because it produces a genuinely interesting engineering problem — preventing a seat from being sold twice under concurrent, high-traffic load — and because it naturally justifies a polyglot, multi-database, event-driven architecture instead of forcing one artificially. Everything about the business domain (bookings, catalog, search) is a means to that end, not the goal itself.

If you're browsing this repo, read it as a platform/infrastructure portfolio project wearing an e-commerce-shaped application as a costume.

## Services

The system is split into three independent microservices, each paired with the language and database that best fits its responsibility:

- **Booking Service** — owns seat inventory, reservations, and payments. Responsible for the core "never sell the same seat twice" guarantee under concurrent load.
  **Language:** Python · **Database:** PostgreSQL

- **Catalog Service** — owns event, venue, and organizer data (concerts, conferences, sports, theater), each with its own varying metadata shape.
  **Language:** Node.js / TypeScript · **Database:** MongoDB

- **Discovery/Search Service** — provides full-text search, filtering, and browsing over events, enriched with live availability data.
  **Language:** Go · **Database:** Elasticsearch

See [docs/architecture.md](docs/architecture.md) for the full design, data flow, and the platform/SRE roadmap.

## Project Management

Work on this project is tracked entirely through GitHub's native project management tools:

- **Issues** — individual units of work (features, bugs, tasks).
- **Milestones** — group issues around a concrete deliverable (e.g. shipping the first working version of a service).
- **Projects** — a board that gives a cross-cutting view of progress across issues and milestones.

There are no external trackers — the GitHub repo is the single source of truth for what's being worked on and why.
