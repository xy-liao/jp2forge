# Security Guide for JP2Forge

> **Supported Python versions:** JP2Forge officially supports Python 3.8 through 3.12 (inclusive).

## Overview
This guide describes the security scanning, alert handling, and emergency response procedures for JP2Forge.

---

## 1. Dependency and Code Scanning
- **Automated scans**: All pushes, PRs, and weekly schedules run Safety (dependency) and Bandit (code) scans via GitHub Actions.
- **Severity policy**: CI/CD only fails for critical/high vulnerabilities. Low/medium issues are reported but do not block builds.
- **False positives**: Known false positives are documented in `.safety-policy.yml` and filtered from alerts.
- **Bandit config**: Subprocess and other non-applicable warnings are skipped (see `bandit.ini`).

## 2. Dependabot and Automated Updates
- **Dependabot**: Weekly checks for pip and GitHub Actions dependencies.
- **Auto-merge**: Patch-level security fixes are auto-merged if tests pass.
- **Manual review**: Major/minor updates require manual review.

## 3. Handling Vulnerabilities
- **Critical/High**: If a critical or high vulnerability is found:
  1. CI/CD fails and blocks merge.
  2. Triage immediately: assess exploitability in the context of JP2Forge (image processing, CLI, no network exposure).
  3. If exploitable, issue a security advisory and patch ASAP.
  4. If not exploitable, document rationale in `.safety-policy.yml` and unblock.
- **Low/Medium**: Document in `.safety-policy.yml` if not relevant. Otherwise, address in regular maintenance.

## 4. Alert Types That Can Be Safely Ignored
- **Subprocess warnings**: JP2Forge legitimately uses subprocess for CLI tools (e.g., Kakadu, ExifTool).
- **Random/Assert warnings**: Not used for security/crypto.
- **Pillow CVE-2021-25287**: Not exploitable in our usage (ICNS parser not used).
- **Other image library warnings**: Only if not used in a vulnerable way (document in `.safety-policy.yml`).

## 5. Emergency Response Procedures
- **If a critical vulnerability is confirmed:**
  1. Immediately restrict repository access if needed.
  2. Issue a GitHub Security Advisory.
  3. Patch and release a fixed version as soon as possible.
  4. Notify users via README, release notes, and security advisory.
  5. Document the incident and response in this file.

---

## Handling Dependency Security Scan Failures

### 1. Understanding Security Scan Types

**Safety (Dependency Vulnerabilities)**
- Scans Python packages in `requirements.txt` against known CVE database
- Reports vulnerabilities in installed dependencies
- May flag transitive dependencies (dependencies of dependencies)

**Bandit (Code Security)**
- Static analysis of Python code for security issues
- Flags potentially unsafe code patterns
- Already configured to skip common false positives for this project

### 2. Dependency Vulnerability Response Strategy

#### Step 1: Assess Severity
```bash
# Run safety scan with details
safety check --full-report

# Check specific package vulnerability
safety check --package pillow
```

**Severity Levels:**
- **Critical/High**: Immediate action required
- **Medium**: Plan update within 1-2 weeks  
- **Low**: Monitor and update in next release cycle

#### Step 2: Update Strategy Priority
1. **Direct Dependencies**: Update in `requirements.txt`
2. **Transitive Dependencies**: May require updating parent package
3. **System Dependencies**: ExifTool, jpylyzer (manual updates)

#### Step 3: Safe Update Process
```bash
# Create isolated test environment
python -m venv test_env
source test_env/bin/activate

# Test specific package update
pip install package_name==NEW_VERSION
python -m pytest tests/

# Run JP2Forge test suite
./test_jp2forge.sh

# Update requirements.txt if tests pass
```

### 3. Common JP2Forge Dependency Issues

#### Image Processing Libraries
```bash
# Pillow (PIL) - common vulnerability target
pip install --upgrade pillow>=10.0.0

# NumPy - numerical computing vulnerabilities
pip install --upgrade numpy>=1.24.0
```

#### XML Processing Libraries
```bash
# lxml - XML processing vulnerabilities
pip install --upgrade lxml>=4.9.3

# Already secured with defusedxml
pip install --upgrade defusedxml>=0.7.1
```

#### System Integration
```bash
# Update system dependencies
# macOS:
brew upgrade exiftool

# Linux:
sudo apt update && sudo apt upgrade libimage-exiftool-perl
```

### 4. Vulnerability Exemption Process

#### When Updates Aren't Immediately Available

**Create `.safety-policy.yml`:**
```yaml
# Security exemptions with justification
exemptions:
  - id: "CVE-2023-XXXXX"
    reason: "No fix available; mitigated by input validation"
    expires: "2024-12-31"
    
  - id: "CVE-2023-YYYYY"  
    reason: "False positive - not applicable to our use case"
    expires: "2024-06-30"
```

**Bandit Configuration `.bandit`:**
```ini
[bandit]
# Skip subprocess warnings for legitimate tool integration
skips = B404,B603,B607

# Skip XML warnings where defusedxml is used
exclude_dirs = examples/
```

### 5. CI/CD Integration

#### Failing Builds Strategy
```yaml
# In .github/workflows/security.yml
- name: Run Safety Check
  run: |
    safety check --json --output safety-report.json || true
    # Don't fail build, but create warning
    safety check || echo "::warning::Dependency vulnerabilities detected"
  continue-on-error: true
```

#### Gradual Enforcement
```bash
# Allow low severity, fail on high/critical
safety check --ignore 70612  # Ignore specific low-severity CVE

# Progressive tightening
safety check --severity medium  # Fail only on medium+ severity
```

### 6. Monitoring and Alerting

#### Weekly Security Reviews
```bash
# Automated security report generation
safety check --json | jq '.vulnerabilities[] | select(.vulnerability_id)'

# Dependency freshness check
pip list --outdated --format=json
```

#### GitHub Security Features
- Enable Dependabot alerts
- Configure Dependabot automatic PRs
- Use GitHub Security Advisories

### 7. Emergency Response Procedure

#### Critical Vulnerability Response
1. **Immediate Assessment** (< 4 hours)
   - Determine if vulnerability affects JP2Forge
   - Check if exploitation is possible in our context

2. **Rapid Mitigation** (< 24 hours)
   - Apply hotfix if available
   - Implement workaround if no fix exists
   - Document temporary measures

3. **Permanent Resolution** (< 1 week)
   - Deploy proper fix
   - Update dependencies
   - Enhance tests to prevent regression

### 8. Example Response Workflows

#### Pillow Vulnerability Example
```bash
# 1. Check current version
pip show pillow

# 2. Research vulnerability
safety check --package pillow --json

# 3. Test update compatibility
pip install --upgrade pillow
python -c "from PIL import Image; print('Basic import works')"

# 4. Run comprehensive tests
python -m cli.workflow test_images/ test_output/

# 5. Update requirements.txt
echo "pillow>=10.1.0  # Security fix for CVE-2023-XXXXX" >> requirements.txt
```

#### No-Fix-Available Scenario
```bash
# 1. Document the issue
echo "# SECURITY NOTICE: CVE-2023-XXXXX" >> SECURITY_NOTES.md
echo "# Affects: library_name < 2.0.0" >> SECURITY_NOTES.md
echo "# Mitigation: Input validation prevents exploitation" >> SECURITY_NOTES.md

# 2. Enhance input validation
# Add extra validation in utils/security.py

# 3. Add monitoring
# Include checks in test suite

# 4. Set review reminder
echo "# Review date: $(date -d '+30 days')" >> SECURITY_NOTES.md
```

### 9. Best Practices

#### Dependency Management
- Pin major versions, allow minor updates: `pillow>=10.0.0,<11.0.0`
- Regular dependency audits (monthly)
- Test updates in isolation
- Maintain security changelog

#### Code Security
- Regular bandit scans in CI/CD
- Security-focused code reviews
- Input validation at all boundaries
- Principle of least privilege

#### Documentation
- Keep SECURITY.md updated
- Document known issues and mitigations
- Maintain security contact information
- Regular security training for contributors

### 10. Tools and Commands Reference

```bash
# Dependency security scanning
safety check --full-report
safety check --json --output report.json
pip-audit  # Alternative to safety

# Code security scanning  
bandit -r . -f json
semgrep --config=auto .

# Dependency updates
pip list --outdated
pip-review --auto  # Automated dependency updates

# System security
exiftool -ver  # Check ExifTool version
jpylyzer --version  # Check jpylyzer version
```

This comprehensive approach ensures JP2Forge maintains security while managing the practical realities of dependency management in an active development environment.