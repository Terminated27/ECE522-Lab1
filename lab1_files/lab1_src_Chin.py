import re
from collections import defaultdict
import subprocess
import os
import sys

# Sample input
text = """
and g0(X1,S0,S1);
and g1(NS1,A,X1);
not g2(NS0,X1);
and g3(Y,A,X1);
"""
def read_verilog_file(file_path):
    """
    Reads a Verilog file and returns its content as a string.
    
    Args:
    - file_path: str - The path to the Verilog file to be read.

    Returns:
    - str: The contents of the Verilog file.

    Raises:
    - FileNotFoundError: If the file does not exist.
    - IOError: If the file cannot be read due to an I/O error.
    """
    try:
        with open(file_path, 'r') as file:
            return file.read()  # Read the entire file into a string
    except FileNotFoundError:
        print(f'The file {file_path} was not found.')
        return None  # You can choose to raise an exception or return None
    except IOError:
        print('An error occurred while trying to read the file.')
        return None  # You can choose to raise an exception or return None

Operation = tuple[str, list[str]]

def extract_operations(text: str) -> list[Operation]:
    # Regex pattern to match the operations followed by the variables only
    pattern = r'\b(and|not)\s+g\d+\(([^)]+)\)'

    # Find all matches
    matches = re.findall(pattern, text)

    # Process the matches to just extract the operation and variables
    extracted = []
    for op, vars_ in matches:
        # Split the variables, and mark them with an underscore as og
        variables = [f'{var.strip()}_' for var in vars_.split(',')]
        extracted.append((op, variables))

    return extracted


def increment_variables(input_list, max_n):
    combined_output = []  # List to hold combined outputs for each n from 0 to max_n

    for n in range(max_n + 1):  # Iterate from 0 to max_n
        # Create a new list to hold the modified tuples for the current n
        modified_list = []
        for operation, variables in input_list:
            # Create a modified tuple with incremented suffix
            modified_tuple = (operation, [f"{var}{n}" for var in variables])
            modified_list.append(modified_tuple)
        # Append current modified list to combined output
        combined_output.append(modified_list)
    return combined_output


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

def index_variables(data):
    """
    This function takes an array of tuples where each tuple contains 
    an operation and a list of variable names. It returns a new array 
    of tuples where each variable is replaced by its unique index.

    :param data: List of tuples, where each tuple is (operation, [list of variables])
    :return: List of tuples with operation and list of variable indices
    """
    # Step 1: Extract unique variables
    unique_vars = set()
    for _, variables in data:
        unique_vars.update(variables)

    # Step 2: Create a mapping from variable to unique index
    var_to_index = {var: idx + 1 for idx, var in enumerate(sorted(unique_vars))}

    # Step 3: Replace variables in the tuples with their indices
    indexed_data = [(operation, [var_to_index[var] for var in variables]) for operation, variables in data]

    return indexed_data

def convert_dimac(operations):
    args = []
    for operation, variables in operations:
        if operation == "and":
            args.append(f"{variables[1]} -{variables[0]} 0")
            args.append(f"{variables[2]} -{variables[0]} 0")
            args.append(f"-{variables[1]} -{variables[2]} {variables[0]} 0")
        if operation == 'not':
            args.append(f"{variables[1]} {variables[0]} 0")
            args.append(f"-{variables[1]} -{variables[0]} 0")
        if operation == 'buffer':
            args.append(f"-{variables[1]} {variables[0]} 0")
            args.append(f"{variables[1]} -{variables[0]} 0")
        if operation == 'one':
            args.append(f"{variables[0]} 0")
        if operation == 'zero':
            args.append(f"-{variables[0]} 0")
    return '\n'.join(args)

def create_dimacs_header(input_string):
    # Split the input string into lines and then parse them into clauses
    lines = input_string.strip().split('\n')
    clauses = []
    
    for line in lines:
        # Split the line by whitespace and convert to integers
        clause = list(map(int, line.split()))
        clauses.append(clause)
    
    # Create a set to track unique variable indices
    unique_vars = set()
    
    # Process each clause
    for clause in clauses:
        # Add the absolute values of the literals to the unique_vars set
        unique_vars.update(abs(literal) for literal in clause if literal != 0)
    
    # Number of variables is the count of unique variable indices
    num_vars = len(unique_vars)
    # Number of clauses is the length of the clauses list
    num_clauses = len(clauses)
    
    # Create the DIMACS header
    header = f"p cnf {num_vars} {num_clauses}"
    
    # Create the DIMACS output
    dimacs_output = [header]
    for clause in clauses:
        # Convert clause to string and append "0" to the end
        dimacs_output.append(" ".join(map(str, clause)))
    
    return "\n".join(dimacs_output)

def write_dimacs_to_file(dimacs_content, filename='output.cnf'):
    """
    Writes the given DIMACS content to a specified file.

    Parameters:
    dimacs_content (str): The DIMACS content as a string.
    filename (str): The name of the file to write to. Default is 'output.cnf'.
    """
    with open(filename, 'w') as file:
        file.write(dimacs_content)

import os
import subprocess
import re

def run_minisat_with_file(file_path):
    """
    Run a DIMACS CNF file through MiniSat and return the output along with execution time.

    Parameters:
    file_path (str): The path to the DIMACS CNF file.

    Returns:
    tuple: A tuple containing stdout, stderr, return code from MiniSat, and extracted runtime.
    """
    # Step 1: Check if the file exists
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    # Step 2: Call MiniSat with the file
    result = subprocess.run(['minisat', file_path], capture_output=True, text=True)

    # Print out the results
    print("MiniSat Output:")
    if "UNSATISFIABLE" in result.stdout:
        print("UNSATISFIABLE")
    elif "SATISFIABLE" in result.stdout:
        print("SATISFIABLE")
    else:
        raise RuntimeError("Unexpected output from MiniSat.")

    # Extract runtime using regex (handling wide spaces)
    runtime_match = re.search(r'CPU time\s*:\s*([\d.]+)\s*s', result.stdout)
    runtime = float(runtime_match.group(1)) if runtime_match else None

    if runtime is not None:
        print(f"Runtime: {runtime:.6f} seconds")

    return result.stdout, result.stderr, result.returncode, runtime


def process_verilog_file(file_path, unroll=0, target_state=''):
    # Read the Verilog file
    text = read_verilog_file(file_path)
    if text is None:
        print("file is empty!")
        return

    # Extract operations from the Verilog code
    operations = extract_operations(text)

    # Increment variables for a specified range
    incremented_operations = increment_variables(operations, unroll)
    # ^ make this output a list of unrolling groups to simplify next step, list[list[tuple[str, list[str]]]]
    # Group variables based on the logic defined

    grouped_operations = group_variables(incremented_operations)

    encoded_states = process_operations(grouped_operations, target_state)
    print("   ", *encoded_states, sep="\n")


    # Index the variables
    indexed_operations = index_variables(encoded_states)

    # Convert operations to DIMAC format
    dimacs_clauses = convert_dimac(indexed_operations)

    # Create the DIMACS header
    dimacs_output = create_dimacs_header(dimacs_clauses)

    # Write the DIMACS output to a file
    write_dimacs_to_file(dimacs_output)

    # Run MiniSat with the generated DIMACS file
    run_minisat_with_file('output.cnf')

if __name__ == "__main__":
    # Check if the correct number of arguments is provided
    if len(sys.argv) != 4:
        print("Usage: python3 lab1_src_Chin_Saville.py <verilog_file> <unroll> <target_state>")
        sys.exit(1)

    # Extract arguments from command line
    file_path = sys.argv[1]
    unroll = int(sys.argv[2])
    target_state = sys.argv[3]
    reversed_state = target_state[::-1]
    # Call the function with extracted arguments
    process_verilog_file(file_path, unroll, reversed_state)