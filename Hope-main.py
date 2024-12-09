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
    
    # Handle the case where there are no operands (optional, depending on your needs)
    if len(operands) == 0:
        operands = None  # Or an empty list depending on how you want to handle this
    
    # For now, we will set 'name' to be the operation (e.g., ADD, LOAD, etc.)
    # You might want to improve this if you need specific instruction names or labels
    name = operation
    
    # Return the Instruction object with the parsed values
    return Instruction(name, operation, operands)



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
    def __init__(self, name, operation, operands):
        self.name = name
        self.operation = operation
        self.operands = operands
        self.issue_cycle = None
        self.start_exec_cycle = None
        self.finish_exec_cycle = None
        self.write_result_cycle = None
        self.commit_cycle = None
    
    def can_issue(self, current_cycle):
        # Implement the logic to check if the instruction can be issued at the current cycle
        # For example, you can check if operands are ready or if there is space in the reservation station
        return self.issue_cycle is None 
    
    def can_start_execution(self, current_cycle):
        # Implement the logic to check if the instruction can start execution at the current cycle
        return self.issue_cycle is not None and self.start_exec_cycle is None
    
    def can_finish_execution(self, current_cycle):
        # Implement the logic to check if the instruction can finish execution at the current cycle
        return self.start_exec_cycle is not None and self.finish_exec_cycle is None
    
    def can_write_result(self, current_cycle):
        # Implement the logic to check if the instruction can write the result at the current cycle
        return self.finish_exec_cycle is not None and self.write_result_cycle is None
    
    def can_commit(self, current_cycle):
        # Implement the logic to check if the instruction can commit at the current cycle
        return self.write_result_cycle is not None and self.commit_cycle is None

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
        """ Helper method to create a new station (dictionary). """
        return {'busy': False, 'op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'cycles_left': 0, 'address': None}

    def is_available(self):
        return any(not station['busy'] for station in self.stations)

    def allocate(self, op, Vj=None, Vk=None, Qj=None, Qk=None, address=None):
        for station in self.stations:
            if not station['busy']:
                station['busy'] = True
                station['op'] = op
                station['Vj'] = Vj
                station['Vk'] = Vk
                station['Qj'] = Qj
                station['Qk'] = Qk
                station['cycles_left'] = self.execution_cycles
                station['address'] = address
                return station
        print(f"Station {self.name} is full, cannot allocate {op}.")
        return None

    def execute(self, register_file, memory):
        for station in self.stations:
            if station['busy'] and station['cycles_left'] > 0:
                station['cycles_left'] -= 1
    
                # Execution logic for different operations
                if station['cycles_left'] == 0:
                    if station['op'] == "ADD":
                        result = station['Vj'] + station['Vk']
                        print(f"ADD Result: {result}")
                    elif station['op'] == "ADDI":
                        result = station['Vj'] + station['Vk']
                        print(f"ADDI Result: {result}")
                    elif station['op'] == "LOAD":
                        result = memory.load(station['address'])
                        print(f"LOAD Result: {result}")
                    elif station['op'] == "STORE":
                        memory.store(station['address'], station['Vj'])
                        print(f"STORE: Stored {station['Vj']} at address {station['address']}")
    
                    # Store the result back to the register if needed
                    if station['op'] in ["ADD", "ADDI"]:
                        # Ensure Qj is not None before using it as an index
                        if station['Qj'] is not None:
                            register_file.set_value(station['Qj'], result)
                        else:
                            print(f"Warning: Qj is None, skipping write back.")
    
                    # Release the station after execution
                    station['busy'] = False
                    return station
        return None

    def release(self, station):
        """ Reset station attributes using a helper method. """
        if station in self.stations:  # Check if station is valid within the reservation station list
            self.stations[self.stations.index(station)] = self._create_station()  # Reset station values

def resolve_operands(register_file, operands):
    Vj, Vk, Qj, Qk = None, None, None, None
    
    # Check the first operand
    if operands[0].startswith('R'):  # First operand, for example, "R1"
        reg_index = int(operands[0][1:].rstrip(','))  # Remove 'R' and any trailing commas
        if 0 <= reg_index < REGISTER_COUNT:
            Vj = register_file.get_value(reg_index)  # Get the value from the register file
            if register_file.status[reg_index] is not None:  # Check if the register is pending
                Qj = register_file.status[reg_index]  # Set the pending register's tag
        else:
            Vj = register_file.get_value(reg_index)

    # Check the second operand (if exists)
    if len(operands) > 1 and operands[1].startswith('R'):  # Second operand, for example, "R0"
        reg_index = int(operands[1][1:].rstrip(','))  # Remove 'R' and any trailing commas
        if 0 <= reg_index < REGISTER_COUNT:
            Vk = register_file.get_value(reg_index)  # Get the value from the register file
            if register_file.status[reg_index] is not None:  # Check if the register is pending
                Qk = register_file.status[reg_index]  # Set the pending register's tag
        else:
            Vj = register_file.get_value(reg_index)

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
    call_ret_station = ReservationStation("CALL/RET", 2, 4)  # CALL/RET station
    
    # Load instructions
    program_path = r'C:\Users\Toqa\Desktop\Tomasulo-with-speculation\sample_program.txt'
    instructions = load_program(program_path)
    instruction_queue=[]
    for instr in instructions:
        instruction_queue.append(instr)

    clock_cycles = 0
    completed_instructions = 0
    total_instructions = len(instructions)
    executed_instructions = set()

    while instruction_queue:
        current_instruction = instruction_queue.pop(0)
        print(f"Cycle {clock_cycles}: Processing {current_instruction.name}")


        # Skip already executed instructions
        if current_instruction in executed_instructions:
            continue

        # Dispatch instructions to reservation stations
        if current_instruction.operation == "ADD" and add_station.is_available():
            Vj, Vk, Qj, Qk = resolve_operands(register_file, current_instruction.operands)
            add_station.allocate(current_instruction.operation, Vj=Vj, Vk=Vk, Qj=Qj, Qk=Qk)
            print(f"Cycle {clock_cycles}: Resolving operands for {current_instruction.name} - Vj: {Vj}, Vk: {Vk}, Qj: {Qj}, Qk: {Qk}")
        elif current_instruction.operation == "ADDI" and addi_station.is_available():
            Vj, Vk, Qj, Qk = resolve_operands(register_file, current_instruction.operands)
            addi_station.allocate(current_instruction.operation, Vj=Vj, Vk=Vk, Qj=Qj, Qk=Qk)
            print(f"Cycle {clock_cycles}: Resolving operands for {current_instruction.name} - Vj: {Vj}, Vk: {Vk}, Qj: {Qj}, Qk: {Qk}")
        elif current_instruction.operation == "LOAD" and load_station.is_available():
            Vj, Vk, Qj, Qk = resolve_operands(register_file, current_instruction.operands)
            offset, reg_index = parse_memory_operand(current_instruction.operands[1])
            if 0 <= reg_index < REGISTER_COUNT:  # Validate register access
                load_station.allocate(current_instruction.operation, address=offset + register_file.get_value(reg_index), Vj=Vj, Vk=Vk, Qj=Qj, Qk=Qk)
                print(f"Cycle {clock_cycles}: Resolving operands for {current_instruction.name} - Vj: {Vj}, Vk: {Vk}, Qj: {Qj}, Qk: {Qk}")
            else:
                print(f"Error: Register {reg_index} out of bounds for LOAD operation.")
        elif current_instruction.operation == "STORE" and store_station.is_available():
            Vj, Vk, Qj, Qk = resolve_operands(register_file, current_instruction.operands)
            offset, reg_index = parse_memory_operand(current_instruction.operands[1])
            if 0 <= reg_index < REGISTER_COUNT:  # Validate register access
                store_station.allocate(current_instruction.operation, Vj=Vj, address=offset + register_file.get_value(reg_index), Qj=Qj, Qk=Qk)
            else:
                print(f"Error: Register {reg_index} out of bounds for STORE operation.")
        elif current_instruction.operation == "NAND" and nand_station.is_available():
            Vj, Vk, Qj, Qk = resolve_operands(register_file, current_instruction.operands)
            nand_station.allocate(current_instruction.operation, Vj=Vj, Vk=Vk, Qj=Qj, Qk=Qk)
        elif current_instruction.operation == "BEQ" and branch_station.is_available():
            reg1_index = int(current_instruction.operands[0][1:].replace(',', ''))
            reg2_index = int(current_instruction.operands[1][1:].replace(',', ''))  # Fixed operand index for reg2
        
            if 0 <= reg1_index < REGISTER_COUNT and 0 <= reg2_index < REGISTER_COUNT:
                Vj, Vk, _, _ = resolve_operands(register_file, current_instruction.operands)
                if Vj == Vk:
                    print(f"Branch taken: {current_instruction.operands[0]} == {current_instruction.operands[1]}")
                    
                    # Determine the index of the current instruction in the instruction stream
                    branch_index = instructions.index(current_instruction)
                    
                    # Flush the instruction queue and prepare for the branch target
                    instruction_queue.clear()
        
                    branch_target_offset = int(current_instruction.operands[2])  # assuming operands[2] is the offset
                    branch_target_address = (branch_index + 1) + (branch_target_offset // 4)  # Calculate target instruction index
        
                    # Add instructions starting from the branch target address to the queue
                    for i in range(branch_target_address, len(instructions)):
                        print(f"Adding instruction {instructions[i].operation} {instructions[i].operands} to the queue.")
                        instruction_queue.append(instructions[i])

        # Update clock cycle here

        # Execute reservation stations for each cycle
        add_station.execute(register_file, memory)
        addi_station.execute(register_file, memory)
        load_station.execute(register_file, memory)
        store_station.execute(register_file, memory)
        nand_station.execute(register_file, memory)
        branch_station.execute(register_file, memory)
        # Handle instruction issue, start execution, finish execution, write result, and commit cycles

        for instruction in instructions:
            clock_cycles += 1
            print(f"End of Cycle {clock_cycles}:")
            
            
            if instruction.can_issue(clock_cycles):
                instruction.issue_cycle = clock_cycles
                print(f"Cycle {clock_cycles}: Issued {instruction.name}")
                if not instruction.can_issue(clock_cycles):
                 print(f"Cycle {clock_cycles}: Cannot issue {instruction.name}")
                break
            if instruction.can_start_execution(clock_cycles):
                instruction.start_exec_cycle = clock_cycles
                break
            if instruction.can_finish_execution(clock_cycles):
                instruction.finish_exec_cycle = clock_cycles
                break
            if instruction.can_write_result(clock_cycles):
                instruction.write_result_cycle = clock_cycles
                break
                
            if instruction.can_commit(clock_cycles):
                instruction.commit_cycle = clock_cycles
                break
                

            # Release completed stations and track execution
            completed_station_add = add_station.release(add_station)
            if completed_station_add:
                completed_instructions += 1
                executed_instructions.add(current_instruction)  # Mark as executed
            
            completed_station_addi = addi_station.release(addi_station)
            if completed_station_addi:
                completed_instructions += 1
            
            completed_station_load = load_station.release(load_station)
            if completed_station_load:
                completed_instructions += 1
            
            completed_station_store = store_station.release(store_station)
            if completed_station_store:
                completed_instructions += 1
            
            completed_station_nand = nand_station.release(nand_station)
            if completed_station_nand:
                completed_instructions += 1
            
            completed_station_branch = branch_station.release(branch_station)
            if completed_station_branch:
                completed_instructions += 1
                
            
          

        if completed_instructions == total_instructions:
            print(f"All instructions completed in {clock_cycles} cycles.")
            break

        # Calculate ICP (Instruction Completion Percent)
        icp = (completed_instructions / total_instructions) * 100
        print(f"ICP (Instruction Completion Percent): {icp:.2f}%")
        
        # Print instruction execution table
        print(clock_cycles)
        print("Instruction Execution Table:")
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
        print(f"\nSimulation Results:")
        print(f"Total Cycles: {total_cycles}")
        print(f"IPC: {ipc:.2f}")


if __name__ == "__main__":
    main()
