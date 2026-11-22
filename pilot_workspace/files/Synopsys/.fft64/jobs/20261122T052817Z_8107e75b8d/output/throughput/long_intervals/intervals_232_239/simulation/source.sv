module fft64_reorder (
    input  wire clk,
    input  wire rst,
    input  wire in_valid,
    input  wire frame_start,
    input  wire signed [13:0] in_re,
    input  wire signed [13:0] in_im,
    output reg  out_valid,
    output reg  signed [13:0] out_re,
    output reg  signed [13:0] out_im
);
    // max(reverse6(k) - k) = 49. Start one cycle later so each read
    // follows its write, including the bin whose input is 49 cycles later.
    localparam [5:0] READ_DELAY = 6'd50;

    reg [27:0] samples [0:63];
    reg [5:0] write_index, read_index, read_delay;
    reg write_reversed, read_reversed;

    function automatic [5:0] reverse6(input [5:0] index);
        reverse6 = {index[0], index[1], index[2], index[3], index[4], index[5]};
    endfunction

    wire start_write = in_valid && frame_start && (write_index == 6'd0);
    wire writing = in_valid && (start_write || (write_index != 6'd0));
    wire reading = (read_delay == 6'd1) || (read_index != 6'd0);
    wire [5:0] write_address = write_reversed ? reverse6(write_index) : write_index;
    wire [5:0] read_address = read_reversed ? reverse6(read_index) : read_index;

    // As bit reversal is an involution, consecutive frames can use opposite
    // write orientations. With II >= 64 the next frame visits each slot
    // after the previous reader has consumed it.
    always @(posedge clk) begin
        if (rst) begin
            write_index <= 6'd0;
            read_index <= 6'd0;
            read_delay <= 6'd0;
            write_reversed <= 1'b0;
            read_reversed <= 1'b1;
            out_valid <= 1'b0;
        end else begin
            if (writing) begin
                write_index <= write_index + 6'd1;
                if (write_index == 6'd63) write_reversed <= !write_reversed;
            end
            if (reading) begin
                read_index <= read_index + 6'd1;
                if (read_index == 6'd63) read_reversed <= !read_reversed;
            end
            if (start_write) read_delay <= READ_DELAY;
            else if (read_delay != 6'd0) read_delay <= read_delay - 6'd1;
            out_valid <= reading;
        end
        if (writing) samples[write_address] <= {in_re, in_im};
        {out_re, out_im} <= samples[read_address];
    end
endmodule

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

module fft64_twiddle #(
    parameter integer WIDTH = 16,
    parameter integer LOG_SPAN = 4,
    parameter integer OUT_WIDTH = WIDTH,
    parameter integer DROP = 0
) (
    input  wire clk,
    input  wire rst,
    input  wire in_valid,
    input  wire signed [WIDTH-1:0] in_re,
    input  wire signed [WIDTH-1:0] in_im,
    output reg  out_valid,
    output reg  signed [OUT_WIDTH-1:0] out_re,
    output reg  signed [OUT_WIDTH-1:0] out_im
);
    localparam integer FRACTION = 11;
    localparam integer SHIFT = FRACTION + DROP;
    localparam integer PRODUCT_WIDTH = WIDTH + 13;

    reg [LOG_SPAN-1:0] phase;
    wire [LOG_SPAN-1:0] offset = {{2{1'b0}}, phase[LOG_SPAN-3:0]};
    reg [LOG_SPAN-1:0] power;
    always @* begin
        case (phase[LOG_SPAN-1 -: 2])
            2'd0: power = 0;
            2'd1: power = offset << 1;
            2'd2: power = offset;
            2'd3: power = (offset << 1) + offset;
        endcase
    end
    wire [5:0] exponent = {power, {(6-LOG_SPAN){1'b0}}};
    wire reflect = exponent[3];
    wire [3:0] angle = reflect ? 4'd0 - exponent[3:0] : exponent[3:0];

    reg signed [11:0] sine;
    reg signed [12:0] cosine_minus_sine, cosine_plus_sine;

    // c and s are independently rounded Q11 values of cos and sin.
    // Store c-s and c+s exactly so the three-product rotation uses the
    // same coefficient matrix as direct four-product multiplication.
    always @* begin
        case (angle)
            4'd0: {sine, cosine_minus_sine, cosine_plus_sine} = {12'd0,    13'd2048, 13'd2048};
            4'd1: {sine, cosine_minus_sine, cosine_plus_sine} = {12'd201,  13'd1837, 13'd2239};
            4'd2: {sine, cosine_minus_sine, cosine_plus_sine} = {12'd400,  13'd1609, 13'd2409};
            4'd3: {sine, cosine_minus_sine, cosine_plus_sine} = {12'd595,  13'd1365, 13'd2555};
            4'd4: {sine, cosine_minus_sine, cosine_plus_sine} = {12'd784,  13'd1108, 13'd2676};
            4'd5: {sine, cosine_minus_sine, cosine_plus_sine} = {12'd965,  13'd841,  13'd2771};
            4'd6: {sine, cosine_minus_sine, cosine_plus_sine} = {12'd1138, 13'd565,  13'd2841};
            4'd7: {sine, cosine_minus_sine, cosine_plus_sine} = {12'd1299, 13'd284,  13'd2882};
            4'd8: {sine, cosine_minus_sine, cosine_plus_sine} = {12'd1448, 13'd0,    13'd2896};
            default: {sine, cosine_minus_sine, cosine_plus_sine} = 0;
        endcase
    end

    function automatic signed [OUT_WIDTH-1:0] round_even(input signed [PRODUCT_WIDTH:0] x);
        reg increment;
        begin
            increment = x[SHIFT-1] && ((|x[SHIFT-2:0]) || x[SHIFT]);
            round_even = x[SHIFT +: OUT_WIDTH] + {{(OUT_WIDTH-1){1'b0}}, increment};
        end
    endfunction

    reg [2:0] valid_pipe;
    reg [2:0] rotation_coeff, rotation_product, rotation_round;
    reg signed [WIDTH-1:0] data_re, data_im;
    reg signed [WIDTH:0] data_sum;
    reg signed [11:0] coeff_shared;
    reg signed [12:0] coeff_re, coeff_im;
    reg signed [PRODUCT_WIDTH-1:0] product_shared, product_re, product_im;
    wire signed [PRODUCT_WIDTH:0] combined_re = product_re + product_shared;
    wire signed [PRODUCT_WIDTH:0] combined_im = product_im - product_shared;
    reg signed [OUT_WIDTH-1:0] rounded_re, rounded_im;
    wire signed [OUT_WIDTH-1:0] signed_re = rotation_round[1] ? -rounded_re : rounded_re;
    wire signed [OUT_WIDTH-1:0] signed_im = rotation_round[0] ? -rounded_im : rounded_im;

    always @(posedge clk) begin
        if (rst) begin
            phase <= 0;
            valid_pipe <= 0;
            out_valid <= 1'b0;
        end else begin
            if (in_valid) phase <= phase + 1'b1;
            valid_pipe <= {valid_pipe[1:0], in_valid};
            out_valid <= valid_pipe[2];
        end

        // Reflecting the angle exchanges I and Q before multiplication
        // and negates the imaginary result. The high exponent bits
        // apply the remaining integral quarter turns at the output.
        data_re <= reflect ? in_im : in_re;
        data_im <= reflect ? in_re : in_im;
        data_sum <= in_re + in_im;
        coeff_shared <= sine;
        coeff_re <= cosine_minus_sine;
        coeff_im <= cosine_plus_sine;
        rotation_coeff <= {exponent[4], exponent[5] ^ exponent[4], exponent[5] ^ reflect};

        // p=(I+Q)*s, I'=I*(c-s)+p, Q'=Q*(c+s)-p.
        product_shared <= data_sum * coeff_shared;
        product_re <= data_re * coeff_re;
        product_im <= data_im * coeff_im;
        rotation_product <= rotation_coeff;

        rounded_re <= round_even(combined_re);
        rounded_im <= round_even(combined_im);
        rotation_round <= rotation_product;

        out_re <= rotation_round[2] ? signed_im : signed_re;
        out_im <= rotation_round[2] ? signed_re : signed_im;
    end
endmodule
