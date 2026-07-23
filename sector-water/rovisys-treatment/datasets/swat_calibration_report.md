# SWaT Dataset Calibration Report

## Overview

This report documents the calibration of SPHERE Water Treatment invariant rules against the SWaT (Secure Water Treatment) dataset from iTrust/SUTD.

**Dataset:** SWaT v1
**Source:** https://itrust.sutd.edu.sg/itrust-labs_datasets/
**Reference:** Goh et al., "A Dataset to Support Research in the Design of Secure Water Treatment Systems", 2017

## Dataset Statistics

### Normal Operation Ranges

Extracted from first 1000 samples of attack dataset (all labeled "Normal"):

| SWaT Tag | SPHERE Tag | Min | Max | Mean | Std | Max Rate |
|----------|------------|-----|-----|------|-----|----------|
| LIT101 | RW_Tank_Level | 522.5 | 655.7 | 546.3 | 33.7 | 1.69 |
| FIT101 | RW_Pump_Flow | 2.42 | 2.68 | 2.54 | 0.07 | 0.06 |
| LIT301 | UF_UFFT_Tank_Level | 902.1 | 1012.3 | 956.2 | 26.4 | 2.12 |

### Valve/Pump State Encoding

SWaT uses different encoding than SPHERE:
- **SWaT:** 1=OFF/CLOSED, 2=ON/OPEN
- **SPHERE:** 0=OFF/CLOSED, 1=ON/OPEN

The `swat_loader.py` does NOT automatically transform these values. Future work should add transform logic.

## Invariant Rule Validation

### Test Methodology

1. Loaded 5000 samples from SWaT attack dataset
2. Mapped Stage 1-3 tags to SPHERE canonical names
3. Ran `invariant_check.py` with `water-treatment.yaml` rules

### Results (5000 samples)

```
Bundle: swat-attack-bundle
Samples: 5000
Violations: 0
Attack Windows: 3 (samples 1754-2693, 3068-3510, 4920-4999)
```

**Finding:** Current SPHERE invariant rules did not detect the SWaT attacks in this sample.

### Analysis

1. **Range Rules:** SWaT attacks often stay within normal operating ranges
   - Attacks modify setpoints gradually or at physically plausible rates
   - Simple min/max bounds are insufficient

2. **Rate-of-Change Rules:** Attack rates may be below detection thresholds
   - SPHERE threshold: 50 mm/sample
   - SWaT max observed: ~2 mm/sample
   - Attacks use gradual changes to avoid detection

3. **Correlation Rules:** State encoding mismatch
   - SWaT uses 1/2 encoding, SPHERE uses 0/1
   - Rules checking "pump on implies flow" fail due to encoding

4. **Causality Rules:** Tag naming differences
   - Rules reference `RW_Pump_Start` (command), but SWaT only has `P101` (status)
   - Command tags not available in SWaT dataset

## Recommendations

### Immediate Fixes

1. **Add value transforms to loader:**
   ```python
   # Transform SWaT 1/2 encoding to SPHERE 0/1
   if swat_value == 2:
       sphere_value = 1
   else:
       sphere_value = 0
   ```

2. **Tighten rate-of-change thresholds:**
   ```yaml
   rate_of_change_rules:
     RW_Tank_Level:
       max_delta: 5  # Down from 50
   ```

3. **Add anomaly detection rules:**
   - Statistical deviation from rolling baseline
   - Correlation consistency between related sensors

### Future Enhancements

1. **Machine Learning Detection:**
   - Train on normal SWaT data
   - Detect anomalies based on learned patterns

2. **Multi-variate Rules:**
   - Correlate tank level changes with pump status AND flow readings
   - Check physical consistency across multiple sensors

3. **Time-series Analysis:**
   - Detect unusual patterns over longer windows
   - Identify slow-moving attacks

## SWaT Attack Types (Reference)

The SWaT dataset contains 36 attack scenarios:

| Attack Type | Description | Detection Strategy |
|-------------|-------------|-------------------|
| SSSP | Single Stage Single Point | Range/rate bounds |
| SSMP | Single Stage Multi Point | Correlation rules |
| MSSP | Multi Stage Single Point | Causality rules |
| MSMP | Multi Stage Multi Point | Multi-variate rules |

## Calibrated Profile Values

Based on SWaT normal data, recommended SPHERE profile adjustments:

```yaml
# profiles/swat-calibrated.yaml (proposed)
actuators:
  motorized_valve:
    tau_seconds: 30  # SWaT uses similar timing
  pump:
    spinup_seconds: 2

sensors:
  level:
    tau_seconds: 5
    noise_sigma_mm: 2  # SWaT shows ~1mm noise

alarms:
  RW_Tank:
    hh_mm: 800  # SWaT LIT101 rarely exceeds 700
    h_mm: 700
    l_mm: 400
    ll_mm: 300
```

## Conclusion

The initial validation shows that SPHERE's rule-based invariant detection is not sufficient to detect sophisticated SWaT attacks. This is expected - SWaT attacks are designed to evade simple detection.

**Next Steps:**
1. Implement value encoding transforms
2. Tighten detection thresholds based on calibration
3. Add statistical anomaly detection layer
4. Consider ML-based detection for subtle attacks

---

*Generated: 2026-03-21*
*Tool: tools/datasets/swat_loader.py*
