PROGRAM SimulatorProgram
  VAR
    (* ===== Bridge command inputs — written by external bridge ===== *)
    cmd_pr_valve AT %QW200 : INT;      (* 0/1  PR valve command *)
    cmd_p6b_valve AT %QW201 : INT;     (* 0/1  P6B valve command *)
    cmd_p_valve AT %QW202 : INT;       (* 0/1  Process valve command *)
    cmd_pump_start AT %QW203 : INT;    (* 0/1  Pump start *)
    cmd_pump_stop AT %QW204 : INT;     (* 0/1  Pump stop *)
    cmd_nacl_valve AT %QW205 : INT;    (* 0/1  NaCl valve command *)
    cmd_naocl_valve AT %QW206 : INT;   (* 0/1  NaOCl valve command *)
    cmd_hcl_valve AT %QW207 : INT;     (* 0/1  HCl valve command *)
    cmd_uf_valve AT %QW208 : INT;      (* 0/1  UF tank valve command *)
    cmd_uf_drain AT %QW209 : INT;      (* 0/1  UF drain valve command *)
    cmd_uf_roft AT %QW210 : INT;       (* 0/1  UF ROFT valve command *)
    cmd_uf_bwp AT %QW211 : INT;        (* 0/1  UF BWP valve command *)
    cmd_pump_speed AT %QW220 : INT;    (* 0-100  pump speed % *)

    (* ===== Bridge sensor outputs — read by bridge ===== *)
    out_rw_level AT %QW300 : INT;           (* RW tank level mm *)
    out_rw_flow AT %QW301 : INT;            (* RW pump flow L/min *)
    out_nacl_level AT %QW302 : INT;         (* NaCl tank level mm *)
    out_naocl_level AT %QW303 : INT;        (* NaOCl tank level mm *)
    out_hcl_level AT %QW304 : INT;          (* HCl tank level mm *)
    out_uf_level AT %QW305 : INT;           (* UF tank level mm *)
    out_pr_valve_sts AT %QW320 : INT;       (* 0/1 *)
    out_p6b_valve_sts AT %QW321 : INT;
    out_p_valve_sts AT %QW322 : INT;
    out_pump_sts AT %QW323 : INT;
    out_pump_fault AT %QW324 : INT;
    out_nacl_valve_sts AT %QW325 : INT;
    out_naocl_valve_sts AT %QW326 : INT;
    out_hcl_valve_sts AT %QW327 : INT;
    out_uf_valve_sts AT %QW328 : INT;
    out_uf_drain_sts AT %QW329 : INT;
    out_uf_roft_sts AT %QW330 : INT;
    out_uf_bwp_sts AT %QW331 : INT;

    (* ===== Internal physics state ===== *)
    rw_tank_level : REAL := 600.0;
    uf_tank_level : REAL := 400.0;
    nacl_level : REAL := 800.0;
    naocl_level : REAL := 800.0;
    hcl_level : REAL := 800.0;
    pump_running : BOOL := FALSE;
    pump_flow : REAL := 0.0;

    (* Valve status with delay timers *)
    pr_valve_open : BOOL := FALSE;
    pr_valve_timer : INT := 0;
    p6b_valve_open : BOOL := FALSE;
    p6b_valve_timer : INT := 0;
    p_valve_open : BOOL := FALSE;
    p_valve_timer : INT := 0;
    nacl_valve_open : BOOL := FALSE;
    nacl_valve_timer : INT := 0;
    naocl_valve_open : BOOL := FALSE;
    naocl_valve_timer : INT := 0;
    hcl_valve_open : BOOL := FALSE;
    hcl_valve_timer : INT := 0;
    uf_valve_open : BOOL := FALSE;
    uf_valve_timer : INT := 0;
    uf_drain_open : BOOL := FALSE;
    uf_drain_timer : INT := 0;
    uf_roft_open : BOOL := FALSE;
    uf_roft_timer : INT := 0;
    uf_bwp_open : BOOL := FALSE;
    uf_bwp_timer : INT := 0;

    pump_timer : INT := 0;
    pump_requested : BOOL := FALSE;

    (* ===== Constants ===== *)
    DT_SEC : REAL := 0.1;            (* 100ms scan interval *)
    PUMP_MAX_FLOW : REAL := 120.0;   (* L/min at 100% speed *)
    PR_INFLOW_RATE : REAL := 50.0;   (* L/min from external source *)
    DOSING_RATE : REAL := 5.0;       (* L/min chemical drain *)
    UF_DRAIN_RATE : REAL := 30.0;    (* L/min UF drain/ROFT *)
    VALVE_DELAY : INT := 5;          (* cycles = 500ms *)
    PUMP_DELAY : INT := 8;           (* cycles = 800ms *)
    RW_TANK_MAX : REAL := 1500.0;
    UF_TANK_MAX : REAL := 1200.0;
    CHEM_TANK_MAX : REAL := 1000.0;
  END_VAR

  (* ========================================================= *)
  (* 1. Update valve status with delay                         *)
  (* ========================================================= *)

  (* PR valve *)
  IF cmd_pr_valve <> 0 THEN
    IF NOT pr_valve_open THEN
      pr_valve_timer := pr_valve_timer + 1;
      IF pr_valve_timer >= VALVE_DELAY THEN
        pr_valve_open := TRUE;
        pr_valve_timer := 0;
      END_IF;
    END_IF;
  ELSE
    IF pr_valve_open THEN
      pr_valve_timer := pr_valve_timer + 1;
      IF pr_valve_timer >= VALVE_DELAY THEN
        pr_valve_open := FALSE;
        pr_valve_timer := 0;
      END_IF;
    ELSE
      pr_valve_timer := 0;
    END_IF;
  END_IF;

  (* P6B valve *)
  IF cmd_p6b_valve <> 0 THEN
    IF NOT p6b_valve_open THEN
      p6b_valve_timer := p6b_valve_timer + 1;
      IF p6b_valve_timer >= VALVE_DELAY THEN
        p6b_valve_open := TRUE;
        p6b_valve_timer := 0;
      END_IF;
    END_IF;
  ELSE
    IF p6b_valve_open THEN
      p6b_valve_timer := p6b_valve_timer + 1;
      IF p6b_valve_timer >= VALVE_DELAY THEN
        p6b_valve_open := FALSE;
        p6b_valve_timer := 0;
      END_IF;
    ELSE
      p6b_valve_timer := 0;
    END_IF;
  END_IF;

  (* P valve *)
  IF cmd_p_valve <> 0 THEN
    IF NOT p_valve_open THEN
      p_valve_timer := p_valve_timer + 1;
      IF p_valve_timer >= VALVE_DELAY THEN
        p_valve_open := TRUE;
        p_valve_timer := 0;
      END_IF;
    END_IF;
  ELSE
    IF p_valve_open THEN
      p_valve_timer := p_valve_timer + 1;
      IF p_valve_timer >= VALVE_DELAY THEN
        p_valve_open := FALSE;
        p_valve_timer := 0;
      END_IF;
    ELSE
      p_valve_timer := 0;
    END_IF;
  END_IF;

  (* NaCl valve *)
  IF cmd_nacl_valve <> 0 THEN
    IF NOT nacl_valve_open THEN
      nacl_valve_timer := nacl_valve_timer + 1;
      IF nacl_valve_timer >= VALVE_DELAY THEN
        nacl_valve_open := TRUE;
        nacl_valve_timer := 0;
      END_IF;
    END_IF;
  ELSE
    IF nacl_valve_open THEN
      nacl_valve_timer := nacl_valve_timer + 1;
      IF nacl_valve_timer >= VALVE_DELAY THEN
        nacl_valve_open := FALSE;
        nacl_valve_timer := 0;
      END_IF;
    ELSE
      nacl_valve_timer := 0;
    END_IF;
  END_IF;

  (* NaOCl valve *)
  IF cmd_naocl_valve <> 0 THEN
    IF NOT naocl_valve_open THEN
      naocl_valve_timer := naocl_valve_timer + 1;
      IF naocl_valve_timer >= VALVE_DELAY THEN
        naocl_valve_open := TRUE;
        naocl_valve_timer := 0;
      END_IF;
    END_IF;
  ELSE
    IF naocl_valve_open THEN
      naocl_valve_timer := naocl_valve_timer + 1;
      IF naocl_valve_timer >= VALVE_DELAY THEN
        naocl_valve_open := FALSE;
        naocl_valve_timer := 0;
      END_IF;
    ELSE
      naocl_valve_timer := 0;
    END_IF;
  END_IF;

  (* HCl valve *)
  IF cmd_hcl_valve <> 0 THEN
    IF NOT hcl_valve_open THEN
      hcl_valve_timer := hcl_valve_timer + 1;
      IF hcl_valve_timer >= VALVE_DELAY THEN
        hcl_valve_open := TRUE;
        hcl_valve_timer := 0;
      END_IF;
    END_IF;
  ELSE
    IF hcl_valve_open THEN
      hcl_valve_timer := hcl_valve_timer + 1;
      IF hcl_valve_timer >= VALVE_DELAY THEN
        hcl_valve_open := FALSE;
        hcl_valve_timer := 0;
      END_IF;
    ELSE
      hcl_valve_timer := 0;
    END_IF;
  END_IF;

  (* UF tank valve *)
  IF cmd_uf_valve <> 0 THEN
    IF NOT uf_valve_open THEN
      uf_valve_timer := uf_valve_timer + 1;
      IF uf_valve_timer >= VALVE_DELAY THEN
        uf_valve_open := TRUE;
        uf_valve_timer := 0;
      END_IF;
    END_IF;
  ELSE
    IF uf_valve_open THEN
      uf_valve_timer := uf_valve_timer + 1;
      IF uf_valve_timer >= VALVE_DELAY THEN
        uf_valve_open := FALSE;
        uf_valve_timer := 0;
      END_IF;
    ELSE
      uf_valve_timer := 0;
    END_IF;
  END_IF;

  (* UF drain valve *)
  IF cmd_uf_drain <> 0 THEN
    IF NOT uf_drain_open THEN
      uf_drain_timer := uf_drain_timer + 1;
      IF uf_drain_timer >= VALVE_DELAY THEN
        uf_drain_open := TRUE;
        uf_drain_timer := 0;
      END_IF;
    END_IF;
  ELSE
    IF uf_drain_open THEN
      uf_drain_timer := uf_drain_timer + 1;
      IF uf_drain_timer >= VALVE_DELAY THEN
        uf_drain_open := FALSE;
        uf_drain_timer := 0;
      END_IF;
    ELSE
      uf_drain_timer := 0;
    END_IF;
  END_IF;

  (* UF ROFT valve *)
  IF cmd_uf_roft <> 0 THEN
    IF NOT uf_roft_open THEN
      uf_roft_timer := uf_roft_timer + 1;
      IF uf_roft_timer >= VALVE_DELAY THEN
        uf_roft_open := TRUE;
        uf_roft_timer := 0;
      END_IF;
    END_IF;
  ELSE
    IF uf_roft_open THEN
      uf_roft_timer := uf_roft_timer + 1;
      IF uf_roft_timer >= VALVE_DELAY THEN
        uf_roft_open := FALSE;
        uf_roft_timer := 0;
      END_IF;
    ELSE
      uf_roft_timer := 0;
    END_IF;
  END_IF;

  (* UF BWP valve *)
  IF cmd_uf_bwp <> 0 THEN
    IF NOT uf_bwp_open THEN
      uf_bwp_timer := uf_bwp_timer + 1;
      IF uf_bwp_timer >= VALVE_DELAY THEN
        uf_bwp_open := TRUE;
        uf_bwp_timer := 0;
      END_IF;
    END_IF;
  ELSE
    IF uf_bwp_open THEN
      uf_bwp_timer := uf_bwp_timer + 1;
      IF uf_bwp_timer >= VALVE_DELAY THEN
        uf_bwp_open := FALSE;
        uf_bwp_timer := 0;
      END_IF;
    ELSE
      uf_bwp_timer := 0;
    END_IF;
  END_IF;

  (* ========================================================= *)
  (* 2. Update pump status with delay                          *)
  (* ========================================================= *)
  pump_requested := cmd_pump_start <> 0 AND cmd_pump_stop = 0;

  IF pump_requested AND NOT pump_running THEN
    pump_timer := pump_timer + 1;
    IF pump_timer >= PUMP_DELAY THEN
      pump_running := TRUE;
      pump_timer := 0;
    END_IF;
  ELSIF NOT pump_requested AND pump_running THEN
    pump_timer := pump_timer + 1;
    IF pump_timer >= PUMP_DELAY THEN
      pump_running := FALSE;
      pump_timer := 0;
    END_IF;
  ELSE
    pump_timer := 0;
  END_IF;

  (* ========================================================= *)
  (* 3. Compute flows                                          *)
  (* ========================================================= *)
  IF pump_running THEN
    pump_flow := INT_TO_REAL(cmd_pump_speed) * PUMP_MAX_FLOW / 100.0;
    IF pump_flow < 0.0 THEN pump_flow := 0.0; END_IF;
    IF pump_flow > PUMP_MAX_FLOW THEN pump_flow := PUMP_MAX_FLOW; END_IF;
  ELSE
    pump_flow := 0.0;
  END_IF;

  (* ========================================================= *)
  (* 4. Tank mass balance — P1: Raw Water                      *)
  (*    inflow: PR valve open → external source                *)
  (*    outflow: pump + P valve → UF tank                      *)
  (* ========================================================= *)
  IF pr_valve_open THEN
    rw_tank_level := rw_tank_level + PR_INFLOW_RATE * DT_SEC / 60.0;
  END_IF;
  IF pump_running AND p_valve_open THEN
    rw_tank_level := rw_tank_level - pump_flow * DT_SEC / 60.0;
  END_IF;
  IF rw_tank_level < 0.0 THEN rw_tank_level := 0.0; END_IF;
  IF rw_tank_level > RW_TANK_MAX THEN rw_tank_level := RW_TANK_MAX; END_IF;

  (* ========================================================= *)
  (* 5. Tank mass balance — P2: Chemical tanks                 *)
  (*    drain when valve open, no inflow modeled               *)
  (* ========================================================= *)
  IF nacl_valve_open THEN
    nacl_level := nacl_level - DOSING_RATE * DT_SEC / 60.0;
  END_IF;
  IF nacl_level < 0.0 THEN nacl_level := 0.0; END_IF;
  IF nacl_level > CHEM_TANK_MAX THEN nacl_level := CHEM_TANK_MAX; END_IF;

  IF naocl_valve_open THEN
    naocl_level := naocl_level - DOSING_RATE * DT_SEC / 60.0;
  END_IF;
  IF naocl_level < 0.0 THEN naocl_level := 0.0; END_IF;
  IF naocl_level > CHEM_TANK_MAX THEN naocl_level := CHEM_TANK_MAX; END_IF;

  IF hcl_valve_open THEN
    hcl_level := hcl_level - DOSING_RATE * DT_SEC / 60.0;
  END_IF;
  IF hcl_level < 0.0 THEN hcl_level := 0.0; END_IF;
  IF hcl_level > CHEM_TANK_MAX THEN hcl_level := CHEM_TANK_MAX; END_IF;

  (* ========================================================= *)
  (* 6. Tank mass balance — P3: UF tank                        *)
  (*    inflow from P1 pump when P valve open                  *)
  (*    outflow via drain and ROFT valves                      *)
  (* ========================================================= *)
  IF pump_running AND p_valve_open THEN
    uf_tank_level := uf_tank_level + pump_flow * DT_SEC / 60.0;
  END_IF;
  IF uf_drain_open THEN
    uf_tank_level := uf_tank_level - UF_DRAIN_RATE * DT_SEC / 60.0;
  END_IF;
  IF uf_roft_open THEN
    uf_tank_level := uf_tank_level - UF_DRAIN_RATE * DT_SEC / 60.0;
  END_IF;
  IF uf_tank_level < 0.0 THEN uf_tank_level := 0.0; END_IF;
  IF uf_tank_level > UF_TANK_MAX THEN uf_tank_level := UF_TANK_MAX; END_IF;

  (* ========================================================= *)
  (* 7. Write outputs to bridge registers                      *)
  (* ========================================================= *)
  out_rw_level := REAL_TO_INT(rw_tank_level);
  out_rw_flow := REAL_TO_INT(pump_flow);
  out_nacl_level := REAL_TO_INT(nacl_level);
  out_naocl_level := REAL_TO_INT(naocl_level);
  out_hcl_level := REAL_TO_INT(hcl_level);
  out_uf_level := REAL_TO_INT(uf_tank_level);

  IF pr_valve_open THEN out_pr_valve_sts := 1; ELSE out_pr_valve_sts := 0; END_IF;
  IF p6b_valve_open THEN out_p6b_valve_sts := 1; ELSE out_p6b_valve_sts := 0; END_IF;
  IF p_valve_open THEN out_p_valve_sts := 1; ELSE out_p_valve_sts := 0; END_IF;
  IF pump_running THEN out_pump_sts := 1; ELSE out_pump_sts := 0; END_IF;
  out_pump_fault := 0;  (* no fault model yet *)
  IF nacl_valve_open THEN out_nacl_valve_sts := 1; ELSE out_nacl_valve_sts := 0; END_IF;
  IF naocl_valve_open THEN out_naocl_valve_sts := 1; ELSE out_naocl_valve_sts := 0; END_IF;
  IF hcl_valve_open THEN out_hcl_valve_sts := 1; ELSE out_hcl_valve_sts := 0; END_IF;
  IF uf_valve_open THEN out_uf_valve_sts := 1; ELSE out_uf_valve_sts := 0; END_IF;
  IF uf_drain_open THEN out_uf_drain_sts := 1; ELSE out_uf_drain_sts := 0; END_IF;
  IF uf_roft_open THEN out_uf_roft_sts := 1; ELSE out_uf_roft_sts := 0; END_IF;
  IF uf_bwp_open THEN out_uf_bwp_sts := 1; ELSE out_uf_bwp_sts := 0; END_IF;

END_PROGRAM


CONFIGURATION Config0
  VAR_GLOBAL
    (* Bridge command inputs *)
    cmd_pr_valve AT %QW200 : INT;
    cmd_p6b_valve AT %QW201 : INT;
    cmd_p_valve AT %QW202 : INT;
    cmd_pump_start AT %QW203 : INT;
    cmd_pump_stop AT %QW204 : INT;
    cmd_nacl_valve AT %QW205 : INT;
    cmd_naocl_valve AT %QW206 : INT;
    cmd_hcl_valve AT %QW207 : INT;
    cmd_uf_valve AT %QW208 : INT;
    cmd_uf_drain AT %QW209 : INT;
    cmd_uf_roft AT %QW210 : INT;
    cmd_uf_bwp AT %QW211 : INT;
    cmd_pump_speed AT %QW220 : INT;
    (* Bridge sensor outputs *)
    out_rw_level AT %QW300 : INT;
    out_rw_flow AT %QW301 : INT;
    out_nacl_level AT %QW302 : INT;
    out_naocl_level AT %QW303 : INT;
    out_hcl_level AT %QW304 : INT;
    out_uf_level AT %QW305 : INT;
    out_pr_valve_sts AT %QW320 : INT;
    out_p6b_valve_sts AT %QW321 : INT;
    out_p_valve_sts AT %QW322 : INT;
    out_pump_sts AT %QW323 : INT;
    out_pump_fault AT %QW324 : INT;
    out_nacl_valve_sts AT %QW325 : INT;
    out_naocl_valve_sts AT %QW326 : INT;
    out_hcl_valve_sts AT %QW327 : INT;
    out_uf_valve_sts AT %QW328 : INT;
    out_uf_drain_sts AT %QW329 : INT;
    out_uf_roft_sts AT %QW330 : INT;
    out_uf_bwp_sts AT %QW331 : INT;
  END_VAR

  RESOURCE Res0 ON PLC
    TASK task_SimulatorProgram(INTERVAL := T#100ms, PRIORITY := 0);
    PROGRAM SimulatorProgram_instance : SimulatorProgram;
  END_RESOURCE
END_CONFIGURATION
