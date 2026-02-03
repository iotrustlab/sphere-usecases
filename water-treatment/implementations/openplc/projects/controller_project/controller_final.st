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
    P1 : P1_UDT;
    P1_SYS : System_State_UDT;
    P2 : P2_UDT;
    P3 : P3_UDT;
  END_VAR
  VAR_INPUT
    (* Original I/O — kept for standalone/legacy mode *)
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
    HMI : HMI_UDT;
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
    (* HMI coils %QX0.0-0.3 *)
    hmi_0_0 : BOOL;  (* HMI_Start_PB - written by external client *)
    hmi_0_1 : BOOL;  (* HMI_Stop_PB  - written by external client *)
    hmi_0_2 : BOOL;  (* HMI_Start_Active - written by controller *)
    hmi_0_3 : BOOL;  (* HMI_Stop_Active  - written by controller *)
    (* System state coils %QX7.0-7.4 *)
    sys_7_0 : BOOL;  (* SYS_IDLE *)
    sys_7_1 : BOOL;  (* SYS_START *)
    sys_7_2 : BOOL;  (* SYS_RUNNING *)
    sys_7_3 : BOOL;  (* SYS_SHUTDOWN *)
    sys_7_4 : BOOL;  (* SYS_Permissives_Ready *)
    (* Alarm coils %QX8.0-8.3 *)
    alm_8_0 : BOOL;  (* Alarm_RW_Tank_LL *)
    alm_8_1 : BOOL;  (* Alarm_RW_Tank_L *)
    alm_8_2 : BOOL;  (* Alarm_RW_Tank_H *)
    alm_8_3 : BOOL;  (* Alarm_RW_Tank_HH *)
    (* Bridge sensor inputs — holding registers written by bridge *)
    bridge_rw_level : INT;       (* %QW300 — RW tank level from simulator *)
    bridge_rw_flow : INT;        (* %QW301 — RW pump flow from simulator *)
    bridge_nacl_level : INT;     (* %QW302 — NaCl tank level *)
    bridge_naocl_level : INT;    (* %QW303 — NaOCl tank level *)
    bridge_hcl_level : INT;      (* %QW304 — HCl tank level *)
    bridge_uf_level : INT;       (* %QW305 — UF tank level *)
    bridge_pr_valve_sts : INT;   (* %QW320 — PR valve status *)
    bridge_p6b_valve_sts : INT;  (* %QW321 — P6B valve status *)
    bridge_p_valve_sts : INT;    (* %QW322 — P valve status *)
    bridge_pump_sts : INT;       (* %QW323 — pump running status *)
    bridge_pump_fault : INT;     (* %QW324 — pump fault *)
    bridge_nacl_valve_sts : INT; (* %QW325 — NaCl valve status *)
    bridge_naocl_valve_sts : INT;(* %QW326 — NaOCl valve status *)
    bridge_hcl_valve_sts : INT;  (* %QW327 — HCl valve status *)
    bridge_uf_valve_sts : INT;   (* %QW328 — UF tank valve status *)
    bridge_uf_drain_sts : INT;   (* %QW329 — UF drain valve status *)
    bridge_uf_roft_sts : INT;    (* %QW330 — UF ROFT valve status *)
    bridge_uf_bwp_sts : INT;    (* %QW331 — UF BWP valve status *)
  END_VAR

  (* ===== HMI button latch ===== *)
  HMI.Start_PB := hmi_0_0;
  HMI.Stop_PB := hmi_0_1;
  IF HMI.Start_PB THEN
    HMI.Start_Active := TRUE;
    HMI.Stop_Active := FALSE;
  ELSIF HMI.Stop_PB THEN
    HMI.Stop_Active := TRUE;
    HMI.Start_Active := FALSE;
  END_IF;

  (* ===== Read sensors from bridge holding registers ===== *)
  (* Levels: INT -> REAL conversion *)
  P1.RW_Tank_tnk_lvl := INT_TO_REAL(bridge_rw_level);
  P1.RW_Pump_flow := INT_TO_REAL(bridge_rw_flow);
  P2.ChemTreat_NaCl_Tank_tnk_lvl := INT_TO_REAL(bridge_nacl_level);
  P2.ChemTreat_NaOCl_Tank_tnk_lvl := INT_TO_REAL(bridge_naocl_level);
  P2.ChemTreat_HCl_Tank_tnk_lvl := INT_TO_REAL(bridge_hcl_level);
  P3.Ultrafiltration_UFFT_Tank_tnk_lvl := INT_TO_REAL(bridge_uf_level);
  (* Valve/pump status: INT -> BOOL (nonzero = TRUE) *)
  P1.RW_Tank_PR_Valve_sts := bridge_pr_valve_sts <> 0;
  P1.RW_Tank_P6B_Valve_sts := bridge_p6b_valve_sts <> 0;
  P1.RW_Tank_P_Valve_sts := bridge_p_valve_sts <> 0;
  P1.RW_Pump_sts := bridge_pump_sts <> 0;
  P1.RW_Pump_fault := bridge_pump_fault <> 0;
  P2.ChemTreat_NaCl_Tank_Valve_sts := bridge_nacl_valve_sts <> 0;
  P2.ChemTreat_NaOCl_Tank_Valve_sts := bridge_naocl_valve_sts <> 0;
  P3.Ultrafiltration_UFFT_Tank_Valve_sts := bridge_uf_valve_sts <> 0;
  P3.Ultrafiltration_UF_Drain_Valve_sts := bridge_uf_drain_sts <> 0;
  P3.Ultrafiltration_UF_ROFT_Valve_sts := bridge_uf_roft_sts <> 0;
  P3.Ultrafiltration_UF_BWP_Valve_sts := bridge_uf_bwp_sts <> 0;

  (* P1 Analog Output *)
  P1.RW_Pump := ao_10_0;
  (* Digital Output *)
  P1.RW_Tank_PR_Valve := do_5_0;
  P1.RW_Tank_P6B_Valve := do_5_1;
  P1.RW_Tank_P_Valve := do_5_2;
  P1.RW_Pump_start := do_5_3;
  P1.RW_Pump_stop := do_5_4;
  (* P2 Digital Output *)
  P2.ChemTreat_NaCl_Tank_Valve := do_5_5;
  P2.ChemTreat_NaOCl_Tank_Valve := do_5_6;
  P2.ChemTreat_HCl_Tank_Valve := do_5_7;
  (* P3 Digital Output *)
  P3.Ultrafiltration_UFFT_Tank_Valve := do_5_8;
  P3.Ultrafiltration_UF_Drain_Valve := do_5_9;
  P3.Ultrafiltration_UF_ROFT_Valve := do_5_10;
  P3.Ultrafiltration_UF_BWP_Valve := do_5_11;

  (* ===== Compute alarms from levels ===== *)
  Alarms.LL_alarm := P1.RW_Tank_tnk_lvl <= 250.0;
  Alarms.L_alarm := P1.RW_Tank_tnk_lvl <= 500.0;
  Alarms.H_alarm := P1.RW_Tank_tnk_lvl >= 800.0;
  Alarms.HH_alarm := P1.RW_Tank_tnk_lvl >= 1200.0;

  (* ===== Raw_water_control ===== *)
  IF P1.RW_Tank_tnk_lvl <= 250.0 AND P1_SYS.RUNNING THEN
    P1.RW_Pump_stop := TRUE;
    P1.RW_Pump_start := FALSE;
  ELSIF P1.RW_Tank_tnk_lvl <= 500.0 AND P1_SYS.RUNNING THEN
    P1.RW_Tank_PR_Valve := TRUE;
  ELSIF P1.RW_Tank_tnk_lvl >= 800.0 AND P1_SYS.RUNNING THEN
    P1.RW_Tank_PR_Valve := FALSE;
  END_IF;

  (* ===== Raw_water_pump ===== *)
  IF P3.Ultrafiltration_UFFT_Tank_tnk_lvl <= 800.0 AND P1_SYS.RUNNING THEN
    P1.RW_Tank_P_Valve := TRUE;
    P1.RW_Pump_start := TRUE;
    P1.RW_Pump_stop := FALSE;
  ELSIF P3.Ultrafiltration_UFFT_Tank_tnk_lvl >= 1000.0 AND P1_SYS.RUNNING THEN
    P1.RW_Tank_P_Valve := FALSE;
    P1.RW_Pump_stop := TRUE;
    P1.RW_Pump_start := FALSE;
  END_IF;

  (* ===== Permissives ===== *)
  P1_SYS.Permissives[0] := P1.RW_Tank_tnk_lvl > 250.0;
  P1_SYS.Permissives[1] := P3.Ultrafiltration_UFFT_Tank_tnk_lvl < 1000.0;

  (* ===== State_change ===== *)
  IF NOT HMI.Start_Active AND NOT HMI.Stop_Active THEN
    P1_SYS.IDLE := TRUE;
    P1_SYS.START := FALSE;
    P1_SYS.RUNNING := FALSE;
    P1_SYS.SHUTDOWN := FALSE;
  ELSIF HMI.Start_Active AND NOT HMI.Stop_Active AND NOT P1_SYS.Permissives_Ready THEN
    P1_SYS.IDLE := FALSE;
    P1_SYS.START := TRUE;
    P1_SYS.RUNNING := FALSE;
    P1_SYS.SHUTDOWN := FALSE;
    P1_SYS.Permissives_Ready := P1_SYS.Permissives[0] AND P1_SYS.Permissives[1];
  ELSIF HMI.Start_Active AND P1_SYS.Permissives_Ready THEN
    P1_SYS.IDLE := FALSE;
    P1_SYS.START := FALSE;
    P1_SYS.RUNNING := TRUE;
    P1_SYS.SHUTDOWN := FALSE;
  ELSIF HMI.Stop_Active THEN
    P1_SYS.IDLE := FALSE;
    P1_SYS.START := FALSE;
    P1_SYS.RUNNING := FALSE;
    P1_SYS.SHUTDOWN := TRUE;
    P1_SYS.Permissives_Ready := FALSE;
  END_IF;

  (* ===== Wire outputs to coils/registers ===== *)
  do_5_0 := P1.RW_Tank_PR_Valve;
  do_5_1 := P1.RW_Tank_P6B_Valve;
  do_5_2 := P1.RW_Tank_P_Valve;
  do_5_3 := P1.RW_Pump_start;
  do_5_4 := P1.RW_Pump_stop;
  do_5_5 := P2.ChemTreat_NaCl_Tank_Valve;
  do_5_6 := P2.ChemTreat_NaOCl_Tank_Valve;
  do_5_7 := P2.ChemTreat_HCl_Tank_Valve;
  do_5_8 := P3.Ultrafiltration_UFFT_Tank_Valve;
  do_5_9 := P3.Ultrafiltration_UF_Drain_Valve;
  do_5_10 := P3.Ultrafiltration_UF_ROFT_Valve;
  do_5_11 := P3.Ultrafiltration_UF_BWP_Valve;
  ao_10_0 := P1.RW_Pump;
  (* HMI status *)
  hmi_0_2 := HMI.Start_Active;
  hmi_0_3 := HMI.Stop_Active;
  (* System state *)
  sys_7_0 := P1_SYS.IDLE;
  sys_7_1 := P1_SYS.START;
  sys_7_2 := P1_SYS.RUNNING;
  sys_7_3 := P1_SYS.SHUTDOWN;
  sys_7_4 := P1_SYS.Permissives_Ready;
  (* Alarms *)
  alm_8_0 := Alarms.LL_alarm;
  alm_8_1 := Alarms.L_alarm;
  alm_8_2 := Alarms.H_alarm;
  alm_8_3 := Alarms.HH_alarm;
END_PROGRAM


CONFIGURATION Config0
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
    (* HMI coils %QX0.0-0.3 *)
    hmi_0_0 AT %QX0.0 : BOOL;
    hmi_0_1 AT %QX0.1 : BOOL;
    hmi_0_2 AT %QX0.2 : BOOL;
    hmi_0_3 AT %QX0.3 : BOOL;
    (* System state coils %QX7.0-7.4 *)
    sys_7_0 AT %QX7.0 : BOOL;
    sys_7_1 AT %QX7.1 : BOOL;
    sys_7_2 AT %QX7.2 : BOOL;
    sys_7_3 AT %QX7.3 : BOOL;
    sys_7_4 AT %QX7.4 : BOOL;
    (* Alarm coils %QX8.0-8.3 *)
    alm_8_0 AT %QX8.0 : BOOL;
    alm_8_1 AT %QX8.1 : BOOL;
    alm_8_2 AT %QX8.2 : BOOL;
    alm_8_3 AT %QX8.3 : BOOL;
    (* Bridge sensor inputs — holding registers writable by bridge *)
    bridge_rw_level AT %QW300 : INT;
    bridge_rw_flow AT %QW301 : INT;
    bridge_nacl_level AT %QW302 : INT;
    bridge_naocl_level AT %QW303 : INT;
    bridge_hcl_level AT %QW304 : INT;
    bridge_uf_level AT %QW305 : INT;
    bridge_pr_valve_sts AT %QW320 : INT;
    bridge_p6b_valve_sts AT %QW321 : INT;
    bridge_p_valve_sts AT %QW322 : INT;
    bridge_pump_sts AT %QW323 : INT;
    bridge_pump_fault AT %QW324 : INT;
    bridge_nacl_valve_sts AT %QW325 : INT;
    bridge_naocl_valve_sts AT %QW326 : INT;
    bridge_hcl_valve_sts AT %QW327 : INT;
    bridge_uf_valve_sts AT %QW328 : INT;
    bridge_uf_drain_sts AT %QW329 : INT;
    bridge_uf_roft_sts AT %QW330 : INT;
    bridge_uf_bwp_sts AT %QW331 : INT;
  END_VAR

  RESOURCE Res0 ON PLC
    TASK task_MainProgram(INTERVAL := T#100ms,PRIORITY := 0);
    PROGRAM MainProgram_instance : MainProgram;
  END_RESOURCE
END_CONFIGURATION
