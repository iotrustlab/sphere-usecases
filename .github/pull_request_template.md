# Pull Request

## 📋 Summary

Brief description of what this PR adds or changes.

## 🎯 Type of Contribution

- [ ] New use case
- [ ] Improvement to existing use case
- [ ] New implementation (Rockwell/OpenPLC)
- [ ] Security experiment
- [ ] Documentation update
- [ ] Bug fix
- [ ] Other (please describe)

## 🏭 Use Case Information

### Use Case Name
<!-- If this is a new use case, provide the name -->

### Process Description
<!-- Brief description of the industrial process -->

### Implementation Status
- [ ] Rockwell implementation (L5X files)
- [ ] OpenPLC implementation (ST files and Python simulation)
- [ ] Both implementations

## 📁 Files Added/Modified

### New Files
<!-- List new files added -->

### Modified Files
<!-- List existing files that were modified -->

## 🔧 Implementation Details

### Rockwell Implementation
- [ ] L5X files included
- [ ] Validation script works (`./implementations/rockwell/scripts/validate.sh`)
- [ ] Deployment script ready (`./implementations/rockwell/scripts/deploy.sh`)
- [ ] I/O mapping complete and consistent

### OpenPLC Implementation
- [ ] Structured Text programs included
- [ ] Python simulation models included
- [ ] Local execution script works (`./implementations/openplc/scripts/run_local.sh`)
- [ ] Simulation tested locally

## 📚 Documentation

### Process Documentation
- [ ] `docs/process_overview.md` - Complete process description
- [ ] `docs/io_map.csv` - Complete I/O mapping with safety notes
- [ ] `docs/pid.pdf` - P&ID diagram (or placeholder if not available)
- [ ] `README.md` - Use case overview and quick start guide

### Security Experiments
- [ ] Experiment descriptions in `experiments/`
- [ ] Attack scenarios documented
- [ ] Recovery procedures included
- [ ] Safety considerations documented

## 🧪 Testing

### Validation
- [ ] All validation scripts run successfully
- [ ] No validation errors or warnings
- [ ] I/O mapping consistency verified

### Simulation
- [ ] OpenPLC simulation runs locally (if applicable)
- [ ] Process model behaves as expected
- [ ] Security experiments tested in simulation

### Safety
- [ ] Safety considerations documented
- [ ] Safety interlocks included in control logic
- [ ] Recovery procedures tested

## 🛡️ Security Considerations

### Attack Scenarios
<!-- Describe any security experiments or attack scenarios included -->

### Safety Measures
<!-- Describe safety measures and interlocks implemented -->

### Recovery Procedures
<!-- Describe how to recover from attacks or failures -->

## 📋 Checklist

### Code Quality
- [ ] Code follows naming conventions
- [ ] Scripts are executable and properly formatted
- [ ] No hardcoded values or sensitive information
- [ ] Comments explain complex logic

### Documentation
- [ ] All required documentation files present
- [ ] Documentation is clear and complete
- [ ] Examples and usage instructions provided
- [ ] Safety considerations clearly documented

### Testing
- [ ] All tests pass
- [ ] Validation scripts work correctly
- [ ] Simulation runs without errors
- [ ] Security experiments are safe and documented

## 🔗 Related Issues

<!-- Link to any related GitHub issues -->

## 📸 Screenshots/Diagrams

<!-- If applicable, include screenshots or diagrams -->

## 🚀 Deployment Notes

<!-- Any special deployment considerations or requirements -->

## 📝 Additional Notes

<!-- Any additional information that reviewers should know -->

---

## Reviewer Checklist

- [ ] Use case follows required structure
- [ ] All required files are present
- [ ] Validation scripts work correctly
- [ ] Documentation is complete and accurate
- [ ] Safety considerations are adequate
- [ ] Security experiments are well-documented
- [ ] I/O mapping is consistent
- [ ] Naming conventions are followed
- [ ] Testing has been performed
- [ ] Ready for merge
