#!/bin/bash

# PHAVerLite executable
PHAVER=phaverlite  # change if path to binary is different
INPUT_FILE="bouncing_ball.pha"
TMP_FILE="tmp_output.txt"
RESULT_FILE="summary_results.txt"

# Partition values to test
PCS=(0.5 0.2 0.1 0.05 0.01 0.005)

# Header
echo "Partition Constraint | Condition Reachable | Num Locations Reached | CPU Time (sec)" > $RESULT_FILE
echo "----------------------|----------------------|------------------------|----------------" >> $RESULT_FILE

for pc in "${PCS[@]}"; do
    # Create modified input file with new pc value
    MODIFIED_FILE="bouncing_ball_pc_${pc}.pha"
    awk -v pcval="$pc" '
    {
        if ($0 ~ /bball\.set_partition_constraints/) {
            print "bball.set_partition_constraints((x," pcval "),(v," pcval "),tau);"
        } else {
            print $0
        }
    }' "$INPUT_FILE" > "$MODIFIED_FILE"

    # Run PHAVerLite
    $PHAVER "$MODIFIED_FILE" > "$TMP_FILE" 2>&1

    # Extract values
    REACHABLE=$(grep -q "cond1 is reachable" "$TMP_FILE" && echo "Yes" || echo "No")
    LOCATIONS=$(grep -oP 'Printing symb\. states in \K[0-9]+' "$TMP_FILE")
    TIME=$(grep -oP 'Time in PHAVerLite: \K[0-9.]+(?= secs)' "$TMP_FILE")

    # Append to result
    printf "%21s | %20s | %22s | %14s\n" "$pc" "$REACHABLE" "$LOCATIONS" "$TIME" >> $RESULT_FILE
done

# Cleanup
rm -f "$TMP_FILE"
echo "Done! Results saved to $RESULT_FILE"

