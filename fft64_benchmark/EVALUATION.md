# Evaluation procedure

Public numerical: >=1,024 independent nonzero 64-point frames plus directed cases. Hidden numerical: >=8,192 plus directed cases. Mandatory service: >=1,024 consecutive frames at II=384. Every scored throughput II: >=1,024 consecutive frames. Mapped simulation: representative numerical/protocol subset. FFT length never changes.

Feasibility uses the minimum applicable nonzero-frame SQNR (>=50dB), exact zero for zero inputs, the maximum observed per-frame first-output and completion delays, mandatory 384-cycle service, reset, timing, and RTL/mapped consistency. Optional shorter-II failures are retained without rejecting mandatory feasibility.

The combined hardware score uses 60% area, 30% sustained throughput, and 10% maximum first-output latency. Effective throughput uses a fixed-netlist STA passing-clock certificate divided by the measured minimum passing II. Frequency is not separately rewarded. Same-backend accurate calibrations are frozen before official agent runs. There is no minimum score for feasibility. See SCORING.md.

Tools/libraries/runtime are detected before any build. Measurements are pre-layout, and finite tests are not a formal worst-case error guarantee. The operator keeps private calibration, hidden inputs and final records outside the public task checkout.
