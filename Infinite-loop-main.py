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

    def execute(self, current_cycle, metadata):
     for station in self.stations:
        if station['busy'] and station['cycles_left'] > 0:
            if station['cycles_left'] == self.execution_cycles:  # Start Execution
                for entry in metadata:
                    if entry['instruction'] == station['op'] and entry['start_exec'] is None:
                        entry['start_exec'] = current_cycle
                        break

            station['cycles_left'] -= 1

            if station['cycles_left'] == 0:  # Finish Execution
                if station['op'] == "ADD":
                    if station['Vj'] is not None and station['Vk'] is not None:
                        station['result'] = station['Vj'] + station['Vk']
                    else:
                        print(f"Error: ADD operands not resolved: Vj={station['Vj']}, Vk={station['Vk']}")
                        continue  # Skip this station and go to the next
                elif station['op'] == "LOAD":
                    if station['Vk'] is not None:
                        station['result'] = station['Vk']  # Simulated memory load
                    else:
                        print(f"Error: LOAD operand not resolved: Vk={station['Vk']}")
                        continue
                elif station['op'] == "STORE":
                    if station['Vj'] is not None:
                        station['result'] = station['Vj']  # Simulated memory store
                    else:
                        print(f"Error: STORE operand not resolved: Vj={station['Vj']}")
                        continue
                else:
                    station['result'] = 0  # Default for unsupported operations

                for entry in metadata:
                    if entry['instruction'] == station['op'] and entry['finish_exec'] is None:
                        entry['finish_exec'] = current_cycle
                        break

                return station
     return None


    def release(self, station):
        station.update({'busy': False, 'op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'cycles_left': 0})

def parse_instruction(line):
    parts = line.strip().split()
    operation = parts[0]
    operands = [op.strip(',') for op in parts[1:]]
    return Instruction(operation, operands)

class InstructionQueue:
    def __init__(self, instructions=None):
        # Initialize with a list of instructions or an empty list
        self.queue = instructions if instructions else []

    def add(self, instruction):
        # Append a new instruction to the queue
        self.queue.append(instruction)

    def fetch(self):
        # Pop the first instruction from the queue
        if self.queue:
            return self.queue.pop(0)
        return None

    def is_empty(self):
        # Check if the queue is empty
        return len(self.queue) == 0

    def __len__(self):
        # Ensure len() works on the InstructionQueue object
        return len(self.queue)


class TomasuloSimulator:
    def __init__(self, program_file):
        self.register_file = RegisterFile(num_registers=REGISTER_COUNT)
        self.memory = Memory(size=MEMORY_SIZE)
        self.instruction_queue = InstructionQueue(self.load_program(program_file))
        self.load_station = ReservationStation("LOAD", 2, 6)
        self.add_station = ReservationStation("ADD/ADDI", 4, 2)
        self.store_station = ReservationStation("STORE", 1, 6)
        self.reorder_buffer = ReorderBuffer(size=6)
        self.instruction_metadata = []
        self.current_cycle = 1

    def load_program(self, file_path):
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

    def resolve_operands(self, operands):
        Vj, Vk, Qj, Qk = None, None, None, None
        reg_index = int(operands[0][1:])
        if self.register_file.is_ready(reg_index):
            Vj = self.register_file.get_value(reg_index)
        else:
            Qj = self.register_file.status[reg_index]

        if len(operands) > 1:
            operand = operands[1]
            if '(' in operand:
                offset, reg = operand.split('(')
                reg = reg.strip(')')
                reg_index = int(reg[1:])
                if self.register_file.is_ready(reg_index):
                    Vk = self.register_file.get_value(reg_index) + int(offset)
                else:
                    Qk = self.register_file.status[reg_index]
            else:
                reg_index = int(operand[1:])
                if self.register_file.is_ready(reg_index):
                    Vk = self.register_file.get_value(reg_index)
                else:
                    Qk = self.register_file.status[reg_index]
        print(f"Resolved Operands - Vj: {Vj}, Vk: {Vk}, Qj: {Qj}, Qk: {Qk}")            
        return Vj, Vk, Qj, Qk

    def execute_and_commit(self, reservation_station):
        completed_station = reservation_station.execute(self.current_cycle, self.instruction_metadata)
        if completed_station:
            for reg_index, status in enumerate(self.register_file.status):
                if status == reservation_station.name:
                    self.register_file.set_value(reg_index, completed_station['result'])
                    self.register_file.clear_status(reg_index)

            rob_entry = self.reorder_buffer.add(completed_station['op'])
            if rob_entry:
                rob_entry['state'] = 'write'

            for metadata_entry in self.instruction_metadata:
                if metadata_entry['instruction'] == completed_station['op']:
                    metadata_entry['write_back'] = self.current_cycle + 1
                    break

            reservation_station.release(completed_station)

    def run(self):
     while not self.instruction_queue.is_empty() or any(
        station['busy'] for station_group in [self.load_station.stations, self.add_station.stations, self.store_station.stations]
        for station in station_group
     ):
        print(f"\nCycle {self.current_cycle}:")
        print(f"Instruction Queue Empty: {self.instruction_queue.is_empty()}")
        print("Reservation Stations Status:")
        for station_group in [self.load_station.stations, self.add_station.stations, self.store_station.stations]:
            print(station_group)

        # Fetch and issue instructions
        if not self.instruction_queue.is_empty():
            instr = self.instruction_queue.fetch()
            print(f"Fetched Instruction: {instr.operation}, Operands: {instr.operands}")
            Vj, Vk, Qj, Qk = self.resolve_operands(instr.operands)

            if instr.operation == "LOAD" and self.load_station.is_available():
                station = self.load_station.allocate(op=instr.operation, Vj=Vj, Vk=Vk, Qj=Qj, Qk=Qk)
                reg_index = int(instr.operands[0][1:])
                self.register_file.set_status(reg_index, "LOAD")
                self.instruction_metadata.append({
                    "instruction": instr.operation,
                    "issued": self.current_cycle,
                    "start_exec": None,
                    "finish_exec": None,
                    "write_back": None
                })
            elif instr.operation == "STORE" and self.store_station.is_available():
                station = self.store_station.allocate(op=instr.operation, Vj=Vj, Vk=Vk, Qj=Qj, Qk=Qk)
                self.instruction_metadata.append({
                    "instruction": instr.operation,
                    "issued": self.current_cycle,
                    "start_exec": None,
                    "finish_exec": None,
                    "write_back": None
                })
            elif instr.operation in ["ADD", "ADDI"] and self.add_station.is_available():
                station = self.add_station.allocate(op=instr.operation, Vj=Vj, Vk=Vk, Qj=Qj, Qk=Qk)
                reg_index = int(instr.operands[0][1:])
                self.register_file.set_status(reg_index, "ADD")
                self.instruction_metadata.append({
                    "instruction": instr.operation,
                    "issued": self.current_cycle,
                    "start_exec": None,
                    "finish_exec": None,
                    "write_back": None
                })

        # Execute and commit instructions
        self.execute_and_commit(self.load_station)
        self.execute_and_commit(self.add_station)
        self.execute_and_commit(self.store_station)

        # Move to the next cycle
        self.current_cycle += 1

        print(f"End of Cycle {self.current_cycle}:")
        print("Instruction Metadata:", self.instruction_metadata)

     print("\nPerformance Metrics:")
     print("Instruction | Issued | Start Exec | Finish Exec | Write Back")
     for entry in self.instruction_metadata:
        print(f"{entry['instruction']:12} | {entry['issued']:6} | {entry.get('start_exec', 'N/A'):10} | {entry.get('finish_exec', 'N/A'):11} | {entry.get('write_back', 'N/A'):10}")



if __name__ == "__main__":
    simulator = TomasuloSimulator(r'C:\Users\Toqa\Desktop\Tomasulo-with-speculation\sample_program.txt')
    simulator.run()

