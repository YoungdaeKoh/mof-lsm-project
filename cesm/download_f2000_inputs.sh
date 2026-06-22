#!/bin/bash
# Download F2000climo_test1 input files
# Run directly on climate00: ssh climate; bash /path/to/download_f2000_inputs.sh

set -e

echo "F2000climo_test1 Input File Download"
echo "===================================="
echo "Time: $(date)"
echo ""

# Load modules
source /home/ydkoh/CESM2.module.sh
echo "✓ Modules loaded"

# Change to case dir
cd ~/CESM/cases/F2000climo_test1
echo "✓ Working dir: $(pwd)"
echo ""

# Show config
echo "Configuration:"
echo "  DIN_LOC_ROOT: $(./xmlquery DIN_LOC_ROOT)"
echo "  NTASKS: $(./xmlquery NTASKS)"
echo ""

# Download
echo "Starting download at $(date)..."
echo "This may take 10-20 minutes depending on file sizes."
echo ""

./check_input_data --download

echo ""
echo "Download completed at $(date)"
echo ""

# Check results
echo "Input file status:"
./check_input_data
