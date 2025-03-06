import re
from collections import defaultdict

def group_variables(operations_with_vars):
    # This will hold grouped results
    grouped = defaultdict(list)

    # Regular expression pattern to match variables
    pattern = r'^(NS(\d+)_(\d+)|S(\d+)_(\d+))$'

    # Process each operation and its variable list
    for operation, variables in operations_with_vars:
        for var in variables:
            match = re.match(pattern, var)
            if match:
                if match.group(2) and match.group(3):  # Matches NSx_n
                    x = match.group(2)  # get x
                    n = int(match.group(3))  # get n
                    grouped[x].append(('NS', n, operation))  # store with operation
                elif match.group(4) and match.group(5):  # Matches Sx_n+1
                    x = match.group(4)  # get x
                    n = int(match.group(5)) - 1  # get n from Sx_n+1 and adjust
                    grouped[x].append(('S', n, operation))  # store with operation
    
    # Prepare output as a list of tuples
    result = []
    for x, items in grouped.items():
        ns_n = None
        s_n_plus_one = None
        ns_var = None
        s_var = None
        
        for item_type, n, operation in items:
            if item_type == 'NS':
                ns_n = n
                ns_var = f'NS{x}_{ns_n}'  # Construct the variable name
            if item_type == 'S':
                s_n_plus_one = n
                s_var = f'S{x}_{s_n_plus_one + 1}'  # Construct the variable name

        # Only include valid pairs in the results
        if ns_var is not None and s_var is not None:
            result.append(('buffer', [ns_var, s_var]))

    return result

# Example usage
input_operations = [
    ('and', ['X1_', 'S0_', 'S1_']),
    ('and', ['NS1_', 'A_', 'X1_']),
    ('not', ['NS0_', 'X1_']),
    ('and', ['Y_', 'A_', 'X1_']),
    ('and', ['X1_0', 'S0_0', 'S1_0']),
    ('and', ['NS1_0', 'A_0', 'X1_0']),
    ('not', ['NS0_0', 'X1_0']),
    ('and', ['Y_0', 'A_0', 'X1_0']),
    ('and', ['X1_1', 'S0_1', 'S1_1']),
    ('and', ['NS1_1', 'A_1', 'X1_1']),
    ('not', ['NS0_1', 'X1_1']),
    ('and', ['Y_1', 'A_1', 'X1_1'])
]

grouped_variables = group_variables(input_operations)
print(grouped_variables)
