#!/bin/bash

# Prompt the user for input file and target state
read -p "Enter input file name: " FILE_NAME
read -p "Enter target state: " TARGET_STATE

# Loop through unroll counts from 1 to 32
for ((i=1; i<=32; i++)); do
    echo "Checking reachability with unroll count: $i"
    RESULT=$(python3 lab1_src_Chin.py "$FILE_NAME" "$i" "$TARGET_STATE")
    
    # Check if the result contains an indication of success (modify this condition as needed)
    if ! echo "$RESULT" | grep -q "UNSATISFIABLE"; then
        echo "Target state is reachable at i=$i"
    fi
done
