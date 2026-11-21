// Copy this interface into your submission and implement the FFT.
module fft64_top (
    input wire clk,
    input wire rst,
    input wire in_valid,
    input wire frame_start,
    input wire signed [15:0] in_re,
    input wire signed [15:0] in_im,
    output wire out_valid,
    output wire out_start,
    output wire signed [23:0] out_re,
    output wire signed [23:0] out_im
);
    // Interface template only.
endmodule
