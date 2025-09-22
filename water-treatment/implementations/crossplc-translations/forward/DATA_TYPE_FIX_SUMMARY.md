# Data Type Compatibility Fix Summary

## Problem
The generated ST code had **data type incompatibility errors** during Matiec compilation:

```
/media/psf/Home/Development/sphere-usecases/water-treatment/implementations/openplc/projects/controller_project/build/plc.st:143-4..143-31: error: Incompatible data types for ':=' operation.
In section: PROGRAM MainProgram
0143:   P1.RW_Tank_tnk_lvl := ai_7_0;
```

## Root Cause Analysis
**Data Type Mismatch**:
- **Rockwell UDT fields**: `P1.RW_Tank_tnk_lvl` declared as `REAL` (floating point)
- **IEC I/O variables**: `ai_7_0` declared as `INT` (integer)
- **Assignment failure**: Cannot assign `INT` to `REAL` field

**Source of Problem**:
1. **I/O Mapping Policy**: Hardcoded to use `INT` for analog I/O
2. **CSV Override**: CSV file entries also used `INT` for analog I/O
3. **Type Mismatch**: Rockwell UDT fields expect `REAL` values for analog data

## Solution

### 1. Fixed I/O Mapping Policy
**File**: `crossplc/io_map.py`
**Change**: Line 113 - Changed analog I/O policy from `INT` to `REAL`

```python
# Before
return iec_addr, "INT"

# After  
return iec_addr, "REAL"
```

### 2. Updated CSV Mapping File
**File**: `/Users/lag/Development/sphere-usecases/water-treatment/docs/io_map.csv`
**Change**: Updated all analog I/O entries from `INT` to `REAL`

```csv
# Before
Local:7:I.Ch0Data,%IW70,INT,pH sensor raw 0..32767
Local:7:O.Ch1Data,%QW71,INT,Analog output to dosing valve

# After
Local:7:I.Ch0Data,%IW70,REAL,pH sensor raw 0..32767
Local:7:O.Ch1Data,%QW71,REAL,Analog output to dosing valve
```

## Results
✅ **XML Generation**: Analog I/O variables now declared as `<REAL />` in XML
✅ **Data Type Compatibility**: `REAL` to `REAL` assignments now work
✅ **Matiec Compilation**: Should resolve "Incompatible data types" errors
✅ **I/O Coverage**: 3 mapped, 27 policy-mapped, 4 unmapped I/O references

## Technical Details
- **Rockwell UDT Fields**: `P1.RW_Tank_tnk_lvl : REAL` (from L5K file)
- **IEC I/O Variables**: `ai_7_0 : REAL` (now correctly mapped)
- **Assignment**: `P1.RW_Tank_tnk_lvl := ai_7_0;` (REAL := REAL ✅)

## Files Updated
1. `crossplc/io_map.py` - Fixed policy mapping for analog I/O
2. `/Users/lag/Development/sphere-usecases/water-treatment/docs/io_map.csv` - Updated CSV entries
3. Generated XML files now use correct `REAL` data types

## Next Steps
- Clean build directories to remove cached files
- Regenerate ST code to verify compilation success
- Test with OpenPLC Editor to ensure compatibility
