# agent-memory Roadmap and Follow-up Work

> Strategic roadmap based on repository audit on 2026-05-14.
> Repository: `/home/zhangtao/projects/agent-memory`
> Project goal: deliver a local-first, zero-external-API-cost memory service for AI agents with MCP + REST access.

## 1. Current-state summary

### 1.1 Confirmed strengths

From `README.md`, recent commits, and source inspection, the project already has a strong v0.1 foundation:

- Local-first positioning is clear: Redis-backed memory service with no vector DB requirement for v1.
- Dual protocol direction is in place:
  - REST layer in `src/memory_mcp/protocol/rest.py`
  - MCP layer in `src/memory_mcp/protocol/mcp.py`
- Core memory architecture exists:
  - models in `src/memory_mcp/models.py`
  - engine in `src/memory_mcp/engine/`
  - Redis/index storage in `src/memory_mcp/storage/`
- Admin surface already exists:
  - auth, API key store, logger, and routes under `src/memory_mcp/admin/`
- ACL groundwork exists in `src/memory_mcp/auth/acl.py`
- Test suite has meaningful breadth:
  - 20 `test_*.py` files under `tests/`
- Recent development focus has been substantial and coherent:
  - `feat: Integrate admin panel and change default port to 5678`
  - `feat: complete admin panel management workflows`
  - doc polish and frontend optimization have already started

### 1.2 Current gaps observed during audit

The main follow-up work is not “start from zero”; it is “turn a promising alpha into an installable, verifiable, open-source-ready product.”

Observed gaps:

1. **Verification/developer ergonomics gap**
   - Running `pytest -q` in the repo currently fails at collection because `memory_mcp` is not importable from a bare checkout.
   - Running `PYTHONPATH=src pytest -q` progresses further but still fails because dependency `redis` is not installed in the current environment.
   - This means “fresh clone → run tests” is not yet smooth enough.

2. **Protocol consistency gap**
   - REST and MCP both exist, but they need stronger schema parity, shared validation rules, and behavior consistency.
   - Some fields visible in response models and README examples should be checked for end-to-end parity across save/get/update/search flows.

3. **Isolation/security model gap**
   - ACL groundwork exists, but the product story around namespace isolation, shared space, API-key scoping, and cross-agent access rules likely needs formalization.

4. **Packaging/onboarding gap**
   - The project has `pyproject.toml`, but the out-of-box contributor/developer experience still needs hardening.
   - There are only two markdown docs right now: `README.md` and `CONTRIBUTING.md`.
   - Missing docs include architecture, deployment, permissions, and examples.

5. **Operations/production-readiness gap**
   - There is a health endpoint and admin logging, but rollout guidance, backup strategy, monitoring shape, and failure handling are not yet documented as a complete operator story.

## 2. Completed / partial / missing scope

### 2.1 Completed enough to build on

- Core project identity and positioning
- Redis-backed persistence foundation
- REST endpoint baseline
- MCP tool baseline
- Admin panel baseline
- API key mechanism baseline
- ACL prototype/foundation
- Test suite skeleton and broad coverage areas
- Packaging metadata in `pyproject.toml`

### 2.2 Partially complete

- REST/MCP contract completeness
- Multi-agent isolation semantics
- Admin observability and operational workflows
- Local development quick-start reliability
- Documentation depth
- Release engineering

### 2.3 Missing or not yet made production-grade

- One-command dev bootstrap with verified test path
- Explicit compatibility/support matrix
- Deployment guide for Docker/local/NAS
- Formal permission model documentation
- Backup/restore/export/import workflow definition
- CI quality gates
- Release checklist and changelog process
- Example client integrations for real agent frameworks

## 3. Roadmap principles

The next phase should optimize for:

1. **Usability before novelty** — make the current feature set easy to install, test, and trust.
2. **Protocol parity before expansion** — keep REST and MCP behavior aligned before adding more feature surface.
3. **Isolation clarity before advanced memory intelligence** — define what an agent is allowed to read/write before adding merge/semantic features.
4. **Open-source adoption before ambitious platform features** — examples, docs, CI, packaging, and demos will create more real value than a flashy but under-documented advanced feature.

## 4. Recommended milestone plan

## M1 — Developer Experience + Minimum Reliable Product

**Goal:** A fresh contributor can install, run, and verify the project without guessing.

### Scope

- Fix test bootstrap and import ergonomics
- Ensure dependencies for local development are correctly declared and documented
- Verify local run paths for:
  - editable install
  - direct `uvicorn` launch
  - console script launch
- Tighten quick-start commands in README
- Add a minimal architecture document

### Concrete tasks

- Make `pytest` work from a fresh clone via one of these approaches:
  - editable install (`pip install -e .[dev]` / `.[all]`)
  - or `pythonpath` configuration in pytest/project config
- Add explicit local-dev setup section to docs:
  - create venv
  - install extras
  - run tests
  - run server
- Add `docs/architecture.md`
- Add `docs/development.md`
- Verify README examples against actual endpoints and payloads

### Acceptance criteria

- Fresh setup instructions are documented and reproducible
- `pytest` runs successfully in the intended setup path
- A user can start the service locally and hit `/api/v1/health`
- README commands are all copy-paste safe

### Why first

Without this milestone, every later feature is harder to validate and harder for outsiders to adopt.

---

## M2 — Protocol Parity + Contract Hardening

**Goal:** REST and MCP expose a coherent, stable memory contract.

### Scope

- Align request/response schemas between REST and MCP
- Standardize error behavior
- Validate optional metadata fields consistently
- Ensure list/search/update semantics match across protocols

### Concrete tasks

- Create a contract checklist covering:
  - save
  - get
  - update
  - delete
  - list
  - search
  - stats
  - health
- Decide which fields are officially supported in v0.1:
  - `content`
  - `tags`
  - `agent`
  - `confidence`
  - `source`
  - `links`
  - `metadata`
  - timestamps/version fields
- Add shared normalization/validation logic if REST and MCP currently diverge
- Add protocol parity tests:
  - same input → same stored data shape
  - same invalid input → equivalent error outcome
- Clarify pagination/search behavior in docs

### Acceptance criteria

- REST and MCP support the same core operations and same field semantics
- Protocol behavior differences, if any, are documented deliberately rather than accidentally
- Regression tests cover parity for core CRUD/search flows

### Why second

The project’s core differentiator is dual protocol support. If the two surfaces drift, the product story weakens immediately.

---

## M3 — Multi-Agent Isolation + Permission Model

**Goal:** Make the security and tenancy story explicit, predictable, and enforceable.

### Scope

- Formalize namespace model
- Define shared memory behavior
- Clarify API key permissions vs agent permissions
- Close the gap between ACL concept and runtime enforcement story

### Concrete tasks

- Write `docs/permissions.md` defining:
  - what `agent` means
  - whether `agent` maps to namespace, identity, or ownership
  - default isolation rules
  - shared read/write rules
  - admin override semantics
- Decide the canonical model:
  - per-agent private memory by default
  - optional shared namespace(s)
  - explicit cross-agent access only
- Audit where ACL is enforced today and where it is not yet enforced
- Add tests for:
  - private access allowed
  - cross-agent access denied by default
  - shared read behavior
  - admin override behavior
- Decide whether REST API keys are only permission classes (`read`, `read_write`, `admin`) or also tenant-bound identities

### Acceptance criteria

- Isolation rules are documented and test-backed
- Default-deny / default-allow behavior is explicit
- Admin, read-only, and write-capable paths behave predictably
- README includes a simple multi-agent example

### Why third

This is where the project becomes a true reusable memory service instead of just a CRUD wrapper.

---

## M4 — Operational Readiness + Open-Source Adoption

**Goal:** Make the project easy to deploy, observe, and trust in the real world.

### Scope

- CI/CD
- release workflow
- deployment guides
- operator docs
- example integrations

### Concrete tasks

- Add GitHub Actions for:
  - pytest
  - black --check
  - flake8
  - mypy
- Add deployment docs for:
  - local Linux host
  - Docker Compose
  - NAS / home server deployment
- Add backup/restore/export/import guidance
- Add `docs/api.md` and `docs/mcp.md`
- Add example clients/integrations:
  - Python REST example
  - Python MCP example
  - Hermes Agent example
- Define release checklist:
  - version bump
  - changelog
  - docs sync
  - verification commands

### Acceptance criteria

- CI runs on every PR/push
- A new user can deploy from docs without reverse-engineering the code
- At least one end-to-end example exists per protocol
- Release process is documented and repeatable

### Why fourth

This milestone converts a working alpha into an adoption-ready open-source project.

---

## M5 — Product Differentiators and Nice-to-Have Growth

**Goal:** Expand carefully after the foundation is stable.

### Candidate scope

- Better ranking/relevance strategy
- memory deduplication / merge heuristics
- expiration / archival policies
- structured metadata filtering
- import/export tooling
- hybrid search or optional semantic upgrades
- richer admin analytics
- audit/event stream for operations

### Suggested rule

Only start M5 after M1–M4 are stable enough that new contributors can reproduce development and test workflows without private context.

## 5. Priority order for the next 2–3 weeks

If prioritizing strictly, the recommended sequence is:

1. **Fix local verification path and dev bootstrap**
2. **Audit README commands against reality**
3. **Add docs for architecture + development**
4. **Create REST/MCP parity checklist and tests**
5. **Define and document isolation/permission model**
6. **Add CI quality gates**
7. **Add deploy/operator documentation**
8. **Then expand advanced memory behavior**

## 6. Immediate backlog candidates

These are the best next issues to create.

### P0

- Make `pytest` pass in a documented fresh-dev setup
- Ensure required runtime/dev dependencies are installed through documented flows
- Verify `memory-mcp` console script launch path
- Reconcile README quick-start with real setup steps

### P1

- Add architecture/development documentation
- Add protocol parity regression tests
- Define official v0.1 field contract for memory objects
- Document permissions and namespace model

### P2

- Add CI workflow
- Add Docker/local deployment verification checklist
- Add import/export/backup guidance
- Add example integrations for REST and MCP

### P3

- Improve search/ranking and metadata filters
- Add dedup/merge policy design
- Add richer dashboards and analytics

## 7. Key risks and mitigations

### Risk 1: Product story outpaces installability

**Symptom:** README looks capable, but a fresh contributor cannot run tests or launch locally.

**Mitigation:** Finish M1 before major feature expansion.

### Risk 2: REST and MCP drift apart

**Symptom:** Same memory behaves differently depending on protocol.

**Mitigation:** Add shared contract tests and explicitly document supported fields.

### Risk 3: Isolation remains conceptually fuzzy

**Symptom:** “multi-agent” is advertised, but permission behavior is ambiguous or inconsistent.

**Mitigation:** Ship documented default rules and test-backed enforcement.

### Risk 4: Admin panel grows faster than backend guarantees

**Symptom:** UI suggests capabilities that backend invariants do not yet fully guarantee.

**Mitigation:** Use backend acceptance criteria as source of truth; document placeholders clearly.

### Risk 5: Advanced features create premature complexity

**Symptom:** semantic search, dedup, or evolution hooks increase scope before baseline reliability is solid.

**Mitigation:** Keep M5 gated behind M1–M4 completion.

## 8. Recommended next action

The recommended next working session is:

### “Stabilize local development and verification”

That session should aim to complete:

- documented environment setup
- a reproducible test command
- a reproducible local run command
- README corrections
- one architecture/development doc pair

This gives the highest leverage because it improves contributor onboarding, issue reproduction, CI setup, and future implementation speed all at once.

## 9. Suggested success definition for v0.1

The project can reasonably call its next public milestone successful when:

- a new user can clone, install, run tests, and launch the service in under 10 minutes
- REST and MCP contracts are intentionally aligned
- multi-agent isolation behavior is documented and covered by tests
- admin/API/auth flows are test-backed and reproducible
- CI enforces the same checks described in `CONTRIBUTING.md`
- docs explain not only what the project is, but how to operate it confidently

## 10. Audit evidence used for this roadmap

- `README.md`
- `CONTRIBUTING.md`
- `pyproject.toml`
- `src/memory_mcp/protocol/rest.py`
- `src/memory_mcp/protocol/mcp.py`
- `src/memory_mcp/auth/acl.py`
- recent git commits on `master`
- verification attempts on 2026-05-14:
  - `pytest -q` → import path failure for `memory_mcp`
  - `PYTHONPATH=src pytest -q` → dependency failure: missing `redis`
