# Logbook Group21
Project: Chess-Playing Robotic Arm

|Members| ID |
|---|---|
|Ben Hollington|201854508|
|Junyi Li|201779164|
|Kieran Fong|201786454|
|Mohamed Hegazy|201825978|
|Mochi Pan|201779181|
|Weican Hong|201779177|


**Main Hardware Components:**

- Joy-it Robot Arm Kit 360 ([Url](https://www.rapidonline.com/joy-it-robotic-arm-kit-360-turnable-compatable-with-arduino-and-raspberry-pi-00-0809))
- Raspberry Pi 4B (8G) ([Url](https://uk.rs-online.com/web/p/raspberry-pi/1822098?gb=a))
- Adafruit 16-Channel PWM Driver ([Url](https://thepihut.com/products/adafruit-16-channel-12-bit-pwm-servo-driver-i2c-interface-pca9685))
- Pi Camera ([Url](https://www.rapidonline.com/raspberry-pi-sc1224-camera-module-3-wide-angle-lens-75-1238))

## Week 1

### Finished
1. **Hardware Inventory & Validation**
    - Component Verification: Received all project components, including the Joy-it robotic arm kit, PCA9685 servo driver, and Raspberry Pi.
    - Integrity Check: Performed visual inspections and basic power-on tests to verify the integrity and functionality of all electronic modules.
2. **Mechanical Assembly & Actuator Calibration** (B.H. K.F. M.H. M.P.)
    - Structural Assembly: Completed the physical build of the robotic arm according to technical specifications.
    - Servo Zeroing: Manually calibrated and zeroed all servos before final installation to ensure a consistent coordinate system.
    - Hardware Integration: Soldered the header pins onto the PCA9685 PWM driver and established connections between the servos and the Raspberry Pi.
    - Custom Design: Drafted and prototyped a custom mounting solution for the Raspberry Pi Camera Module to ensure an optimal overhead view of the chessboard.
    - Reliability Testing: Conducted iterative movement checks to ensure mechanical stability and clear range of motion for each joint.
3. **Computing Environment Configuration** (M.P. J.L.)
    - OS & Remote Access: Initialized the Raspberry Pi OS and configured VNC/SSH for headless remote operation.
    - Environment Setup: Installed essential Python libraries and dependencies for GPIO control and I2C communication.
    - Hardware Interfacing: Enabled the CSI camera interface and I2C ports; configured user permissions for hardware access.
    - Resource Validation: Verified that the system correctly identifies the PCA9685 and the camera feed.
4. **Chess Engine Deployment** (M.P. W.H.)
    - Local Installation: Deployed the Stockfish chess engine onto the Raspberry Pi.
    - Performance Benchmarking: Executed stress tests and depth-analysis trials to ensure the engine runs efficiently on ARM architecture without overheating or latency issues.
    - Functional Verification: Confirmed the engine correctly processes FEN strings and returns valid move suggestions via the command line.
5. **System Design & Software Architecture**
    - Hardware Optimization: Refined the overall hardware design based on assembly findings, specifically improving cable management and power distribution.
    - Software Framework: Developed the preliminary software architecture, defining the interfaces between the vision module (input), the chess engine (logic), and the servo controller (output).
    - API Definition: Drafted initial API endpoints for the "Move Execution" and "Board Recognition" modules.

### Plan for Week 2

1. Complete basic build of hardware. (B.H. K.F. M.H.)
2. Hang the camera to a suitable position. (K.F.)
3. Pick something up and put things down. (M.P.)
4. Detect the chessboard and know where each pieces located. (J.L.)
5. Basically complete the logic processing. (W.H.)