(*
 * Water Distribution UC0 Controller
 * SPHERE CPS Enclave - OpenPLC Implementation
 *
 * IEC 61131-3 Structured Text
 *
 * This controller manages:
 *   - Supply Line: Supply tank level control, pump operation
 *   - Distribution Grid: Elevated tank filling via valve control
 *   - Return Water System: RWS tank level control, pump operation
 *
 * Architecture:
 *   Controller PLC <-> Modbus Bridge <-> Simulator PLC
 *
 * Register Mapping (from openplc_map.yaml):
 *   Input Registers (from Simulator via Bridge):
 *     %IW70: Supply_Tank_Level
 *     %IW71: Supply_Pump_Flow
 *     %IW72: Supply_NaOCl_Level
 *     %IW73: Supply_NH4Cl_Level
 *     %IW74: Grid_Elev_Tank_Level
 *     %IW75: Grid_Consum_Tank_Level
 *     %IW76: RWS_Tank_Level
 *
 *   Discrete Inputs (from Simulator via Bridge):
 *     %IX2.0: Supply_Pump_Sts
 *     %IX2.1: Supply_Mixer_Sts
 *     %IX2.2: Supply_Tank_Valve_Sts
 *     %IX2.3: Grid_Elev_Valve_Sts
 *     %IX2.4: RWS_Pump_Sts
 *     %IX2.5: RWS_Tank_Valve_Sts
 *
 *   Holding Registers (to Simulator via Bridge):
 *     %QW100: Supply_Pump_Speed
 *     %QW101: RWS_Pump_Speed
 *
 *   Coils (to Simulator via Bridge):
 *     %QX5.0 (40): Supply_Tank_Valve
 *     %QX5.1 (41): Grid_Elev_Valve
 *     %QX5.2 (42): RWS_Tank_Valve
 *
 *   System State Coils:
 *     %QX7.0 (56): SYS_IDLE
 *     %QX7.1 (57): SYS_RUNNING
 *
 *   Alarm Coils:
 *     %QX8.0 (64): Alarm_Supply_Tank_HH
 *)

(* =========================================================================
   GLOBAL VARIABLES - I/O Mapping
   ========================================================================= *)

VAR_GLOBAL
    (* --- Analog Inputs (from Simulator) --- *)
    ai_supply_tank_level AT %IW70 : REAL;       (* Supply tank level [mm] *)
    ai_supply_pump_flow AT %IW71 : REAL;        (* Supply pump flow [L/min] *)
    ai_supply_naocl_level AT %IW72 : REAL;      (* NaOCl tank level [mm] *)
    ai_supply_nh4cl_level AT %IW73 : REAL;      (* NH4Cl tank level [mm] *)
    ai_grid_elev_level AT %IW74 : REAL;         (* Elevated tank level [mm] *)
    ai_grid_consum_level AT %IW75 : REAL;       (* Consumer tank level [mm] *)
    ai_rws_tank_level AT %IW76 : REAL;          (* RWS tank level [mm] *)

    (* --- Digital Inputs (from Simulator) --- *)
    di_supply_pump_sts AT %IX2.0 : BOOL;        (* Supply pump running *)
    di_supply_mixer_sts AT %IX2.1 : BOOL;       (* Supply mixer running *)
    di_supply_valve_sts AT %IX2.2 : BOOL;       (* Supply valve open *)
    di_grid_elev_valve_sts AT %IX2.3 : BOOL;    (* Elevated tank valve open *)
    di_rws_pump_sts AT %IX2.4 : BOOL;           (* RWS pump running *)
    di_rws_valve_sts AT %IX2.5 : BOOL;          (* RWS valve open *)

    (* --- Analog Outputs (to Simulator) --- *)
    ao_supply_pump_speed AT %QW100 : REAL;      (* Supply pump speed [%] *)
    ao_rws_pump_speed AT %QW101 : REAL;         (* RWS pump speed [%] *)

    (* --- Digital Outputs (to Simulator) --- *)
    do_supply_valve AT %QX5.0 : BOOL;           (* Supply valve command *)
    do_grid_elev_valve AT %QX5.1 : BOOL;        (* Elevated tank valve command *)
    do_rws_valve AT %QX5.2 : BOOL;              (* RWS valve command *)

    (* --- System State --- *)
    do_sys_idle AT %QX7.0 : BOOL;               (* System idle state *)
    do_sys_running AT %QX7.1 : BOOL;            (* System running state *)

    (* --- Alarms --- *)
    do_alarm_supply_hh AT %QX8.0 : BOOL;        (* Supply tank HH alarm *)

    (* --- HMI Inputs (Coils 0-3 for external control) --- *)
    hmi_start AT %IX0.0 : BOOL;                 (* Start button *)
    hmi_stop AT %IX0.1 : BOOL;                  (* Stop button *)
END_VAR

(* =========================================================================
   TYPE DEFINITIONS
   ========================================================================= *)

TYPE
    (* System State Enumeration *)
    SYS_STATE_TYPE : (
        STATE_IDLE,
        STATE_START,
        STATE_RUNNING,
        STATE_SHUTDOWN
    );
END_TYPE

(* =========================================================================
   PROGRAM VARIABLES
   ========================================================================= *)

VAR
    (* System State Machine *)
    sys_state : SYS_STATE_TYPE := STATE_IDLE;
    permissive_supply_ok : BOOL := FALSE;
    permissive_grid_ok : BOOL := FALSE;
    permissives_ready : BOOL := FALSE;

    (* Control Setpoints *)
    supply_tank_low_sp : REAL := 500.0;         (* Start pump below this [mm] *)
    supply_tank_high_sp : REAL := 1200.0;       (* Stop pump above this [mm] *)
    supply_tank_hh_sp : REAL := 1200.0;         (* HH alarm threshold [mm] *)

    grid_elev_low_sp : REAL := 2000.0;          (* Open valve below this [mm] *)
    grid_elev_high_sp : REAL := 5000.0;         (* Close valve above this [mm] *)

    rws_tank_low_sp : REAL := 300.0;            (* Start pump below this [mm] *)
    rws_tank_high_sp : REAL := 1200.0;          (* Stop pump above this [mm] *)

    (* Pump Speed Setpoints *)
    supply_pump_normal_speed : REAL := 75.0;    (* Normal operating speed [%] *)
    rws_pump_normal_speed : REAL := 50.0;       (* Normal operating speed [%] *)

    (* Internal State *)
    supply_pump_cmd : BOOL := FALSE;
    rws_pump_cmd : BOOL := FALSE;
END_VAR

(* =========================================================================
   MAIN PROGRAM
   ========================================================================= *)

PROGRAM MainProgram

BEGIN
    (* =====================================================================
       STATE MACHINE - System Operating State
       ===================================================================== *)

    CASE sys_state OF

        STATE_IDLE:
            (* System is idle, waiting for start command *)
            do_sys_idle := TRUE;
            do_sys_running := FALSE;

            (* All outputs off in idle *)
            ao_supply_pump_speed := 0.0;
            ao_rws_pump_speed := 0.0;
            do_supply_valve := FALSE;
            do_grid_elev_valve := FALSE;
            do_rws_valve := FALSE;

            (* Transition: Start button pressed *)
            IF hmi_start AND NOT hmi_stop THEN
                sys_state := STATE_START;
            END_IF;

        STATE_START:
            (* Starting up - check permissives *)
            do_sys_idle := FALSE;
            do_sys_running := FALSE;

            (* Check permissives *)
            (* Supply tank has enough water to start *)
            permissive_supply_ok := (ai_supply_tank_level > 300.0);

            (* Elevated tank not overfull *)
            permissive_grid_ok := (ai_grid_elev_level < 5500.0);

            permissives_ready := permissive_supply_ok AND permissive_grid_ok;

            (* Transition: Permissives met -> RUNNING *)
            IF permissives_ready THEN
                sys_state := STATE_RUNNING;
            END_IF;

            (* Transition: Stop pressed -> SHUTDOWN *)
            IF hmi_stop THEN
                sys_state := STATE_SHUTDOWN;
            END_IF;

        STATE_RUNNING:
            (* Normal operation *)
            do_sys_idle := FALSE;
            do_sys_running := TRUE;

            (* =========================================================
               SUPPLY LINE CONTROL
               ========================================================= *)

            (* Level-based pump control *)
            (* Start pump when supply tank is low (drawing from treatment plant) *)
            IF ai_supply_tank_level <= supply_tank_low_sp THEN
                supply_pump_cmd := TRUE;
            ELSIF ai_supply_tank_level >= supply_tank_high_sp THEN
                supply_pump_cmd := FALSE;
            END_IF;

            (* Set pump speed *)
            IF supply_pump_cmd THEN
                ao_supply_pump_speed := supply_pump_normal_speed;
                do_supply_valve := TRUE;  (* Open outlet valve when pumping *)
            ELSE
                ao_supply_pump_speed := 0.0;
                do_supply_valve := FALSE;
            END_IF;

            (* Supply tank HH alarm *)
            IF ai_supply_tank_level >= supply_tank_hh_sp THEN
                do_alarm_supply_hh := TRUE;
            ELSE
                do_alarm_supply_hh := FALSE;
            END_IF;

            (* =========================================================
               DISTRIBUTION GRID CONTROL
               ========================================================= *)

            (* Elevated tank filling via valve control *)
            (* Open valve to fill elevated tank when level is low *)
            IF ai_grid_elev_level <= grid_elev_low_sp THEN
                do_grid_elev_valve := TRUE;
            ELSIF ai_grid_elev_level >= grid_elev_high_sp THEN
                do_grid_elev_valve := FALSE;
            END_IF;

            (* =========================================================
               RETURN WATER SYSTEM CONTROL
               ========================================================= *)

            (* Level-based pump control for RWS *)
            (* Pump returns water back to supply when RWS tank is high *)
            IF ai_rws_tank_level >= rws_tank_high_sp THEN
                rws_pump_cmd := TRUE;
            ELSIF ai_rws_tank_level <= rws_tank_low_sp THEN
                rws_pump_cmd := FALSE;
            END_IF;

            (* Set RWS pump speed *)
            IF rws_pump_cmd THEN
                ao_rws_pump_speed := rws_pump_normal_speed;
                do_rws_valve := TRUE;  (* Open outlet valve when pumping *)
            ELSE
                ao_rws_pump_speed := 0.0;
                do_rws_valve := FALSE;
            END_IF;

            (* =========================================================
               TRANSITION CHECK
               ========================================================= *)

            (* Transition: Stop pressed -> SHUTDOWN *)
            IF hmi_stop THEN
                sys_state := STATE_SHUTDOWN;
            END_IF;

        STATE_SHUTDOWN:
            (* Shutting down - stop all equipment *)
            do_sys_idle := FALSE;
            do_sys_running := FALSE;

            (* Stop all pumps *)
            ao_supply_pump_speed := 0.0;
            ao_rws_pump_speed := 0.0;
            supply_pump_cmd := FALSE;
            rws_pump_cmd := FALSE;

            (* Close all valves *)
            do_supply_valve := FALSE;
            do_grid_elev_valve := FALSE;
            do_rws_valve := FALSE;

            (* Clear alarms *)
            do_alarm_supply_hh := FALSE;

            (* Clear permissives *)
            permissive_supply_ok := FALSE;
            permissive_grid_ok := FALSE;
            permissives_ready := FALSE;

            (* Transition: Stop released -> IDLE *)
            IF NOT hmi_stop THEN
                sys_state := STATE_IDLE;
            END_IF;

    END_CASE;

END_PROGRAM
