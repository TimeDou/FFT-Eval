# Reset diagnosis

The accurate iterative FFT's original four-state gate simulation stopped at cycle 411. A private VCS build reproduced the failure. A 138-cell control subnetwork reproduced it in Icarus as well. The stage counter's least significant bit remained X after reset because of reconvergent Boolean cancellation (`q | ~q`).

The supplied `reset_control.sv` cuts the 24 control FF outputs into arbitrary Boolean inputs and exposes their next states. The SAT command in `diagnostic_manifest.json` proves that asserted reset makes every one of these next states zero. This proves the control reset property, not full FFT sequential equivalence.

The complete native mapped FFT was then run from all-zero, all-one and seed-20261121 time-zero register states. Each start produced exactly the same 132108 observed control/payload rows as RTL across 168 input frames, resets during processing, and a long idle. Initialization is not repeated during reset or execution. The official v0.3 flow applies the same multi-start check on its complete dataset.

Pilot failures remain recorded here; they are not substituted for the final v0.3 calibration. Numerical specification, 50 dB SQNR, input domain, FFT gain/order and service protocol are unchanged.
