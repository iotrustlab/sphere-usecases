(*
 * SPHERE Power Systems - Generic Hydro Station Simulator
 * IEC 61131-3 Structured Text for OpenPLC (matiec compatible)
 *
 * Physics model for hydro power generation:
 *   Reservoir -> Penstock -> Wicket Gate -> Turbine -> Generator -> Breaker -> Grid
 *
 * I/O Mapping (configured in OpenPLC web interface):
 *   Inputs from Controller (via bridge):
 *     in_Gate_Cmd -> %IW200
 *     in_Breaker_Cmd -> %IX3.0
 *     in_Spill_Cmd -> %IX3.1
 *
 *   Outputs to Controller (via bridge):
 *     out_Gate_Pos -> %QW300
 *     out_Res_Level -> %QW301
 *     out_Head -> %QW302
 *     out_Flow -> %QW303
 *     out_Pressure -> %QW304
 *     out_Speed_Pct -> %QW305
 *     out_Freq_Hz -> %QW306
 *     out_Power_MW -> %QW307
 *     out_Breaker_Sts -> %QX40.0
 *     out_Spill_Sts -> %QX40.1
 *)

PROGRAM HydroSimulator
  VAR_INPUT
    (* Inputs from Controller via bridge *)
    in_Gate_Cmd : INT;                (* Gate command 0-1000 = 0-100% *)
    in_Breaker_Cmd : BOOL;            (* Breaker close command *)
    in_Spill_Cmd : BOOL;              (* Spillway open command *)
  END_VAR

  VAR_OUTPUT
    (* Outputs to Controller via bridge *)
    out_Gate_Pos : INT;               (* Gate position 0-1000 = 0-100% *)
    out_Res_Level : INT;              (* Reservoir level 0-3000 = 0-30.00 m *)
    out_Head : INT;                   (* Head 0-1500 = 0-150.0 m *)
    out_Flow : INT;                   (* Flow 0-1500 = 0-150.0 m3/s *)
    out_Pressure : INT;               (* Pressure 0-2000 kPa *)
    out_Speed_Pct : INT;              (* Speed 0-1500 = 0-150.0% *)
    out_Freq_Hz : INT;                (* Frequency 5500-6500 = 55.00-65.00 Hz *)
    out_Power_MW : INT;               (* Power 0-1000 = 0-100.0 MW *)
    out_Breaker_Sts : BOOL;           (* Breaker closed status *)
    out_Spill_Sts : BOOL;             (* Spillway open status *)
  END_VAR

  VAR
    (* Physical Parameters *)
    Res_Area_m2 : REAL := 10000.0;
    Res_Level_m : REAL := 20.0;
    Res_Inflow_m3s : REAL := 50.0;
    Res_Min_m : REAL := 5.0;
    Res_Max_m : REAL := 25.0;
    Tailwater_m : REAL := 0.0;

    Penstock_Tau_sec : REAL := 5.0;
    Static_Head_m : REAL := 100.0;

    Q_Max_m3s : REAL := 100.0;
    Eta_Turbine : REAL := 0.90;
    K_Q : REAL := 10.0;

    Eta_Gen : REAL := 0.97;
    P_Rated_MW : REAL := 80.0;
    Inertia_H : REAL := 4.0;
    Sync_Speed_Pct : REAL := 100.0;

    Gate_Travel_sec : REAL := 10.0;
    Gate_Slew_Max : REAL := 10.0;
    Gate_Tau_sec : REAL := 1.0;
    Gate_Emerg_sec : REAL := 3.0;

    Breaker_Open_sec : REAL := 0.06;
    Breaker_Close_sec : REAL := 0.05;
    Spill_Open_sec : REAL := 5.0;

    RHO : REAL := 1000.0;
    G : REAL := 9.81;

    (* State Variables *)
    Gate_Pos_Pct : REAL := 0.0;
    Gate_Vel : REAL := 0.0;
    Flow_m3s : REAL := 0.0;
    Flow_Target_m3s : REAL := 0.0;
    Head_m : REAL := 100.0;
    Pressure_kPa : REAL := 981.0;
    Speed_Pct : REAL := 0.0;
    Freq_Hz : REAL := 0.0;
    P_Mech_MW : REAL := 0.0;
    P_Elec_MW : REAL := 0.0;

    Breaker_Closed : BOOL := FALSE;
    Breaker_Timer : REAL := 0.0;
    Spill_Open : BOOL := FALSE;
    Spill_Timer : REAL := 0.0;

    (* Intermediate Calculations *)
    Gate_Cmd_Pct : REAL;
    Gate_Error : REAL;
    dQ_dt : REAL;
    dLevel_dt : REAL;
    dSpeed_dt : REAL;
    P_Load_MW : REAL;
    Spill_Flow_m3s : REAL;
    abs_dQ_dt : REAL;

    Timestep : REAL := 0.1;

    Overspeed : BOOL := FALSE;
    Overpressure : BOOL := FALSE;
    LowHead : BOOL := FALSE;
    OverpresThreshold : REAL;
  END_VAR

  (* 1. PROCESS INPUTS *)
  Gate_Cmd_Pct := INT_TO_REAL(in_Gate_Cmd) / 10.0;

  IF Gate_Cmd_Pct < 0.0 THEN
    Gate_Cmd_Pct := 0.0;
  END_IF;
  IF Gate_Cmd_Pct > 100.0 THEN
    Gate_Cmd_Pct := 100.0;
  END_IF;

  (* 2. GATE ACTUATOR DYNAMICS *)
  Gate_Error := Gate_Cmd_Pct - Gate_Pos_Pct;
  Gate_Vel := Gate_Error / Gate_Tau_sec;

  IF Gate_Vel > Gate_Slew_Max THEN
    Gate_Vel := Gate_Slew_Max;
  ELSIF Gate_Vel < -Gate_Slew_Max THEN
    Gate_Vel := -Gate_Slew_Max;
  END_IF;

  Gate_Pos_Pct := Gate_Pos_Pct + Gate_Vel * Timestep;

  IF Gate_Pos_Pct < 0.0 THEN
    Gate_Pos_Pct := 0.0;
  END_IF;
  IF Gate_Pos_Pct > 100.0 THEN
    Gate_Pos_Pct := 100.0;
  END_IF;

  (* 3. RESERVOIR MASS BALANCE *)
  IF Spill_Open THEN
    IF Res_Level_m > 22.0 THEN
      Spill_Flow_m3s := 20.0 * (Res_Level_m - 22.0);
    ELSE
      Spill_Flow_m3s := 0.0;
    END_IF;
  ELSE
    Spill_Flow_m3s := 0.0;
  END_IF;

  dLevel_dt := (Res_Inflow_m3s - Flow_m3s - Spill_Flow_m3s) / Res_Area_m2;
  Res_Level_m := Res_Level_m + dLevel_dt * Timestep;

  IF Res_Level_m < 0.0 THEN
    Res_Level_m := 0.0;
  END_IF;
  IF Res_Level_m > Res_Max_m THEN
    Res_Level_m := Res_Max_m;
  END_IF;

  Head_m := Res_Level_m + Static_Head_m - Tailwater_m;
  IF Head_m < 0.0 THEN
    Head_m := 0.0;
  END_IF;

  (* 4. PENSTOCK FLOW DYNAMICS *)
  IF Head_m > 0.0 THEN
    Flow_Target_m3s := K_Q * (Gate_Pos_Pct / 100.0) * SQRT(Head_m);
  ELSE
    Flow_Target_m3s := 0.0;
  END_IF;

  IF Flow_Target_m3s > Q_Max_m3s THEN
    Flow_Target_m3s := Q_Max_m3s;
  END_IF;

  dQ_dt := (Flow_Target_m3s - Flow_m3s) / Penstock_Tau_sec;
  Flow_m3s := Flow_m3s + dQ_dt * Timestep;

  IF Flow_m3s < 0.0 THEN
    Flow_m3s := 0.0;
  END_IF;

  Pressure_kPa := RHO * G * Head_m / 1000.0;

  abs_dQ_dt := dQ_dt;
  IF abs_dQ_dt < 0.0 THEN
    abs_dQ_dt := -abs_dQ_dt;
  END_IF;
  IF abs_dQ_dt > 20.0 THEN
    Pressure_kPa := Pressure_kPa * 1.5;
  END_IF;

  (* 5. TURBINE/GENERATOR DYNAMICS *)
  P_Mech_MW := RHO * G * Flow_m3s * Head_m * Eta_Turbine / 1000000.0;

  IF Breaker_Closed THEN
    Speed_Pct := 100.0;
    Freq_Hz := 60.0;

    P_Elec_MW := P_Mech_MW * Eta_Gen;
    IF P_Elec_MW > P_Rated_MW THEN
      P_Elec_MW := P_Rated_MW;
    END_IF;
  ELSE
    IF Flow_m3s > 0.1 THEN
      dSpeed_dt := (P_Mech_MW / (P_Rated_MW * 0.1) - Speed_Pct / 50.0) / Inertia_H;
      Speed_Pct := Speed_Pct + dSpeed_dt * Timestep;
    ELSE
      dSpeed_dt := -Speed_Pct / (Inertia_H * 10.0);
      Speed_Pct := Speed_Pct + dSpeed_dt * Timestep;
    END_IF;

    IF Speed_Pct < 0.0 THEN
      Speed_Pct := 0.0;
    END_IF;
    IF Speed_Pct > 150.0 THEN
      Speed_Pct := 150.0;
    END_IF;

    Freq_Hz := 60.0 * Speed_Pct / 100.0;
    P_Elec_MW := 0.0;
  END_IF;

  (* 6. BREAKER DYNAMICS *)
  IF in_Breaker_Cmd AND NOT Breaker_Closed THEN
    Breaker_Timer := Breaker_Timer + Timestep;
    IF Breaker_Timer >= Breaker_Close_sec THEN
      IF Speed_Pct >= 99.0 AND Speed_Pct <= 101.0 THEN
        Breaker_Closed := TRUE;
      END_IF;
      Breaker_Timer := 0.0;
    END_IF;
  ELSIF NOT in_Breaker_Cmd AND Breaker_Closed THEN
    Breaker_Timer := Breaker_Timer + Timestep;
    IF Breaker_Timer >= Breaker_Open_sec THEN
      Breaker_Closed := FALSE;
      Breaker_Timer := 0.0;
    END_IF;
  ELSE
    Breaker_Timer := 0.0;
  END_IF;

  (* 7. SPILLWAY DYNAMICS *)
  IF in_Spill_Cmd AND NOT Spill_Open THEN
    Spill_Timer := Spill_Timer + Timestep;
    IF Spill_Timer >= Spill_Open_sec THEN
      Spill_Open := TRUE;
      Spill_Timer := 0.0;
    END_IF;
  ELSIF NOT in_Spill_Cmd AND Spill_Open THEN
    Spill_Timer := Spill_Timer + Timestep;
    IF Spill_Timer >= Spill_Open_sec THEN
      Spill_Open := FALSE;
      Spill_Timer := 0.0;
    END_IF;
  ELSE
    Spill_Timer := 0.0;
  END_IF;

  (* 8. TRIP CONDITION DETECTION *)
  Overspeed := Speed_Pct > 110.0;
  OverpresThreshold := (RHO * G * Static_Head_m / 1000.0) * 1.5;
  Overpressure := Pressure_kPa > OverpresThreshold;
  LowHead := Head_m < 10.0;

  (* 9. WRITE OUTPUTS *)
  out_Gate_Pos := REAL_TO_INT(Gate_Pos_Pct * 10.0);
  out_Res_Level := REAL_TO_INT(Res_Level_m * 100.0);
  out_Head := REAL_TO_INT(Head_m * 10.0);
  out_Flow := REAL_TO_INT(Flow_m3s * 10.0);
  out_Pressure := REAL_TO_INT(Pressure_kPa);
  out_Speed_Pct := REAL_TO_INT(Speed_Pct * 10.0);
  out_Freq_Hz := REAL_TO_INT(Freq_Hz * 100.0);
  out_Power_MW := REAL_TO_INT(P_Elec_MW * 10.0);

  out_Breaker_Sts := Breaker_Closed;
  out_Spill_Sts := Spill_Open;

END_PROGRAM
