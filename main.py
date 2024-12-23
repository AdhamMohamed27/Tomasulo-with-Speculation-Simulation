import sys
import re

def parse_memory_operand(operand):
    match = re.match(r"(\d+)\((R\d+)\)", operand)
    if match:
        immediate = int(match.group(1))  # The immediate value (e.g., 4)
        register = int(match.group(2)[1])  # Extract the register number (e.g., R2 -> 2)
        return immediate, register
    else:
        raise ValueError(f"Invalid memory operand format: {operand}")
        

# Simulator Constants
REGISTER_COUNT = 8  # R0 to R7
MEMORY_SIZE = 128 * 1024  # 128 KB word-addressable memory

class RegisterFile:
    def __init__(self, num_registers):
        self.values = [0] * num_registers  # Register values
        self.status = [None] * num_registers  # None if register is ready

    def get_value(self, reg_index):
        return self.values[reg_index]

    def set_value(self, reg_index, value):
        self.values[reg_index] = value

    def is_ready(self, reg_index):
        return self.status[reg_index] is None

    def set_status(self, reg_index, station_name):
        self.status[reg_index] = station_name

    def clear_status(self, reg_index):
        self.status[reg_index] = None
        
class Memory:
    def __init__(self, size):
        # Initialize memory with the specified size (e.g., number of memory locations)
        self.memory = [0] * size  # Initialize all memory locations to 0

    def load(self, address):
        # Load data from memory at a given address
        if 0 <= address < len(self.memory):
            return self.memory[address]
        else:
            raise ValueError(f"Address {address} out of bounds")

    def store(self, address, value):
        # Store data in memory at a given address
        if 0 <= address < len(self.memory):
            self.memory[address] = value
        else:
            raise ValueError(f"Address {address} out of bounds")

    def initialize_data(self, data_dict):
        """
        Initialize memory with values from a dictionary.
        Example of data_dict: {address: value}
        """
        for address, value in data_dict.items():
            self.store(address, value)

    def __repr__(self):
        # Optionally, you can provide a representation of the memory contents
        return str(self.memory)


def parse_instruction(line):
    # Split the line into operation and operands
    parts = line.split()
    operation = parts[0]  # First part is the operation (e.g., ADD, ADDI, LOAD, etc.)
    operands = parts[1:]  # Everything after the first part is an operand
    execution_time = get_execution_time(operation)  # Define this function to return the execution time based on the operation
    # Handle the case where there are no operands (optional, depending on your needs)
    if len(operands) == 0:
        operands = None  # Or an empty list depending on how you want to handle this
    
    # For now, we will set 'name' to be the operation (e.g., ADD, LOAD, etc.)
    # You might want to improve this if you need specific instruction names or labels
    name = operation
    
    # Return the Instruction object with the parsed values
    return Instruction(name, operation, operands, execution_time)



def load_program(file_path):
    instructions = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if line.strip():
                    instructions.append(parse_instruction(line))
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        sys.exit(1)
    return instructions

class Instruction:
    def __init__(self, name, operation, operands, execution_time):
        self.name = name
        self.operation = operation
        self.operands = operands
        self.execution_time = execution_time
        self.issue_cycle = None
        self.start_exec_cycle = None
        self.finish_exec_cycle = None
        self.write_result_cycle = None
        self.commit_cycle = None
    
    def can_issue(self, current_cycle, register_file, reservation_stations, rob):
        # Resolve operands to check if they are ready
        Vj, Vk, Qj, Qk = resolve_operands(register_file, self.operands)
        # Check if the instruction can be issued
        rs_available = any(rs.has_available_station() for rs in reservation_stations)
        rob_available = any(not entry['busy'] for entry in rob.entries)
        return self.issue_cycle is None and Qj is None and Qk is None and rs_available and rob_available
    
    def can_start_execution(self, current_cycle, reservation_stations, register_file):
        # Check if the instruction can start execution
        Vj, Vk, Qj, Qk = resolve_operands(register_file, self.operands)
        rs_available = any(rs.has_busy_station_with_op(self.operation) for rs in reservation_stations)
        return self.issue_cycle is not None and self.start_exec_cycle is None and current_cycle > self.issue_cycle and rs_available and Qj is None and Qk is None
    
    def can_finish_execution(self, current_cycle):
        # Check if the instruction can finish execution
        return self.start_exec_cycle is not None and self.finish_exec_cycle is None and current_cycle >= self.start_exec_cycle + self.execution_time
    
    def can_write_result(self, current_cycle):
        # Check if the instruction can write the result
        # For example, check if the instruction has finished execution and if the write-back unit is available
        return self.finish_exec_cycle is not None and self.write_result_cycle is None and current_cycle > self.finish_exec_cycle
    
    def can_commit(self, current_cycle):
        # Check if the instruction can commit
        # For example, check if the instruction has written the result and if the commit unit is available
        return self.write_result_cycle is not None and self.commit_cycle is None and current_cycle > self.write_result_cycle

    def flush(self):
        """Flush the entire queue."""
        self.queue = []
    
    def flush_after(self, branch_index):
        # Remove all instructions after the branch_index
        self.queue = self.queue[:branch_index + 1]


class ReservationStation:
    def __init__(self, name, num_stations, execution_cycles, op_type=None):
        self.name = name
        self.num_stations = num_stations
        self.execution_cycles = execution_cycles
        self.op_type = op_type
        self.stations = [self._create_station() for _ in range(num_stations)]

    def _create_station(self):
        return {'busy': False, 'op': None, 'Vj': None, 'Vk': None,
                'Qj': None, 'Qk': None, 'cycles_left': 0, 'address': None}

    def allocate(self, op, Vj=None, Vk=None, Qj=None, Qk=None, address=None):
        for station in self.stations:
            if not station['busy']:
                station.update({
                    'busy': True, 'op': op, 'Vj': Vj, 'Vk': Vk,
                    'Qj': Qj, 'Qk': Qk, 'cycles_left': self.execution_cycles,
                    'address': address
                })
                return station
        return None

    def execute(self, register_file, memory):
        for station in self.stations:
            if station['busy'] and station['cycles_left'] > 0:
                station['cycles_left'] -= 1
                if station['cycles_left'] == 0:
                    print(f"{station['op']} Execution Complete")
                    return station
        return None
    
    def has_available_station(self):
        return any(not station['busy'] for station in self.stations)

    def has_busy_station_with_op(self, operation):
        return any(station['busy'] and station['op'] == operation for station in self.stations)

    def free_station_with_op(self, operation):
        for station in self.stations:
            if station['busy'] and station['op'] == operation:
                station['busy'] = False
                station['op'] = None
                station['Vj'] = None
                station['Vk'] = None
                station['Qj'] = None
                station['Qk'] = None
                station['cycles_left'] = 0
                station['address'] = None
                return True
        return False


def resolve_operands(register_file, operands):
    Vj, Vk, Qj, Qk = None, None, None, None
    
    # Check the first operand
    if operands[0].startswith('R'):  # First operand, for example, "R1"
        reg_index = int(operands[0][1:].rstrip(','))  # Remove 'R' and any trailing commas
        if 0 <= reg_index < REGISTER_COUNT:
            Vj = register_file.get_value(reg_index)  # Get the value from the register file
            if register_file.status[reg_index] is not None:  # Check if the register is pending
                Qj = register_file.status[reg_index]  # Set the pending register's tag

    # Check the second operand (if exists)
    if len(operands) > 1 and operands[1].startswith('R'):  # Second operand, for example, "R0"
        reg_index = int(operands[1][1:].rstrip(','))  # Remove 'R' and any trailing commas
        if 0 <= reg_index < REGISTER_COUNT:
            Vk = register_file.get_value(reg_index)  # Get the value from the register file
            if register_file.status[reg_index] is not None:  # Check if the register is pending
                Qk = register_file.status[reg_index]  # Set the pending register's tag

    return Vj, Vk, Qj, Qk


class ReorderBuffer:
    def __init__(self, size):
        # Each entry holds:
        # - 'busy': whether the entry is occupied
        # - 'instruction': the actual instruction
        # - 'state': current state of the instruction ('issue', 'execute', 'write', 'commit')
        # - 'result': the computed result, or None if not yet computed
        # - 'destination': destination register, if the instruction writes back
        self.entries = [{'busy': False, 'instruction': None, 'state': 'issue', 'result': None, 'destination': None}
                        for _ in range(size)]

    def add(self, instruction, destination=None):
        """ Adds an instruction to the reorder buffer. """
        for entry in self.entries:
            if not entry['busy']:  # Find an empty slot
                entry['busy'] = True
                entry['instruction'] = instruction
                entry['state'] = 'issue'
                entry['result'] = None
                entry['destination'] = destination  # Where to write the result, if any
                return entry
        return None

    def write_result(self, instruction, result):
        """ Writes a result back to the reorder buffer when execution is complete. """
        for entry in self.entries:
            if entry['busy'] and entry['instruction'] == instruction:
                entry['state'] = 'write'  # Once result is available, mark as ready to write
                entry['result'] = result
                return True
        return False

    def commit(self, current_cycle, metadata, register_file):
        """ Commits completed instructions from the reorder buffer to the register file. """
        for entry in self.entries:
            if entry['busy'] and entry['state'] == 'write':  # Instruction is ready to commit
                entry['state'] = 'commit'
                entry['busy'] = False
                # Update the register file or memory based on the instruction's result
                if entry['destination']:
                    register_file.write(entry['destination'], entry['result'])

                # Also update metadata for instruction commit cycle
                for meta in metadata:
                    if meta['instruction'] == entry['instruction'] and meta.get('commit') is None:
                        meta['commit'] = current_cycle
                        break
                return True
        return False


def get_execution_time(operation):
    execution_times = {
        'ADD': 2,
        'ADDI': 2,
        'LOAD': 6,
        'STORE': 6,
        'NAND': 2,
        'BEQ': 1,
        'MUL': 8,
        'CALL': 4,
        'RET': 4
    }
    return execution_times.get(operation, 1)  # Default to 1 cycle if operation is not found


def main():
    REGISTER_COUNT = 32  # Example number of registers
    MEMORY_SIZE = 128    # Example size for memory
    register_file = RegisterFile(REGISTER_COUNT)
    memory = Memory(MEMORY_SIZE)

    # Initialize specific memory locations with values
    memory.store(0, 42)  # Memory location 0 gets the value 42
    memory.store(1, 100)  # Memory location 1 gets the value 100
    memory.store(5, 255)  # Memory location 5 gets the value 255
    memory.store(10, 123) # Memory location 10 gets the value 123

    # Initialize reservation stations for different operations
    add_station = ReservationStation("ADD", 4, 2, op_type="ADD")
    addi_station = ReservationStation("ADDI", 4, 2, op_type="ADDI")
    load_station = ReservationStation("LOAD", 2, 6, op_type="LOAD")
    store_station = ReservationStation("STORE", 1, 6, op_type="STORE")
    nand_station = ReservationStation("NAND", 2, 2, op_type="NAND")
    branch_station = ReservationStation("BEQ", 2, 1, op_type="BEQ")
    mul_station = ReservationStation("MUL", 1, 8, op_type="MUL")
    call_ret_station = ReservationStation("CALL/RET", 2, 4)  # CALL/RET station
    
    reservation_stations = [add_station, addi_station, load_station, store_station, nand_station, branch_station, mul_station, call_ret_station]
    rob = ReorderBuffer(32)  # Example size for ROB

    # Load instructions
    program_path = 'sample_program.txt'
    instructions = load_program(program_path)
    instruction_queue = instructions[:]

    clock_cycles = 0
    completed_instructions = 0
    total_instructions = len(instructions)
    executed_instructions = set()

    while completed_instructions < total_instructions:
        clock_cycles += 1
        # print(f"\nCycle {clock_cycles}:")

        issued_this_cycle = False
        for instruction in instructions:
            if not issued_this_cycle and instruction.can_issue(clock_cycles, register_file, reservation_stations, rob):
                instruction.issue_cycle = clock_cycles
                # Allocate reservation station and ROB entry
                rs = next(rs for rs in reservation_stations if rs.has_available_station())
                rs.allocate(instruction.operation)
                rob_entry = rob.add(instruction)
                issued_this_cycle = True
                # print(f"Issue: {instruction.name}")
            
            if instruction.can_start_execution(clock_cycles, reservation_stations, register_file):
                instruction.start_exec_cycle = clock_cycles

            if instruction.can_finish_execution(clock_cycles):
                instruction.finish_exec_cycle = clock_cycles

            if instruction.can_write_result(clock_cycles):
                instruction.write_result_cycle = clock_cycles

            if instruction.can_commit(clock_cycles):
                instruction.commit_cycle = clock_cycles
                completed_instructions += 1
                # Free reservation station and ROB entry
                rs = next(rs for rs in reservation_stations if rs.has_busy_station_with_op(instruction.operation))
                rs.free_station_with_op(instruction.operation)
                rob_entry = next(entry for entry in rob.entries if entry['instruction'] == instruction)
                rob_entry['busy'] = False
                # print(f"Commit: {instruction.name}")

        # Simulate execution delay by cycling reservation stations
        for rs in reservation_stations:
            rs.execute(register_file, memory)

        # print(f"End of Cycle {clock_cycles}:")

    # Generate the instruction execution table after all cycles complete
    print("\nInstruction Execution Table:")
    print(f"{'Instruction':<20}{'Issue':<10}{'Start Exec':<15}{'Finish Exec':<15}{'Write Result':<15}{'Commit':<10}")
    for instr in instructions:
        print(f"{instr.name:<20}"
              f"{instr.issue_cycle if instr.issue_cycle is not None else '-':<10}"
              f"{instr.start_exec_cycle if instr.start_exec_cycle is not None else '-':<15}"
              f"{instr.finish_exec_cycle if instr.finish_exec_cycle is not None else '-':<15}"
              f"{instr.write_result_cycle if instr.write_result_cycle is not None else '-':<15}"
              f"{instr.commit_cycle if instr.commit_cycle is not None else '-':<10}")

    # Calculate IPC
    total_cycles = max((instr.commit_cycle for instr in instructions if instr.commit_cycle is not None), default=0)
    ipc = total_instructions / total_cycles if total_cycles > 0 else 0
    # print(f"\nSimulation Results:")
    print(f"Total Cycles: {total_cycles}")
    print(f"IPC: {ipc:.2f}")

if __name__ == "__main__":
    main()
