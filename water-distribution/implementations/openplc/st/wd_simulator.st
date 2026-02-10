(*
 * Water Distribution UC0 Simulator
 * SPHERE CPS Enclave - OpenPLC Implementation
 *
 * IEC 61131-3 Structured Text (OpenPLC/matiec compatible)
 *
 * This simulator models the physical dynamics of:
 *   - Supply Line: Supply tank, chemical tanks, pump, valves
 *   - Distribution Grid: Elevated tank, consumer tank, valves
 *   - Return Water System: RWS tank, pump, valves
 *
 * Architecture:
 *   Controller PLC <-> Modbus Bridge <-> Simulator PLC (this)
 *
 * I/O Mapping (configured in OpenPLC web interface):
 *   Command Inputs (from Controller via Bridge):
 *     cmd_supply_pump_speed -> %QW200
 *     cmd_rws_pump_speed -> %QW201
 *     cmd_supply_valve -> %QX3.0
 *     cmd_grid_elev_valve -> %QX3.1
 *     cmd_rws_valve -> %QX3.2
 *
 *   Sensor Outputs (to Controller via Bridge):
 *     out_supply_tank_level -> %QW300
 *     out_supply_pump_flow -> %QW301
 *     out_supply_naocl_level -> %QW302
 *     out_supply_nh4cl_level -> %QW303
 *     out_grid_elev_level -> %QW304
 *     out_grid_consum_level -> %QW305
 *     out_rws_tank_level -> %QW306
 *
 *   Status Outputs (to Controller via Bridge):
 *     out_supply_pump_sts -> %QX40.0
 *     out_supply_mixer_sts -> %QX40.1
 *     out_supply_valve_sts -> %QX40.2
 *     out_grid_elev_valve_sts -> %QX40.3
 *     out_rws_pump_sts -> %QX40.4
 *     out_rws_valve_sts -> %QX40.5
 *)

PROGRAM MainProgram
  VAR_INPUT
    (* Command Inputs from Controller via Bridge *)
    cmd_supply_pump_speed : REAL;     (* Supply pump speed cmd [%] *)
    cmd_rws_pump_speed : REAL;        (* RWS pump speed cmd [%] *)
    cmd_supply_valve : BOOL;          (* Supply valve command *)
    cmd_grid_elev_valve : BOOL;       (* Elevated tank valve cmd *)
    cmd_rws_valve : BOOL;             (* RWS valve command *)
  END_VAR

  VAR_OUTPUT
    (* Sensor Outputs to Controller via Bridge *)
    out_supply_tank_level : REAL;     (* Supply tank level [mm] *)
    out_supply_pump_flow : REAL;      (* Supply pump flow [L/min] *)
    out_supply_naocl_level : REAL;    (* NaOCl tank level [mm] *)
    out_supply_nh4cl_level : REAL;    (* NH4Cl tank level [mm] *)
    out_grid_elev_level : REAL;       (* Elevated tank level [mm] *)
    out_grid_consum_level : REAL;     (* Consumer tank level [mm] *)
    out_rws_tank_level : REAL;        (* RWS tank level [mm] *)

    (* Status Outputs to Controller via Bridge *)
    out_supply_pump_sts : BOOL;       (* Supply pump running *)
    out_supply_mixer_sts : BOOL;      (* Supply mixer running *)
    out_supply_valve_sts : BOOL;      (* Supply valve open *)
    out_grid_elev_valve_sts : BOOL;   (* Elevated tank valve open *)
    out_rws_pump_sts : BOOL;          (* RWS pump running *)
    out_rws_valve_sts : BOOL;         (* RWS valve open *)
  END_VAR

  VAR
    (* Simulation Constants - Timing *)
    DT_SEC : REAL := 0.1;                       (* Simulation timestep [s] *)
    MOTORIZED_VALVE_DELAY : INT := 600;         (* 60s at 100ms scan *)
    PUMP_SPINUP_DELAY : INT := 20;              (* 2s at 100ms scan *)

    (* Physical parameters - Supply *)
    SUPPLY_TANK_AREA_M2 : REAL := 40.0;
    SUPPLY_TANK_MAX_MM : REAL := 1500.0;
    SUPPLY_INFLOW_LPM : REAL := 150.0;
    SUPPLY_PUMP_MAX_LPM : REAL := 200.0;

    (* Physical parameters - Chemical tanks *)
    NAOCL_TANK_AREA_M2 : REAL := 0.1;
    NAOCL_DOSE_LPM : REAL := 0.038;
    NH4CL_TANK_AREA_M2 : REAL := 0.1;
    NH4CL_DOSE_LPM : REAL := 0.019;

    (* Physical parameters - Grid *)
    ELEV_TANK_AREA_M2 : REAL := 60.0;
    ELEV_TANK_MAX_MM : REAL := 2000.0;
    CONSUM_TANK_AREA_M2 : REAL := 10.0;
    CONSUM_TANK_MAX_MM : REAL := 2000.0;
    GRID_DEMAND_LPM : REAL := 100.0;
    ELEV_DRAIN_LPM : REAL := 300.0;

    (* Physical parameters - RWS *)
    RWS_TANK_AREA_M2 : REAL := 0.3;
    RWS_TANK_MAX_MM : REAL := 1500.0;
    RWS_PUMP_MAX_LPM : REAL := 38.0;
    RETURN_FRACTION : REAL := 0.9;

    (* Tank levels [mm] *)
    supply_tank_level : REAL := 1000.0;
    naocl_tank_level : REAL := 800.0;
    nh4cl_tank_level : REAL := 800.0;
    grid_elev_level : REAL := 1200.0;
    grid_consum_level : REAL := 1000.0;
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
    mixer_running : BOOL := TRUE;

    (* Temporary calculation variables *)
    delta_level : REAL := 0.0;
    flow_in : REAL := 0.0;
    flow_out : REAL := 0.0;
  END_VAR

  (* =====================================================================
     VALVE DELAY MODELING
     ===================================================================== *)

  (* Supply Tank Valve *)
  IF cmd_supply_valve AND NOT supply_valve_state THEN
    supply_valve_timer := supply_valve_timer + 1;
    IF supply_valve_timer >= MOTORIZED_VALVE_DELAY THEN
      supply_valve_state := TRUE;
      supply_valve_timer := MOTORIZED_VALVE_DELAY;
    END_IF;
  ELSIF NOT cmd_supply_valve AND supply_valve_state THEN
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
     ===================================================================== *)

  (* Supply Pump *)
  IF cmd_supply_pump_speed > 0.0 THEN
    IF NOT supply_pump_state THEN
      supply_pump_timer := supply_pump_timer + 1;
      IF supply_pump_timer >= PUMP_SPINUP_DELAY THEN
        supply_pump_state := TRUE;
      END_IF;
    END_IF;
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

  IF supply_pump_state AND supply_valve_state THEN
    supply_pump_flow := (supply_pump_actual_speed / 100.0) * SUPPLY_PUMP_MAX_LPM;
  ELSE
    supply_pump_flow := 0.0;
  END_IF;

  IF rws_pump_state AND rws_valve_state THEN
    rws_pump_flow := (rws_pump_actual_speed / 100.0) * RWS_PUMP_MAX_LPM;
  ELSE
    rws_pump_flow := 0.0;
  END_IF;

  grid_demand_actual := GRID_DEMAND_LPM;
  return_flow := grid_demand_actual * RETURN_FRACTION;

  (* =====================================================================
     MASS BALANCE CALCULATIONS
     ===================================================================== *)

  (* Supply Tank Mass Balance *)
  flow_in := SUPPLY_INFLOW_LPM + rws_pump_flow;
  flow_out := supply_pump_flow;
  delta_level := ((flow_in - flow_out) / SUPPLY_TANK_AREA_M2) * DT_SEC / 60.0 * 1000.0;
  supply_tank_level := supply_tank_level + delta_level;

  IF supply_tank_level < 0.0 THEN
    supply_tank_level := 0.0;
  ELSIF supply_tank_level > SUPPLY_TANK_MAX_MM THEN
    supply_tank_level := SUPPLY_TANK_MAX_MM;
  END_IF;

  (* Chemical Tank Drain *)
  IF supply_pump_state THEN
    delta_level := (NAOCL_DOSE_LPM / NAOCL_TANK_AREA_M2) * DT_SEC / 60.0 * 1000.0;
    naocl_tank_level := naocl_tank_level - delta_level;
    IF naocl_tank_level < 0.0 THEN
      naocl_tank_level := 0.0;
    END_IF;

    delta_level := (NH4CL_DOSE_LPM / NH4CL_TANK_AREA_M2) * DT_SEC / 60.0 * 1000.0;
    nh4cl_tank_level := nh4cl_tank_level - delta_level;
    IF nh4cl_tank_level < 0.0 THEN
      nh4cl_tank_level := 0.0;
    END_IF;
  END_IF;

  (* Elevated Tank Mass Balance *)
  IF grid_elev_valve_state THEN
    flow_in := supply_pump_flow;
  ELSE
    flow_in := 0.0;
  END_IF;
  flow_out := ELEV_DRAIN_LPM;
  delta_level := ((flow_in - flow_out) / ELEV_TANK_AREA_M2) * DT_SEC / 60.0 * 1000.0;
  grid_elev_level := grid_elev_level + delta_level;

  IF grid_elev_level < 0.0 THEN
    grid_elev_level := 0.0;
  ELSIF grid_elev_level > ELEV_TANK_MAX_MM THEN
    grid_elev_level := ELEV_TANK_MAX_MM;
  END_IF;

  (* Consumer Tank Mass Balance *)
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

  out_supply_tank_level := supply_tank_level;
  out_supply_pump_flow := supply_pump_flow;
  out_supply_naocl_level := naocl_tank_level;
  out_supply_nh4cl_level := nh4cl_tank_level;
  out_grid_elev_level := grid_elev_level;
  out_grid_consum_level := grid_consum_level;
  out_rws_tank_level := rws_tank_level;

  out_supply_pump_sts := supply_pump_state;
  out_supply_mixer_sts := mixer_running;
  out_supply_valve_sts := supply_valve_state;
  out_grid_elev_valve_sts := grid_elev_valve_state;
  out_rws_pump_sts := rws_pump_state;
  out_rws_valve_sts := rws_valve_state;

END_PROGRAM
