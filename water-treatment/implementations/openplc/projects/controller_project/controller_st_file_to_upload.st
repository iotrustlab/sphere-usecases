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
  VAR_EXTERNAL
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
  VAR_EXTERNAL
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
    ao_10_0 AT %QW100 : REAL;
    di_2_0 AT %IX2.0 : BOOL;
    di_2_1 AT %IX2.1 : BOOL;
    di_2_10 AT %IX2.10 : BOOL;
    di_2_11 AT %IX2.11 : BOOL;
    di_2_2 AT %IX2.2 : BOOL;
    di_2_3 AT %IX2.3 : BOOL;
    di_2_4 AT %IX2.4 : BOOL;
    di_2_5 AT %IX2.5 : BOOL;
    di_2_6 AT %IX2.6 : BOOL;
    di_2_8 AT %IX2.8 : BOOL;
    di_2_9 AT %IX2.9 : BOOL;
    do_5_0 AT %QX5.0 : BOOL;
    do_5_1 AT %QX5.1 : BOOL;
    do_5_10 AT %QX5.10 : BOOL;
    do_5_11 AT %QX5.11 : BOOL;
    do_5_2 AT %QX5.2 : BOOL;
    do_5_3 AT %QX5.3 : BOOL;
    do_5_4 AT %QX5.4 : BOOL;
    do_5_5 AT %QX5.5 : BOOL;
    do_5_6 AT %QX5.6 : BOOL;
    do_5_7 AT %QX5.7 : BOOL;
    do_5_8 AT %QX5.8 : BOOL;
    do_5_9 AT %QX5.9 : BOOL;
    ai_7_0 AT %IW70 : REAL;
    di_7_ch0halarm AT %IX7.0 : BOOL;
    di_7_ch0hhalarm AT %IX7.0 : BOOL;
    di_7_ch0lalarm AT %IX7.0 : BOOL;
    di_7_ch0llalarm AT %IX7.0 : BOOL;
    ai_7_1 AT %IW71 : REAL;
    ai_7_2 AT %IW72 : REAL;
    ai_7_3 AT %IW73 : REAL;
    ai_7_4 AT %IW74 : REAL;
    ai_7_5 AT %IW75 : REAL;
  END_VAR

  RESOURCE res_MainProgram ON PLC
    TASK task_MainProgram(INTERVAL := T#100ms,PRIORITY := 0);
    PROGRAM MainProgram_instance : MainProgram;
  END_RESOURCE
END_CONFIGURATION

(*DBG:char md5[] = "527971c67af0de80c69f5223004ec189";*)
(*DBG:/**)
(*DBG: * This file is part of OpenPLC Runtime*)
(*DBG: **)
(*DBG: * Copyright (C) 2023 Autonomy, GP Orcullo*)
(*DBG: * Based on the work by GP Orcullo on Beremiz for uC*)
(*DBG: **)
(*DBG: * This program is free software; you can redistribute it and/or*)
(*DBG: * modify it under the terms of the GNU General Public License*)
(*DBG: * as published by the Free Software Foundation; either version 2*)
(*DBG: * of the License, or (at your option) any later version.*)
(*DBG: **)
(*DBG: * This program is distributed in the hope that it will be useful,*)
(*DBG: * but WITHOUT ANY WARRANTY; without even the implied warranty of*)
(*DBG: * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the*)
(*DBG: * GNU General Public License for more details.*)
(*DBG: **)
(*DBG: * You should have received a copy of the GNU General Public License*)
(*DBG: * along with this program; If not, see <http://www.gnu.org/licenses/>.*)
(*DBG: **)
(*DBG: */*)
(*DBG:*)
(*DBG:#include <stdbool.h>*)
(*DBG:*)
(*DBG:#include "iec_types_all.h"*)
(*DBG:#include "POUS.h"*)
(*DBG:*)
(*DBG:#define SAME_ENDIANNESS      0*)
(*DBG:#define REVERSE_ENDIANNESS   1*)
(*DBG:*)
(*DBG:uint8_t endianness;*)
(*DBG:*)
(*DBG:*)
(*DBG:extern __IEC_REAL_t CONFIG__AO_10_0;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_2_0;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_2_1;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_2_10;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_2_11;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_2_2;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_2_3;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_2_4;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_2_5;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_2_6;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_2_8;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_2_9;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DO_5_0;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DO_5_1;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DO_5_10;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DO_5_11;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DO_5_2;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DO_5_3;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DO_5_4;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DO_5_5;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DO_5_6;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DO_5_7;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DO_5_8;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DO_5_9;*)
(*DBG:extern __IEC_REAL_t CONFIG__AI_7_0;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_7_CH0HALARM;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_7_CH0HHALARM;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_7_CH0LALARM;*)
(*DBG:extern __IEC_BOOL_t CONFIG__DI_7_CH0LLALARM;*)
(*DBG:extern __IEC_REAL_t CONFIG__AI_7_1;*)
(*DBG:extern __IEC_REAL_t CONFIG__AI_7_2;*)
(*DBG:extern __IEC_REAL_t CONFIG__AI_7_3;*)
(*DBG:extern __IEC_REAL_t CONFIG__AI_7_4;*)
(*DBG:extern __IEC_REAL_t CONFIG__AI_7_5;*)
(*DBG:extern MAINPROGRAM RES_MAINPROGRAM__MAINPROGRAM_INSTANCE;*)
(*DBG:*)
(*DBG:static const struct {*)
(*DBG:    void *ptr;*)
(*DBG:    __IEC_types_enum type;*)
(*DBG:} debug_vars[] = {*)
(*DBG:    {&(CONFIG__AO_10_0), REAL_ENUM},*)
(*DBG:    {&(CONFIG__DI_2_0), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DI_2_1), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DI_2_10), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DI_2_11), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DI_2_2), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DI_2_3), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DI_2_4), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DI_2_5), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DI_2_6), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DI_2_8), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DI_2_9), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DO_5_0), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DO_5_1), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DO_5_10), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DO_5_11), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DO_5_2), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DO_5_3), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DO_5_4), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DO_5_5), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DO_5_6), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DO_5_7), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DO_5_8), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DO_5_9), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__AI_7_0), REAL_ENUM},*)
(*DBG:    {&(CONFIG__DI_7_CH0HALARM), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DI_7_CH0HHALARM), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DI_7_CH0LALARM), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__DI_7_CH0LLALARM), BOOL_ENUM},*)
(*DBG:    {&(CONFIG__AI_7_1), REAL_ENUM},*)
(*DBG:    {&(CONFIG__AI_7_2), REAL_ENUM},*)
(*DBG:    {&(CONFIG__AI_7_3), REAL_ENUM},*)
(*DBG:    {&(CONFIG__AI_7_4), REAL_ENUM},*)
(*DBG:    {&(CONFIG__AI_7_5), REAL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_2_0), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_2_1), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_2_10), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_2_11), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_2_2), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_2_3), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_2_4), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_2_5), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_2_6), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_2_8), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_2_9), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.AI_7_0), REAL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_7_CH0HALARM), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_7_CH0HHALARM), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_7_CH0LALARM), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DI_7_CH0LLALARM), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.AI_7_1), REAL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.AI_7_2), REAL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.AI_7_3), REAL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.AI_7_4), REAL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.AI_7_5), REAL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.AO_10_0), REAL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DO_5_0), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DO_5_1), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DO_5_10), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DO_5_11), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DO_5_2), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DO_5_3), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DO_5_4), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DO_5_5), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DO_5_6), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DO_5_7), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DO_5_8), BOOL_ENUM},*)
(*DBG:    {&(RES_MAINPROGRAM__MAINPROGRAM_INSTANCE.DO_5_9), BOOL_ENUM},*)
(*DBG:};*)
(*DBG:*)
(*DBG:#define VAR_COUNT               68*)
(*DBG:*)
(*DBG:uint16_t get_var_count(void)*)
(*DBG:{*)
(*DBG:    return VAR_COUNT;*)
(*DBG:}*)
(*DBG:*)
(*DBG:size_t get_var_size(size_t idx)*)
(*DBG:{*)
(*DBG:    if (idx >= VAR_COUNT)*)
(*DBG:    {*)
(*DBG:        return 0;*)
(*DBG:    }*)
(*DBG:    switch (debug_vars[idx].type) {*)
(*DBG:    case REAL_ENUM:*)
(*DBG:        return sizeof(REAL);*)
(*DBG:    case BOOL_ENUM:*)
(*DBG:        return sizeof(BOOL);*)
(*DBG:    default:*)
(*DBG:        return 0;*)
(*DBG:    }*)
(*DBG:}*)
(*DBG:*)
(*DBG:void *get_var_addr(size_t idx)*)
(*DBG:{*)
(*DBG:    void *ptr = debug_vars[idx].ptr;*)
(*DBG:*)
(*DBG:    switch (debug_vars[idx].type) {*)
(*DBG:    case REAL_ENUM:*)
(*DBG:        return (void *)&((__IEC_REAL_t *) ptr)->value;*)
(*DBG:    case BOOL_ENUM:*)
(*DBG:        return (void *)&((__IEC_BOOL_t *) ptr)->value;*)
(*DBG:    default:*)
(*DBG:        return 0;*)
(*DBG:    }*)
(*DBG:}*)
(*DBG:*)
(*DBG:void force_var(size_t idx, bool forced, void *val)*)
(*DBG:{*)
(*DBG:    void *ptr = debug_vars[idx].ptr;*)
(*DBG:*)
(*DBG:    if (forced) {*)
(*DBG:        size_t var_size = get_var_size(idx);*)
(*DBG:        switch (debug_vars[idx].type) {*)
(*DBG:        case REAL_ENUM: {*)
(*DBG:            memcpy(&((__IEC_REAL_t *) ptr)->value, val, var_size);*)
(*DBG:            //((__IEC_REAL_t *) ptr)->value = *((REAL *) val);*)
(*DBG:            ((__IEC_REAL_t *) ptr)->flags |= __IEC_FORCE_FLAG;*)
(*DBG:            break;*)
(*DBG:        }*)
(*DBG:        case BOOL_ENUM: {*)
(*DBG:            memcpy(&((__IEC_BOOL_t *) ptr)->value, val, var_size);*)
(*DBG:            //((__IEC_BOOL_t *) ptr)->value = *((BOOL *) val);*)
(*DBG:            ((__IEC_BOOL_t *) ptr)->flags |= __IEC_FORCE_FLAG;*)
(*DBG:            break;*)
(*DBG:        }*)
(*DBG:        default:*)
(*DBG:            break;*)
(*DBG:        }*)
(*DBG:    } else {*)
(*DBG:        switch (debug_vars[idx].type) {*)
(*DBG:        case REAL_ENUM:*)
(*DBG:            ((__IEC_REAL_t *) ptr)->flags &= ~__IEC_FORCE_FLAG;*)
(*DBG:            break;*)
(*DBG:        case BOOL_ENUM:*)
(*DBG:            ((__IEC_BOOL_t *) ptr)->flags &= ~__IEC_FORCE_FLAG;*)
(*DBG:            break;*)
(*DBG:        default:*)
(*DBG:            break;*)
(*DBG:        }*)
(*DBG:    }*)
(*DBG:}*)
(*DBG:*)
(*DBG:void swap_bytes(void *ptr, size_t size) *)
(*DBG:{*)
(*DBG:    uint8_t *bytePtr = (uint8_t *)ptr;*)
(*DBG:    size_t i;*)
(*DBG:    for (i = 0; i < size / 2; ++i) *)
(*DBG:    {*)
(*DBG:        uint8_t temp = bytePtr[i];*)
(*DBG:        bytePtr[i] = bytePtr[size - 1 - i];*)
(*DBG:        bytePtr[size - 1 - i] = temp;*)
(*DBG:    }*)
(*DBG:}*)
(*DBG:*)
(*DBG:void trace_reset(void)*)
(*DBG:{*)
(*DBG:    for (size_t i=0; i < VAR_COUNT; i++) *)
(*DBG:    {*)
(*DBG:        force_var(i, false, 0);*)
(*DBG:    }*)
(*DBG:}*)
(*DBG:*)
(*DBG:void set_trace(size_t idx, bool forced, void *val)*)
(*DBG:{*)
(*DBG:    if (idx >= 0 && idx < VAR_COUNT) *)
(*DBG:    {*)
(*DBG:        if (endianness == REVERSE_ENDIANNESS)*)
(*DBG:        {*)
(*DBG:            // Aaaaarghhhh... Stupid AVR is Big Endian.*)
(*DBG:            swap_bytes(val, get_var_size(idx));*)
(*DBG:        }*)
(*DBG:*)
(*DBG:        force_var(idx, forced, val);*)
(*DBG:    }*)
(*DBG:}*)
(*DBG:*)
(*DBG:void set_endianness(uint8_t value)*)
(*DBG:{*)
(*DBG:    if (value == SAME_ENDIANNESS || value == REVERSE_ENDIANNESS)*)
(*DBG:    {*)
(*DBG:        endianness = value;*)
(*DBG:    }*)
(*DBG:}*)
(*DBG:*)