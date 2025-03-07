import re
from collections import defaultdict

def group_variables(operations_list):
    # This will hold all operations and their associated variables
    all_operations = []

    # Regular expression pattern to match variables
    pattern = r'^(NS(\d+)_(\d+)|S(\d+)_(\d+))$'

    # Variable to hold the last NS variables from the previous block
    last_ns_vars = {}

    # Iterate through each set of operations
    for operations in operations_list:
        # This will hold grouped results for the specific operations set
        grouped = defaultdict(list)

        # Process each operation and its variable list
        for operation, variables in operations:
            for var in variables:
                match = re.match(pattern, var)
                if match:
                    if match.group(2) and match.group(3):  # Matches NSx_n
                        x = match.group(2)  # extract x
                        n = int(match.group(3))  # extract n
                        grouped[x].append(('NS', n, operation))
                    elif match.group(4) and match.group(5):  # Matches Sx_n+1
                        x = match.group(4)  # extract x
                        n = int(match.group(5)) - 1  # adjust n
                        grouped[x].append(('S', n, operation))

        # Prepare a dict to hold the current block's NS variables
        current_ns_vars = {}

        # Process each grouped variable for the current block
        for x, items in grouped.items():
            ns_var = None
            s_var = None

            # For each group x, determine the NS and S variables
            for item_type, n, operation in items:
                if item_type == 'NS':
                    ns_var = f'NS{x}_{n}'
                elif item_type == 'S':
                    s_var = f'S{x}_{n + 1}'

            # Save the NS variable (if exists) for the current block
            if ns_var is not None:
                current_ns_vars[x] = ns_var

            # If a previous NS for this x exists and we have an S variable, add a buffer link
            if x in last_ns_vars and s_var is not None:
                last_ns_index = int(last_ns_vars[x].split('_')[-1])
                current_s_index = int(s_var.split('_')[-1]) - 1  # get n from Sx_(n+1)
                if last_ns_index == current_s_index:
                    all_operations.append(('buffer', [last_ns_vars[x], s_var]))

        # Update last_ns_vars for the next block and add the current operations
        last_ns_vars = current_ns_vars
        all_operations.extend(operations)

    return all_operations

# Example usage:
input_data = [
    [('and', ['X1_0', 'S0_0', 'S1_0']), 
     ('and', ['NS1_0', 'A_0', 'X1_0']), 
     ('not', ['NS0_0', 'X1_0']), 
     ('and', ['Y_0', 'A_0', 'X1_0'])],
    
    [('and', ['X1_1', 'S0_1', 'S1_1']), 
     ('and', ['NS1_1', 'A_1', 'X1_1']), 
     ('not', ['NS0_1', 'X1_1']), 
     ('and', ['Y_1', 'A_1', 'X1_1'])],
    
    [('and', ['X1_2', 'S0_2', 'S1_2']), 
     ('and', ['NS1_2', 'A_2', 'X1_2']), 
     ('not', ['NS0_2', 'X1_2']), 
     ('and', ['Y_2', 'A_2', 'X1_2'])]
]

result = group_variables(input_data)

print("    ", *result, sep="\n    ")
