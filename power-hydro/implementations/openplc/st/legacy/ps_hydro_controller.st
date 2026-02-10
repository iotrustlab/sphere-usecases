(*
 * SPHERE Power Systems - Generic Hydro Station Controller
 * IEC 61131-3 Structured Text for OpenPLC
 *
 * Control state machine for hydro power generation:
 *   IDLE -> STARTUP -> RUNNING -> SHUTDOWN -> IDLE
 *                  \-> TRIPPED (on any trip) -> IDLE (after reset)
 *
 * This program runs on the CONTROLLER PLC and implements:
 *   - State machine for unit operation
 *   - Permissive checks for startup
 *   - Power tracking via gate modulation (P-control)
 *   - Trip detection and response
 *   - Mismatch alarm generation
 *
 * Inputs (from HMI):
 *   - Start, Stop, Reset commands (%IX0.0-0.2)
 *   - Mode Auto, Run Enable (%IX0.3-0.4)
 *
 * Inputs (from Simulator via bridge):
 *   - Gate position, sensors (%IW70-77)
 *   - Breaker/Spill status (%IX2.0-2.1)
 *
 * Outputs (to Simulator via bridge):
 *   - Gate command (%QW100)
 *   - Breaker/Spill commands (%QX5.0-5.1)
 *
 * Outputs (to HMI):
 *   - State indicators (%QX7.0-7.5)
 *   - Trip indicators (%QX8.0-8.3)
 *   - Alarm indicators (%QX9.0-9.2)
 *)

(* ═══════════════════════════════════════════════════════════════════════════
   GLOBAL VARIABLES - I/O MAPPING
   ═══════════════════════════════════════════════════════════════════════════ *)
VAR_GLOBAL
    (* HMI Inputs *)
    in_Start_Cmd AT %IX0.0 : BOOL;      (* Start pushbutton *)
    in_Stop_Cmd AT %IX0.1 : BOOL;       (* Stop pushbutton *)
    in_Reset_Cmd AT %IX0.2 : BOOL;      (* Trip reset pushbutton *)
    in_Mode_Auto AT %IX0.3 : BOOL;      (* Auto mode enable *)
    in_Run_Enable AT %IX0.4 : BOOL;     (* Run permissive *)

    (* Power setpoint - could come from HMI or external *)
    in_Power_Setpoint AT %IW60 : INT;   (* 0-1000 = 0-100 MW *)

    (* Process Inputs from Simulator (via bridge) *)
    in_Gate_Pos AT %IW70 : INT;         (* Gate position 0-1000 = 0-100% *)
    in_Res_Level AT %IW71 : INT;        (* Reservoir level 0-3000 = 0-30.00 m *)
    in_Head AT %IW72 : INT;             (* Head 0-1500 = 0-150.0 m *)
    in_Flow AT %IW73 : INT;             (* Flow 0-1500 = 0-150.0 m3/s *)
    in_Pressure AT %IW74 : INT;         (* Pressure kPa *)
    in_Speed_Pct AT %IW75 : INT;        (* Speed 0-1500 = 0-150.0% *)
    in_Freq_Hz AT %IW76 : INT;          (* Frequency 5500-6500 = 55-65 Hz *)
    in_Power_MW AT %IW77 : INT;         (* Power 0-1000 = 0-100 MW *)

    in_Breaker_Sts AT %IX2.0 : BOOL;    (* Breaker closed status *)
    in_Spill_Sts AT %IX2.1 : BOOL;      (* Spillway open status *)

    (* Actuator Outputs to Simulator (via bridge) *)
    out_Gate_Cmd AT %QW100 : INT;       (* Gate command 0-1000 = 0-100% *)
    out_Power_Setpoint AT %QW101 : INT; (* Power setpoint passthrough *)
    out_Breaker_Cmd AT %QX5.0 : BOOL;   (* Breaker close command *)
    out_Spill_Cmd AT %QX5.1 : BOOL;     (* Spillway open command *)

    (* State Outputs to HMI *)
    out_State_Idle AT %QX7.0 : BOOL;
    out_State_Startup AT %QX7.1 : BOOL;
    out_State_Running AT %QX7.2 : BOOL;
    out_State_Shutdown AT %QX7.3 : BOOL;
    out_State_Tripped AT %QX7.4 : BOOL;
    out_Permissives_Ready AT %QX7.5 : BOOL;

    (* Trip Outputs *)
    out_Trip_Overspeed AT %QX8.0 : BOOL;
    out_Trip_Overpressure AT %QX8.1 : BOOL;
    out_Trip_LowHead AT %QX8.2 : BOOL;
    out_Trip_Manual AT %QX8.3 : BOOL;

    (* Alarm Outputs *)
    out_Alarm_GateMismatch AT %QX9.0 : BOOL;
    out_Alarm_BreakerMismatch AT %QX9.1 : BOOL;
    out_Alarm_LowLevel AT %QX9.2 : BOOL;
END_VAR

(* ═══════════════════════════════════════════════════════════════════════════
   MAIN PROGRAM
   ═══════════════════════════════════════════════════════════════════════════ *)
PROGRAM HydroController
VAR
    (* ─── State Machine ──────────────────────────────────────────────────── *)
    State : INT := 0;                   (* 0=IDLE, 1=STARTUP, 2=RUNNING, 3=SHUTDOWN, 4=TRIPPED *)
    STATE_IDLE : INT := 0;
    STATE_STARTUP : INT := 1;
    STATE_RUNNING : INT := 2;
    STATE_SHUTDOWN : INT := 3;
    STATE_TRIPPED : INT := 4;

    (* ─── Permissives ────────────────────────────────────────────────────── *)
    Perm_Level_OK : BOOL := FALSE;      (* Reservoir level adequate *)
    Perm_Head_OK : BOOL := FALSE;       (* Head above minimum *)
    Perm_No_Trips : BOOL := FALSE;      (* No active trips *)
    Perm_Run_Enable : BOOL := FALSE;    (* Operator run enable *)
    All_Permissives : BOOL := FALSE;    (* Combined permissive *)

    (* ─── Trip Latches ───────────────────────────────────────────────────── *)
    Trip_Overspeed_Latch : BOOL := FALSE;
    Trip_Overpressure_Latch : BOOL := FALSE;
    Trip_LowHead_Latch : BOOL := FALSE;
    Trip_Manual_Latch : BOOL := FALSE;
    Any_Trip : BOOL := FALSE;

    (* ─── Control Parameters ─────────────────────────────────────────────── *)
    No_Load_Gate_Pct : REAL := 5.0;     (* Gate position for no-load sync *)
    Sync_Speed_Low : REAL := 99.0;      (* Min speed for sync % *)
    Sync_Speed_High : REAL := 101.0;    (* Max speed for sync % *)
    Min_Power_MW : REAL := 1.0;         (* Min power before breaker open *)
    Kp_Gate : REAL := 2.0;              (* Power control gain *)
    Gate_Shutdown_Rate : REAL := 5.0;   (* %/sample during shutdown *)
    Gate_Emerg_Rate : REAL := 20.0;     (* %/sample during trip *)

    (* ─── Trip Thresholds ────────────────────────────────────────────────── *)
    Overspeed_Trip_Pct : REAL := 110.0;
    Overpressure_Trip_kPa : REAL := 1500.0;
    Min_Head_m : REAL := 10.0;
    Low_Level_m : REAL := 8.0;          (* Alarm threshold *)

    (* ─── Mismatch Alarm Parameters ──────────────────────────────────────── *)
    Gate_Mismatch_Pct : REAL := 5.0;    (* Alarm if error > 5% *)
    Gate_Mismatch_Delay : INT := 50;    (* 5 sec at 100ms cycle *)
    Breaker_Mismatch_Delay : INT := 5;  (* 0.5 sec *)
    Gate_Mismatch_Timer : INT := 0;
    Breaker_Mismatch_Timer : INT := 0;

    (* ─── Process Values (scaled) ────────────────────────────────────────── *)
    Gate_Pos_Pct : REAL;
    Gate_Cmd_Pct : REAL := 0.0;
    Res_Level_m : REAL;
    Head_m : REAL;
    Flow_m3s : REAL;
    Pressure_kPa : REAL;
    Speed_Pct : REAL;
    Freq_Hz : REAL;
    Power_MW : REAL;
    Power_Setpoint_MW : REAL;

    (* ─── Control Calculations ───────────────────────────────────────────── *)
    Power_Error : REAL;
    Gate_Adjustment : REAL;

    (* ─── Edge Detection ─────────────────────────────────────────────────── *)
    Start_Cmd_Prev : BOOL := FALSE;
    Stop_Cmd_Prev : BOOL := FALSE;
    Reset_Cmd_Prev : BOOL := FALSE;
    Start_Rising : BOOL := FALSE;
    Stop_Rising : BOOL := FALSE;
    Reset_Rising : BOOL := FALSE;
END_VAR

(* ═══════════════════════════════════════════════════════════════════════════
   CONTROL LOGIC
   ═══════════════════════════════════════════════════════════════════════════ *)

(* ─── 1. SCALE INPUTS ─────────────────────────────────────────────────────── *)
Gate_Pos_Pct := INT_TO_REAL(in_Gate_Pos) / 10.0;
Res_Level_m := INT_TO_REAL(in_Res_Level) / 100.0;
Head_m := INT_TO_REAL(in_Head) / 10.0;
Flow_m3s := INT_TO_REAL(in_Flow) / 10.0;
Pressure_kPa := INT_TO_REAL(in_Pressure);
Speed_Pct := INT_TO_REAL(in_Speed_Pct) / 10.0;
Freq_Hz := INT_TO_REAL(in_Freq_Hz) / 100.0;
Power_MW := INT_TO_REAL(in_Power_MW) / 10.0;
Power_Setpoint_MW := INT_TO_REAL(in_Power_Setpoint) / 10.0;

(* ─── 2. EDGE DETECTION FOR COMMANDS ──────────────────────────────────────── *)
Start_Rising := in_Start_Cmd AND NOT Start_Cmd_Prev;
Stop_Rising := in_Stop_Cmd AND NOT Stop_Cmd_Prev;
Reset_Rising := in_Reset_Cmd AND NOT Reset_Cmd_Prev;
Start_Cmd_Prev := in_Start_Cmd;
Stop_Cmd_Prev := in_Stop_Cmd;
Reset_Cmd_Prev := in_Reset_Cmd;

(* ─── 3. TRIP DETECTION ───────────────────────────────────────────────────── *)
(* Check trip conditions and latch *)
IF Speed_Pct > Overspeed_Trip_Pct THEN
    Trip_Overspeed_Latch := TRUE;
END_IF;

IF Pressure_kPa > Overpressure_Trip_kPa THEN
    Trip_Overpressure_Latch := TRUE;
END_IF;

IF Head_m < Min_Head_m AND State = STATE_RUNNING THEN
    Trip_LowHead_Latch := TRUE;
END_IF;

(* Manual trip via Stop during running with specific pattern *)
(* For now, no separate manual trip - Stop just initiates shutdown *)

(* Combined trip check *)
Any_Trip := Trip_Overspeed_Latch OR Trip_Overpressure_Latch OR
            Trip_LowHead_Latch OR Trip_Manual_Latch;

(* ─── 4. PERMISSIVE CHECKS ────────────────────────────────────────────────── *)
Perm_Level_OK := Res_Level_m > Low_Level_m;
Perm_Head_OK := Head_m >= Min_Head_m;
Perm_No_Trips := NOT Any_Trip;
Perm_Run_Enable := in_Run_Enable;

All_Permissives := Perm_Level_OK AND Perm_Head_OK AND
                   Perm_No_Trips AND Perm_Run_Enable;

(* ─── 5. STATE MACHINE ────────────────────────────────────────────────────── *)
CASE State OF
    (* ═══ IDLE STATE ═══ *)
    0: (* STATE_IDLE *)
        (* Outputs: gate closed, breaker open *)
        Gate_Cmd_Pct := 0.0;
        out_Breaker_Cmd := FALSE;
        out_Spill_Cmd := FALSE;

        (* Transitions *)
        IF Start_Rising AND All_Permissives THEN
            State := STATE_STARTUP;
        END_IF;

    (* ═══ STARTUP STATE ═══ *)
    1: (* STATE_STARTUP *)
        (* Ramp gate to no-load position *)
        IF Gate_Cmd_Pct < No_Load_Gate_Pct THEN
            Gate_Cmd_Pct := Gate_Cmd_Pct + 1.0;  (* Ramp up 1%/cycle *)
        ELSE
            Gate_Cmd_Pct := No_Load_Gate_Pct;
        END_IF;

        (* Check for sync conditions *)
        IF Speed_Pct >= Sync_Speed_Low AND Speed_Pct <= Sync_Speed_High THEN
            (* Close breaker when speed is in sync range *)
            out_Breaker_Cmd := TRUE;

            (* Transition to running when breaker closes *)
            IF in_Breaker_Sts THEN
                State := STATE_RUNNING;
            END_IF;
        END_IF;

        (* Trip handling *)
        IF Any_Trip THEN
            State := STATE_TRIPPED;
        END_IF;

        (* Stop command *)
        IF Stop_Rising THEN
            State := STATE_SHUTDOWN;
        END_IF;

    (* ═══ RUNNING STATE ═══ *)
    2: (* STATE_RUNNING *)
        (* Power tracking via P-control *)
        Power_Error := Power_Setpoint_MW - Power_MW;
        Gate_Adjustment := Kp_Gate * Power_Error;

        (* Apply adjustment with limits *)
        Gate_Cmd_Pct := Gate_Cmd_Pct + Gate_Adjustment;

        (* Clamp gate command *)
        IF Gate_Cmd_Pct < 0.0 THEN Gate_Cmd_Pct := 0.0; END_IF;
        IF Gate_Cmd_Pct > 100.0 THEN Gate_Cmd_Pct := 100.0; END_IF;

        (* Breaker stays closed *)
        out_Breaker_Cmd := TRUE;

        (* Trip handling - immediate transition *)
        IF Any_Trip THEN
            State := STATE_TRIPPED;
        END_IF;

        (* Stop command - normal shutdown *)
        IF Stop_Rising THEN
            State := STATE_SHUTDOWN;
        END_IF;

    (* ═══ SHUTDOWN STATE ═══ *)
    3: (* STATE_SHUTDOWN *)
        (* Ramp gate down *)
        Gate_Cmd_Pct := Gate_Cmd_Pct - Gate_Shutdown_Rate;
        IF Gate_Cmd_Pct < 0.0 THEN
            Gate_Cmd_Pct := 0.0;
        END_IF;

        (* Open breaker when power is low enough *)
        IF Power_MW < Min_Power_MW THEN
            out_Breaker_Cmd := FALSE;
        END_IF;

        (* Transition to idle when gate closed and breaker open *)
        IF Gate_Cmd_Pct <= 0.0 AND NOT in_Breaker_Sts THEN
            State := STATE_IDLE;
        END_IF;

        (* Trip can still occur during shutdown *)
        IF Any_Trip THEN
            State := STATE_TRIPPED;
        END_IF;

    (* ═══ TRIPPED STATE ═══ *)
    4: (* STATE_TRIPPED *)
        (* Emergency actions *)
        out_Breaker_Cmd := FALSE;           (* Open breaker immediately *)

        (* Fast gate close *)
        Gate_Cmd_Pct := Gate_Cmd_Pct - Gate_Emerg_Rate;
        IF Gate_Cmd_Pct < 0.0 THEN
            Gate_Cmd_Pct := 0.0;
        END_IF;

        (* Open spillway on overspeed to dump water *)
        IF Trip_Overspeed_Latch THEN
            out_Spill_Cmd := TRUE;
        END_IF;

        (* Reset handling - only when gate closed and breaker open *)
        IF Reset_Rising AND Gate_Cmd_Pct <= 0.0 AND NOT in_Breaker_Sts THEN
            (* Clear all trip latches *)
            Trip_Overspeed_Latch := FALSE;
            Trip_Overpressure_Latch := FALSE;
            Trip_LowHead_Latch := FALSE;
            Trip_Manual_Latch := FALSE;

            (* Close spillway *)
            out_Spill_Cmd := FALSE;

            (* Return to idle *)
            State := STATE_IDLE;
        END_IF;

END_CASE;

(* ─── 6. MISMATCH ALARM LOGIC ─────────────────────────────────────────────── *)
(* Gate mismatch alarm *)
IF ABS(Gate_Cmd_Pct - Gate_Pos_Pct) > Gate_Mismatch_Pct THEN
    Gate_Mismatch_Timer := Gate_Mismatch_Timer + 1;
    IF Gate_Mismatch_Timer >= Gate_Mismatch_Delay THEN
        out_Alarm_GateMismatch := TRUE;
    END_IF;
ELSE
    Gate_Mismatch_Timer := 0;
    out_Alarm_GateMismatch := FALSE;
END_IF;

(* Breaker mismatch alarm *)
IF out_Breaker_Cmd <> in_Breaker_Sts THEN
    Breaker_Mismatch_Timer := Breaker_Mismatch_Timer + 1;
    IF Breaker_Mismatch_Timer >= Breaker_Mismatch_Delay THEN
        out_Alarm_BreakerMismatch := TRUE;
    END_IF;
ELSE
    Breaker_Mismatch_Timer := 0;
    out_Alarm_BreakerMismatch := FALSE;
END_IF;

(* Low level alarm *)
out_Alarm_LowLevel := Res_Level_m < Low_Level_m;

(* ─── 7. WRITE OUTPUTS ────────────────────────────────────────────────────── *)
(* Scale and write gate command *)
out_Gate_Cmd := REAL_TO_INT(Gate_Cmd_Pct * 10.0);

(* Pass through power setpoint *)
out_Power_Setpoint := in_Power_Setpoint;

(* State indicators *)
out_State_Idle := (State = STATE_IDLE);
out_State_Startup := (State = STATE_STARTUP);
out_State_Running := (State = STATE_RUNNING);
out_State_Shutdown := (State = STATE_SHUTDOWN);
out_State_Tripped := (State = STATE_TRIPPED);
out_Permissives_Ready := All_Permissives;

(* Trip indicators *)
out_Trip_Overspeed := Trip_Overspeed_Latch;
out_Trip_Overpressure := Trip_Overpressure_Latch;
out_Trip_LowHead := Trip_LowHead_Latch;
out_Trip_Manual := Trip_Manual_Latch;

END_PROGRAM
