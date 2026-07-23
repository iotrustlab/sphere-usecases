# SPHERE HMI Demo Checklist

Step-by-step instructions for demonstrating the SPHERE CPS HMI with each use case.

## Pre-Demo Setup

1. **Verify Prerequisites**
   - [ ] Docker Desktop running
   - [ ] Ports 502, 503, 1881, 8080, 8081 available
   - [ ] At least 4GB RAM available for containers

2. **Clone Required Repos**
   ```bash
   # Both repos must be siblings
   cd ~/Development
   git clone <sphere-usecases>
   git clone <cps-enclave-model>
   ```

3. **Build OpenPLC Base Image** (first time only)
   ```bash
   cd cps-enclave-model/docker/openplc
   docker build -t sphere-openplc .
   ```

---

## Water Treatment (WT) Demo

### Start

```bash
cd sphere-usecases/hmi
USECASE=wt ./scripts/start_demo.sh
```

### Demo Flow

1. **Open FUXA HMI**: http://localhost:1881

2. **Configure Modbus Connection** (first time)
   - Go to Setup > DAQ/Modbus
   - Add device: `controller`, Host: `10.100.0.10`, Port: `502`
   - Test connection

3. **Verify Initial State**
   - [ ] System shows IDLE state (gray indicator)
   - [ ] All tank levels at initial values
   - [ ] Pump speed at 0%

4. **Start System**
   - [ ] Click Start button
   - [ ] Observe: IDLE → STARTUP transition
   - [ ] Wait for STARTUP → RUNNING
   - [ ] Tank levels begin changing

5. **Adjust Pump Speed**
   - [ ] Move pump speed slider to 75%
   - [ ] Observe flow rate increases
   - [ ] Watch tank levels respond

6. **Observe Alarms**
   - [ ] If tank reaches HH level, alarm activates
   - [ ] Alarm banner turns red

7. **Stop System**
   - [ ] Click Stop button
   - [ ] Observe: RUNNING → SHUTDOWN
   - [ ] Wait for SHUTDOWN → IDLE

### Expected Screenshots
- `10_wt_hmi_idle.png` - IDLE state with all indicators
- `11_wt_hmi_running.png` - RUNNING with flow visible
- `12_wt_trend_level_flow.png` - Trend chart of level + flow

---

## Water Distribution (WD) Demo

### Start

```bash
cd sphere-usecases/hmi
USECASE=wd ./scripts/start_demo.sh
```

### Demo Flow

1. **Open FUXA HMI**: http://localhost:1881

2. **Verify Initial State**
   - [ ] System shows IDLE state
   - [ ] Supply, Elevated, Return tank levels visible
   - [ ] All valves closed, pumps off

3. **Start System**
   - [ ] Click Start button
   - [ ] Watch transition to RUNNING

4. **Adjust Pump Speeds**
   - [ ] Set Supply Pump to 60%
   - [ ] Set Return Pump to 40%
   - [ ] Observe flow through system

5. **Toggle Valves**
   - [ ] Open Supply Valve
   - [ ] Open Elevated Tank Valve
   - [ ] Watch tank levels respond

6. **Simulate High Demand**
   - [ ] Increase Supply Pump to 100%
   - [ ] Close Return Valve
   - [ ] Watch Elevated Tank drain

7. **Stop System**
   - [ ] Click Stop button
   - [ ] Return to IDLE

### Expected Screenshots
- `20_wd_hmi_idle.png` - IDLE state overview
- `21_wd_hmi_running.png` - RUNNING with flows
- `22_wd_high_demand.png` - High demand scenario

---

## Power Hydro (PS) Demo

### Start

```bash
cd sphere-usecases/hmi
USECASE=ps ./scripts/start_demo.sh
```

### Demo Flow

1. **Open FUXA HMI**: http://localhost:1881

2. **Verify Initial State**
   - [ ] Unit shows IDLE state
   - [ ] Gate position at 0%
   - [ ] Reservoir level visible
   - [ ] Power output at 0 MW

3. **Enable Run Permissive**
   - [ ] Toggle Run Enable ON
   - [ ] Toggle Auto Mode ON
   - [ ] Verify READY indicator lights green

4. **Start Unit**
   - [ ] Click Start button
   - [ ] Observe: IDLE → STARTUP
   - [ ] Gate begins opening
   - [ ] Speed increases toward synchronous

5. **Synchronize Generator**
   - [ ] Wait for STARTUP → RUNNING
   - [ ] Breaker closes automatically
   - [ ] Power output begins ramping

6. **Adjust Power Output**
   - [ ] Move Power Setpoint slider to 50 MW
   - [ ] Observe gate adjusts
   - [ ] Power output follows setpoint

7. **Trip Demonstration** (optional)
   - [ ] Increase power beyond limits
   - [ ] Observe RUNNING → TRIPPED
   - [ ] Note which trip activated (Overspeed/Overpressure/LowHead)
   - [ ] Click Reset to clear trip
   - [ ] Returns to IDLE

8. **Normal Shutdown**
   - [ ] Click Stop button
   - [ ] Observe: RUNNING → SHUTDOWN
   - [ ] Gate closes, breaker opens
   - [ ] Returns to IDLE

### Expected Screenshots
- `30_ps_idle.png` - IDLE state, gate at 0%
- `31_ps_startup.png` - STARTUP with gate opening
- `32_ps_running.png` - RUNNING at 50 MW
- `33_ps_trip.png` - TRIPPED state with trip cause

---

## Post-Demo

### Stop Containers
```bash
./scripts/stop_demo.sh
```

### Clean Up (if needed)
```bash
./scripts/stop_demo.sh --clean
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| PLCs not starting | Check `docker compose logs controller` |
| Bridge errors | Wait for PLC health checks to pass |
| FUXA not connecting | Verify Modbus device config points to `10.100.0.10:502` |
| No data updating | Check bridge logs: `docker compose logs bridge` |
| Slow compilation | First build takes longer; subsequent starts are faster |

---

## Evidence Capture

After completing demos, capture evidence:

```bash
# Screenshots (requires Playwright)
python scripts/capture_screenshots.py

# GIFs (manual - see script for instructions)
./scripts/capture_gifs.sh
```

Place output in: `docs/demo-evidence/2026-02-09/`
