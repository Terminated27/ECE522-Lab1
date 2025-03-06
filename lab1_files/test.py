def process_operations(operations, state_string):
    # Extract the highest suffix number from the operations:
    max_suffix = max(int(var.split('_')[1]) for _, vars in operations for var in vars)

    new_operations = []
    
    # Iterate through the provided operations
    for operation, vars in operations:
        new_operations.append((operation, vars))
    
    # Identify the initial states and final states
    num_initial_states = len(state_string)  # This is the length of the state_string
    for index in range(num_initial_states):  # Iterate through the length of the state string
        initial_state = f'S{index}_0'
        final_state = f'S{index}_{max_suffix}'
        
        # Always add 'zero' block for initial states
        new_operations.append(('zero', [initial_state]))

        # Determine whether to add 'one' or 'zero' for the final states based on the state_string
        if state_string[index] == '1':
            new_operations.append(('one', [final_state]))
        else:
            new_operations.append(('zero', [final_state]))
    
    return new_operations

# Sample input
sample_input = [
    ('and', ['X1_0', 'S0_0', 'S1_0']),
    ('and', ['NS1_0', 'A_0', 'X1_0']),
    ('not', ['NS0_0', 'X1_0']),
    ('and', ['Y_0', 'A_0', 'X1_0']),
    ('and', ['X1_1', 'S0_1', 'S1_1']),
    ('and', ['NS1_1', 'A_1', 'X1_1']),
    ('not', ['NS0_1', 'X1_1']),
    ('and', ['Y_1', 'A_1', 'X1_1']),
    ('and', ['X1_2', 'S0_2', 'S1_2']),
    ('and', ['NS1_2', 'A_2', 'X1_2']),
    ('not', ['NS0_2', 'X1_2']),
    ('and', ['Y_2', 'A_2', 'X1_2']),
    ('buffer', ['NS0_2', 'S0_2']),
    ('buffer', ['NS1_2', 'S1_2'])
]

# Example state string (length corresponds to the number of initial states)
state_string = "110"  # Should be the same length as the number of initial states (in this case 3)

# Process the operations
result = process_operations(sample_input, state_string)

# Output the result
for entry in result:
    print(entry)
