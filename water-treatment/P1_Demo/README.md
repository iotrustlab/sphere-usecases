# Water Treatment Testbed Demo (P1 → P3)

## Overview

This project demonstrates a simplified water treatment process using two PLCs:

- **Simulator PLC** – Simulates the plant by generating tank levels and sensor values.
- **Controller PLC** – Runs the control logic using the simulated inputs.

The simulator and controller PLCs are connected together, with the outputs of one PLC acting as the inputs of the other.

The process begins by filling the **P1 Raw Water Tank (`P1.RW_Tank`)** from a simulated raw water source. Once the tank reaches approximately **800 mm**, a transfer valve and pump are activated to move water into the **P3 Ultrafiltration Tank (`P3.Ultrafiltration_Tank`)**.

When the P3 tank reaches its maximum capacity of **1000 mm**, the tank is held full for a randomly selected time between **5 and 8 seconds** before draining. Once the tank is emptied, the process repeats by filling the P1 tank again.

---

## Differences from the Full P1–P6 Process

This demo represents only a small portion of the complete water treatment process.

The following stages are omitted:

- **P2 (Chemical Mixing)** – In the complete system, water passes through a chemical mixing process before entering P3. This stage is not simulated.
- **P4–P6 (Downstream Processes)** – In the full system, water leaving the ultrafiltration tank continues through additional treatment stages. In this demo, the P3 tank simply drains to restart the simulation.

---

## HMI

### Required HMI Files

Import the following FactoryTalk View SE display files into your project:

- `Graph.xml`
- `HMI_Start_Stop.xml`

### Connecting PLC Tags

After importing the displays, configure the HMI tag connections to reference the tags created in the Studio 5000 controller project.

Refer to **[HMI_Document](https://docs.google.com/document/d/1BMLtfDSWW5HnUIFVvH2NNYvGX_wp7LKe_QNLaL3Sytg/edit?usp=sharing)** for instructions on configuring the FactoryTalk View application.

### Running the HMI

1. Open the FactoryTalk View SE project inside the virtual machine.
2. Import `Graph.xml` and `HMI_Start_Stop.xml`.
3. Configure the tag references.
4. Click the **Run/Test Display** (Play button) in FactoryTalk View Studio.
5. Press **Start_Sim** to begin the simulator.
6. Press **Start_Cont** to start the controller.

While running, the HMI displays:

- Tank levels
- Pump status
- Valve status
- Process state
- Animated tank level overlays

The main HMI also contains a button that opens a second display showing a graph of the tank levels over time.

### HMI Controls

| Button | Description |
|---------|-------------|
| **RST** | Resets the simulator, tank levels, valves, and process values. |
| **Start_Sim** | Starts the simulator PLC and begins updating process values. |
| **Start_Cont** | Starts the controller PLC and begins executing the control logic. |
| **Stop_Cont** | Stops the controller and transitions the state machine to shutdown. |

The controller follows the state sequence:

```text
IDLE
  ↓
START
  ↓
RUNNING
  ↓
SHUTDOWN
```

---

## Required PLC Files

The following Studio 5000 project files are required:

- Simulator PLC `.L5X`
- Controller PLC `.L5X`

Both files are located in the `P1_demo` directory.

---

## Known Limitations

This demo is intended to demonstrate PLC communication and process control rather than accurately model a real water treatment plant.

Current limitations include:

- Water flow is modeled using simple inflow and outflow constants with a PLC scan-time (`dt`) update.
- Tank behavior does not account for pressure, pump curves, or hydraulic losses.
- Simulated analog values are ideal and do not include sensor noise or calibration error.
- No Gaussian or other measurement noise is modeled.
- Only Processes P1 and P3 are implemented.
- The P3 tank drains directly instead of feeding downstream treatment stages (P4–P6).

---
##HMI Storage
Hmi is stored as an xml file, for the two displays that were created

## Process Flow

```text
Fill P1 Raw Water Tank
        │
        ▼
P1 reaches ~800 mm
        │
        ▼
Open transfer valve
Start transfer pump
        │
        ▼
Fill P3 Ultrafiltration Tank
        │
        ▼
P3 reaches 1000 mm
        │
        ▼
Wait 5–8 seconds
        │
        ▼
Drain P3 Tank
        │
        ▼
Repeat
```
##Video Demonstartion of HMI and Simulator and Controller Process working together
https://youtu.be/Wm_Pji_4yi4
