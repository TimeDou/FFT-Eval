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
    wire v0, v1, v2, v_tw16, v3, v4, v_tw64, v5;
    wire signed [13:0] r0, i0;
    wire signed [14:0] r1, i1;
    wire signed [15:0] r2, i2;
    wire signed [16:0] r_tw16, i_tw16;
    wire signed [17:0] r3, i3;
    wire signed [18:0] r4, i4;
    wire signed [17:0] r_tw64, i_tw64;
    wire signed [18:0] r5, i5;
    wire signed [19:0] r6, i6;

    // Q14 uses a 14-bit signed code. Its positive endpoint is one count
    // below +0.5. Round to even and saturate the endpoint.
    function automatic signed [13:0] input_q14(input signed [15:0] sample);
        begin
            if (sample >= 16'sd16383) input_q14 = 14'sd8191;
            else if (sample < -16'sd16384) input_q14 = 14'sh2000;
            else input_q14 = sample[14:1] + {13'd0, sample[0] && sample[1]};
        end
    endfunction

    fft64_reorder reorder_samples (
        .clk(clk), .rst(rst), .in_valid(in_valid), .frame_start(frame_start),
        .in_re(input_q14(in_re)), .in_im(input_q14(in_im)), .out_valid(v0), .out_re(r0), .out_im(i0)
    );
    fft64_sdf #(.WIDTH(14), .LOG_DELAY(0), .ROTATE_DIFF(1)) butterfly_2 (
        .clk(clk), .rst(rst), .in_valid(v0), .in_re(r0), .in_im(i0),
        .out_valid(v1), .out_re(r1), .out_im(i1)
    );
    fft64_sdf #(.WIDTH(15), .LOG_DELAY(1)) butterfly_4 (
        .clk(clk), .rst(rst), .in_valid(v1), .in_re(r1), .in_im(i1),
        .out_valid(v2), .out_re(r2), .out_im(i2)
    );
    fft64_twiddle #(.WIDTH(16), .LOG_SPAN(4), .OUT_WIDTH(17)) twiddle_16 (
        .clk(clk), .rst(rst), .in_valid(v2), .in_re(r2), .in_im(i2),
        .out_valid(v_tw16), .out_re(r_tw16), .out_im(i_tw16)
    );
    fft64_sdf #(.WIDTH(17), .LOG_DELAY(2), .ROTATE_DIFF(1)) butterfly_8 (
        .clk(clk), .rst(rst), .in_valid(v_tw16), .in_re(r_tw16), .in_im(i_tw16),
        .out_valid(v3), .out_re(r3), .out_im(i3)
    );
    fft64_sdf #(.WIDTH(18), .LOG_DELAY(3)) butterfly_16 (
        .clk(clk), .rst(rst), .in_valid(v3), .in_re(r3), .in_im(i3),
        .out_valid(v4), .out_re(r4), .out_im(i4)
    );
    fft64_twiddle #(.WIDTH(19), .LOG_SPAN(6), .OUT_WIDTH(18), .DROP(1)) twiddle_64 (
        .clk(clk), .rst(rst), .in_valid(v4), .in_re(r4), .in_im(i4),
        .out_valid(v_tw64), .out_re(r_tw64), .out_im(i_tw64)
    );
    fft64_sdf #(.WIDTH(18), .LOG_DELAY(4), .ROTATE_DIFF(1)) butterfly_32 (
        .clk(clk), .rst(rst), .in_valid(v_tw64), .in_re(r_tw64), .in_im(i_tw64),
        .out_valid(v5), .out_re(r5), .out_im(i5)
    );
    fft64_sdf #(.WIDTH(19), .LOG_DELAY(5)) butterfly_64 (
        .clk(clk), .rst(rst), .in_valid(v5), .in_re(r5), .in_im(i5),
        .out_valid(out_valid), .out_re(r6), .out_im(i6)
    );

    reg [5:0] output_index;
    reg first_output;
    always @(posedge clk) begin
        if (rst) begin
            output_index <= 6'd0;
            first_output <= 1'b0;
        end else begin
            if (v5) output_index <= output_index + 6'd1;
            // The final butterfly starts producing data 32 cycles after v5.
            first_output <= v5 && (output_index == 6'd32);
        end
    end

    assign out_start = out_valid && first_output;
    assign out_re = {{2{r6[19]}}, r6, 2'b00};
    assign out_im = {{2{i6[19]}}, i6, 2'b00};
endmodule
