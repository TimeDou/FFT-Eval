# RTL interface and cycle semantics

The top-level module is **`fft64_top`** with the following fixed ports. A header is supplied in `interface/fft64_top.sv`.

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
    // Implement the FFT.
endmodule
```

Inputs are stable before a rising edge. The evaluator observes outputs after that edge, including nonblocking assignments. For a frame whose first input is captured at cycle 0, the remaining inputs are captured at cycles 1–63.

- `rst` is synchronous and active high. At a reset edge, `out_valid=out_start=0`; unfinished pre-reset work is discarded. Outputs emitted before a mid-output reset need not be retracted. New frames after reset must compute correctly.
- `frame_start=1` only on the first of 64 consecutive `in_valid=1` edges. There is no `ready`; the circuit accepts every legal offered frame.
- Mandatory-service frames start at least 384 cycles apart. Optional throughput tests use shorter integer intervals down to 64; failure there only limits measured capacity. Longer idle intervals, including beyond a 16-bit counter range, remain legal.
- Each output frame contains 64 consecutive valid edges. `out_start=1` only on its first valid edge; it is zero when `out_valid=0`.
- First output is between cycles 63 and 300 inclusive. The last output is no later than cycle 364. Natural frequency order is required.
- Payload outside `out_valid` is don't-care. Valid output payload and control must be known in four-state simulation.
- There is only one positive-edge `clk`. All memories, buffers and ordering logic are part of the implementation.

The two's-complement input/output integer codes have 15 fractional bits. Internal representation is a design choice. If internal scaling changes, restore the declared external FFT gain before output.

Output latency may depend on the frame as long as all deadlines and the offered service load are met. The service requirement does not require identical output-start intervals for variable-latency implementations.
