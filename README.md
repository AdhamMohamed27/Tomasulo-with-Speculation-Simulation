# femTomas: Tomasulo Algorithm Simulation

## Project Overview

femTomas is a simulation project designed to model the performance of a simplified out-of-order 16-bit RISC processor that utilizes Tomasulo’s algorithm with speculation. This simulator is part of the CSCE 3301 – Computer Architecture course for Fall 2024.

The project simulates instruction execution in a RISC processor architecture, supporting Tomasulo’s algorithm to manage data hazards and improve instruction throughput. The goal is to evaluate the effectiveness of speculative execution and out-of-order completion in enhancing performance.

## How to Run

1. Clone the repository.
2. Ensure Python is installed (if using Python for the implementation).
3. Place your assembly program in the project directory.
4. Run the main simulation script:
   ```
   python main.py
   ```
5. The output will include the full execution table, IPC, total cycles, and misprediction rate.

## Inputs

- Assembly program to simulate.
- Initial data values and memory locations to preload.
- Starting program address.

## Outputs

- A detailed execution table showing:
  - **The cycle of issue, start execution, finish execution, write result, and commit**.
- Total execution time (in cycles).
- IPC (Instructions Per Cycle).
- Branch misprediction percentage.

## License

This project is for educational purposes only as part of CSCE 3301 at [Your University Name]. Unauthorized distribution or copying of the project code is prohibited.

---

For questions or clarifications, feel free to reach out to the course instructor or the project team.

