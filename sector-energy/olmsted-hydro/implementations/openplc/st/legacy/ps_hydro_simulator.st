(*
 * SPHERE Power Systems - Generic Hydro Station Simulator
 * IEC 61131-3 Structured Text for OpenPLC
 *
 * Physics model for hydro power generation:
 *   Reservoir -> Penstock -> Wicket Gate -> Turbine -> Generator -> Breaker -> Grid
 *
 * This program runs on the SIMULATOR PLC and models:
 *   - Reservoir mass balance with head calculation
 *   - Penstock flow dynamics (1st-order lag)
 *   - Wicket gate actuator with slew limits
 *   - Turbine/generator power conversion
 *   - Breaker dynamics
 *   - Trip condition detection
 *
 * Inputs (from Controller via bridge):
 *   - Gate command (%IW200)
 *   - Breaker command (%IX3.0)
 *   - Spill command (%IX3.1)
 *
 * Outputs (to Controller via bridge):
 *   - Gate position (%QW300)
 *   - Reservoir level, head, flow, pressure, speed, freq, power (%QW301-307)
 *   - Breaker status, spill status (%QX40.0-40.1)
 *)

(* ═══════════════════════════════════════════════════════════════════════════
   GLOBAL VARIABLES - I/O MAPPING
   ═══════════════════════════════════════════════════════════════════════════ *)
VAR_GLOBAL
    (* Inputs from Controller (via bridge) *)
    in_Gate_Cmd AT %IW200 : INT;        (* Gate command 0-1000 = 0-100% *)
    in_Breaker_Cmd AT %IX3.0 : BOOL;    (* Breaker close command *)
    in_Spill_Cmd AT %IX3.1 : BOOL;      (* Spillway open command *)

    (* Outputs to Controller (via bridge) *)
    out_Gate_Pos AT %QW300 : INT;       (* Gate position 0-1000 = 0-100% *)
    out_Res_Level AT %QW301 : INT;      (* Reservoir level 0-3000 = 0-30.00 m *)
    out_Head AT %QW302 : INT;           (* Head 0-1500 = 0-150.0 m *)
    out_Flow AT %QW303 : INT;           (* Flow 0-1500 = 0-150.0 m3/s *)
    out_Pressure AT %QW304 : INT;       (* Pressure 0-2000 kPa *)
    out_Speed_Pct AT %QW305 : INT;      (* Speed 0-1500 = 0-150.0% *)
    out_Freq_Hz AT %QW306 : INT;        (* Frequency 5500-6500 = 55.00-65.00 Hz *)
    out_Power_MW AT %QW307 : INT;       (* Power 0-1000 = 0-100.0 MW *)

    out_Breaker_Sts AT %QX40.0 : BOOL;  (* Breaker closed status *)
    out_Spill_Sts AT %QX40.1 : BOOL;    (* Spillway open status *)
END_VAR

(* ═══════════════════════════════════════════════════════════════════════════
   MAIN PROGRAM
   ═══════════════════════════════════════════════════════════════════════════ *)
PROGRAM HydroSimulator
VAR
    (* ─── Physical Parameters (from profile) ─────────────────────────────── *)
    (* Reservoir *)
    Res_Area_m2 : REAL := 10000.0;      (* Reservoir surface area *)
    Res_Level_m : REAL := 20.0;         (* Current reservoir level *)
    Res_Inflow_m3s : REAL := 50.0;      (* Natural inflow *)
    Res_Min_m : REAL := 5.0;            (* Minimum operating level *)
    Res_Max_m : REAL := 25.0;           (* Maximum level *)
    Tailwater_m : REAL := 0.0;          (* Tailwater elevation *)

    (* Penstock *)
    Penstock_Tau_sec : REAL := 5.0;     (* Flow inertia time constant *)
    Static_Head_m : REAL := 100.0;      (* Reference static head *)

    (* Turbine *)
    Q_Max_m3s : REAL := 100.0;          (* Maximum flow capacity *)
    Eta_Turbine : REAL := 0.90;         (* Turbine efficiency *)
    K_Q : REAL := 10.0;                 (* Flow coefficient *)

    (* Generator *)
    Eta_Gen : REAL := 0.97;             (* Generator efficiency *)
    P_Rated_MW : REAL := 80.0;          (* Rated power *)
    Inertia_H : REAL := 4.0;            (* Inertia constant (seconds) *)
    Sync_Speed_Pct : REAL := 100.0;     (* Synchronous speed reference *)

    (* Gate actuator *)
    Gate_Travel_sec : REAL := 10.0;     (* Full stroke time *)
    Gate_Slew_Max : REAL := 10.0;       (* Max slew rate %/s *)
    Gate_Tau_sec : REAL := 1.0;         (* Servo time constant *)
    Gate_Emerg_sec : REAL := 3.0;       (* Emergency close time *)

    (* Breaker *)
    Breaker_Open_sec : REAL := 0.06;    (* Open time *)
    Breaker_Close_sec : REAL := 0.05;   (* Close time *)

    (* Spillway *)
    Spill_Open_sec : REAL := 5.0;       (* Spillway open time *)

    (* Physical constants *)
    RHO : REAL := 1000.0;               (* Water density kg/m3 *)
    G : REAL := 9.81;                   (* Gravity m/s2 *)

    (* ─── State Variables ────────────────────────────────────────────────── *)
    Gate_Pos_Pct : REAL := 0.0;         (* Actual gate position % *)
    Gate_Vel : REAL := 0.0;             (* Gate velocity %/s *)
    Flow_m3s : REAL := 0.0;             (* Actual flow rate *)
    Flow_Target_m3s : REAL := 0.0;      (* Target flow (gate opening) *)
    Head_m : REAL := 100.0;             (* Net hydraulic head *)
    Pressure_kPa : REAL := 981.0;       (* Penstock pressure *)
    Speed_Pct : REAL := 0.0;            (* Turbine speed % of sync *)
    Freq_Hz : REAL := 0.0;              (* Electrical frequency *)
    P_Mech_MW : REAL := 0.0;            (* Mechanical power *)
    P_Elec_MW : REAL := 0.0;            (* Electrical power *)

    Breaker_Closed : BOOL := FALSE;     (* Breaker state *)
    Breaker_Timer : REAL := 0.0;        (* Breaker transition timer *)
    Spill_Open : BOOL := FALSE;         (* Spillway state *)
    Spill_Timer : REAL := 0.0;          (* Spillway transition timer *)

    (* ─── Intermediate Calculations ──────────────────────────────────────── *)
    Gate_Cmd_Pct : REAL;                (* Commanded gate position % *)
    Gate_Error : REAL;                  (* Gate position error *)
    dQ_dt : REAL;                       (* Flow rate of change *)
    dLevel_dt : REAL;                   (* Level rate of change *)
    dSpeed_dt : REAL;                   (* Speed rate of change *)
    P_Load_MW : REAL;                   (* Grid load (when connected) *)
    Spill_Flow_m3s : REAL;              (* Spillway discharge *)

    (* ─── Timing ─────────────────────────────────────────────────────────── *)
    DT : REAL := 0.1;                   (* Simulation timestep (100ms) *)

    (* ─── Trip Detection ─────────────────────────────────────────────────── *)
    Overspeed : BOOL := FALSE;
    Overpressure : BOOL := FALSE;
    LowHead : BOOL := FALSE;
END_VAR

(* ═══════════════════════════════════════════════════════════════════════════
   SIMULATION LOGIC
   ═══════════════════════════════════════════════════════════════════════════ *)

(* ─── 1. PROCESS INPUTS ───────────────────────────────────────────────────── *)
(* Convert scaled integer inputs to engineering units *)
Gate_Cmd_Pct := INT_TO_REAL(in_Gate_Cmd) / 10.0;  (* 0-1000 -> 0-100% *)

(* Clamp command to valid range *)
IF Gate_Cmd_Pct < 0.0 THEN Gate_Cmd_Pct := 0.0; END_IF;
IF Gate_Cmd_Pct > 100.0 THEN Gate_Cmd_Pct := 100.0; END_IF;

(* ─── 2. GATE ACTUATOR DYNAMICS ───────────────────────────────────────────── *)
(* First-order servo response with slew limiting *)
Gate_Error := Gate_Cmd_Pct - Gate_Pos_Pct;
Gate_Vel := Gate_Error / Gate_Tau_sec;

(* Apply slew rate limits *)
IF Gate_Vel > Gate_Slew_Max THEN
    Gate_Vel := Gate_Slew_Max;
ELSIF Gate_Vel < -Gate_Slew_Max THEN
    Gate_Vel := -Gate_Slew_Max;
END_IF;

(* Integrate gate position *)
Gate_Pos_Pct := Gate_Pos_Pct + Gate_Vel * DT;

(* Clamp to physical limits *)
IF Gate_Pos_Pct < 0.0 THEN Gate_Pos_Pct := 0.0; END_IF;
IF Gate_Pos_Pct > 100.0 THEN Gate_Pos_Pct := 100.0; END_IF;

(* ─── 3. RESERVOIR MASS BALANCE ───────────────────────────────────────────── *)
(* Calculate spillway flow if open *)
IF Spill_Open THEN
    (* Simple spillway model: proportional to level above threshold *)
    IF Res_Level_m > 22.0 THEN
        Spill_Flow_m3s := 20.0 * (Res_Level_m - 22.0);
    ELSE
        Spill_Flow_m3s := 0.0;
    END_IF;
ELSE
    Spill_Flow_m3s := 0.0;
END_IF;

(* Mass balance: dV/dt = Q_in - Q_turbine - Q_spill *)
dLevel_dt := (Res_Inflow_m3s - Flow_m3s - Spill_Flow_m3s) / Res_Area_m2;
Res_Level_m := Res_Level_m + dLevel_dt * DT;

(* Clamp reservoir level *)
IF Res_Level_m < 0.0 THEN Res_Level_m := 0.0; END_IF;
IF Res_Level_m > Res_Max_m THEN Res_Level_m := Res_Max_m; END_IF;

(* Calculate net head: H = reservoir_level - tailwater *)
Head_m := Res_Level_m + Static_Head_m - Tailwater_m;
IF Head_m < 0.0 THEN Head_m := 0.0; END_IF;

(* ─── 4. PENSTOCK FLOW DYNAMICS ───────────────────────────────────────────── *)
(* Target flow based on gate opening and head *)
(* Q = k_q * (gate_pos/100) * sqrt(H) *)
IF Head_m > 0.0 THEN
    Flow_Target_m3s := K_Q * (Gate_Pos_Pct / 100.0) * SQRT(Head_m);
ELSE
    Flow_Target_m3s := 0.0;
END_IF;

(* Limit to maximum flow *)
IF Flow_Target_m3s > Q_Max_m3s THEN
    Flow_Target_m3s := Q_Max_m3s;
END_IF;

(* First-order lag for flow inertia: dQ/dt = (Q_target - Q) / tau *)
dQ_dt := (Flow_Target_m3s - Flow_m3s) / Penstock_Tau_sec;
Flow_m3s := Flow_m3s + dQ_dt * DT;

(* Clamp flow *)
IF Flow_m3s < 0.0 THEN Flow_m3s := 0.0; END_IF;

(* Calculate penstock pressure: P = rho * g * H *)
Pressure_kPa := RHO * G * Head_m / 1000.0;

(* Check for water hammer (rapid flow change) *)
IF ABS(dQ_dt) > 20.0 THEN
    (* Approximate pressure surge *)
    Pressure_kPa := Pressure_kPa * 1.5;
END_IF;

(* ─── 5. TURBINE/GENERATOR DYNAMICS ───────────────────────────────────────── *)
(* Mechanical power: P_mech = rho * g * Q * H * eta_t *)
P_Mech_MW := RHO * G * Flow_m3s * Head_m * Eta_Turbine / 1000000.0;

(* Speed dynamics depend on breaker state *)
IF Breaker_Closed THEN
    (* Connected to grid - speed locked to sync *)
    Speed_Pct := 100.0;
    Freq_Hz := 60.0;

    (* Electrical power = min(mechanical power * eta_g, rated) *)
    P_Elec_MW := P_Mech_MW * Eta_Gen;
    IF P_Elec_MW > P_Rated_MW THEN
        P_Elec_MW := P_Rated_MW;
    END_IF;
ELSE
    (* Offline - speed determined by turbine power vs losses *)
    (* Simplified: speed rises with flow, falls with friction *)
    IF Flow_m3s > 0.1 THEN
        (* Accelerating: dSpeed/dt proportional to (torque - friction) *)
        dSpeed_dt := (P_Mech_MW / (P_Rated_MW * 0.1) - Speed_Pct / 50.0) / Inertia_H;
        Speed_Pct := Speed_Pct + dSpeed_dt * DT;
    ELSE
        (* Decelerating: coast down *)
        dSpeed_dt := -Speed_Pct / (Inertia_H * 10.0);
        Speed_Pct := Speed_Pct + dSpeed_dt * DT;
    END_IF;

    (* Clamp speed *)
    IF Speed_Pct < 0.0 THEN Speed_Pct := 0.0; END_IF;
    IF Speed_Pct > 150.0 THEN Speed_Pct := 150.0; END_IF;

    (* Frequency proportional to speed *)
    Freq_Hz := 60.0 * Speed_Pct / 100.0;

    (* No electrical power when offline *)
    P_Elec_MW := 0.0;
END_IF;

(* ─── 6. BREAKER DYNAMICS ─────────────────────────────────────────────────── *)
IF in_Breaker_Cmd AND NOT Breaker_Closed THEN
    (* Close command received - start closing *)
    Breaker_Timer := Breaker_Timer + DT;
    IF Breaker_Timer >= Breaker_Close_sec THEN
        (* Check sync conditions before closing *)
        IF Speed_Pct >= 99.0 AND Speed_Pct <= 101.0 THEN
            Breaker_Closed := TRUE;
        END_IF;
        Breaker_Timer := 0.0;
    END_IF;
ELSIF NOT in_Breaker_Cmd AND Breaker_Closed THEN
    (* Open command received - start opening *)
    Breaker_Timer := Breaker_Timer + DT;
    IF Breaker_Timer >= Breaker_Open_sec THEN
        Breaker_Closed := FALSE;
        Breaker_Timer := 0.0;
    END_IF;
ELSE
    Breaker_Timer := 0.0;
END_IF;

(* ─── 7. SPILLWAY DYNAMICS ────────────────────────────────────────────────── *)
IF in_Spill_Cmd AND NOT Spill_Open THEN
    Spill_Timer := Spill_Timer + DT;
    IF Spill_Timer >= Spill_Open_sec THEN
        Spill_Open := TRUE;
        Spill_Timer := 0.0;
    END_IF;
ELSIF NOT in_Spill_Cmd AND Spill_Open THEN
    Spill_Timer := Spill_Timer + DT;
    IF Spill_Timer >= Spill_Open_sec THEN
        Spill_Open := FALSE;
        Spill_Timer := 0.0;
    END_IF;
ELSE
    Spill_Timer := 0.0;
END_IF;

(* ─── 8. TRIP CONDITION DETECTION ─────────────────────────────────────────── *)
(* These are informational - actual trip logic is in controller *)
Overspeed := Speed_Pct > 110.0;
Overpressure := Pressure_kPa > (RHO * G * Static_Head_m / 1000.0) * 1.5;
LowHead := Head_m < 10.0;

(* ─── 9. WRITE OUTPUTS ────────────────────────────────────────────────────── *)
(* Convert engineering units to scaled integers for Modbus *)
out_Gate_Pos := REAL_TO_INT(Gate_Pos_Pct * 10.0);           (* 0-100% -> 0-1000 *)
out_Res_Level := REAL_TO_INT(Res_Level_m * 100.0);          (* 0-30m -> 0-3000 *)
out_Head := REAL_TO_INT(Head_m * 10.0);                     (* 0-150m -> 0-1500 *)
out_Flow := REAL_TO_INT(Flow_m3s * 10.0);                   (* 0-150m3/s -> 0-1500 *)
out_Pressure := REAL_TO_INT(Pressure_kPa);                  (* kPa direct *)
out_Speed_Pct := REAL_TO_INT(Speed_Pct * 10.0);             (* 0-150% -> 0-1500 *)
out_Freq_Hz := REAL_TO_INT(Freq_Hz * 100.0);                (* 55-65Hz -> 5500-6500 *)
out_Power_MW := REAL_TO_INT(P_Elec_MW * 10.0);              (* 0-100MW -> 0-1000 *)

out_Breaker_Sts := Breaker_Closed;
out_Spill_Sts := Spill_Open;

END_PROGRAM
