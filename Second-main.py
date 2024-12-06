# simulator.py
import sys
import os 

# Simulator Constants
REGISTER_COUNT = 8  # R0 to R7
MEMORY_SIZE = 128 * 1024  # 128 KB word-addressable memory
ROB_SIZE = 6  # reorder buffer size

# Classes for Core Components
class RegisterFile:
    def __init__(self):
        # R0 is always 0, the rest are used for any reason 
        self.registers = [0] * REGISTER_COUNT
        self.status = [None] * REGISTER_COUNT  # track reservation stations

    def read(self, reg_index):
        return self.registers[reg_index]

    def write(self, reg_index, value):
        if reg_index != 0:  # R0 is read-only
            self.registers[reg_index] = value

    def set_status(self, reg_index, status):
        self.status[reg_index] = status

    def clear_status(self, reg_index):
        self.status[reg_index] = None

    def get_status(self, reg_index):
        return self.status[reg_index]

class Memory:
    def __init__(self, size):
        self.memory = [0] * size

    def load(self, address):
        return self.memory[address]

    def store(self, address, value):
        self.memory[address] = value


register_file = RegisterFile()
memory = Memory(MEMORY_SIZE)

# How our simulator reads and writes instructions 
class Instruction:
    def __init__(self, operation, operands):
        self.operation = operation
        self.operands = operands  

def parse_instruction(line): #just parsing the code

    parts = line.strip().split()
    operation = parts[0]
    operands = [op.strip(',') for op in parts[1:]]
    return Instruction(operation, operands)

def load_program(file_path): #just for basically loading a assembly program from the sample .txt 

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


class InstructionQueue: #take all the parsed instructions and keep them here for issuing 
    def __init__(self):
        self.queue = []

    def add(self, instruction): #Adds an instruction to the queue
        
        self.queue.append(instruction)

    def fetch(self): #Fetches the next instruction from the queue
        
        return self.queue.pop(0) if self.queue else None

    def is_empty(self): #Checks if the queue is empty
        
        return len(self.queue) == 0


class ReservationStation: #Manages instruction dependencies and execution.
    def __init__(self, name, num_stations, execution_cycles):
        self.name = name
        self.num_stations = num_stations
        self.execution_cycles = execution_cycles  # Cycles needed to execute
        self.stations = [{'busy': False, 'op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'cycles_left': 0} 
                         for _ in range(num_stations)]

    def is_available(self): #Checks if there's an available station
       
        return any(not station['busy'] for station in self.stations)

    def allocate(self, op, Vj=None, Vk=None, Qj=None, Qk=None): #Allocates a station for a new instruction
       
        for station in self.stations:
            if not station['busy']:
                station.update({'busy': True, 'op': op, 'Vj': Vj, 'Vk': Vk, 'Qj': Qj, 'Qk': Qk, 'cycles_left': self.execution_cycles})
                return station
        return None

    def execute(self): #Simulates one cycle of execution for all busy stations
        
        for station in self.stations:
            if station['busy'] and station['cycles_left'] > 0:
                station['cycles_left'] -= 1
                if station['cycles_left'] == 0:
                    print(f"Station in {self.name} completed execution for operation {station['op']}")
                    return station  # Returns the completed station
        return None

    def release(self, station): #Releases a station after execution is complete
        
        station.update({'busy': False, 'op': None, 'Vj': None, 'Vk': None, 'Qj': None, 'Qk': None, 'cycles_left': 0})



class ReorderBuffer: 
    def __init__(self, size):
        self.entries = [{'busy': False, 'instruction': None, 'state': 'issue', 'result': None} 
                        for _ in range(size)]

    def add(self, instruction): #Adds an instruction to the ROB
      
        for entry in self.entries:
            if not entry['busy']:
                entry.update({'busy': True, 'instruction': instruction, 'state': 'issue', 'result': None})
                return entry
        return None

    def commit(self): #Commits the earliest ready instruction.
      
        for entry in self.entries:
            if entry['busy'] and entry['state'] == 'write':
                entry.update({'busy': False, 'instruction': None, 'state': 'issue', 'result': None})
                return True
        return False


if __name__ == "__main__":
    print("Welcome to Tomasulo Simulator!")

    # Provide the correct file path
    program = load_program(r'C:\Users\Toqa\Desktop\Tomasulo-with-speculation\sample_program.txt')

    for instr in program:
        print(f"Operation: {instr.operation}, Operands: {instr.operands}")
        
    # Initialize the instruction queue
    instruction_queue = InstructionQueue()
    for instr in program:
        instruction_queue.add(instr)

    # Print the instructions to confirm they are in the queue
    while not instruction_queue.is_empty():
        instr = instruction_queue.fetch()
        print(f"Fetched Instruction: {instr.operation}, Operands: {instr.operands}")    

    # Initialize reservation stations for each functional unit
    load_station = ReservationStation("LOAD", 2, 6)  # 2 (compute address) + 4 (read from memory)
    store_station = ReservationStation("STORE", 1, 6)  # 2 (compute address) + 4 (write to memory)
    beq_station = ReservationStation("BEQ", 1, 1)
    call_ret_station = ReservationStation("CALL/RET", 1, 1)
    add_station = ReservationStation("ADD/ADDI", 4, 2)
    nand_station = ReservationStation("NAND", 2, 1)
    mul_station = ReservationStation("MUL", 1, 8)

    # Example: Allocate an ADD instruction to a reservation station
    if add_station.is_available():
        station = add_station.allocate(op="ADD", Vj=5, Vk=10)
        print("Allocated Station:", station)

    # Simulate execution for one cycle
    completed_station = add_station.execute()
    if completed_station:
        add_station.release(completed_station)

