# OpenPLC I/O Mapping Policy and Adapters

This document explains the I/O mapping policy for converting Rockwell `Local:` addresses to IEC 61131-3 I/O addresses in OpenPLC projects.

## Address Families

### Digital I/O
- **Input bits**: `%IX<slot>.<bit>` - Digital inputs from hardware modules
- **Output bits**: `%QX<slot>.<bit>` - Digital outputs to hardware modules

### Analog I/O
- **Input words**: `%IW<index>` - 16-bit analog inputs (0-32767 range)
- **Output words**: `%QW<index>` - 16-bit analog outputs (0-32767 range)
- **Input double words**: `%ID<index>` - 32-bit analog inputs
- **Output double words**: `%QD<index>` - 32-bit analog outputs

## Slot-to-Index Policy

### Digital I/O Mapping
- **Input**: `Local:<slot>:I.Data.<bit>` → `%IX<slot>.<bit>`
- **Output**: `Local:<slot>:O.Data.<bit>` → `%QX<slot>.<bit>`

### Analog I/O Mapping
- **Input**: `Local:<slot>:I.Ch<channel>Data` → `%IW<slot*10 + channel>`
- **Output**: `Local:<slot>:O.Ch<channel>Data` → `%QW<slot*10 + channel>`

**Examples:**
- `Local:7:I.Ch0Data` → `%IW70` (slot 7, channel 0)
- `Local:7:I.Ch1Data` → `%IW71` (slot 7, channel 1)
- `Local:8:O.Ch0Data` → `%QW80` (slot 8, channel 0)

## Data Type Conventions

### Digital I/O
- **Type**: `BOOL`
- **Range**: `TRUE`/`FALSE`
- **Usage**: Discrete on/off signals, status indicators, control commands

### Analog I/O
- **Type**: `INT` (16-bit) or `DINT` (32-bit)
- **Range**: 0-32767 (16-bit) or 0-2147483647 (32-bit)
- **Scaling**: Raw counts from hardware modules
- **Engineering Units**: Converted in application logic

## Scaling and Engineering Units

### Raw to Engineering Conversion
```iecst
VAR_GLOBAL
  ai_ph_raw AT %IW70 : INT; // Rockwell: Local:7:I.Ch0Data
END_VAR

VAR
  ph_value : REAL;
END_VAR

// Convert raw 0-32767 to pH 0-14
ph_value := REAL(ai_ph_raw) * 14.0 / 32767.0;
```

### Common Scaling Factors
- **pH sensors**: 0-32767 → 0-14 pH
- **Temperature**: 0-32767 → -40°C to +125°C
- **Pressure**: 0-32767 → 0-100 PSI
- **Flow**: 0-32767 → 0-100 GPM

## I/O Mapping Modes

### 1. IEC-AT Mode (Default)
- Generates `AT %I*/%Q*` bindings from CSV mapping
- Direct hardware addressing
- Best for OpenPLC Editor compatibility

### 2. Comment-Only Mode
- Declares variables without `AT` bindings
- Adds `// TODO map: Local:...` comments
- Useful for initial porting and manual mapping

### 3. Adapter Mode
- Logical tags only (no `AT` bindings)
- Generates bridge mapping files (e.g., Modbus)
- Useful for protocol translation scenarios

## Edge Cases and Limitations

### Unmapped Addresses
- Addresses not in `io_map.csv` will use policy fallback
- If policy fails, variables are declared without `AT` bindings
- Coverage report highlights unmapped entries

### Module Configuration
- I/O mapping assumes standard module configurations
- Custom module types may require manual mapping
- Verify module addressing with hardware documentation

### Signedness
- Analog inputs are typically unsigned (0-32767)
- Some sensors may use signed ranges (-16384 to +16383)
- Check sensor documentation for proper scaling

## Bridge File Formats

### Modbus Mapping (Adapter Mode)
```csv
tag,register,type,notes
ai_ph_raw,30070,INT,from Local:7:I.Ch0Data
do_pump_enable,10035,BOOL,from Local:3:O.Data.5
```

### OPC-UA Mapping
```csv
tag,node_id,type,notes
ai_ph_raw,ns=2;s=pH_Sensor,INT,from Local:7:I.Ch0Data
do_pump_enable,ns=2;s=Pump_Enable,BOOL,from Local:3:O.Data.5
```

## Validation and Testing

### Coverage Report
The I/O mapping system generates coverage reports showing:
- **Mapped**: Addresses found in CSV with successful mapping
- **Policy Mapped**: Addresses mapped using policy rules
- **Unmapped**: Addresses that need manual mapping

### Roundtrip Validation
- ST → XML → ST conversion preserves I/O mappings
- Validation ensures no `Local:` references remain
- Coverage reports verify mapping completeness

## Best Practices

1. **Maintain CSV**: Keep `io_map.csv` synchronized with hardware changes
2. **Document Changes**: Update this document when adding new module types
3. **Test Coverage**: Run coverage reports to identify unmapped addresses
4. **Validate Roundtrip**: Ensure I/O mappings survive conversion cycles
5. **Hardware Verification**: Verify I/O addresses with actual hardware configuration

