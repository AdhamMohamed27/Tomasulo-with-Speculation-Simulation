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

if __name__ == "__main__":
    print("Welcome to femTomas Simulator!")

    # Provide the correct file path
    program = load_program(r'C:\Users\Toqa\Desktop\Tomasulo-with-speculation\sample_program.txt')

    for instr in program:
        print(f"Operation: {instr.operation}, Operands: {instr.operands}")

