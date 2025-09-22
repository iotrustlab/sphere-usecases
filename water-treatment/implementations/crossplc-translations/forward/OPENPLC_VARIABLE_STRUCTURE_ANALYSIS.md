# OpenPLC Editor Variable Structure Analysis

## Overview
Analysis of how the OpenPLC Editor handles variable properties at the same abstraction level, based on investigation of the source code.

## Variable Properties Structure

### OpenPLC Editor VariablePanel Columns
The OpenPLC Editor's VariablePanel defines these columns in order:

1. **#** - Row number
2. **Name** - Variable name
3. **Class** - Variable class (Local, Global, External, etc.)
4. **Type** - Data type (BOOL, INT, REAL, etc.)
5. **Location** - Address/location (e.g., %IX2.0, %QW100)
6. **Initial Value** - Initial value
7. **Option** - Variable options (Constant, Retain, Non_retain)
8. **Documentation** - Documentation text

### Internal Variable Structure (_VariableInfos)
The OpenPLC Editor uses `_VariableInfos` class with these properties:

```python
__slots__ = ["Name", "Class", "Option", "Location", "InitialValue",
             "Edit", "Documentation", "Type", "Tree", "Number"]
```

### XML Schema Mapping
In the PLCopen XML schema, these properties map as follows:

| OpenPLC Property | XML Element/Attribute | Notes |
|----------------|----------------------|-------|
| Name | `<variable name="...">` | Required attribute |
| Class | Variable scope (inputVars, outputVars, localVars, etc.) | Determined by parent element |
| Type | `<type><BOOL/></type>` | Child element with data type |
| Location | `<variable address="...">` | **Key finding: Location → address attribute** |
| Initial Value | `<initialValue><simpleValue value="..."/></initialValue>` | Child element |
| Option | Variable list attributes (constant, retain, non_retain) | Parent varList attributes |
| Documentation | `<documentation><xhtml:p>...</xhtml:p></documentation>` | Child element |

## Key Findings

### 1. Location → Address Mapping
- **OpenPLC Editor**: Uses `Location` property in `_VariableInfos`
- **XML Schema**: Uses `address` attribute on `<variable>` element
- **Code Evidence**: `var.setaddress(location)` and `var.getaddress()` methods
- **Schema Definition**: `<xsd:attribute name="address" type="xsd:string" use="optional"/>`

### 2. Variable Class → XML Structure
- **Local/Global variables**: Appear in `<globalVars>` section
- **Input variables**: Appear in `<inputVars>` section  
- **Output variables**: Appear in `<outputVars>` section
- **Class determines**: Which XML section the variable appears in

### 3. Data Type Handling
- **Basic types**: `<BOOL/>`, `<INT/>`, `<REAL/>`, etc.
- **UDT types**: `<derived name="UDT_NAME"/>`
- **Array types**: `<array><dimension>...</dimension><baseType>...</baseType></array>`

### 4. Location Validation
- **Pattern matching**: Uses `LOCATION_MODEL` regex for validation
- **Format**: `%[IQM][XBWDL]?[0-9]+(\.[0-9]+)*`
- **Examples**: `%IX2.0`, `%QW100`, `%MX0.0`

## Implementation Implications

### For CrossPLC XML Emitter
1. **Use `address` attribute**: Not `location` attribute or child element
2. **Variable placement**: Put I/O variables in appropriate sections (inputVars/outputVars)
3. **Data type mapping**: Map Rockwell types to IEC types correctly
4. **Location format**: Use IEC address format (`%IX2.0` not `Local:2:I.Data.0`)

### For I/O Mapping
1. **Address generation**: Convert Rockwell `Local:X:I/Y.Data.Z` to IEC `%IX/Y.Z`
2. **Variable naming**: Generate stable IEC-compliant names
3. **Scope determination**: Input variables go to inputVars, output to outputVars
4. **Documentation**: Include Rockwell source as documentation

## Code References
- **VariablePanel**: `/Users/lag/Development/OpenPLC_Editor/editor/controls/VariablePanel.py`
- **VariableInfoCollector**: `/Users/lag/Development/OpenPLC_Editor/editor/plcopen/VariableInfoCollector.py`
- **XML Schema**: `/Users/lag/Development/OpenPLC_Editor/editor/plcopen/tc6_xml_v201.xsd`
- **Location Editor**: `/Users/lag/Development/OpenPLC_Editor/editor/controls/LocationCellEditor.py`

## Conclusion
The OpenPLC Editor's variable structure is well-defined and consistent. The key insight is that the **Location** property in the editor corresponds to the **address** attribute in the XML schema, not a child element or different attribute name. This understanding enables proper XML generation that is compatible with the OpenPLC Editor.
