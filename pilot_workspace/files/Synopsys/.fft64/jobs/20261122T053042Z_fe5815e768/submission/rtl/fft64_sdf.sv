module fft64_sdf #(
    parameter integer WIDTH = 16,
    parameter integer LOG_DELAY = 0,
    parameter integer ROTATE_DIFF = 0
) (
    input  wire clk,
    input  wire rst,
    input  wire in_valid,
    input  wire signed [WIDTH-1:0] in_re,
    input  wire signed [WIDTH-1:0] in_im,
    output reg  out_valid,
    output reg  signed [WIDTH:0] out_re,
    output reg  signed [WIDTH:0] out_im
);
    localparam integer DELAY = 1 << LOG_DELAY;
    localparam integer PHASE_WIDTH = LOG_DELAY + 1 + ROTATE_DIFF;

    reg [PHASE_WIDTH-1:0] phase;
    reg [DELAY-1:0] valid_delay;
    reg signed [WIDTH:0] delay_re [0:DELAY-1];
    reg signed [WIDTH:0] delay_im [0:DELAY-1];

    wire butterfly = phase[LOG_DELAY];
    wire signed [WIDTH:0] last_re = delay_re[DELAY-1];
    wire signed [WIDTH:0] last_im = delay_im[DELAY-1];
    wire signed [WIDTH:0] sum_re = last_re + in_re;
    wire signed [WIDTH:0] sum_im = last_im + in_im;
    wire signed [WIDTH:0] diff_re = last_re - in_re;
    wire signed [WIDTH:0] diff_im = last_im - in_im;
    wire signed [WIDTH:0] feedback_re, feedback_im;

    // The transpose of the DIF radix-2-squared pair places the -j
    // rotation on the difference of the fourth quarter of a DIT pair.
    generate
        if (ROTATE_DIFF != 0) begin : gen_rotation
            wire rotate = phase[LOG_DELAY+1];
            assign feedback_re = rotate ? diff_im : diff_re;
            assign feedback_im = rotate ? -diff_re : diff_im;
        end else begin : gen_no_rotation
            assign feedback_re = diff_re;
            assign feedback_im = diff_im;
        end
    endgenerate

    integer tap;
    always @(posedge clk) begin
        if (rst) begin
            phase <= {PHASE_WIDTH{1'b0}};
            valid_delay <= {DELAY{1'b0}};
            out_valid <= 1'b0;
        end else begin
            if (in_valid) phase <= phase + 1'b1;
            valid_delay[0] <= in_valid;
            for (tap = 1; tap < DELAY; tap = tap + 1)
                valid_delay[tap] <= valid_delay[tap-1];
            out_valid <= valid_delay[DELAY-1];
        end
    end

    integer data_tap;
    always @(posedge clk) begin
        delay_re[0] <= butterfly ? feedback_re : {in_re[WIDTH-1], in_re};
        delay_im[0] <= butterfly ? feedback_im : {in_im[WIDTH-1], in_im};
        out_re <= butterfly ? sum_re : last_re;
        out_im <= butterfly ? sum_im : last_im;
        for (data_tap = 1; data_tap < DELAY; data_tap = data_tap + 1) begin
            delay_re[data_tap] <= delay_re[data_tap-1];
            delay_im[data_tap] <= delay_im[data_tap-1];
        end
    end
endmodule
