#!/usr/bin/env python3
"""
Download F2000climo_test1 input files.
Usage: python3 download_inputs.py ~/CESM/cases/F2000climo_test1
"""
import subprocess
import sys
import os

case_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/CESM/cases/F2000climo_test1")
case_dir = os.path.expanduser(case_dir)

os.chdir(case_dir)
print(f"Working in: {case_dir}")
print(f"DIN_LOC_ROOT: {subprocess.check_output(['./xmlquery', 'DIN_LOC_ROOT'], text=True).strip()}")

# Run check_input_data --download
result = subprocess.run(["./check_input_data", "--download"], capture_output=True, text=True)
print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr)
print(f"Return code: {result.returncode}")
