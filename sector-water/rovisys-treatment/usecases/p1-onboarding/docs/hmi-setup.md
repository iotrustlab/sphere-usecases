# P1 Onboarding Demo — Studio 5000 and FactoryTalk View SE Setup

End-to-end setup for someone who has cloned this repository and has no prior
context: how to get the two PLC projects into Studio 5000, wire the HMI displays
to them in FactoryTalk View SE, and run the demo.

> **Scope note.** The steps below were reconstructed from the exported project
> files in this repository (controller/simulator L5X, the FactoryTalk display
> exports, and the batch-import manifest). Versions, controller names, shortcut
> names, and the tag list are read directly from those files and are exact.
> Menu wording in Studio 5000 and FactoryTalk View Studio varies slightly
> between releases — if a menu path differs on your install, please correct it
> here in a follow-up PR rather than working around it locally.

---

## Prerequisites

| Requirement | Version / value | Source |
|---|---|---|
| Studio 5000 Logix Designer | v37 or later | `SoftwareRevision="37.00"` in both L5X files |
| Controller platform | ControlLogix **1756-L72** | `ProcessorType` in both L5X files |
| FactoryTalk View SE | **v16** (Studio + Client) | displays declare `Gfx-SE16.xsd` |
| FactoryTalk Linx | Matching SE install | required for the device shortcuts below |

The demo uses **two** controllers — one running the plant simulation, one
running the control logic — connected so that each one's outputs are the
other's inputs.

| Role | Controller name | Project files |
|---|---|---|
| Control logic | `Controller_PLC` | `implementations/rockwell/controller/Controller_PLC.L5X` / `.L5K` |
| Plant simulation | `Simulation_PLC` | `implementations/rockwell/simulator/Simulator_PLC.L5X` / `.L5K` |

> Note the asymmetry: the simulator's *file* is named `Simulator_PLC` but the
> *controller inside it* is named `Simulation_PLC`. Both names appear during
> setup.

### L5X vs L5K — which to use

Both formats contain the same logic; they are alternate export formats, not
different programs.

- **`.L5X` (XML)** — use this for import. It is the standard Studio 5000
  import/export format and is what the steps below assume.
- **`.L5K` (ASCII)** — text format, kept for diff and review in pull requests.
  Importable, but there is no reason to prefer it here.

---

## Part 1 — Import the PLC projects into Studio 5000

Repeat for **both** projects (controller and simulator).

1. Open **Studio 5000 Logix Designer**.
2. Choose **File → Open**, then set the file-type filter to show
   `Logix Designer XML Files (*.L5X)`.
3. Select `Controller_PLC.L5X` (or `Simulator_PLC.L5X`).
4. Studio 5000 converts the L5X into a new `.ACD` project. Choose a working
   directory outside this repository — **do not commit `.ACD` files**, the L5X
   exports are the version-controlled source of truth.
5. Confirm the controller path: **Who Active** → select the target chassis/slot
   for this controller.
6. **Download** the project to the controller and put it in **Run** mode.

Do this for the simulator first, then the controller — the controller reacts to
values the simulator produces.

### If you are re-exporting after changes

Export back to L5X (**File → Save As → L5X**) and commit that file. The `.ACD`
is a local build artifact; the L5X is what other people consume.

---

## Part 2 — Configure the FactoryTalk device shortcuts

**This is the step that most commonly breaks the demo.** The display exports do
not embed controller addresses — they reference two named device shortcuts.
Those shortcut names must match **exactly**, including case, or every animated
object on the displays will fail to resolve its tags.

| Shortcut name | Must point to |
|---|---|
| `HMI_Sphere` | the **`Controller_PLC`** controller |
| `HMI_Simulator` | the **`Simulation_PLC`** controller |

To create them:

1. In **FactoryTalk View Studio**, open (or create) the SE application for this
   demo.
2. Open **FactoryTalk Linx** (or **RSLinx Enterprise** on older installs) →
   **Communication Setup**.
3. Under **Device Shortcuts**, choose **Add** and name the first shortcut
   exactly `HMI_Sphere`.
4. With that shortcut selected, browse the network tree to the ControlLogix
   chassis, select the **`Controller_PLC`** controller, and click **Apply**.
5. Repeat with a second shortcut named exactly `HMI_Simulator`, pointing at the
   **`Simulation_PLC`** controller.
6. **Verify** each shortcut resolves before continuing — the browse tree should
   show the controller online and its tag database should be readable.

---

## Part 3 — Import the HMI displays

The displays live in `implementations/rockwell/hmi/`:

| File | Display | Purpose |
|---|---|---|
| `HMI_Start_Stop.xml` | **Main Display** | Operator controls, tank levels, valve/pump status |
| `Graph.xml` | **Graphs** | Tank levels trended over time |
| `BatchImport_PLC_V2.xml` | — | Batch manifest that imports both displays in one pass |
| `DisplaysExport.txt` | — | Log from the original export; reference only, not imported |

### Option A — batch import (both displays at once)

1. In FactoryTalk View Studio, right-click **Displays** in the Explorer tree and
   choose **Import and Export**.
2. Select **Import graphic information into displays**, then
   **Multiple displays batch import file**.
3. Point it at `BatchImport_PLC_V2.xml`.

`BatchImport_PLC_V2.xml` references the two display files **by bare filename**,
so keep all three files in the same directory when importing, or the batch will
not find them.

### Option B — import each display individually

Run the same **Import and Export** wizard once per display, selecting
**Single display import file** and choosing `HMI_Start_Stop.xml`, then
`Graph.xml`.

---

## Part 4 — Run the demo

1. Confirm both controllers are downloaded and in **Run** mode (Part 1).
2. Open **Main Display** in FactoryTalk View Studio.
3. Click **Run/Test Display** (the play button) — or launch the display from a
   FactoryTalk View SE Client.
4. Press **`Start_Sim`** to start the simulator.
5. Press **`Start_Cont`** to start the controller.

### Operator controls

| Button | Action |
|---|---|
| `Start_Sim` | Start the simulator PLC; process values begin updating |
| `Start_Cont` | Start the controller PLC; control logic begins executing |
| `Stop_Cont` | Stop the controller; state machine transitions to shutdown |
| `RST` | Reset the simulator, tank levels, valves, and process values |

The controller advances through `IDLE → START → RUNNING → SHUTDOWN`.

Expected behaviour: the P1 raw water tank fills to ~800 mm, the transfer valve
and pump open to move water into the P3 ultrafiltration tank, P3 fills to
1000 mm, drains for a random 5–8 s, and the cycle repeats. The Main Display
also has a button that opens the **Graphs** display.

---

## Tag reference

Complete list of PLC tags the displays bind to, extracted from the display
exports. All controller-side tags are verified present in
`Controller_PLC.L5X`, and both simulator-side tags in `Simulator_PLC.L5X`.

### Via the `HMI_Sphere` shortcut → `Controller_PLC`

| Tag | Meaning |
|---|---|
| `P1.RW_Tank_tnk_lvl` | P1 raw water tank level (mm) |
| `P1.RW_Pump_start` | Raw water transfer pump run command |
| `P1.RW_Tank_PR_Valve` | Raw water tank PR valve |
| `P1.RW_Tank_P_Valve` | Raw water tank P valve |
| `P3.Ultrafiltration_UFFT_Tank_tnk_lvl` | P3 ultrafiltration tank level (mm) |
| `P3.Ultrafiltration_UFFT_Tank_Valve_sts` | P3 tank valve status |
| `P1_SYS.IDLE` | State machine — idle |
| `P1_SYS.START` | State machine — starting |
| `P1_SYS.RUNNING` | State machine — running |
| `P1_SYS.SHUTDOWN` | State machine — shutting down |
| `HMI.Start_Active` | Controller start latched from HMI |
| `HMI.Stop_Active` | Controller stop latched from HMI |

### Via the `HMI_Simulator` shortcut → `Simulation_PLC`

| Tag | Type | Meaning |
|---|---|---|
| `Start_ACTIVE` | `BOOL` | Simulator running |
| `RST_ACTIVE` | `BOOL` | Simulator reset asserted |

These are structured tags built on user-defined types carried in the L5X
(`HMI_UDT`, `P1_UDT`, `P2_UDT`, `P3_UDT`, `Phases_UDT`, `System_State_UDT`,
`RW_tank_AL_UDT`, `SYS_MESSAGES`) — importing the L5X creates the UDTs, so no
separate tag database import is needed.

---

## Troubleshooting

**Every animated object shows errors, `####`, or fails to resolve tags.**
Almost always a shortcut-name mismatch. The names must be exactly `HMI_Sphere`
and `HMI_Simulator` (Part 2) — a shortcut named e.g. `HMI_SPHERE` or
`Controller` will not bind.

**Some objects resolve, others do not.**
Likely one of the two shortcuts is configured and the other is not, or the two
are pointed at the same controller. `HMI_Sphere` and `HMI_Simulator` must
target two *different* controllers.

**Batch import cannot find the display files.**
`BatchImport_PLC_V2.xml` references `Graph.xml` and `HMI_Start_Stop.xml` by
bare filename. Keep all three in one directory, or import each display
individually (Part 3, Option B).

**Displays import but values never change.**
Check that both controllers are in **Run** mode, not Program mode, and that
`Start_Sim` was pressed before `Start_Cont` — the controller has nothing to act
on until the simulator is producing values.

**Tank levels move but the process never cycles.**
Confirm the controller project is the current export from this repository. The
scan-time based flow model depends on tags (`dt`, `Fill_rate`, `In_Flow_P3`,
`Out_Flow_P3`) that are not present in older exports of this demo.

---

## Related

- [`../README.md`](../README.md) — use case overview and quick start
- [`../implementations/rockwell/README.md`](../implementations/rockwell/README.md) — Rockwell file inventory and CrossPLC translation
- Known limitations of the demo are listed in the use case README
