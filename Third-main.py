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
        available = any(not station['busy'] for station in self.stations)
        print(f"{self.name} availability: {available}")
        return available

    def allocate(self, op, Vj=None, Vk=None, Qj=None, Qk=None):
        for station in self.stations:
            if not station['busy']:
                station.update({'busy': True, 'op': op, 'Vj': Vj, 'Vk': Vk, 'Qj': Qj, 'Qk': Qk, 'cycles_left': self.execution_cycles})
                return station
        return None

    def execute(self):
        for station in self.stations:
            if station['busy'] and station['cycles_left'] > 0:
                print(f"{self.name} station executing {station['op']} with {station['cycles_left']} cycles left.")
                station['cycles_left'] -= 1
                if station['cycles_left'] == 0:
                    print(f"Station in {self.name} completed execution for operation {station['op']}")
                    station['result'] = 42  # Simulated result
                    return station
        return None

    def release(self, station):
        station.update({'busy': False, 'op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'cycles_left': 0})


def resolve_operands(register_file, operands):
    """Resolves operands for an instruction, handling immediate and register addressing."""
    Vj, Vk, Qj, Qk = None, None, None, None

    # Resolve the first operand (destination register, e.g., R1)
    reg_index = int(operands[0][1:])  # Extract index after 'R'
    if register_file.is_ready(reg_index):
        Vj = register_file.get_value(reg_index)
        print(f"Register R{reg_index} is ready with value {Vj}.")
    else:
        Qj = register_file.status[reg_index]
        print(f"Register R{reg_index} is waiting for station {Qj}.")

    # Resolve the second operand (e.g., source register or immediate like 4(R2))
    if len(operands) > 1:
        operand = operands[1]
        if '(' in operand:  # Handle base-displacement addressing like 4(R2)
            offset, reg = operand.split('(')
            reg = reg.strip(')')  # Remove the closing parenthesis
            reg_index = int(reg[1:])  # Extract index after 'R'
            if register_file.is_ready(reg_index):
                Vk = register_file.get_value(reg_index) + int(offset)  # Add offset
                print(f"Base-displacement: Register R{reg_index} with offset {offset} resolved to value {Vk}.")
            else:
                Qk = register_file.status[reg_index]
                print(f"Base-displacement: Register R{reg_index} is waiting for station {Qk}.")
        else:  # Handle simple register like R2
            reg_index = int(operand[1:])
            if register_file.is_ready(reg_index):
                Vk = register_file.get_value(reg_index)
                print(f"Register R{reg_index} is ready with value {Vk}.")
            else:
                Qk = register_file.status[reg_index]
                print(f"Register R{reg_index} is waiting for station {Qk}.")

    print(f"Resolved Operands - Vj: {Vj}, Vk: {Vk}, Qj: {Qj}, Qk: {Qk}")
    return Vj, Vk, Qj, Qk



def execute_and_commit(reservation_station, register_file):
    completed_station = reservation_station.execute()
    if completed_station:
        print(f"Completed execution in {reservation_station.name}: {completed_station}")
        result = completed_station['result']
        for reg_index, status in enumerate(register_file.status):
            if status == reservation_station.name:
                register_file.set_value(reg_index, result)
                register_file.clear_status(reg_index)
                print(f"Register R{reg_index} updated with result {result}.")
        reservation_station.release(completed_station)
    else:
        print(f"No instruction completed in {reservation_station.name}")


if __name__ == "__main__":
    print("Welcome to Tomasulo Simulator!")

    # Initialize the register file
    register_file = RegisterFile(num_registers=REGISTER_COUNT)

    # Load program
    program = load_program(r'C:\Users\Toqa\Desktop\Tomasulo-with-speculation\sample_program.txt')
    instruction_queue = InstructionQueue()
    for instr in program:
        instruction_queue.add(instr)

    # Initialize reservation stations
    load_station = ReservationStation("LOAD", 2, 6)
    add_station = ReservationStation("ADD/ADDI", 4, 2)

    while not instruction_queue.is_empty():
        instr = instruction_queue.fetch()
        print(f"Fetched Instruction: {instr.operation}, Operands: {instr.operands}")

        Vj, Vk, Qj, Qk = resolve_operands(register_file, instr.operands)

        if instr.operation in ["LOAD", "STORE"]:
            if load_station.is_available():
                station = load_station.allocate(op=instr.operation, Vj=Vj, Vk=Vk, Qj=Qj, Qk=Qk)
                print(f"Allocated {instr.operation} to LOAD station: {station}")
                reg_index = int(instr.operands[0][1:])
                register_file.set_status(reg_index, "LOAD")
            else:
                print(f"{instr.operation} instruction is waiting for a free station.")

        elif instr.operation in ["ADD", "ADDI"]:
            if add_station.is_available():
                station = add_station.allocate(op=instr.operation, Vj=Vj, Vk=Vk, Qj=Qj, Qk=Qk)
                print(f"Allocated {instr.operation} to ADD station: {station}")
                reg_index = int(instr.operands[0][1:])
                register_file.set_status(reg_index, "ADD")
            else:
                print(f"{instr.operation} instruction is waiting for a free station.")

        execute_and_commit(load_station, register_file)
        execute_and_commit(add_station, register_file)

