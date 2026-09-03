# Event Ticketing Platform — Design Doc

A portfolio project demonstrating DevOps / Platform Engineering / SRE skills through a polyglot microservices system: **Python + Postgres**, **Node/TypeScript + MongoDB**, and **Go + Elasticsearch**.

---

## 1. Concept

An event ticketing platform (concerts, conferences, sports, theater). The domain naturally justifies each language/database pairing instead of forcing them:

- **Transactional correctness** (seats, payments) → Postgres
- **Flexible, heterogeneous metadata** (event types) → MongoDB
- **Fast full-text/faceted search** (discovery) → Elasticsearch

### The core design tension

The one hard problem that drives the whole system: **you cannot sell the same seat twice**, even under concurrent load or a flash-sale traffic spike. This is the headline SRE story of the project — search and discovery are comparatively low-stakes; booking correctness under load is not. Keep this front and center — it justifies later platform-layer choices (locking strategy, queueing, rate limiting).

---

## 2. Service Breakdown

### 2.1 Booking Service — Python + Postgres

**Owns:** bookings, seat/inventory state, payments, order status

Responsibilities:
- Seat map & inventory per event (available / held / sold)
- Reservation flow: hold a seat for N minutes during checkout → confirm or release
- Payment processing (mock provider or Stripe test mode)
- Booking history per user

**Why Postgres fits:** requires row-level locking or `SELECT ... FOR UPDATE` / optimistic concurrency to prevent double-booking. This is the natural place to demonstrate transaction isolation levels and write a "how I prevented double-booking under concurrent load" doc backed by a load test.

**Key entities:** `users`, `bookings`, `booking_items` (seat + price), `payments`, `seat_inventory`

**Suggested API:**
- `POST /bookings/hold` — reserve seats temporarily
- `POST /bookings/{id}/confirm` — pay & confirm
- `DELETE /bookings/{id}` — cancel/release
- `GET /users/{id}/bookings`

---

### 2.2 Event Catalog Service — Node/TypeScript + MongoDB

**Owns:** event details, venues, artists/organizers, seat map structure, pricing tiers

**Why Mongo fits:** a concert, conference, sports match, and theater play have very different metadata shapes — line-ups, speaker lists, team rosters, seating chart shapes, age restrictions, custom fields per category. Modeling this relationally means sparse tables full of nulls; a document per event type is the natural fit.

**Key entities:** `events` (polymorphic by category), `venues`, `organizers`, `pricing_tiers`

This service is the source of truth for what events exist, and publishes change events (`event.created`, `event.updated`, `event.cancelled`) to the message bus.

**Suggested API:**
- `POST /events`, `PATCH /events/{id}`, `DELETE /events/{id}`
- `GET /events/{id}`
- `POST /venues`

---

### 2.3 Discovery/Search Service — Go + Elasticsearch

**Owns:** nothing authoritative — a read-optimized projection of Catalog + live availability from Booking

Responsibilities:
- Full-text search (e.g. "Taylor Swift Athens")
- Faceted filters (category, city, date range, price range)
- Geo search ("concerts within 20km")
- Autocomplete/typeahead
- Trending/popular events

**Why Go fits:** this endpoint absorbs far more read traffic than booking during a big on-sale moment — a good place to demonstrate handling high fan-in read load with low latency, and to use goroutines for concurrent enrichment (merging ES results with live "tickets remaining" data).

**Suggested API:**
- `GET /search?q=&city=&category=&date_from=&date_to=`
- `GET /events/{id}/availability` (proxied/cached from Booking via event stream)
- `GET /trending`

---

## 3. Data Flow / Event Architecture

This is where the project demonstrates event-driven architecture instead of three REST APIs sitting side by side.

```
Catalog Service (Node)          Booking Service (Python)         Search Service (Go)
  |  publishes                      |  publishes                     |
  |  event.created                  |  seat.reserved                 |
  |  event.updated                  |  seat.released                 |
  |  event.cancelled                |  seat.sold                     |
  v                                 v                                 |
              ---------------  Kafka / NATS  ---------------
                                    |
                                    v
                    Search Service consumes all of the above
                    and updates its Elasticsearch index
                    (denormalized: event info + live availability)
```

Concrete examples:
- Event created in Catalog → `event.created` → Search indexes it.
- User reserves 2 seats in Booking → `seat.reserved` → Search updates "tickets remaining: 148" near-real-time.
- Hold expires unpaid → Booking publishes `seat.released` → Search increments availability back.

This gives a legitimate **eventual consistency** story worth documenting: "search availability can lag actual availability by X ms — here's how I measured and bounded that lag."

It's also a natural **CQRS** example: Booking is the write model (strong consistency), Search is the read model (eventually consistent, optimized for query patterns) — a real, defensible architecture pattern rather than a decorative buzzword.

---

## 4. Interesting Edge Cases to Build (strong interview talking points)

- **Flash sale / thundering herd** — popular event goes on sale at noon, 10k people hit "buy" in the same second for 500 seats. Solutions to explore: queueing, rate limiting, a waiting-room pattern (à la real-world Ticketmaster).
- **Seat hold expiry** — reserved-but-unpaid seats must release after N minutes. Good place to show a scheduled job or Redis TTL key pattern.
- **Overselling protection under partial failure** — payment succeeds but the confirmation event never reaches Search. Explore outbox pattern, retries, idempotency keys.
- **Cancellation ripple** — organizer cancels an event → bookings refunded, Search de-indexed, users notified. Good saga/orchestration example.

---

## 5. Optional Fourth Piece (stretch goal, not core scope)

A lightweight **Notification service** (email/SMS on booking confirmation, event reminders) would plug naturally into the existing event bus as one more async consumer. Not required for the core showcase.

---

## 6. Platform & SRE Layer (build after the services exist)

### Tier 1 — Foundation (must-have)
- Dockerfiles (multi-stage builds) for all 3 services
- docker-compose for local dev (3 services + 3 DBs + reverse proxy)
- Kubernetes manifests or Helm charts per service, with resource requests/limits and liveness/readiness probes
- CI pipeline (GitHub Actions): lint → test → build → scan → push image
- README with an architecture diagram

### Tier 2 — Platform Engineering
- GitOps deployment via ArgoCD or Flux
- Helm chart templating with per-environment values (dev/staging/prod)
- Ingress/API gateway (nginx-ingress, Kong, or Envoy) in front of the 3 services
- Async communication via Kafka or NATS (the event flow described in Section 3)
- Secrets management (Sealed Secrets or External Secrets Operator + Vault)
- Terraform to provision infra (EKS/GKE, managed Postgres/Mongo Atlas, VPC, IAM) — or a local kind/k3d cluster if avoiding cloud cost

### Tier 3 — SRE Showcase (the differentiator)
- Full observability stack: Prometheus + Grafana (metrics), Loki (logs), Tempo/Jaeger (traces), instrumented via **OpenTelemetry across all 3 languages**
- Defined SLOs/SLIs per service (e.g. "search API p99 < 200ms, 99.9% availability") with error-budget burn-rate alerts in Alertmanager
- Runbooks + ADRs (Architecture Decision Records) in the repo
- Chaos engineering experiments (Chaos Mesh/Litmus) — kill a pod, inject latency into the ES call, demonstrate graceful degradation (circuit breakers, retries, timeouts)
- Load testing with k6 — results checked into the repo and tied to the SLOs (great fit for the flash-sale edge case above)
- Autoscaling: HPA on custom metrics (e.g. scale search on request latency, not just CPU), or KEDA scaling on Kafka lag
- A game-day / postmortem doc simulating an incident (e.g. "Elasticsearch cluster went yellow during a flash sale — timeline, root cause, remediation")

### Tier 4 — Extra Polish (nice-to-have)
- Security scanning (Trivy for images, Semgrep for SAST, Dependabot/Renovate for deps)
- Policy-as-code with OPA/Gatekeeper (e.g. block deploys without resource limits)
- Canary or blue-green deploys via Argo Rollouts, with automated rollback on SLO violation
- Cost breakdown doc if deployed to real cloud infra

---

## 7. Suggested Repo Structure

```
/services
  /booking-service     (Python/FastAPI + Postgres)
  /catalog-service      (Node/TS + Mongo)
  /search-service        (Go + Elasticsearch)
/infra
  /terraform
  /k8s (or /helm)
  /argocd
/observability
  /grafana-dashboards
  /prometheus-rules
/docs
  /adr
  /runbooks
  architecture.md
/load-tests (k6 scripts)
```

---

## 8. What Makes This Land Well on GitHub
- Clean architecture diagram at the top of the README
- GitHub Actions badges showing green builds
- Actual Grafana dashboard screenshots or a short demo GIF
- ADRs explaining *why* (e.g. Kafka over RabbitMQ, Helm over raw manifests) — signals judgment, not just tool familiarity
- A chaos-experiment writeup — rare in portfolios, strong SRE signal

---

