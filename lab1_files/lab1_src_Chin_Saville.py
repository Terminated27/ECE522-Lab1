import argparse
import subprocess
import re

def get_var_id(var, cycle=0, var_map=None):
    """
    Assigns or retrieves a unique CNF ID for a variable at a specific cycle.

    Args:
        var (str): The name of the variable.
        cycle (int): The time step (unrolling cycle).
        var_map (dict): A dictionary mapping variables to unique CNF IDs.

    Returns:
        int: The unique CNF ID for the variable at the specified cycle.
    """
    var_name = f"{var}_{cycle}"
    if var_map is None:
        var_map = {}
    if var_name not in var_map:
        var_map[var_name] = len(var_map) + 1
    return var_map[var_name]

def extract_transitions(verilog_code, unroll_count, var_map):
    """
    Extracts state transitions from the Verilog 'always' block and converts them to CNF clauses.

    Args:
        verilog_code (str): The contents of the Verilog file.
        unroll_count (int): The number of state transitions to unroll.
        var_map (dict): A dictionary mapping variables to unique CNF IDs.

    Returns:
        list: A list of CNF clauses representing state transitions.
    """
    cnf_clauses = []
    always_block = re.search(r'always\s*@\(posedge\s+\w+\)\s*begin(.*?)end', verilog_code, re.DOTALL)
    
    if always_block:
        transitions = re.findall(r'(\w+)\s*<=\s*(\w+);', always_block.group(1))
        
        for cycle in range(unroll_count):
            for dst, src in transitions:
                dst_id = get_var_id(dst, cycle, var_map)
                src_id = get_var_id(src, cycle + 1, var_map)

                cnf_clauses.append([-(src_id), dst_id])  # (¬src_(t+1) ∨ dst_t)
                cnf_clauses.append([-(dst_id), src_id])  # (¬dst_t ∨ src_(t+1))

                next_dst_id = get_var_id(dst, cycle + 1, var_map)
                cnf_clauses.append([-(src_id), next_dst_id])  # (¬src_(t+1) ∨ dst_(t+1))
                cnf_clauses.append([-(next_dst_id), src_id])  # (¬dst_(t+1) ∨ src_(t+1))

    return cnf_clauses

def enforce_initial_state(var_map):
    """
    Forces all state variables to start at 0 at cycle 0.

    Args:
        var_map (dict): A dictionary mapping variables to unique CNF IDs.

    Returns:
        list: A list of CNF clauses enforcing the initial state.
    """
    return [[-var_map[var]] for var in var_map if var.endswith("_0")]

def enforce_final_state(final_state, unroll_count, var_map):
    """
    Enforces the specified final state at the last cycle.

    Args:
        final_state (list): A binary string (e.g., "0100") representing the desired final state.
        unroll_count (int): The last cycle in the unrolled sequence.
        var_map (dict): A dictionary mapping variables to unique CNF IDs.

    Returns:
        list: A list of CNF clauses enforcing the final state.
    """
    cnf_clauses = []
    for i, value in enumerate(final_state):
        var_name = f"S{i}"  # Assuming state variables are named S0, S1, S2, etc.
        var_id = get_var_id(var_name, unroll_count, var_map)
        cnf_clauses.append([var_id] if value == "1" else [-var_id])
    return cnf_clauses

def generate_cnf_header(cnf_clauses, var_map):
    """
    Generates the CNF header in DIMACS format.

    Args:
        cnf_clauses (list): A list of CNF clauses.
        var_map (dict): A dictionary mapping variables to unique CNF IDs.

    Returns:
        list: The CNF header in DIMACS format.
    """
    return [f"p cnf {len(var_map)} {len(cnf_clauses)}"]

def parse_verilog(file_name, unroll_count, final_state):
    """
    Parses a Verilog file, extracts transitions, and generates CNF constraints.

    Args:
        file_name (str): The name of the Verilog file.
        unroll_count (int): The number of state transitions to unroll.
        final_state (list): The desired final state as a binary string.

    Returns:
        tuple: A CNF string in DIMACS format and a variable mapping dictionary.
    """
    with open(file_name, 'r') as verilog:
        verilog_code = verilog.read()

    var_map = {}
    cnf_clauses = extract_transitions(verilog_code, unroll_count, var_map)
    cnf_clauses += enforce_initial_state(var_map)
    cnf_clauses += enforce_final_state(final_state, unroll_count, var_map)

    cnf_header = generate_cnf_header(cnf_clauses, var_map)
    cnf_output = cnf_header + [" ".join(map(str, clause)) + " 0" for clause in cnf_clauses]

    return "\n".join(cnf_output), var_map

def write_cnf_file(cnf_text, output_file):
    """
    Writes the CNF formula to a file in DIMACS format.

    Args:
        cnf_text (str): The CNF representation as a formatted string.
        output_file (str): The filename to write the CNF to.
    """
    with open(output_file, 'w') as f:
        f.write(cnf_text)

def run_sat_solver(cnf_file):
    """
    Runs MiniSat on the given CNF file and captures the output.

    Args:
        cnf_file (str): Path to the CNF file.

    Returns:
        str: "SATISFIABLE" if the final state is reachable, otherwise "UNSATISFIABLE".
    """
    try:
        result = subprocess.run(["minisat", cnf_file], capture_output=True, text=True)
        output = result.stdout
        return "UNSATISFIABLE" if "UN" in output else "SATISFIABLE"
    except FileNotFoundError:
        return "Error: MiniSat is not installed or not in the system PATH."

def main():
    """
    Handles command-line arguments and runs the SAT solver.
    """
    parser = argparse.ArgumentParser(description="Verilog to CNF Converter & SAT Solver Runner")
    parser.add_argument("verilog_file", type=str, help="The Verilog file to process")
    parser.add_argument("unroll_count", type=int, help="Number of state transition unrolls")
    parser.add_argument("final_state", type=str, help="Target state as a binary string (e.g., 0100)")

    args = parser.parse_args()

    final_state = list(args.final_state)  # Convert "0100" to ['0', '1', '0', '0']

    cnf_text, _ = parse_verilog(args.verilog_file, args.unroll_count, final_state)
    write_cnf_file(cnf_text, "output.cnf")

    sat_result = run_sat_solver("output.cnf")
    print(f"SAT Solver Result: {sat_result}")

if __name__ == "__main__":
    main()
