TYPE
  HMI_UDT : STRUCT
    Start_PB : BOOL;
    Stop_PB : BOOL;
    Start_Active : BOOL;
    Stop_Active : BOOL;
  END_STRUCT;
  P1_UDT : STRUCT
    RW_Tank_tnk_lvl : REAL;
    RW_Pump_flow : REAL;
    RW_Tank_PR_Valve_sts : BOOL;
    RW_Tank_P6B_Valve_sts : BOOL;
    RW_Tank_P_Valve_sts : BOOL;
    RW_Pump_sts : BOOL;
    RW_Pump_fault : BOOL;
    RW_Pump : REAL;
    RW_Tank_PR_Valve : BOOL;
    RW_Tank_P_Valve : BOOL;
    RW_Pump_start : BOOL;
    RW_Pump_stop : BOOL;
    RW_Tank_P6B_Valve : BOOL;
  END_STRUCT;
  P2_UDT : STRUCT
    ChemTreat_NaCl_Tank_tnk_lvl : REAL;
    ChemTreat_NaOCl_Tank_tnk_lvl : REAL;
    ChemTreat_HCl_Tank_tnk_lvl : REAL;
    ChemTreat_NaCl_Tank_Valve_sts : BOOL;
    ChemTreat_NaOCl_Tank_Valve_sts : BOOL;
    ChemTreat_HCl_Tank_Valve_sts : BOOL;
    ChemTreat_NaCl_Tank_Valve : BOOL;
    ChemTreat_NaOCl_Tank_Valve : BOOL;
    ChemTreat_HCl_Tank_Valve : BOOL;
  END_STRUCT;
  P3_UDT : STRUCT
    Ultrafiltration_UFFT_Tank_tnk_lvl : REAL;
    Ultrafiltration_UFFT_Tank_Valve_sts : BOOL;
    Ultrafiltration_UF_Drain_Valve_sts : BOOL;
    Ultrafiltration_UF_ROFT_Valve_sts : BOOL;
    Ultrafiltration_UF_BWP_Valve_sts : BOOL;
    Ultrafiltration_UFFT_Tank_Valve : BOOL;
    Ultrafiltration_UF_Drain_Valve : BOOL;
    Ultrafiltration_UF_ROFT_Valve : BOOL;
    Ultrafiltration_UF_BWP_Valve : BOOL;
  END_STRUCT;
  Phases_UDT : STRUCT
    Filling : BOOL;
    Draining : BOOL;
  END_STRUCT;
  RW_tank_AL_UDT : STRUCT
    LL_alarm : BOOL;
    L_alarm : BOOL;
    H_alarm : BOOL;
    HH_alarm : BOOL;
  END_STRUCT;
  System_State_UDT : STRUCT
    IDLE : BOOL;
    START : BOOL;
    RUNNING : BOOL;
    SHUTDOWN : BOOL;
    Permissives : ARRAY [0..31] OF BOOL;
    Permissives_Ready : BOOL;
  END_STRUCT;
  SYS_MESSAGES : STRUCT
    ProgramScanTime : DINT;
    AvailableMemory : REAL;
    ControllerStatus : SINT;
    ScanTime : REAL;
  END_STRUCT;
END_TYPE

PROGRAM MainProgram
  VAR_INPUT
    Alarms : RW_tank_AL_UDT;
    GSV_Message : SYS_MESSAGES;
    HMI : HMI_UDT;
    P1 : P1_UDT;
    P1_SYS : System_State_UDT;
    P2 : P2_UDT;
    P3 : P3_UDT;
  END_VAR
  VAR_INPUT
    di_2_0 : BOOL;
    di_2_1 : BOOL;
    di_2_10 : BOOL;
    di_2_11 : BOOL;
    di_2_2 : BOOL;
    di_2_3 : BOOL;
    di_2_4 : BOOL;
    di_2_5 : BOOL;
    di_2_6 : BOOL;
    di_2_8 : BOOL;
    di_2_9 : BOOL;
    ai_7_0 : REAL;
    di_7_ch0halarm : BOOL;
    di_7_ch0hhalarm : BOOL;
    di_7_ch0lalarm : BOOL;
    di_7_ch0llalarm : BOOL;
    ai_7_1 : REAL;
    ai_7_2 : REAL;
    ai_7_3 : REAL;
    ai_7_4 : REAL;
    ai_7_5 : REAL;
  END_VAR
  VAR_OUTPUT
    ao_10_0 : REAL;
    do_5_0 : BOOL;
    do_5_1 : BOOL;
    do_5_10 : BOOL;
    do_5_11 : BOOL;
    do_5_2 : BOOL;
    do_5_3 : BOOL;
    do_5_4 : BOOL;
    do_5_5 : BOOL;
    do_5_6 : BOOL;
    do_5_7 : BOOL;
    do_5_8 : BOOL;
    do_5_9 : BOOL;
  END_VAR

  (* IO_setup *)
  (* P1 Analog Input *)
  P1.RW_Tank_tnk_lvl := ai_7_0;
  P1.RW_Pump_flow := ai_7_1;
  (* P1 Digital Input *)
  P1.RW_Tank_PR_Valve_sts := di_2_0;
  P1.RW_Tank_P6B_Valve_sts := di_2_1;
  P1.RW_Tank_P_Valve_sts := di_2_2;
  P1.RW_Pump_sts := di_2_3;
  P1.RW_Pump_fault := di_2_4;
  (* P1 Analog Output *)
  P1.RW_Pump := ao_10_0;
  (* Digital Output *)
  P1.RW_Tank_PR_Valve := do_5_0;
  P1.RW_Tank_P6B_Valve := do_5_1;
  P1.RW_Tank_P_Valve := do_5_2;
  P1.RW_Pump_start := do_5_3;
  P1.RW_Pump_stop := do_5_4;
  (* P1 raw water tank alarms *)
  Alarms.LL_alarm := di_7_ch0llalarm;
  Alarms.L_alarm := di_7_ch0lalarm;
  Alarms.H_alarm := di_7_ch0halarm;
  Alarms.HH_alarm := di_7_ch0hhalarm;
  (* P2 Analog Input *)
  P2.ChemTreat_NaCl_Tank_tnk_lvl := ai_7_2;
  P2.ChemTreat_NaOCl_Tank_tnk_lvl := ai_7_3;
  P2.ChemTreat_HCl_Tank_tnk_lvl := ai_7_4;
  (* P2 Digital Input *)
  P2.ChemTreat_NaCl_Tank_Valve_sts := di_2_5;
  P2.ChemTreat_NaOCl_Tank_Valve_sts := di_2_6;
  (* P2 Analog Output *)
  (* NONE *)
  (* P2 Digital Output *)
  P2.ChemTreat_NaCl_Tank_Valve := do_5_5;
  P2.ChemTreat_NaOCl_Tank_Valve := do_5_6;
  P2.ChemTreat_HCl_Tank_Valve := do_5_7;
  (* P3 Analog Input *)
  P3.Ultrafiltration_UFFT_Tank_tnk_lvl := ai_7_5;
  (* P3 Digital Input *)
  P3.Ultrafiltration_UFFT_Tank_Valve_sts := di_2_8;
  P3.Ultrafiltration_UF_Drain_Valve_sts := di_2_9;
  P3.Ultrafiltration_UF_Drain_Valve_sts := di_2_10;
  P3.Ultrafiltration_UF_BWP_Valve_sts := di_2_11;
  (* P3 Analog Output *)
  (* none *)
  (* P3 Digital Output *)
  P3.Ultrafiltration_UFFT_Tank_Valve := do_5_8;
  P3.Ultrafiltration_UF_Drain_Valve := do_5_9;
  P3.Ultrafiltration_UF_ROFT_Valve := do_5_10;
  P3.Ultrafiltration_UF_BWP_Valve := do_5_11;

  (* Raw_water_control *)
  if P1.RW_Tank_tnk_lvl = 250.0 and P1_SYS.RUNNING then
  P1.RW_Pump_stop := True;
  P1.RW_Pump_start := False; (* send the outputs *)
  Alarms.LL_alarm := True;
  (* if the level is at 500 or lower than 500 open the valve *)
  elsif P1.RW_Tank_tnk_lvl <= 500.0 and P1_SYS.RUNNING then
  (* output to turn the valve open *)
  P1.RW_Tank_PR_Valve := True;
  Alarms.L_alarm := True;
  (* if level is at 800 *)
  elsif  P1.RW_Tank_tnk_lvl = 800.0 and P1_SYS.RUNNING then
  P1.RW_Tank_PR_Valve := False; (* close the valve *)
  Alarms.H_alarm := True;
  elsif P1.RW_Tank_tnk_lvl = 1200.0 and P1_SYS.RUNNING then
  Alarms.HH_alarm := True; (* if the tank is higher than or equal to 1200 set the high high alarm *)
  end_if;

  (* Raw_water_pump *)
  if P3.Ultrafiltration_UFFT_Tank_tnk_lvl = 800.0 AND P1_SYS.RUNNING then
  (* start the pump and open the valve from the other tank *)
  P1.RW_Tank_P_Valve := True;
  P1.RW_Pump_start := True;
  P1.RW_Pump_stop := False;
  elsif P3.Ultrafiltration_UFFT_Tank_tnk_lvl = 1000.0 AND P1_SYS.RUNNING then
  (* stop the pump and close the valve *)
  P1.RW_Tank_P_Valve := False;
  P1.RW_Pump_stop := True;
  P1.RW_Pump_start := False;
  end_if;

  (* State_change *)
  if not HMI.Start_Active AND not HMI.Stop_Active then
  (* if start and stop is not pressed go to idle *)
  P1_SYS.IDLE := True;
  P1_SYS.START := False;
  P1_SYS.RUNNING := False;
  P1_SYS.SHUTDOWN := False;
  elsif  HMI.Start_Active AND not HMI.Stop_Active then
  (* if the start pb and stop is not pressed then change the state of process one to starting *)
  P1_SYS.IDLE := False;
  P1_SYS.START := True;
  P1_SYS.RUNNING := False;
  P1_SYS.SHUTDOWN := False;
  (* if the tank level is greater than 250 at the start and UFFT is less than a 1000 we can start *)
  (* then and all permissves cond together into one tag so we know the plant is ready to start *)
  P1_SYS.Permissives_Ready := P1_SYS.Permissives[0] AND P1_SYS.Permissives[1];
  elsif HMI.Start_Active AND P1_SYS.Permissives_Ready then
  (* if the start was pressed and permissives are ready start running Process one *)
  P1_SYS.IDLE := False;
  P1_SYS.START := False;
  P1_SYS.RUNNING := True;
  P1_SYS.SHUTDOWN := False;
  elsif HMI.Stop_Active then
  (* if the stop button is pressed then go to shutdown state *)
  P1_SYS.IDLE := False;
  P1_SYS.START := False;
  P1_SYS.RUNNING := False;
  P1_SYS.SHUTDOWN := True;
  (* set all permissives to false *)
  P1_SYS.Permissives_Ready := False;
  end_if;
END_PROGRAM


CONFIGURATION config
  VAR_GLOBAL
    ao_10_0 : REAL;
    di_2_0 : BOOL;
    di_2_1 : BOOL;
    di_2_10 : BOOL;
    di_2_11 : BOOL;
    di_2_2 : BOOL;
    di_2_3 : BOOL;
    di_2_4 : BOOL;
    di_2_5 : BOOL;
    di_2_6 : BOOL;
    di_2_8 : BOOL;
    di_2_9 : BOOL;
    do_5_0 : BOOL;
    do_5_1 : BOOL;
    do_5_10 : BOOL;
    do_5_11 : BOOL;
    do_5_2 : BOOL;
    do_5_3 : BOOL;
    do_5_4 : BOOL;
    do_5_5 : BOOL;
    do_5_6 : BOOL;
    do_5_7 : BOOL;
    do_5_8 : BOOL;
    do_5_9 : BOOL;
    ai_7_0 : REAL;
    di_7_ch0halarm : BOOL;
    di_7_ch0hhalarm : BOOL;
    di_7_ch0lalarm : BOOL;
    di_7_ch0llalarm : BOOL;
    ai_7_1 : REAL;
    ai_7_2 : REAL;
    ai_7_3 : REAL;
    ai_7_4 : REAL;
    ai_7_5 : REAL;
  END_VAR

  RESOURCE res_MainProgram ON PLC
    TASK task_MainProgram(INTERVAL := T#100ms,PRIORITY := 0);
    PROGRAM MainProgram_instance : MainProgram;
  END_RESOURCE
END_CONFIGURATION

