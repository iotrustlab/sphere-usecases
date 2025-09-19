# SPHERE Use-Cases • Cursor Task Plan

> Owner: **PI Garcia (Utah)** · Scope: reorg repo to support multiple *self‑contained* CPS processes, each with one or more implementations (Rockwell, OpenPLC/virtual, etc.) and clean developer workflows.

---

## Why this change (1–2 sentences)
- Current repo mixes **Rockwell** PLC programs with a top-level README focused on **OpenPLC** setup, and includes a placeholder *chemical-mixing* use case that was intended to be **oil-and-gas distribution**. We need a consistent, scalable structure and contributor flow.

---

## Target principles
1. **One process = one use case** (self‑contained by default).
2. **Implementations live under the use case** (`implementations/rockwell`, `implementations/openplc`, …).
3. **Docs live with the use case**, with a small top-level README that only routes users.
4. **Separation of concerns**: physical P&IDs & I/O maps vs controller logic vs simulators vs security experiments.
5. **Reproducibility**: validate > simulate > (optionally) deploy; same CLI verbs across implementations.
6. **Future multi-process orchestration**: support later via `bridges/` adapters (not in MVP).

---

## Final directory layout (MVP)
```
sphere-usecases/
├── README.md                          # Top-level router (short)
├── templates/                         # Golden skeletons
│   ├── single-process/                # Use this for most MVP use cases
│   │   ├── README.md
│   │   ├── docs/
│   │   │   ├── process_overview.md
│   │   │   ├── pid.pdf
│   │   │   └── io_map.csv
│   │   ├── implementations/
│   │   │   ├── rockwell/
│   │   │   │   ├── plc/
│   │   │   │   │   ├── control.l5x
│   │   │   │   │   └── simulation.l5x
│   │   │   │   ├── scripts/
│   │   │   │   │   ├── validate.sh
│   │   │   │   │   └── deploy.sh
│   │   │   └── openplc/               # purely virtual
│   │   │       ├── plc_st/
│   │   │       │   ├── control.st
│   │   │       │   └── simulation.st
│   │   │       ├── sim/
│   │   │       │   ├── process_model.py
│   │   │       │   └── test_model.py
│   │   │       └── scripts/
│   │   │           ├── validate.sh
│   │   │           └── run_local.sh
│   │   └── experiments/
│   │       ├── sensor_spoofing/
│   │       └── setpoint_manipulation/
│   └── README.md
├── water-treatment/
│   ├── README.md
│   ├── docs/
│   │   ├── process_overview.md
│   │   ├── pid.pdf
│   │   └── io_map.csv
│   ├── implementations/
│   │   ├── rockwell/
│   │   │   ├── plc/
│   │   │   │   ├── Controller_PLC.L5X
│   │   │   │   ├── Simulator_PLC.L5X
│   │   │   │   └── (archival .L5K if needed)
│   │   │   └── scripts/
│   │   │       ├── validate.sh
│   │   │       └── deploy.sh
│   │   └── openplc/                   # optional (virtual)
│   │       ├── plc_st/
│   │       ├── sim/
│   │       └── scripts/
│   └── experiments/
│       ├── sensor_spoofing/
│       └── pump_override/
├── oil-and-gas-distribution/          # (rename from chemical-mixing placeholder)
│   ├── README.md                      # initially a stub using template
│   ├── docs/
│   ├── implementations/
│   └── experiments/
├── controller-mappings/               # keep as a shared reference (optional move to each use case)
│   └── README.md
├── tag-layouts/                       # shared tag schemas (may migrate copies into each use case)
│   └── README.md
└── diagrams/                          # global diagrams (legacy; move per-use-case into docs/)
    └── README.md
```
Notes:
- **OpenPLC** directories are **virtual-only** reference implementations (local sim + ST code).
- **Rockwell** directories reflect **actual SPHERE testbed** deployments (Studio 5000, L5X).

---

## Global tasks (do in order)

### T0 — Create templates & tooling
**Goal:** provide a golden skeleton and standard scripts (validate/deploy).  
**Steps:**
- [ ] Add `templates/single-process/` (structure above).
- [ ] Add `scripts/` in each implementation with common verb names:
  - `validate.sh` → schema/XIR checks, lints, basic sim runs
  - `deploy.sh` (rockwell only) → handoff to enclave infra (no-op in OpenPLC)
  - `run_local.sh` (openplc only) → run virtual sim locally
- [ ] Provide example **io_map.csv** schema (Tag, Address, Type, Units, Range, SafetyNotes).

**Definition of Done (DoD):**
- Running `tree templates/single-process/` matches the structure.
- `chmod +x` scripts; `./scripts/validate.sh` prints a helpful stub message.

---

### T1 — Top-level README becomes a router
**Goal:** make the root README concise and accurate.  
**Steps:**
- [ ] Replace current long-form README with a short router:
  - What this repo is (use-cases only).
  - Where to start (pick a use case; read its README).
  - Matrix of implementations (Rockwell = testbed, OpenPLC = virtual).
  - Contribution link to **templates/single-process**.
- [ ] Move deep guidance into `templates/README.md`.

**DoD:**
- Top-level README ≤ ~120 lines and has links to each use case’s README.

---

### T2 — Migrate **water-treatment** to the new structure
**Goal:** keep history, make it self-contained under `implementations/rockwell`.  
**Steps:**
- [ ] Create `water-treatment/docs/` and move/author:
  - `process_overview.md` (P&ID, stages, safety)
  - `io_map.csv` (from tag-layouts/controller-mappings if available)
  - `pid.pdf` (move from `diagrams/` if specific)
- [ ] Move Rockwell files into `implementations/rockwell/plc/`:
  - `Controller_PLC.L5X`, `Simulator_PLC.L5X`, and (optionally) `.L5K` archives.
- [ ] Create `implementations/rockwell/scripts/validate.sh`:
  - calls shared infra validator if available; else stub with TODOs
- [ ] Create `implementations/rockwell/scripts/deploy.sh`:
  - delegates to SPHERE enclave infra (placeholder call)
- [ ] Create `experiments/` with two stubs (`sensor_spoofing/`, `pump_override/`) and a mini README.
- [ ] Update `water-treatment/README.md` to:
  - Clarify that **Rockwell** is authoritative for SPHERE testbed deployment.
  - Note **OpenPLC** is optional/virtual and may land later under `implementations/openplc/`.

**DoD:**
- `tree water-treatment/` matches target layout.
- `./implementations/rockwell/scripts/validate.sh` runs and exits 0 with stub text.

**Suggested Git moves:**
```bash
git mv water-treatment/plc-programs/Controller_PLC.L5X water-treatment/implementations/rockwell/plc/
git mv water-treatment/plc-programs/Simulator_PLC.L5X  water-treatment/implementations/rockwell/plc/
# (optional) keep .L5K in same folder or move to plc/archive/
mkdir -p water-treatment/docs water-treatment/experiments/sensor_spoofing water-treatment/experiments/pump_override
```

---

### T3 — Rename **chemical-mixing** → **oil-and-gas-distribution**
**Goal:** align with the intended use case.  
**Steps:**
- [ ] `git mv chemical-mixing oil-and-gas-distribution`
- [ ] Replace its README with a stub based on `templates/single-process/README.md`.
- [ ] Mark implementation status = “planned” (no files) and link to templates.

**DoD:**
- `tree oil-and-gas-distribution/` shows the skeleton with TODOs.

---

### T4 — Normalize shared references
**Goal:** reduce ambiguity between global vs per-use-case docs.  
**Steps:**
- [ ] For any diagrams in `diagrams/` that are specific to **water-treatment**, move them into `water-treatment/docs/`.
- [ ] Keep `controller-mappings/` & `tag-layouts/` as **reference** (global), but **copy** a frozen CSV into each use case’s `docs/io_map.csv` for reproducibility snapshots.
- [ ] Update both READMEs to explain “reference vs snapshot” policy.

**DoD:**
- Per-use-case `docs/io_map.csv` exists and is versioned with the use case.

---

### T5 — Add contributor workflow
**Goal:** consistent PRs for new use cases or new implementations.  
**Steps:**
- [ ] Add `CONTRIBUTING.md` with:
  - How to copy `templates/single-process/`.
  - Required docs/files & naming.
  - Validation script expectations.
  - Review checklist (security + safety notes).
- [ ] Add PR template `.github/pull_request_template.md`:
  - Links to P&ID, io_map, implementation scripts, basic sim proof.

**DoD:**
- Contributors can run through a checklist before review.

---

### T6 — Standardize CLI verbs & validation
**Goal:** every implementation exposes the same verbs.  
**Steps:**
- [ ] Define the minimal contract for scripts:
  - `validate.sh` must: check schema, print I/O summary, return non‑zero on failure.
  - `deploy.sh` (rockwell): noop if **not** on enclave; otherwise call infra.
  - `run_local.sh` (openplc): run Python sim or OpenPLC container locally.
- [ ] Provide a shared `tools/validate_xir.py` (or just stub now) that both implementations call.

**DoD:**
- Running `find . -name validate.sh -exec {} \;` succeeds across all implementations.

---

### T7 — (Future) Multi‑process orchestration hooks
**Goal:** leave room for SWaT‑style cross‑process comms later.  
**Steps (docs only for now):**
- [ ] Add `docs/bridges.md` describing how **bridges/** will emulate inter‑process I/O (e.g., Modbus/TCP adapters) without changing the single‑process contract.
- [ ] Define interface: a bridge exposes a `docker-compose.yml` and a `bridge.yaml` mapping.

**DoD:**
- Documented plan; **no code** required in MVP.

---

## Quick patch script (safe to run incrementally)
> Use this only after reading tasks T0–T4. It creates folders and stubs; it does **not** delete files.

```bash
# from repo root
set -euo pipefail

# 0) templates
mkdir -p templates/single-process/{docs,implementations/{rockwell/{plc,scripts},openplc/{plc_st,sim,scripts}},experiments}
cat > templates/single-process/README.md <<'EOF'
# Use Case Template (Single Process)
(brief purpose, safety, and how to run implementations)
EOF
printf '%s\n' "Tag,Address,Type,Units,Range,SafetyNotes" > templates/single-process/docs/io_map.csv
printf '%s\n' "#!/usr/bin/env bash\necho \"[stub] validate: add schema checks & mini sim\"" > templates/single-process/implementations/rockwell/scripts/validate.sh
printf '%s\n' "#!/usr/bin/env bash\necho \"[stub] deploy: SPHERE enclave handoff (no-op off enclave)\"" > templates/single-process/implementations/rockwell/scripts/deploy.sh
printf '%s\n' "#!/usr/bin/env bash\necho \"[stub] run_local: start virtual sim\"" > templates/single-process/implementations/openplc/scripts/run_local.sh
chmod +x templates/single-process/implementations/rockwell/scripts/*.sh templates/single-process/implementations/openplc/scripts/*.sh

# 1) water-treatment restructure
mkdir -p water-treatment/{docs,implementations/rockwell/{plc,scripts},experiments/{sensor_spoofing,pump_override}}

# 2) move PLCs if present (ignore errors if not found)
mv water-treatment/plc-programs/Controller_PLC.L5X water-treatment/implementations/rockwell/plc/ 2>/dev/null || true
mv water-treatment/plc-programs/Simulator_PLC.L5X  water-treatment/implementations/rockwell/plc/ 2>/dev/null || true

# 3) create rockwell scripts (idempotent)
cat > water-treatment/implementations/rockwell/scripts/validate.sh <<'EOF'
#!/usr/bin/env bash
set -e
echo "[water-treatment/rockwell] validate: (stub) run XIR/tag checks; verify L5X present"
exit 0
EOF

cat > water-treatment/implementations/rockwell/scripts/deploy.sh <<'EOF'
#!/usr/bin/env bash
set -e
echo "[water-treatment/rockwell] deploy: (stub) handoff to SPHERE enclave infra"
exit 0
EOF
chmod +x water-treatment/implementations/rockwell/scripts/*.sh

# 4) rename chemical-mixing -> oil-and-gas-distribution if present
if [ -d "chemical-mixing" ]; then
  git mv chemical-mixing oil-and-gas-distribution 2>/dev/null || mv chemical-mixing oil-and-gas-distribution
fi

# 5) ensure stubs
for U in oil-and-gas-distribution; do
  mkdir -p "$U"/{docs,implementations,experiments}
  touch "$U"/README.md
done

echo "Scaffold complete."
```

---

## Acceptance checklist (MVP)
- [ ] Top-level README is a router; detailed guidance lives in templates & per-use-case docs.
- [ ] `water-treatment/` follows the new structure; Rockwell is authoritative; OpenPLC is optional.
- [ ] `oil-and-gas-distribution/` exists as a stub (replacing chemical-mixing).
- [ ] Templates exist; contributors can copy them and pass `validate.sh` stubs.
- [ ] No dependence on multi‑process orchestration for MVP; documented plan exists.

---

## Notes on implementations
- **Rockwell** (Studio 5000, L5X) = **real SPHERE testbed** deployment path (scripts only delegate; keep secrets/infra in `sphere-infra` repo).
- **OpenPLC** = **virtual only** (no testbed deployment); used for rapid prototyping, CI, and student labs.

---

## Small task backlog (next)
- Add a `tools/` folder with shared validators (XIR/tag schema), CLI (`python -m sphere_usecases.tools.validate`).
- Pre-commit hooks: tag schema lint, forbidden file patterns in `implementations/rockwell/plc`.
- GitHub Actions to run `validate.sh` in changed paths.
- Minimal example experiment notebook per use case (plot setpoint vs process variable; show perturbation).

---

## Comms snippet (for the repo README)
> “SPHERE CPS Enclave (NSF infrastructure based at USC ISI) provides the real hardware ICS environment; the **Utah-led CPS enclave** is designed, developed, and tested by **PI Garcia**, and this repository hosts the **use-case processes** that run on that enclave. Each use case may offer multiple implementations: **Rockwell** for enclave deployment and **OpenPLC (virtual)** for local exploration.”

