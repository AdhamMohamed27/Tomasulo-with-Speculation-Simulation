# Tomasulo Algorithm Simulation README

## Project Overview

The Tomasulo Algorithm Simulator simulates the execution of a simplified 16-bit RISC processor that utilizes Tomasulo's algorithm with speculative execution. The simulator models the architecture of a processor that supports out-of-order execution of instructions, along with features such as branch prediction, reservation stations, reorder buffers, and functional units.

This project is designed to evaluate the performance of the processor by simulating the execution of a series of assembly instructions and calculating performance metrics, including cycles, instructions per cycle (IPC), and branch misprediction rate.

## Features

### Support for Basic RISC Instructions:
- Load/Store operations
- Conditional Branches
- Call and Return operations
- Arithmetic and Logic operations (ADD, ADDI, NAND, MUL)

### Tomasulo’s Algorithm Implementation:
- Reservation Stations for different functional units
- Reorder Buffer (ROB) to handle out-of-order execution and speculative execution
- Branch prediction (Always Not Taken)

### Performance Metrics:
- Number of instructions completed
- Number of conditional branches encountered
- Total number of cycles spanned
- Branch misprediction percentage

### Simplified 16-bit RISC Processor:
- 8 general-purpose registers (R0 to R7)
- Word addressable memory with 128 KB capacity
- Support for a basic instruction set and corresponding data operations

### Backend Stages:
- **Issue**: 1 cycle
- **Execute**: Variable cycles depending on the functional unit
- **Write**: 1 cycle
- **Commit**: 1 cycle (except for stores)

## Instructions Supported

The simulator supports the following 16-bit instructions:

### Load/Store:
- `LOAD rA, offset(rB)`
- `STORE rA, offset(rB)`

### Branch Operations:
- `BEQ rA, rB, offset`

### Call/Return:
- `CALL label`
- `RET`

### Arithmetic and Logic:
- `ADD rA, rB, rC`
- `ADDI rA, rB, imm`
- `NAND rA, rB, rC`
- `MUL rA, rB, rC`

## Functional Units and Cycles

The following functional units and their respective cycle counts are modeled in the simulation:

| Functional Unit | Reservation Stations | Cycles Required |
|-----------------|----------------------|-----------------|
| **LOAD**        | 2                    | 2 (address computation) + 4 (memory read) |
| **STORE**       | 1                    | 2 (address computation) + 4 (memory write) |
| **BEQ**          | 1                    | 1 (compare and compute target) |
| **CALL/RET**     | 1                    | 1 (compute target and return address) |
| **ADD/ADDI**     | 4                    | 2               |
| **NAND**         | 2                    | 1               |
| **MUL**          | 1                    | 8               |

## Input Format

- **Assembly Program**: The user can input an assembly program consisting of instructions that are to be simulated. The program can be entered line-by-line or loaded from a file.
- **Memory Data**: Initial data for memory, including the value and memory address for each item, must be provided. All data is assumed to be 16-bit values.

## Output Format

At the end of the simulation, the following performance metrics will be displayed:

- **Instruction Cycle Table**: Clock cycle time at which each instruction was issued, started execution, finished execution, written, and committed.
- **Total Execution Time**: Total number of cycles spanned during the execution.
- **IPC (Instructions Per Cycle)**: The ratio of instructions completed to the total cycles.
- **Branch Misprediction Percentage**: Percentage of mispredicted branches during simulation.

## Simulator Assumptions

- Fetching and decoding take 0 cycles, and all instructions are already available for simulation.
- No floating-point instructions are supported.
- No input/output or interrupt/exception handling is required.
- The program and its data are assumed to be fully loaded in memory before execution.
- The number of reservation stations corresponds to the number of functional units, with each reservation station dedicated to a single functional unit.
- No cache or virtual memory is simulated (a bonus feature can be added to simulate this).

## How to Use

1. **Input the assembly program**: Provide the assembly instructions along with any necessary labels for jump targets and function calls.
2. **Load initial memory data**: Input the memory values with corresponding memory addresses.
3. **Run the simulation**: The simulator will process the instructions using Tomasulo’s algorithm and generate performance metrics.
4. **View the results**: After the simulation completes, review the output, including cycle times and performance metrics.

## Team Members

- **Member 1**: Toqa Mahmoud
- **Member 2**: Adham Salem

## Deliverables

- **Simulator Source Code**: The main program files implementing the Tomasulo algorithm.
- **Test Cases**: At least three assembly programs used to test the simulator, covering all instruction types and one program with a loop.
- **Report**: A detailed report discussing the implementation, results, and any bonus features included in the project.

## Known Issues

[List any known issues here, if any.]

## License

This project is submitted as part of the CSCE 3301 course and is not intended for redistribution.
