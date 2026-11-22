# FFT64 design plan

The baseline is a streaming radix-2² DIF FFT with three butterfly pairs and two general complex rotators. It carries 15 fractional bits through every stage, grows one integer bit per butterfly, and rounds products with 12 fractional-bit twiddles. A single 64-word buffer uses alternating address permutations to overlap natural-order output with bit-reversed input. The hypothesis is that the streaming architecture can sustain II=64 with a small enough arithmetic footprint to preserve its throughput and latency credit.

A folded radix-2 FFT could use one general complex rotator, but would add butterfly memory ports and lengthen the compute schedule. Compare its weighted area gain with the loss from the longer initiation interval and first-output delay. A second streaming option is a delay-based reorder network, which could remove the large addressed read mux while increasing the count of delay registers. The read-mux timing path and full area diagnostic will guide that choice.

Measure precision changes on complete frames, including minimum-RMS sign patterns and bin sweeps. Test a tighter DC synthesis target after locating the critical paths in PrimeTime. Keep the frozen evaluation constraints and use independent mapped checks for custom exports.

