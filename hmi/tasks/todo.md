# Tasks: SPHERE MVP HMI + Demo Evidence Pack

## Current State (2026-02-09)

**Status**: Implementation complete, pending verification

All implementation tasks completed. The HMI stack and evidence pack structure are in place. Manual verification with actual container deployment needed.

## Completed Tasks

- [x] **Phase 1: Infrastructure** — Create `sphere-usecases/hmi/` with docker-compose, bridge, fuxa skeleton
- [x] **Phase 2: HMI Tag Mappings** — Create tag mapping YAML files for WT/WD/PS
- [x] **Phase 3: FUXA Dashboards** — Skipped (manual FUXA config, will be done during demo)
- [x] **Phase 4: Demo Scripts** — Create start_demo.sh, stop_demo.sh, DEMO_CHECKLIST.md
- [x] **Phase 5: Evidence Capture** — Create capture_screenshots.py, capture_gifs.sh
- [x] **Phase 6: Evidence Pack** — Create docs/demo-evidence/2026-02-09/ structure

## Files Created

### sphere-usecases/hmi/
```
hmi/
├── docker-compose.yml          # 4-service stack (controller, simulator, bridge, fuxa)
├── bridge/
│   ├── Dockerfile              # Python 3.11 + pymodbus
│   └── bridge.py               # Generic bridge for WT/WD/PS
├── fuxa/.gitkeep               # FUXA project data (populated on first run)
├── scripts/
│   ├── start_demo.sh           # Launch demo by use case
│   ├── stop_demo.sh            # Stop demo
│   ├── capture_screenshots.py  # Playwright automation
│   └── capture_gifs.sh         # GIF recording instructions
├── tags/
│   ├── wt_hmi_tags.yaml        # Water Treatment HMI tags
│   ├── wd_hmi_tags.yaml        # Water Distribution HMI tags
│   └── ps_hydro_hmi_tags.yaml  # Power Hydro HMI tags
├── DEMO_CHECKLIST.md           # Step-by-step demo instructions
└── README.md                   # Usage documentation
```

### sphere-usecases/docs/demo-evidence/2026-02-09/
```
2026-02-09/
├── screens/                    # Screenshot placeholders
├── gifs/                       # GIF placeholders
└── README.md                   # Evidence manifest
```

## Verification Steps (Manual)

1. **Docker Build Test**
   ```bash
   cd ../sphere-usecases/hmi
   docker compose build
   ```

2. **Water Treatment Demo**
   ```bash
   USECASE=wt ./scripts/start_demo.sh
   # Wait for health checks to pass
   # Open http://localhost:1881 (FUXA)
   # Open http://localhost:8080 (Controller WebUI)
   ./scripts/stop_demo.sh
   ```

3. **Water Distribution Demo**
   ```bash
   USECASE=wd ./scripts/start_demo.sh
   # Same verification
   ./scripts/stop_demo.sh
   ```

4. **Power Hydro Demo**
   ```bash
   USECASE=ps ./scripts/start_demo.sh
   # Same verification
   ./scripts/stop_demo.sh
   ```

## Notes

- FUXA project.json will be created manually during first demo run and exported
- Some screenshots are manual (repo tree, CI pass, RUNNING states)
- GIF recording is fully manual with OBS or screen capture

## Dependencies

- Docker Desktop with docker compose v2
- OpenPLC Dockerfile at `cps-enclave-model/docker/openplc/`
- ST files at expected paths in sphere-usecases
- Playwright (optional, for automated screenshots)
