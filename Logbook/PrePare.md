# Plan for Bench Inspection

## Responsibility

|  Member  |  Responsibility  ||
|---|---|---|
|Ben        | [Introduction](#introduction) |[Conclusion & Further Plans](#conclusion--further-plans)|
|Kieran     | [Mechanical Structure](#mechanical-structure) |[3D Print / Lazer-cut components](#3d-print--lazer-cut-components)|
|Mohamed    | [Hardware components](#hardware-components) | [Hardware connection and Electrical Security](#hardware-connection-and-electrical-security)|
|Mochi      | [Reference Coordinate & Kinematic Solution](#reference-coordinate--kinematic-solution) |[System Integration & Project Management](#system-integration--project-management)|
|Junyi      | [Visual Detection & Identification System](#visual-detection--identification-system) ||
|Weican     | [Chess Game Playing System](#chess-game-playing-system) |[TUI Interface System](#tui-interface-system)|

## Presentation Process

### Introduction

- Project Name: Chess-Playing Robotic Arm
- An **Interactive** Chess Robot System
- build a system that combines precise mechanical control with chess intelligence
- designed the system with a **Modular Architecture**
- group division and the responsibility of each members

### Mechanical Structure

- 6 Degrees of Freedom, 5 for Positioning and 1 for End-Effector
- ...

### 3D Print / Lazer-cut components
- ...

### Hardware components
- Raspberry Pi 4B 8G, 1.5GHz 4-core ARM CPU
- Adafruit 16-Channel PWM Driver, use PCA9685 as main chip, control 16 motors synchronously
- Three-wire PWM servo motor

### Hardware connection and Electrical Security
- Low-voltage electrical circuit / Logic Power: provide by Raspberry Pi from Type-C ($5V/3A$)
- High-voltage electrical circuit / Drive Power: provide by DC power supplier ($5.2V/5A$)
- To ensure the consistency of the reference level of the PWM control signal, we performed **common grounding** for the logic ground and the power ground. This **eliminated signal drift** and **ensured that the servo motor did not shake**.
- We used the PWM driver board with I2C interface, which only occupied 2 pins (SDA/SCL) of the Raspberry Pi, significantly saving the IO resources, and the driver board also provided **a stable clock signal**.

### Reference Coordinate & Kinematic Solution

- Geometric Approach
- Decompose the three-dimensional coordinate system into two sets of two-dimensional coordinate systems to simplify the calculation.
- Always keep the End-Effector horizontal.

### Visual Detection & Identification System

- perspective transformation: Transform from an oblique perspective to a top-down perspective through geometric transformation.
- Since the camera is mounted at an angle, the raw image is distorted. We applied a Perspective Warp algorithm to map the trapezoidal board into a perfect $8\times8$ square grid. This ensures that every square has the same pixel dimensions for processing.
- We slice the processed image into 64 individual Regions of Interest (ROIs) and adjust the ROIs according to the perspective changes of the chess pieces.
- To simplifer the model, we only identify grid with white chesspiece, grid with black chesspiece and empty grid, and each of the three classes are separated into multiple subclasses to enhance the accurancy and confidency.
- While this algorithm is functional, we found that it requires strictly controlled environment to be 100% accurate. Hence, to ensure the Safety and Smoothness we will display the vision system separately from the integrate system.

### Chess Game Playing System

- Stockfish Engine: currently the strongest chess AI can be deployed locally
- UCI form input and output
- Move Validation and Legitimacy test

### TUI Interface System

- based on rich library of python
- Use readchar to monitor keyboard input in a separate thread
- Run in the local terminal or in a remote SSH window

### System Integration & Project Management

- we implemented a Multi-threaded System using Python's threading library.
- We designed specific threads for each subsystem.
- In the overall plan, the visual system and the logical system each occupy a separate thread and alternate the use of most computing power. One thread is responsible for the servo motor control. One for UI refresh and update. One for main program.
- - -
- We used a GitHub Team Repository to host not just our code, but also our datasets and documentation. This allowed for seamless version management and conflict resolution among our 6 members.
- We maintained a strict 'Lab Logbook' protocol. After every session, we updated the logbook with experimental data and bug reports.
- This structured workflow transformed us from a group of students into a cohesive engineering team.

### Conclusion & Further Plans

- We successfully integrated Inverse Kinematics, Game AI (Stockfish), and Safety Protocols into a lightweight Python architecture.
- Through our modular design and strict project management, we can ensure our system is reliable, safe and with potential to be improved.
- - -
- Currently, our OpenCV algorithm is sensitive to environment, if we have the opportunity to continue this project, we will explore the possibility of using **deep learning models (e.g. YOLOv8)**.
- We plan to manufacture the Ring Gripper that Kieran designed.
- We plan to implement the high-level function such as 'Castling' and 'En Passant'.


