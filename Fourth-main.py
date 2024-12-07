import sys

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
        self.memory = [0] * size

    def load(self, address):
        return self.memory[address]

    def store(self, address, value):
        self.memory[address] = value


class Instruction:
    def __init__(self, operation, operands):
        self.operation = operation
        self.operands = operands


def parse_instruction(line):
    parts = line.strip().split()
    operation = parts[0]
    operands = [op.strip(',') for op in parts[1:]]
    return Instruction(operation, operands)


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


class InstructionQueue:
    def __init__(self):
        self.queue = []

    def add(self, instruction):
        self.queue.append(instruction)

    def fetch(self):
        return self.queue.pop(0) if self.queue else None

    def is_empty(self):
        return len(self.queue) == 0


class ReservationStation:
    def __init__(self, name, num_stations, execution_cycles):
        self.name = name
        self.num_stations = num_stations
        self.execution_cycles = execution_cycles
        self.stations = [{'busy': False, 'op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'cycles_left': 0} 
                         for _ in range(num_stations)]

    def is_available(self):
        return any(not station['busy'] for station in self.stations)

    def allocate(self, op, Vj=None, Vk=None, Qj=None, Qk=None):
        for station in self.stations:
            if not station['busy']:
                station.update({'busy': True, 'op': op, 'Vj': Vj, 'Vk': Vk, 'Qj': Qj, 'Qk': Qk, 'cycles_left': self.execution_cycles})
                return station
        return None

    def execute(self):
        for station in self.stations:
            if station['busy'] and station['cycles_left'] > 0:
                station['cycles_left'] -= 1
                if station['cycles_left'] == 0:
                    station['result'] = 42  # Example result
                    return station
        return None

    def release(self, station):
        station.update({'busy': False, 'op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'cycles_left': 0})


class ReorderBuffer:
    def __init__(self, size):
        self.entries = [{'busy': False, 'instruction': None, 'state': 'issue', 'result': None} 
                        for _ in range(size)]

    def add(self, instruction):
        for entry in self.entries:
            if not entry['busy']:
                entry.update({'busy': True, 'instruction': instruction, 'state': 'issue', 'result': None})
                return entry
        return None

    def commit(self):
        for entry in self.entries:
            if entry['busy'] and entry['state'] == 'write':
                entry.update({'busy': False, 'instruction': None, 'state': 'issue', 'result': None})
                return True
        return False


def resolve_operands(register_file, operands):
    """Resolves operands for an instruction, handling immediate and register addressing."""
    Vj, Vk, Qj, Qk = None, None, None, None

    # Resolve the first operand (destination register, e.g., R1)
    reg_index = int(operands[0][1:])  # Extract index after 'R'
    if register_file.is_ready(reg_index):
        Vj = register_file.get_value(reg_index)
    else:
        Qj = register_file.status[reg_index]

    # Resolve the second operand (e.g., source register or immediate like 4(R2))
    if len(operands) > 1:
        operand = operands[1]
        if '(' in operand:  # Handle base-displacement addressing like 4(R2)
            offset, reg = operand.split('(')
            reg = reg.strip(')')
            reg_index = int(reg[1:])
            if register_file.is_ready(reg_index):
                Vk = register_file.get_value(reg_index) + int(offset)
            else:
                Qk = register_file.status[reg_index]
        else:  # Handle simple register like R2
            reg_index = int(operand[1:])
            if register_file.is_ready(reg_index):
                Vk = register_file.get_value(reg_index)
            else:
                Qk = register_file.status[reg_index]
    return Vj, Vk, Qj, Qk


def execute_and_commit(reservation_station, register_file, reorder_buffer, current_cycle, metadata):
    completed_station = reservation_station.execute()
    if completed_station:
        for reg_index, status in enumerate(register_file.status):
            if status == reservation_station.name:
                register_file.set_value(reg_index, completed_station['result'])
                register_file.clear_status(reg_index)

        rob_entry = reorder_buffer.add(completed_station['op'])
        if rob_entry:
            rob_entry['state'] = 'write'

        metadata.append({
            "instruction": completed_station['op'],
            "finish_exec": current_cycle
        })

        reservation_station.release(completed_station)


if __name__ == "__main__":
    
    register_file = RegisterFile(num_registers=REGISTER_COUNT)
    reorder_buffer = ReorderBuffer(size=6)
    program = load_program(r'C:\Users\Toqa\Desktop\Tomasulo-with-speculation\sample_program.txt')
    instruction_queue = InstructionQueue()

    for instr in program:
        instruction_queue.add(instr)

    load_station = ReservationStation("LOAD", 2, 6)
    add_station = ReservationStation("ADD/ADDI", 4, 2)
    store_station = ReservationStation("STORE", 1, 6)
    
    current_cycle = 1
    instruction_metadata = []
    
    while not instruction_queue.is_empty() or any(
        station['busy'] for station_group in [load_station.stations, add_station.stations, store_station.stations] 
        for station in station_group
    ):
        print(f"Cycle {current_cycle}:")
        
        if not instruction_queue.is_empty():
            instr = instruction_queue.fetch()
            print(f"Fetched Instruction: {instr.operation}, Operands: {instr.operands}")
            Vj, Vk, Qj, Qk = resolve_operands(register_file, instr.operands)

            if instr.operation == "LOAD" and load_station.is_available():
                station = load_station.allocate(op=instr.operation, Vj=Vj, Vk=Vk, Qj=Qj, Qk=Qk)
                reg_index = int(instr.operands[0][1:])
                register_file.set_status(reg_index, "LOAD")
                instruction_metadata.append({"instruction": instr.operation, "issued": current_cycle})
            elif instr.operation == "STORE" and store_station.is_available():
                station = store_station.allocate(op=instr.operation, Vj=Vj, Vk=Vk, Qj=Qj, Qk=Qk)
                instruction_metadata.append({"instruction": instr.operation, "issued": current_cycle})
            elif instr.operation in ["ADD", "ADDI"] and add_station.is_available():
                station = add_station.allocate(op=instr.operation, Vj=Vj, Vk=Vk, Qj=Qj, Qk=Qk)
                reg_index = int(instr.operands[0][1:])
                register_file.set_status(reg_index, "ADD")
                instruction_metadata.append({"instruction": instr.operation, "issued": current_cycle})

        execute_and_commit(load_station, register_file, reorder_buffer, current_cycle, instruction_metadata)
        execute_and_commit(add_station, register_file, reorder_buffer, current_cycle, instruction_metadata)
        execute_and_commit(store_station, register_file, reorder_buffer, current_cycle, instruction_metadata)

        current_cycle += 1
        # print("Debugging Metadata:", instruction_metadata)


    print("\nPerformance Metrics:")
    print("Instruction | Issued | Finish Exec")
    for entry in instruction_metadata:
         issued = entry.get('issued', 'N/A')
         finish_exec = entry.get('finish_exec', 'N/A')
         print(f"{entry['instruction']:12} | {issued:6} | {finish_exec:8}")
         
         