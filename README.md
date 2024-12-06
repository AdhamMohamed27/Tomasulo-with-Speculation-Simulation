# Tomasulo Algorithm with Speculation Simulation

A Python-based simulation of the Tomasulo algorithm with speculative execution. This project aims to illustrate how Tomasulo's dynamic scheduling mechanism handles instruction-level parallelism in processors, including speculation to optimize execution for branch instructions.

## Overview

Tomasulo's algorithm is a hardware-based approach to dynamic scheduling that resolves data hazards and enables out-of-order execution. This simulation incorporates speculative execution to improve performance in scenarios with branching.

Key features of this simulation include:
- Dynamic scheduling with reservation stations.
- Speculative execution with rollback support for incorrect branch predictions.
- Support for floating-point and integer instructions.
