# Water Treatment PLC/HMI Inventory

This document answers the PLC/HMI inventory questions for the water treatment use case after the repository refactor. The current water treatment root is `sector-water/rovisys-treatment/`; older task text that refers to `water-treatment/` maps to this new location.

## Summary

| Scope | Current answer |
|-------|----------------|
| P1 onboarding demo | Exists as a packaged demo under `usecases/p1-onboarding/` |
| CTF1 baseline | Reuses the P1 onboarding demo assets and scenarios |
| Full P1-P6 implementation | Skeleton exists under `usecases/full-system-p1-to-p6/`; P2-P6 PLC/HMI implementations are not started |
| Rockwell deployment | P1 controller, simulator, HMI, maps, tests, and scripts exist |
| OpenPLC simulation | P1 controller, simulator, Modbus maps, scripts, tests, and deployment files exist |
| HMI | P1 Rockwell HMI XML exists; full P1-P6 HMI screens are missing |

## Deliverable Locations

| Required deliverable | Current repo path |
|----------------------|-------------------|
| PLC inventory Markdown | `sector-water/rovisys-treatment/docs/plc-inventory.md` |
| PLC inventory CSV | `sector-water/rovisys-treatment/docs/plc-inventory.csv` |
| Controller/simulator map | `sector-water/rovisys-treatment/usecases/full-system-p1-to-p6/controller-simulator-map.md` |

## Process Inventory

| Process | Name | Controller PLC needed | Simulator/process PLC needed | HMI needs | Existing implementation | Files in repo today | Missing files | Stale or incorrectly placed files |
|---------|------|-----------------------|------------------------------|-----------|-------------------------|--------------------|---------------|-----------------------------------|
| P1 | Raw Water Intake | One controller PLC for raw water valve, pump, alarm, permissive, and state logic | One simulator PLC for tank level, pump flow, valve status, pump status, and fault feedback | Start/stop controls, raw-water tank level, pump speed/flow, valve states, alarms, system state | Rockwell and OpenPLC both exist for onboarding demo | `usecases/p1-onboarding/implementations/rockwell/controller/`, `simulator/`, `hmi/`, `rockwell_map.yaml`, `hw_test_config.yaml`; `usecases/p1-onboarding/implementations/openplc/controller/`, `simulator/`, `configs/`, `st/`, `scripts/`, `tests/`; `tag_contract.yaml`; `docs/process-models/wt-p1-raw-water.md` | Full-system P1 placement under `processes/p1/`; production full-system HMI screen; finalized shared tag-contract location | Rockwell README refers to old `plc/Controller_PLC.L5X` and `plc/Simulator_PLC.L5X` paths, but current files are under `controller/` and `simulator/`; `_archive/` contains old Rockwell/OpenPLC copies |
| P2 | Chemical Dosing | One controller PLC section for chemical valve commands and future dosing logic | One simulator/process PLC section for NaCl, NaOCl, and HCl tank levels and valve status | Chemical tank levels, valve commands/status, low chemical alarms, dosing status | Tag contract and process model exist; full implementation is not started in the new full-system README | `tag_contract.yaml`; `docs/process-models/wt-p2-chemical-treatment.md` | Controller PLC program, simulator PLC program, HMI screen, scenarios, tests, process folder assets under `processes/p2/` | Process model says implemented, but `usecases/full-system-p1-to-p6/README.md` says P2 is not started; treat the process model as design/reference until PLC files are organized |
| P3 | Ultrafiltration | One controller PLC section for UF valves, UF tank level coordination, drain/ROFT/BWP commands, and interlocks | One simulator/process PLC section for UF feed tank level and valve feedback | UF tank level, inlet/drain/ROFT/BWP valve status, backwash/drain indicators, alarms | Tag contract and process model exist; full implementation is not started in the new full-system README | `tag_contract.yaml`; `docs/process-models/wt-p3-ultrafiltration.md` | Controller PLC program, simulator PLC program, HMI screen, scenarios, tests, process folder assets under `processes/p3/` | Process model says implemented, but `usecases/full-system-p1-to-p6/README.md` says P3 is not started; treat the process model as design/reference until PLC files are organized |
| P4 | Dechlorination (UV) | One controller PLC section for UV/dechlorination sequencing, permissives, and alarms | One simulator/process PLC section for UV/dechlorination process state and feedback | UV/dechlorination status, enable/disable, alarms, process values from final tag list | Not started | Placeholder directory `processes/p4/` | Tag contract entries, process model, controller PLC program, simulator PLC program, HMI screen, scenarios, tests | No stale implementation found; directory is only a placeholder |
| P5 | Reverse Osmosis | One controller PLC section for RO sequencing, feed/permeate/reject control, permissives, and alarms | One simulator/process PLC section for RO feed/permeate/reject behavior and feedback | RO feed/permeate/reject status, valve/pump status, pressure/flow/quality tags when finalized | Not started | Placeholder directory `processes/p5/` | Tag contract entries, process model, controller PLC program, simulator PLC program, HMI screen, scenarios, tests | No stale implementation found; directory is only a placeholder |
| P6 | Permeate Storage | One controller PLC section for permeate storage, transfer/distribution, permissives, and alarms | One simulator/process PLC section for permeate tank level, transfer flow, and feedback | Permeate tank level, transfer status, valve/pump status, alarms | Not started | Placeholder directory `processes/p6/` | Tag contract entries, process model, controller PLC program, simulator PLC program, HMI screen, scenarios, tests | No stale implementation found; directory is only a placeholder |

## PLCs Needed by Use Case

| Use case | PLCs needed | Current status |
|----------|-------------|----------------|
| P1 onboarding demo | P1 controller PLC plus P1 simulator PLC. Rockwell uses Studio 5000 files; OpenPLC uses controller and simulator OpenPLC projects. | Exists for both Rockwell and OpenPLC under `usecases/p1-onboarding/implementations/` |
| CTF1 | Same as P1 onboarding demo: P1 controller PLC plus P1 simulator PLC, with attack/evidence scenarios layered on top. | Existing P1 demo assets are the best base |
| Full P1-P6 water treatment | Six controller PLC modules or programs and six simulator/process PLC modules or programs, one pair per process. They may be packaged as separate PLCs or as coordinated sections of larger controller/simulator projects, but the inventory should track each process independently. | Skeleton exists; P2-P6 implementation files are missing |
| Rockwell deployment | Rockwell controller PLC and simulator PLC for each implemented process, plus HMI project files and tag/address maps. | P1 exists; P2-P6 missing |
| OpenPLC simulation | OpenPLC controller and simulator projects for each implemented process, plus Modbus maps, scripts, tests, and deployment assets. | P1 exists; P2-P6 missing |

## Existing P1 Files

### Rockwell

| Purpose | Path |
|---------|------|
| Controller PLC | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/rockwell/controller/Controller_PLC_V1.1.L5X` |
| Controller PLC text export | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/rockwell/controller/Controller_PLC_V1.1.L5K` |
| Simulator PLC | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/rockwell/simulator/Simulator_PLC_V1.1.L5X` |
| Simulator PLC text export | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/rockwell/simulator/Simulator_PLC_V1.1.L5K` |
| HMI | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/rockwell/hmi/HMI_V1.1.xml` |
| Rockwell map | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/rockwell/rockwell_map.yaml` |
| Hardware test config | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/rockwell/hw_test_config.yaml` |
| Tests | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/rockwell/tests/` |

### OpenPLC

| Purpose | Path |
|---------|------|
| Controller project | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/openplc/controller/controller_project/plc.xml` |
| Simulator project | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/openplc/simulator/simulator_project/plc.xml` |
| Controller structured text | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/openplc/st/controller_flat.st` |
| Simulator structured text | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/openplc/st/simulator_flat.st` |
| Modbus map | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/openplc/configs/modbus_map.yaml` |
| OpenPLC map | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/openplc/configs/openplc_map.yaml` |
| Explicit I/O map | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/openplc/configs/explicit_io_map.csv` |
| Deployment scenario | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/openplc/scenario.yaml` |
| Operator and collector scripts | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/openplc/scripts/` |
| Tests | `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/openplc/tests/` |

## HMI Screens and Tags Needed

| Scope | Screen/tag need |
|-------|-----------------|
| P1 onboarding | Start/stop pushbuttons, system state indicators, raw-water tank level, pump speed, pump flow, valve commands/status, pump status/fault, low/high/high-high alarms |
| P2 | Chemical tank levels, NaCl/NaOCl/HCl valve commands/status, dosing status, low chemical alarms |
| P3 | UF tank level, UF inlet/drain/ROFT/BWP valve commands/status, backwash/drain indicators, UF alarms |
| P4 | UV/dechlorination status, commands, permissives, alarms, and any finalized process-quality values |
| P5 | RO feed/permeate/reject status, pump/valve commands/status, pressure/flow/quality values once finalized |
| P6 | Permeate tank level, transfer/distribution commands/status, storage alarms |
| Full system | Overview screen showing P1-P6 status, cross-process permissives, active alarms, and navigation to each process screen |

## Cross-Boundary Signals

Signals crossing controller/simulator boundaries are documented in detail in `usecases/full-system-p1-to-p6/controller-simulator-map.md`. For the current P1 demo, the important boundary tags are:

| Direction | Tags |
|-----------|------|
| HMI to controller | `HMI_Start_PB`, `HMI_Stop_PB` |
| Controller to HMI | `HMI_Start_Active`, `HMI_Stop_Active`, `SYS_IDLE`, `SYS_START`, `SYS_RUNNING`, `SYS_SHUTDOWN`, alarm tags |
| Controller to simulator | `RW_Tank_PR_Valve`, `RW_Tank_P6B_Valve`, `RW_Tank_P_Valve`, `RW_Pump_Start`, `RW_Pump_Stop`, `RW_Pump_Speed` |
| Simulator to controller | `RW_Tank_Level`, `RW_Pump_Flow`, `RW_Tank_PR_Valve_Sts`, `RW_Tank_P6B_Valve_Sts`, `RW_Tank_P_Valve_Sts`, `RW_Pump_Sts`, `RW_Pump_Fault` |
| Cross-process logic | `UF_UFFT_Tank_Level` influences P1 pump start/stop logic in the current UC1/P1-P3 tag contract |

## Reusable Assets

| Asset | Reuse recommendation |
|-------|----------------------|
| `tag_contract.yaml` | Reuse as the current P1-P3 tag reference, then move or copy into `shared/tag-contracts/` after the inventory is approved |
| `docs/io_map.csv` | Keep as the frozen use-case snapshot for controller I/O mapping |
| `docs/process-models/` | Reuse P1-P3 process models as design references, but reconcile their "Implemented" status with the new full-system README |
| `usecases/p1-onboarding/implementations/openplc/configs/` | Reuse Modbus mapping patterns for future OpenPLC process maps |
| `usecases/p1-onboarding/implementations/rockwell/rockwell_map.yaml` | Reuse mapping pattern for future Rockwell process maps |
| `usecases/p1-onboarding/scenarios/` | Reuse scenario naming and structure for future P2-P6 tests |

## Open Follow-Up Work

- Create or move approved per-process assets into `sector-water/rovisys-treatment/processes/p1/` through `p6/`.
- Decide whether full-system PLCs are separate PLCs per process or combined controller/simulator projects with per-process modules.
- Extend the tag contract for P4-P6 using the final water treatment PCF/FDS source.
- Add P2-P6 Rockwell and OpenPLC controller/simulator files.
- Add full-system HMI screens for P1-P6 and the system overview.
- Fix stale Rockwell README paths so they match the current `controller/`, `simulator/`, and `hmi/` folders.
- Classify `_archive/` files as historical reference only or migrate any still-valid assets.
