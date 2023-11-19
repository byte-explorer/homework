## Intro
This is a minimalistic approach to create an automated test environment for `mkdir` linux (unix) command as a homework assignment.

Test execution expects a creation of system users for testing purpose, so the test routine should be initiated as the root user.

Before running the test routine, please run setup.sh to install docker, python3 and pip requirements.

Execution against remote targets expects a no-password access as the root user via ssh.

Functional Requirements to be tested are stored in the [functional_requirements.txt](functional_requirements.txt), FR coverage by the test cases is shown in the [Requirements Traceability Matrix](Requirements_Traceability_Matrix.xlsx).

### Default test config runs the test against:
- localhost (Ubuntu 20.04)
- remote host (Raspberry Pi 2B, Ubuntu MATE 18.04)
- Docker image `oraclelinux:9`
- Docker image `redhat/ubi8`
- Docker image `arm64v8/ubuntu:22.04`

### Test execution

Preparation
```
./setup.sh
```

Test Routine
```
source venv/bin/activate
python3 routine.py test_configs/default.json # Full run
python3 routine.py test_configs/minimal.json --debug # Minimal run in debug mode
```
