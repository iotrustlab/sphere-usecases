# Address Attribute Fix Summary

## Problem
The generated XML files had location information as child elements (`<location>%IX2.0</location>`) which caused XML schema validation errors:
```
Element '{http://www.plcopen.org/xml/tc6_0201}variable', attribute 'location': The attribute 'location' is not allowed.
```

## Root Cause Analysis
After investigating the OpenPLC Editor source code and the PLCopen XML schema, we discovered:

1. **OpenPLC Editor Source Code**: Uses `var.setaddress(location)` and `var.getaddress()` methods
2. **PLCopen XML Schema**: Defines `<xsd:attribute name="address" type="xsd:string" use="optional"/>` for variable elements
3. **Schema Compliance**: Location information must be an **attribute** named `address`, not a child element

## Solution
Modified `crossplc/openplc_emitter.py` in the `_create_variable_element` method:

**Before:**
```python
# Add location as attribute if this is an I/O variable
if hasattr(tag, 'location') and tag.location:
    var_elem.set("location", tag.location)
```

**After:**
```python
# Add address as attribute if this is an I/O variable
if hasattr(tag, 'location') and tag.location:
    var_elem.set("address", tag.location)
```

## Key Findings
- **PLCopen XML Schema**: Location information is defined as an optional `address` attribute on `<variable>` elements
- **OpenPLC Editor**: Expects `address` attribute, not `location` attribute or child element
- **XML Structure**: `<variable name="di_2_0" address="%IX2.0">` is the correct format

## Results
✅ **XML Schema Validation**: Both controller and simulator projects now pass validation
✅ **Address Attributes**: I/O variables now have proper `address="%IX2.0"` attributes
✅ **Coverage**: 3 mapped, 27 policy-mapped, 4 unmapped I/O references
✅ **Structure**: Variables are properly declared in both POU interface and globalVars sections
✅ **Schema Compliance**: Generated XML now conforms to the PLCopen XML schema

## Generated Files
- `~/Development/sphere-usecases/water-treatment/implementations/openplc/projects/controller_project/plc.xml`
- `~/Development/sphere-usecases/water-treatment/implementations/openplc/projects/simulator_project/plc.xml`

Both files now contain properly formatted address attributes and should be fully compatible with the OpenPLC Editor.

## Technical Details
- **Schema Reference**: `/Users/lag/Development/OpenPLC_Editor/editor/plcopen/tc6_xml_v201.xsd`
- **Attribute Definition**: `<xsd:attribute name="address" type="xsd:string" use="optional"/>`
- **OpenPLC Editor Methods**: `var.setaddress(location)` and `var.getaddress()`
