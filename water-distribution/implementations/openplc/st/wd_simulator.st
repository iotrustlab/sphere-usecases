(*
 * Water Distribution UC0 Simulator
 * SPHERE CPS Enclave - OpenPLC Implementation
 *
 * IEC 61131-3 Structured Text
 *
 * This simulator models the physical dynamics of:
 *   - Supply Line: Supply tank, chemical tanks, pump, valves
 *   - Distribution Grid: Elevated tank, consumer tank, valves
 *   - Return Water System: RWS tank, pump, valves
 *
 * Architecture:
 *   Controller PLC <-> Modbus Bridge <-> Simulator PLC (this)
 *
 * The simulator:
 *   - Receives commands from controller via bridge
 *   - Models physical processes (mass balance, delays)
 *   - Outputs sensor values to controller via bridge
 *
 * Register Mapping (from openplc_map.yaml):
 *   Holding Registers (Commands from Controller via Bridge):
 *     %IW200: Supply_Pump_Speed command
 *     %IW201: RWS_Pump_Speed command
 *     %IX3.0: Supply_Tank_Valve command
 *     %IX3.1: Grid_Elev_Valve command
 *     %IX3.2: RWS_Tank_Valve command
 *
 *   Holding Registers (Sensor outputs to Controller via Bridge):
 *     %QW300: Supply_Tank_Level
 *     %QW301: Supply_Pump_Flow
 *     %QW302: Supply_NaOCl_Level
 *     %QW303: Supply_NH4Cl_Level
 *     %QW304: Grid_Elev_Tank_Level
 *     %QW305: Grid_Consum_Tank_Level
 *     %QW306: RWS_Tank_Level
 *
 *   Coils (Status outputs to Controller via Bridge):
 *     %QX40.0: Supply_Pump_Sts
 *     %QX40.1: Supply_Mixer_Sts
 *     %QX40.2: Supply_Tank_Valve_Sts
 *     %QX40.3: Grid_Elev_Valve_Sts
 *     %QX40.4: RWS_Pump_Sts
 *     %QX40.5: RWS_Tank_Valve_Sts
 *)

(* =========================================================================
   GLOBAL VARIABLES - I/O Mapping
   ========================================================================= *)

VAR_GLOBAL
    (* --- Command Inputs (from Controller via Bridge) --- *)
    cmd_supply_pump_speed AT %IW200 : REAL;     (* Supply pump speed cmd [%] *)
    cmd_rws_pump_speed AT %IW201 : REAL;        (* RWS pump speed cmd [%] *)
    cmd_supply_valve AT %IX3.0 : BOOL;          (* Supply valve command *)
    cmd_grid_elev_valve AT %IX3.1 : BOOL;       (* Elevated tank valve cmd *)
    cmd_rws_valve AT %IX3.2 : BOOL;             (* RWS valve command *)

    (* --- Sensor Outputs (to Controller via Bridge) --- *)
    out_supply_tank_level AT %QW300 : REAL;     (* Supply tank level [mm] *)
    out_supply_pump_flow AT %QW301 : REAL;      (* Supply pump flow [L/min] *)
    out_supply_naocl_level AT %QW302 : REAL;    (* NaOCl tank level [mm] *)
    out_supply_nh4cl_level AT %QW303 : REAL;    (* NH4Cl tank level [mm] *)
    out_grid_elev_level AT %QW304 : REAL;       (* Elevated tank level [mm] *)
    out_grid_consum_level AT %QW305 : REAL;     (* Consumer tank level [mm] *)
    out_rws_tank_level AT %QW306 : REAL;        (* RWS tank level [mm] *)

    (* --- Status Outputs (to Controller via Bridge) --- *)
    out_supply_pump_sts AT %QX40.0 : BOOL;      (* Supply pump running *)
    out_supply_mixer_sts AT %QX40.1 : BOOL;     (* Supply mixer running *)
    out_supply_valve_sts AT %QX40.2 : BOOL;     (* Supply valve open *)
    out_grid_elev_valve_sts AT %QX40.3 : BOOL;  (* Elevated tank valve open *)
    out_rws_pump_sts AT %QX40.4 : BOOL;         (* RWS pump running *)
    out_rws_valve_sts AT %QX40.5 : BOOL;        (* RWS valve open *)
END_VAR

(* =========================================================================
   SIMULATION PARAMETERS
   ========================================================================= *)

VAR CONSTANT
    (* Timing constants (in scan cycles, assuming 100ms scan) *)
    DT_SEC : REAL := 0.1;                       (* Simulation timestep [s] *)

    (* Valve delays (in cycles) *)
    MOTORIZED_VALVE_DELAY : INT := 600;         (* 60s at 100ms scan *)
    PUMP_SPINUP_DELAY : INT := 20;              (* 2s at 100ms scan *)

    (* Physical parameters - Supply *)
    SUPPLY_TANK_AREA_M2 : REAL := 40.0;         (* Tank cross-section [m²] *)
    SUPPLY_TANK_MAX_MM : REAL := 1500.0;        (* Max level [mm] *)
    SUPPLY_INFLOW_LPM : REAL := 150.0;          (* Inflow from treatment [L/min] *)
    SUPPLY_PUMP_MAX_LPM : REAL := 380.0;        (* Max pump flow [L/min] *)

    (* Physical parameters - Chemical tanks *)
    NAOCL_TANK_AREA_M2 : REAL := 0.1;           (* Tank cross-section [m²] *)
    NAOCL_DOSE_LPM : REAL := 0.038;             (* Dosing rate [L/min] *)
    NH4CL_TANK_AREA_M2 : REAL := 0.1;
    NH4CL_DOSE_LPM : REAL := 0.019;

    (* Physical parameters - Grid *)
    ELEV_TANK_AREA_M2 : REAL := 60.0;           (* Tank cross-section [m²] *)
    ELEV_TANK_MAX_MM : REAL := 6000.0;          (* Max level [mm] *)
    CONSUM_TANK_AREA_M2 : REAL := 10.0;         (* Tank cross-section [m²] *)
    CONSUM_TANK_MAX_MM : REAL := 4000.0;        (* Max level [mm] *)
    GRID_DEMAND_LPM : REAL := 100.0;            (* Base grid demand [L/min] *)
    ELEV_DRAIN_LPM : REAL := 300.0;             (* Gravity drain rate [L/min] *)

    (* Physical parameters - RWS *)
    RWS_TANK_AREA_M2 : REAL := 0.3;             (* Tank cross-section [m²] *)
    RWS_TANK_MAX_MM : REAL := 1500.0;           (* Max level [mm] *)
    RWS_PUMP_MAX_LPM : REAL := 38.0;            (* Max pump flow [L/min] *)
    RETURN_FRACTION : REAL := 0.9;              (* Fraction of demand returned *)
END_VAR

(* =========================================================================
   SIMULATION STATE VARIABLES
   ========================================================================= *)

VAR
    (* Tank levels [mm] *)
    supply_tank_level : REAL := 1000.0;
    naocl_tank_level : REAL := 800.0;
    nh4cl_tank_level : REAL := 800.0;
    grid_elev_level : REAL := 4000.0;
    grid_consum_level : REAL := 3000.0;
    rws_tank_level : REAL := 500.0;

    (* Valve states with delay modeling *)
    supply_valve_timer : INT := 0;
    supply_valve_state : BOOL := FALSE;
    grid_elev_valve_timer : INT := 0;
    grid_elev_valve_state : BOOL := FALSE;
    rws_valve_timer : INT := 0;
    rws_valve_state : BOOL := FALSE;

    (* Pump states with delay modeling *)
    supply_pump_timer : INT := 0;
    supply_pump_state : BOOL := FALSE;
    supply_pump_actual_speed : REAL := 0.0;
    rws_pump_timer : INT := 0;
    rws_pump_state : BOOL := FALSE;
    rws_pump_actual_speed : REAL := 0.0;

    (* Flow rates [L/min] *)
    supply_pump_flow : REAL := 0.0;
    rws_pump_flow : REAL := 0.0;
    grid_demand_actual : REAL := 0.0;
    return_flow : REAL := 0.0;

    (* Mixer state *)
    mixer_running : BOOL := TRUE;               (* Always on when system running *)

    (* Temporary calculation variables *)
    delta_level : REAL := 0.0;
    flow_in : REAL := 0.0;
    flow_out : REAL := 0.0;
END_VAR

(* =========================================================================
   MAIN PROGRAM
   ========================================================================= *)

PROGRAM MainProgram

BEGIN
    (* =====================================================================
       VALVE DELAY MODELING
       Model motorized valve opening/closing with time constant
       ===================================================================== *)

    (* Supply Tank Valve *)
    IF cmd_supply_valve AND NOT supply_valve_state THEN
        (* Opening *)
        supply_valve_timer := supply_valve_timer + 1;
        IF supply_valve_timer >= MOTORIZED_VALVE_DELAY THEN
            supply_valve_state := TRUE;
            supply_valve_timer := MOTORIZED_VALVE_DELAY;
        END_IF;
    ELSIF NOT cmd_supply_valve AND supply_valve_state THEN
        (* Closing *)
        supply_valve_timer := supply_valve_timer - 1;
        IF supply_valve_timer <= 0 THEN
            supply_valve_state := FALSE;
            supply_valve_timer := 0;
        END_IF;
    ELSIF cmd_supply_valve AND supply_valve_state THEN
        supply_valve_timer := MOTORIZED_VALVE_DELAY;
    ELSE
        supply_valve_timer := 0;
    END_IF;

    (* Grid Elevated Tank Valve *)
    IF cmd_grid_elev_valve AND NOT grid_elev_valve_state THEN
        grid_elev_valve_timer := grid_elev_valve_timer + 1;
        IF grid_elev_valve_timer >= MOTORIZED_VALVE_DELAY THEN
            grid_elev_valve_state := TRUE;
            grid_elev_valve_timer := MOTORIZED_VALVE_DELAY;
        END_IF;
    ELSIF NOT cmd_grid_elev_valve AND grid_elev_valve_state THEN
        grid_elev_valve_timer := grid_elev_valve_timer - 1;
        IF grid_elev_valve_timer <= 0 THEN
            grid_elev_valve_state := FALSE;
            grid_elev_valve_timer := 0;
        END_IF;
    ELSIF cmd_grid_elev_valve AND grid_elev_valve_state THEN
        grid_elev_valve_timer := MOTORIZED_VALVE_DELAY;
    ELSE
        grid_elev_valve_timer := 0;
    END_IF;

    (* RWS Tank Valve *)
    IF cmd_rws_valve AND NOT rws_valve_state THEN
        rws_valve_timer := rws_valve_timer + 1;
        IF rws_valve_timer >= MOTORIZED_VALVE_DELAY THEN
            rws_valve_state := TRUE;
            rws_valve_timer := MOTORIZED_VALVE_DELAY;
        END_IF;
    ELSIF NOT cmd_rws_valve AND rws_valve_state THEN
        rws_valve_timer := rws_valve_timer - 1;
        IF rws_valve_timer <= 0 THEN
            rws_valve_state := FALSE;
            rws_valve_timer := 0;
        END_IF;
    ELSIF cmd_rws_valve AND rws_valve_state THEN
        rws_valve_timer := MOTORIZED_VALVE_DELAY;
    ELSE
        rws_valve_timer := 0;
    END_IF;

    (* =====================================================================
       PUMP DELAY MODELING
       Model pump spinup with time constant
       ===================================================================== *)

    (* Supply Pump *)
    IF cmd_supply_pump_speed > 0.0 THEN
        IF NOT supply_pump_state THEN
            supply_pump_timer := supply_pump_timer + 1;
            IF supply_pump_timer >= PUMP_SPINUP_DELAY THEN
                supply_pump_state := TRUE;
            END_IF;
        END_IF;
        (* Ramp speed to command *)
        IF supply_pump_state THEN
            IF supply_pump_actual_speed < cmd_supply_pump_speed THEN
                supply_pump_actual_speed := supply_pump_actual_speed + 1.0;
                IF supply_pump_actual_speed > cmd_supply_pump_speed THEN
                    supply_pump_actual_speed := cmd_supply_pump_speed;
                END_IF;
            ELSIF supply_pump_actual_speed > cmd_supply_pump_speed THEN
                supply_pump_actual_speed := supply_pump_actual_speed - 1.0;
                IF supply_pump_actual_speed < cmd_supply_pump_speed THEN
                    supply_pump_actual_speed := cmd_supply_pump_speed;
                END_IF;
            END_IF;
        END_IF;
    ELSE
        (* Pump stopping *)
        supply_pump_timer := 0;
        supply_pump_state := FALSE;
        supply_pump_actual_speed := 0.0;
    END_IF;

    (* RWS Pump *)
    IF cmd_rws_pump_speed > 0.0 THEN
        IF NOT rws_pump_state THEN
            rws_pump_timer := rws_pump_timer + 1;
            IF rws_pump_timer >= PUMP_SPINUP_DELAY THEN
                rws_pump_state := TRUE;
            END_IF;
        END_IF;
        (* Ramp speed to command *)
        IF rws_pump_state THEN
            IF rws_pump_actual_speed < cmd_rws_pump_speed THEN
                rws_pump_actual_speed := rws_pump_actual_speed + 1.0;
                IF rws_pump_actual_speed > cmd_rws_pump_speed THEN
                    rws_pump_actual_speed := cmd_rws_pump_speed;
                END_IF;
            ELSIF rws_pump_actual_speed > cmd_rws_pump_speed THEN
                rws_pump_actual_speed := rws_pump_actual_speed - 1.0;
                IF rws_pump_actual_speed < cmd_rws_pump_speed THEN
                    rws_pump_actual_speed := cmd_rws_pump_speed;
                END_IF;
            END_IF;
        END_IF;
    ELSE
        rws_pump_timer := 0;
        rws_pump_state := FALSE;
        rws_pump_actual_speed := 0.0;
    END_IF;

    (* =====================================================================
       FLOW CALCULATIONS
       ===================================================================== *)

    (* Supply pump flow: only flows if pump running AND valve open *)
    IF supply_pump_state AND supply_valve_state THEN
        supply_pump_flow := (supply_pump_actual_speed / 100.0) * SUPPLY_PUMP_MAX_LPM;
    ELSE
        supply_pump_flow := 0.0;
    END_IF;

    (* RWS pump flow: only flows if pump running AND valve open *)
    IF rws_pump_state AND rws_valve_state THEN
        rws_pump_flow := (rws_pump_actual_speed / 100.0) * RWS_PUMP_MAX_LPM;
    ELSE
        rws_pump_flow := 0.0;
    END_IF;

    (* Grid demand: base demand (simplified model) *)
    grid_demand_actual := GRID_DEMAND_LPM;

    (* Return flow: fraction of demand goes to RWS *)
    return_flow := grid_demand_actual * RETURN_FRACTION;

    (* =====================================================================
       MASS BALANCE CALCULATIONS
       dL/dt = (Q_in - Q_out) / A * (1000 mm/m)
       ===================================================================== *)

    (* Supply Tank Mass Balance *)
    (* Inflow: from treatment plant + RWS return *)
    (* Outflow: to supply pump *)
    flow_in := SUPPLY_INFLOW_LPM + rws_pump_flow;
    flow_out := supply_pump_flow;
    delta_level := ((flow_in - flow_out) / SUPPLY_TANK_AREA_M2) * DT_SEC / 60.0 * 1000.0;
    supply_tank_level := supply_tank_level + delta_level;

    (* Clamp to physical limits *)
    IF supply_tank_level < 0.0 THEN
        supply_tank_level := 0.0;
    ELSIF supply_tank_level > SUPPLY_TANK_MAX_MM THEN
        supply_tank_level := SUPPLY_TANK_MAX_MM;
    END_IF;

    (* Chemical Tank Drain (when pump is running, chemicals are dosed) *)
    IF supply_pump_state THEN
        (* NaOCl drain *)
        delta_level := (NAOCL_DOSE_LPM / NAOCL_TANK_AREA_M2) * DT_SEC / 60.0 * 1000.0;
        naocl_tank_level := naocl_tank_level - delta_level;
        IF naocl_tank_level < 0.0 THEN
            naocl_tank_level := 0.0;
        END_IF;

        (* NH4Cl drain *)
        delta_level := (NH4CL_DOSE_LPM / NH4CL_TANK_AREA_M2) * DT_SEC / 60.0 * 1000.0;
        nh4cl_tank_level := nh4cl_tank_level - delta_level;
        IF nh4cl_tank_level < 0.0 THEN
            nh4cl_tank_level := 0.0;
        END_IF;
    END_IF;

    (* Elevated Tank Mass Balance *)
    (* Inflow: from supply pump (when elev valve is open) *)
    (* Outflow: gravity drain to consumer tank *)
    IF grid_elev_valve_state THEN
        flow_in := supply_pump_flow;
    ELSE
        flow_in := 0.0;
    END_IF;
    flow_out := ELEV_DRAIN_LPM;  (* Continuous gravity drain to maintain pressure *)
    delta_level := ((flow_in - flow_out) / ELEV_TANK_AREA_M2) * DT_SEC / 60.0 * 1000.0;
    grid_elev_level := grid_elev_level + delta_level;

    IF grid_elev_level < 0.0 THEN
        grid_elev_level := 0.0;
    ELSIF grid_elev_level > ELEV_TANK_MAX_MM THEN
        grid_elev_level := ELEV_TANK_MAX_MM;
    END_IF;

    (* Consumer Tank Mass Balance *)
    (* Inflow: from elevated tank (gravity) *)
    (* Outflow: grid demand *)
    flow_in := ELEV_DRAIN_LPM;
    flow_out := grid_demand_actual;
    delta_level := ((flow_in - flow_out) / CONSUM_TANK_AREA_M2) * DT_SEC / 60.0 * 1000.0;
    grid_consum_level := grid_consum_level + delta_level;

    IF grid_consum_level < 0.0 THEN
        grid_consum_level := 0.0;
    ELSIF grid_consum_level > CONSUM_TANK_MAX_MM THEN
        grid_consum_level := CONSUM_TANK_MAX_MM;
    END_IF;

    (* RWS Tank Mass Balance *)
    (* Inflow: return flow from grid *)
    (* Outflow: RWS pump back to supply *)
    flow_in := return_flow;
    flow_out := rws_pump_flow;
    delta_level := ((flow_in - flow_out) / RWS_TANK_AREA_M2) * DT_SEC / 60.0 * 1000.0;
    rws_tank_level := rws_tank_level + delta_level;

    IF rws_tank_level < 0.0 THEN
        rws_tank_level := 0.0;
    ELSIF rws_tank_level > RWS_TANK_MAX_MM THEN
        rws_tank_level := RWS_TANK_MAX_MM;
    END_IF;

    (* =====================================================================
       OUTPUT UPDATES
       ===================================================================== *)

    (* Sensor outputs *)
    out_supply_tank_level := supply_tank_level;
    out_supply_pump_flow := supply_pump_flow;
    out_supply_naocl_level := naocl_tank_level;
    out_supply_nh4cl_level := nh4cl_tank_level;
    out_grid_elev_level := grid_elev_level;
    out_grid_consum_level := grid_consum_level;
    out_rws_tank_level := rws_tank_level;

    (* Status outputs *)
    out_supply_pump_sts := supply_pump_state;
    out_supply_mixer_sts := mixer_running;
    out_supply_valve_sts := supply_valve_state;
    out_grid_elev_valve_sts := grid_elev_valve_state;
    out_rws_pump_sts := rws_pump_state;
    out_rws_valve_sts := rws_valve_state;

END_PROGRAM
