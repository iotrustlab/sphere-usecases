(*
 * SPHERE Power Systems - Generic Hydro Station Controller
 * IEC 61131-3 Structured Text for OpenPLC (matiec compatible)
 *
 * Control state machine for hydro power generation:
 *   IDLE -> STARTUP -> RUNNING -> SHUTDOWN -> IDLE
 *                  \-> TRIPPED (on any trip) -> IDLE (after reset)
 *
 * I/O Mapping (configured in OpenPLC web interface):
 *   HMI Inputs:
 *     in_Start_Cmd -> %IX0.0
 *     in_Stop_Cmd -> %IX0.1
 *     in_Reset_Cmd -> %IX0.2
 *     in_Mode_Auto -> %IX0.3
 *     in_Run_Enable -> %IX0.4
 *     in_Power_Setpoint -> %IW60
 *
 *   Process Inputs from Simulator (via bridge):
 *     in_Gate_Pos -> %IW70
 *     in_Res_Level -> %IW71
 *     in_Head -> %IW72
 *     in_Flow -> %IW73
 *     in_Pressure -> %IW74
 *     in_Speed_Pct -> %IW75
 *     in_Freq_Hz -> %IW76
 *     in_Power_MW -> %IW77
 *     in_Breaker_Sts -> %IX2.0
 *     in_Spill_Sts -> %IX2.1
 *
 *   Actuator Outputs to Simulator (via bridge):
 *     out_Gate_Cmd -> %QW100
 *     out_Power_Setpoint -> %QW101
 *     out_Breaker_Cmd -> %QX5.0
 *     out_Spill_Cmd -> %QX5.1
 *
 *   State Outputs to HMI:
 *     out_State_Idle -> %QX7.0
 *     out_State_Startup -> %QX7.1
 *     out_State_Running -> %QX7.2
 *     out_State_Shutdown -> %QX7.3
 *     out_State_Tripped -> %QX7.4
 *     out_Permissives_Ready -> %QX7.5
 *
 *   Trip Outputs:
 *     out_Trip_Overspeed -> %QX8.0
 *     out_Trip_Overpressure -> %QX8.1
 *     out_Trip_LowHead -> %QX8.2
 *     out_Trip_Manual -> %QX8.3
 *
 *   Alarm Outputs:
 *     out_Alarm_GateMismatch -> %QX9.0
 *     out_Alarm_BreakerMismatch -> %QX9.1
 *     out_Alarm_LowLevel -> %QX9.2
 *)

PROGRAM HydroController
  VAR_INPUT
    (* HMI Inputs *)
    in_Start_Cmd : BOOL;              (* Start pushbutton *)
    in_Stop_Cmd : BOOL;               (* Stop pushbutton *)
    in_Reset_Cmd : BOOL;              (* Trip reset pushbutton *)
    in_Mode_Auto : BOOL;              (* Auto mode enable *)
    in_Run_Enable : BOOL;             (* Run permissive *)
    in_Power_Setpoint : INT;          (* 0-1000 = 0-100 MW *)

    (* Process Inputs from Simulator *)
    in_Gate_Pos : INT;                (* Gate position 0-1000 = 0-100% *)
    in_Res_Level : INT;               (* Reservoir level 0-3000 = 0-30.00 m *)
    in_Head : INT;                    (* Head 0-1500 = 0-150.0 m *)
    in_Flow : INT;                    (* Flow 0-1500 = 0-150.0 m3/s *)
    in_Pressure : INT;                (* Pressure kPa *)
    in_Speed_Pct : INT;               (* Speed 0-1500 = 0-150.0% *)
    in_Freq_Hz : INT;                 (* Frequency 5500-6500 = 55-65 Hz *)
    in_Power_MW : INT;                (* Power 0-1000 = 0-100 MW *)
    in_Breaker_Sts : BOOL;            (* Breaker closed status *)
    in_Spill_Sts : BOOL;              (* Spillway open status *)
  END_VAR

  VAR_OUTPUT
    (* Actuator Outputs to Simulator *)
    out_Gate_Cmd : INT;               (* Gate command 0-1000 = 0-100% *)
    out_Power_Setpoint : INT;         (* Power setpoint passthrough *)
    out_Breaker_Cmd : BOOL;           (* Breaker close command *)
    out_Spill_Cmd : BOOL;             (* Spillway open command *)

    (* State Outputs to HMI *)
    out_State_Idle : BOOL;
    out_State_Startup : BOOL;
    out_State_Running : BOOL;
    out_State_Shutdown : BOOL;
    out_State_Tripped : BOOL;
    out_Permissives_Ready : BOOL;

    (* Trip Outputs *)
    out_Trip_Overspeed : BOOL;
    out_Trip_Overpressure : BOOL;
    out_Trip_LowHead : BOOL;
    out_Trip_Manual : BOOL;

    (* Alarm Outputs *)
    out_Alarm_GateMismatch : BOOL;
    out_Alarm_BreakerMismatch : BOOL;
    out_Alarm_LowLevel : BOOL;
  END_VAR

  VAR
    (* State Machine - 0=IDLE, 1=STARTUP, 2=RUNNING, 3=SHUTDOWN, 4=TRIPPED *)
    State : INT := 0;
    STATE_IDLE : INT := 0;
    STATE_STARTUP : INT := 1;
    STATE_RUNNING : INT := 2;
    STATE_SHUTDOWN : INT := 3;
    STATE_TRIPPED : INT := 4;

    (* Permissives *)
    Perm_Level_OK : BOOL := FALSE;
    Perm_Head_OK : BOOL := FALSE;
    Perm_No_Trips : BOOL := FALSE;
    Perm_Run_Enable : BOOL := FALSE;
    All_Permissives : BOOL := FALSE;

    (* Trip Latches *)
    Trip_Overspeed_Latch : BOOL := FALSE;
    Trip_Overpressure_Latch : BOOL := FALSE;
    Trip_LowHead_Latch : BOOL := FALSE;
    Trip_Manual_Latch : BOOL := FALSE;
    Any_Trip : BOOL := FALSE;

    (* Control Parameters *)
    No_Load_Gate_Pct : REAL := 5.0;
    Sync_Speed_Low : REAL := 99.0;
    Sync_Speed_High : REAL := 101.0;
    Min_Power_MW : REAL := 1.0;
    Kp_Gate : REAL := 2.0;
    Gate_Shutdown_Rate : REAL := 5.0;
    Gate_Emerg_Rate : REAL := 20.0;

    (* Trip Thresholds *)
    Overspeed_Trip_Pct : REAL := 110.0;
    Overpressure_Trip_kPa : REAL := 1500.0;
    Min_Head_m : REAL := 10.0;
    Low_Level_m : REAL := 8.0;

    (* Mismatch Alarm Parameters *)
    Gate_Mismatch_Pct : REAL := 5.0;
    Gate_Mismatch_Delay : INT := 50;
    Breaker_Mismatch_Delay : INT := 5;
    Gate_Mismatch_Timer : INT := 0;
    Breaker_Mismatch_Timer : INT := 0;

    (* Process Values (scaled) *)
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

    (* Control Calculations *)
    Power_Error : REAL;
    Gate_Adjustment : REAL;
    Gate_Error : REAL;

    (* Edge Detection *)
    Start_Cmd_Prev : BOOL := FALSE;
    Stop_Cmd_Prev : BOOL := FALSE;
    Reset_Cmd_Prev : BOOL := FALSE;
    Start_Rising : BOOL := FALSE;
    Stop_Rising : BOOL := FALSE;
    Reset_Rising : BOOL := FALSE;
  END_VAR

  (* 1. SCALE INPUTS *)
  Gate_Pos_Pct := INT_TO_REAL(in_Gate_Pos) / 10.0;
  Res_Level_m := INT_TO_REAL(in_Res_Level) / 100.0;
  Head_m := INT_TO_REAL(in_Head) / 10.0;
  Flow_m3s := INT_TO_REAL(in_Flow) / 10.0;
  Pressure_kPa := INT_TO_REAL(in_Pressure);
  Speed_Pct := INT_TO_REAL(in_Speed_Pct) / 10.0;
  Freq_Hz := INT_TO_REAL(in_Freq_Hz) / 100.0;
  Power_MW := INT_TO_REAL(in_Power_MW) / 10.0;
  Power_Setpoint_MW := INT_TO_REAL(in_Power_Setpoint) / 10.0;

  (* 2. EDGE DETECTION FOR COMMANDS *)
  Start_Rising := in_Start_Cmd AND NOT Start_Cmd_Prev;
  Stop_Rising := in_Stop_Cmd AND NOT Stop_Cmd_Prev;
  Reset_Rising := in_Reset_Cmd AND NOT Reset_Cmd_Prev;
  Start_Cmd_Prev := in_Start_Cmd;
  Stop_Cmd_Prev := in_Stop_Cmd;
  Reset_Cmd_Prev := in_Reset_Cmd;

  (* 3. TRIP DETECTION *)
  IF Speed_Pct > Overspeed_Trip_Pct THEN
    Trip_Overspeed_Latch := TRUE;
  END_IF;

  IF Pressure_kPa > Overpressure_Trip_kPa THEN
    Trip_Overpressure_Latch := TRUE;
  END_IF;

  IF Head_m < Min_Head_m AND State = STATE_RUNNING THEN
    Trip_LowHead_Latch := TRUE;
  END_IF;

  Any_Trip := Trip_Overspeed_Latch OR Trip_Overpressure_Latch OR
              Trip_LowHead_Latch OR Trip_Manual_Latch;

  (* 4. PERMISSIVE CHECKS *)
  Perm_Level_OK := Res_Level_m > Low_Level_m;
  Perm_Head_OK := Head_m >= Min_Head_m;
  Perm_No_Trips := NOT Any_Trip;
  Perm_Run_Enable := in_Run_Enable;

  All_Permissives := Perm_Level_OK AND Perm_Head_OK AND
                     Perm_No_Trips AND Perm_Run_Enable;

  (* 5. STATE MACHINE *)
  CASE State OF

    0: (* STATE_IDLE *)
      Gate_Cmd_Pct := 0.0;
      out_Breaker_Cmd := FALSE;
      out_Spill_Cmd := FALSE;

      IF Start_Rising AND All_Permissives THEN
        State := STATE_STARTUP;
      END_IF;

    1: (* STATE_STARTUP *)
      IF Gate_Cmd_Pct < No_Load_Gate_Pct THEN
        Gate_Cmd_Pct := Gate_Cmd_Pct + 1.0;
      ELSE
        Gate_Cmd_Pct := No_Load_Gate_Pct;
      END_IF;

      IF Speed_Pct >= Sync_Speed_Low AND Speed_Pct <= Sync_Speed_High THEN
        out_Breaker_Cmd := TRUE;
        IF in_Breaker_Sts THEN
          State := STATE_RUNNING;
        END_IF;
      END_IF;

      IF Any_Trip THEN
        State := STATE_TRIPPED;
      END_IF;

      IF Stop_Rising THEN
        State := STATE_SHUTDOWN;
      END_IF;

    2: (* STATE_RUNNING *)
      Power_Error := Power_Setpoint_MW - Power_MW;
      Gate_Adjustment := Kp_Gate * Power_Error;
      Gate_Cmd_Pct := Gate_Cmd_Pct + Gate_Adjustment;

      IF Gate_Cmd_Pct < 0.0 THEN
        Gate_Cmd_Pct := 0.0;
      END_IF;
      IF Gate_Cmd_Pct > 100.0 THEN
        Gate_Cmd_Pct := 100.0;
      END_IF;

      out_Breaker_Cmd := TRUE;

      IF Any_Trip THEN
        State := STATE_TRIPPED;
      END_IF;

      IF Stop_Rising THEN
        State := STATE_SHUTDOWN;
      END_IF;

    3: (* STATE_SHUTDOWN *)
      Gate_Cmd_Pct := Gate_Cmd_Pct - Gate_Shutdown_Rate;
      IF Gate_Cmd_Pct < 0.0 THEN
        Gate_Cmd_Pct := 0.0;
      END_IF;

      IF Power_MW < Min_Power_MW THEN
        out_Breaker_Cmd := FALSE;
      END_IF;

      IF Gate_Cmd_Pct <= 0.0 AND NOT in_Breaker_Sts THEN
        State := STATE_IDLE;
      END_IF;

      IF Any_Trip THEN
        State := STATE_TRIPPED;
      END_IF;

    4: (* STATE_TRIPPED *)
      out_Breaker_Cmd := FALSE;

      Gate_Cmd_Pct := Gate_Cmd_Pct - Gate_Emerg_Rate;
      IF Gate_Cmd_Pct < 0.0 THEN
        Gate_Cmd_Pct := 0.0;
      END_IF;

      IF Trip_Overspeed_Latch THEN
        out_Spill_Cmd := TRUE;
      END_IF;

      IF Reset_Rising AND Gate_Cmd_Pct <= 0.0 AND NOT in_Breaker_Sts THEN
        Trip_Overspeed_Latch := FALSE;
        Trip_Overpressure_Latch := FALSE;
        Trip_LowHead_Latch := FALSE;
        Trip_Manual_Latch := FALSE;
        out_Spill_Cmd := FALSE;
        State := STATE_IDLE;
      END_IF;

  END_CASE;

  (* 6. MISMATCH ALARM LOGIC *)
  Gate_Error := Gate_Cmd_Pct - Gate_Pos_Pct;
  IF Gate_Error < 0.0 THEN
    Gate_Error := -Gate_Error;
  END_IF;
  IF Gate_Error > Gate_Mismatch_Pct THEN
    Gate_Mismatch_Timer := Gate_Mismatch_Timer + 1;
    IF Gate_Mismatch_Timer >= Gate_Mismatch_Delay THEN
      out_Alarm_GateMismatch := TRUE;
    END_IF;
  ELSE
    Gate_Mismatch_Timer := 0;
    out_Alarm_GateMismatch := FALSE;
  END_IF;

  IF out_Breaker_Cmd <> in_Breaker_Sts THEN
    Breaker_Mismatch_Timer := Breaker_Mismatch_Timer + 1;
    IF Breaker_Mismatch_Timer >= Breaker_Mismatch_Delay THEN
      out_Alarm_BreakerMismatch := TRUE;
    END_IF;
  ELSE
    Breaker_Mismatch_Timer := 0;
    out_Alarm_BreakerMismatch := FALSE;
  END_IF;

  out_Alarm_LowLevel := Res_Level_m < Low_Level_m;

  (* 7. WRITE OUTPUTS *)
  out_Gate_Cmd := REAL_TO_INT(Gate_Cmd_Pct * 10.0);
  out_Power_Setpoint := in_Power_Setpoint;

  out_State_Idle := (State = STATE_IDLE);
  out_State_Startup := (State = STATE_STARTUP);
  out_State_Running := (State = STATE_RUNNING);
  out_State_Shutdown := (State = STATE_SHUTDOWN);
  out_State_Tripped := (State = STATE_TRIPPED);
  out_Permissives_Ready := All_Permissives;

  out_Trip_Overspeed := Trip_Overspeed_Latch;
  out_Trip_Overpressure := Trip_Overpressure_Latch;
  out_Trip_LowHead := Trip_LowHead_Latch;
  out_Trip_Manual := Trip_Manual_Latch;

END_PROGRAM
