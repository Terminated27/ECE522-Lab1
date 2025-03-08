#!/bin/bash

# Define the input file and unroll count
FILE_NAME="stoplight2.v"
UNROLL_COUNT=17

# Loop through all possible 5-bit target states (00000 to 11111)
for ((state=0; state<32; state++)); do
    # Convert state to a 5-bit binary string
    TARGET_STATE=$(printf "%05d" "$(echo "obase=2; $state" | bc)")
    
    echo "Checking reachability for target state: $TARGET_STATE"
    RESULT=$(python3 lab1_src_Chin.py "$FILE_NAME" "$UNROLL_COUNT" "$TARGET_STATE")
    
    # Check if the result does NOT contain "UNSATISFIABLE" to determine reachability
    if ! echo "$RESULT" | grep -q "UNSATISFIABLE"; then
        echo "Target state $TARGET_STATE is reachable"
    fi
done
