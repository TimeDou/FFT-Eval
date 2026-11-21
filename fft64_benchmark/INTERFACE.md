# FFT64 RTL Interface and Cycle Contract

The submission must include the synthesizable top-level module `fft64_top` with the fixed ports below. A declaration-only template is supplied in `interface/fft64_top.sv`; it is **not** a functional FFT.

```systemverilog
module fft64_top (
    input  wire clk,
    input  wire rst,
    input  wire in_valid,
    input  wire frame_start,
    input  wire signed [15:0] in_re,
    input  wire signed [15:0] in_im,
    output wire out_valid,
    output wire out_start,
    output wire signed [23:0] out_re,
    output wire signed [23:0] out_im
);
    // Design implementation goes here.
endmodule
```

## Input transactions

- Inputs are stable before the rising edge; outputs are observed after that edge, including nonblocking assignment updates.
- A frame begins when `in_valid=1` and `frame_start=1`, then provides **64 consecutive valid complex samples**. The first sample is cycle 0, the last cycle 63.
- The mandatory service interval between frame starts is **at least 384 cycles**, with no input backpressure. Longer and variable gaps are legal, including long intervals beyond a 16-bit counter range.
- Optional throughput tests use 64–383-cycle intervals to find additional *verified* capacity. Failure at an optional faster interval does not invalidate the mandatory service requirement.

## Output transactions and latency

- Each completed frame produces **64 consecutive `out_valid=1` cycles** in natural frequency order.
- Exactly the first output of each frame asserts `out_start=1`; `out_start=0` whenever `out_valid=0`.
- The first output must occur after the last required input, between cycles 63 and 300 inclusive. The last output must occur by cycle 364.
- The grader measures the **maximum per-frame** first-output and completion latency over the tested frames. Latency need not be constant across legal frames.
- Output payload is don't-care outside `out_valid`; inside valid cycles, all output data and control must be known under four-state simulation.

## Reset and hardware restrictions

Synchronous active-high `rst` aborts unfinished frames. An output prefix emitted before a reset need not be retracted, but no unfinished frame may reappear after reset. New frames following reset must be correct. Use only the specified positive-edge `clk`; storage, buffering, ordering logic and control must all be accounted for in the synthesized design. No uncounted SRAM, testbench-dependent lookup, or second clock is allowed.

Input/output real and imaginary fields are two's-complement with **15 fractional bits**. Intermediate representation may change, but the external FFT gain, scale and order may not.
