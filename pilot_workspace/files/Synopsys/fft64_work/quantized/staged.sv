module fft64_reorder (
    input  wire clk,
    input  wire rst,
    input  wire in_valid,
    input  wire frame_start,
    input  wire signed [14:0] in_re,
    input  wire signed [14:0] in_im,
    output reg  out_valid,
    output reg  signed [14:0] out_re,
    output reg  signed [14:0] out_im
);
    // max(reverse6(k) - k) = 49. Start one cycle later so each read
    // follows its write, including the bin whose input is 49 cycles later.
    localparam [5:0] READ_DELAY = 6'd50;

    reg [29:0] samples [0:63];
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
    wire signed [14:0] r0, i0;
    wire signed [15:0] r1, i1;
    wire signed [16:0] r2, i2, r_tw16, i_tw16;
    wire signed [17:0] r3, i3;
    wire signed [18:0] r4, i4;
    wire signed [17:0] r_tw64, i_tw64;
    wire signed [18:0] r5, i5;
    wire signed [19:0] r6, i6;

    // Round Q15 to Q14 before the input register file.
    wire signed [14:0] input_re_q14 = in_re[15:1] + {14'd0, in_re[0] && in_re[1]};
    wire signed [14:0] input_im_q14 = in_im[15:1] + {14'd0, in_im[0] && in_im[1]};

    fft64_reorder reorder_samples (
        .clk(clk), .rst(rst), .in_valid(in_valid), .frame_start(frame_start),
        .in_re(input_re_q14), .in_im(input_im_q14), .out_valid(v0), .out_re(r0), .out_im(i0)
    );
    fft64_sdf #(.WIDTH(15), .LOG_DELAY(0), .ROTATE_DIFF(1)) butterfly_2 (
        .clk(clk), .rst(rst), .in_valid(v0), .in_re(r0), .in_im(i0),
        .out_valid(v1), .out_re(r1), .out_im(i1)
    );
    fft64_sdf #(.WIDTH(16), .LOG_DELAY(1)) butterfly_4 (
        .clk(clk), .rst(rst), .in_valid(v1), .in_re(r1), .in_im(i1),
        .out_valid(v2), .out_re(r2), .out_im(i2)
    );
    fft64_twiddle #(.WIDTH(17), .LOG_SPAN(4)) twiddle_16 (
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
    fft64_twiddle #(.WIDTH(19), .LOG_SPAN(6), .DROP(1)) twiddle_64 (
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
    parameter integer WIDTH = 18,
    parameter integer LOG_SPAN = 4,
    parameter integer DROP = 0
) (
    input  wire clk,
    input  wire rst,
    input  wire in_valid,
    input  wire signed [WIDTH-1:0] in_re,
    input  wire signed [WIDTH-1:0] in_im,
    output reg  out_valid,
    output reg  signed [WIDTH-DROP-1:0] out_re,
    output reg  signed [WIDTH-DROP-1:0] out_im
);
    localparam integer FRACTION = 11;
    localparam integer SHIFT = FRACTION + DROP;
    localparam integer COEFF_WIDTH = FRACTION + 2;
    localparam integer PRODUCT_WIDTH = WIDTH + COEFF_WIDTH;

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

    // The first quadrant of sin(2*pi*k/64), rounded to 11 fraction bits.
    function automatic signed [COEFF_WIDTH-1:0] sine(input [5:0] angle);
        reg [4:0] index;
        reg [FRACTION:0] magnitude;
        begin
            index = angle[4] ? (5'd16 - {1'b0, angle[3:0]})
                             : {1'b0, angle[3:0]};
            case (index)
                5'd0:  magnitude = 12'd0;
                5'd1:  magnitude = 12'd201;
                5'd2:  magnitude = 12'd400;
                5'd3:  magnitude = 12'd595;
                5'd4:  magnitude = 12'd784;
                5'd5:  magnitude = 12'd965;
                5'd6:  magnitude = 12'd1138;
                5'd7:  magnitude = 12'd1299;
                5'd8:  magnitude = 12'd1448;
                5'd9:  magnitude = 12'd1583;
                5'd10: magnitude = 12'd1703;
                5'd11: magnitude = 12'd1806;
                5'd12: magnitude = 12'd1892;
                5'd13: magnitude = 12'd1960;
                5'd14: magnitude = 12'd2009;
                5'd15: magnitude = 12'd2038;
                5'd16: magnitude = 12'd2048;
                default: magnitude = 12'd0;
            endcase
            sine = angle[5] ? -$signed({1'b0, magnitude}) : $signed({1'b0, magnitude});
        end
    endfunction

    function automatic signed [WIDTH-DROP-1:0] round_even(input signed [PRODUCT_WIDTH:0] x);
        reg increment;
        begin
            increment = x[SHIFT-1] && ((|x[SHIFT-2:0]) || x[SHIFT]);
            round_even = x[SHIFT +: WIDTH-DROP] + {{(WIDTH-DROP-1){1'b0}}, increment};
        end
    endfunction

    reg valid_coeff, valid_product;
    reg signed [WIDTH-1:0] data_re, data_im;
    reg signed [COEFF_WIDTH-1:0] coeff_cos, coeff_sin;
    reg signed [PRODUCT_WIDTH-1:0] re_cos, re_sin, im_cos, im_sin;
    wire signed [PRODUCT_WIDTH:0] combined_re = re_cos + im_sin;
    wire signed [PRODUCT_WIDTH:0] combined_im = im_cos - re_sin;

    always @(posedge clk) begin
        if (rst) begin
            phase <= {LOG_SPAN{1'b0}};
            valid_coeff <= 1'b0;
            valid_product <= 1'b0;
            out_valid <= 1'b0;
        end else begin
            if (in_valid) phase <= phase + 1'b1;
            valid_coeff <= in_valid;
            valid_product <= valid_coeff;
            out_valid <= valid_product;
        end

        coeff_sin <= sine(exponent);
        coeff_cos <= sine(exponent + 6'd16);
        data_re <= in_re;
        data_im <= in_im;

        re_cos <= data_re * coeff_cos;
        re_sin <= data_re * coeff_sin;
        im_cos <= data_im * coeff_cos;
        im_sin <= data_im * coeff_sin;

        out_re <= round_even(combined_re);
        out_im <= round_even(combined_im);
    end
endmodule
