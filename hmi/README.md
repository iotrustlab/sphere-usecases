# SPHERE HMI Demo Stack

Self-contained Docker Compose stack for demonstrating SPHERE CPS use cases with a web-based HMI (FUXA).

## Architecture

```
                    ┌─────────────────┐
                    │  FUXA HMI       │
                    │  :1881          │
                    └────────┬────────┘
                             │ Modbus TCP
                             ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Controller PLC  │◄──►│  Modbus Bridge  │◄──►│  Simulator PLC  │
│ 10.100.0.10:502 │    │  10.100.0.30    │    │  10.100.0.20:502│
│ WebUI :8080     │    │                 │    │  WebUI :8081    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Supported Use Cases

| Use Case | Code | Controller ST | Simulator ST |
|----------|------|---------------|--------------|
| Water Treatment UC1 | `wt` | `controller_final.st` | `simulator_final.st` |
| Water Distribution UC0 | `wd` | `wd_controller.st` | `wd_simulator.st` |
| Power Hydro PS-1 | `ps` | `ps_hydro_controller.st` | `ps_hydro_simulator.st` |

## Quick Start

```bash
# Start Water Treatment demo
USECASE=wt ./scripts/start_demo.sh

# Start Water Distribution demo
USECASE=wd ./scripts/start_demo.sh

# Start Power Hydro demo
USECASE=ps ./scripts/start_demo.sh

# Stop any demo
./scripts/stop_demo.sh
```

## Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| FUXA HMI | http://localhost:1881 | Web-based HMI |
| Controller WebUI | http://localhost:8080 | OpenPLC Controller WebUI |
| Simulator WebUI | http://localhost:8081 | OpenPLC Simulator WebUI |
| Controller Modbus | localhost:502 | Modbus TCP (for debugging) |
| Simulator Modbus | localhost:503 | Modbus TCP (for debugging) |

## Directory Structure

```
hmi/
├── docker-compose.yml     # Main orchestration file
├── bridge/
│   ├── Dockerfile         # Python bridge container
│   └── bridge.py          # Generic Modbus bridge
├── fuxa/                   # FUXA project data (auto-populated)
├── scripts/
│   ├── start_demo.sh      # Start demo stack
│   ├── stop_demo.sh       # Stop demo stack
│   ├── capture_screenshots.py  # Automated screenshot capture
│   └── capture_gifs.sh    # GIF recording instructions
├── tags/                   # HMI tag mapping files
│   ├── wt_hmi_tags.yaml
│   ├── wd_hmi_tags.yaml
│   └── ps_hydro_hmi_tags.yaml
├── DEMO_CHECKLIST.md      # Step-by-step demo instructions
└── README.md              # This file
```

## FUXA Configuration

FUXA projects are stored in `fuxa/` and persist across container restarts.

### Initial Setup

1. Start the demo: `USECASE=wt ./scripts/start_demo.sh`
2. Open FUXA: http://localhost:1881
3. Create a new project or import from `fuxa/project.json`
4. Configure Modbus connection:
   - Host: `10.100.0.10` (controller)
   - Port: `502`
   - Protocol: Modbus TCP

### Tag Mappings

See `tags/*.yaml` for HMI-specific tag addresses. Key patterns:

| Register Type | Address Range | Purpose |
|---------------|---------------|---------|
| Coil 0-3 | %QX0.0-0.3 | HMI buttons (Start, Stop) |
| Coil 40-51 | %QX5.* | Valve/pump commands |
| Coil 56-60 | %QX7.* | System state (IDLE, RUNNING, etc.) |
| HR 100-101 | %QW100-101 | Pump speed setpoints |
| IR 70-77 | %IW70-77 | Analog sensor values |

## Evidence Capture

For demo documentation:

```bash
# Capture screenshots (requires Playwright)
pip install playwright
playwright install chromium
python scripts/capture_screenshots.py

# Record GIFs (see instructions)
./scripts/capture_gifs.sh
```

## Troubleshooting

### PLCs not connecting

1. Check container health: `docker compose ps`
2. View logs: `docker compose logs controller`
3. Verify Modbus: `docker compose exec bridge python -c "from pymodbus.client import ModbusTcpClient; c=ModbusTcpClient('10.100.0.10'); print(c.connect())"`

### FUXA not loading

1. Check FUXA logs: `docker compose logs fuxa`
2. Ensure port 1881 is available
3. Clear browser cache and refresh

### Bridge errors

1. Check bridge logs: `docker compose logs -f bridge`
2. Verify both PLCs are healthy before bridge starts
3. Increase retry count if PLCs take longer to start

## Development

### Building locally

```bash
# Build all images
docker compose build

# Rebuild specific service
docker compose build controller
```

### Testing bridge locally

```bash
cd bridge
python bridge.py --usecase wt --controller localhost:502 --simulator localhost:503 -v
```

## Related Documentation

- [WT Modbus Map](../water-treatment/implementations/openplc/configs/modbus_map.yaml)
- [WD Modbus Map](../water-distribution/implementations/openplc/configs/openplc_map.yaml)
- [PS Modbus Map](../power-hydro/implementations/openplc/configs/openplc_map.yaml)
- [OpenPLC Dockerfile](../../cps-enclave-model/docker/openplc/Dockerfile)
