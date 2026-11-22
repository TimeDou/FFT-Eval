module fft64_top (
    input  wire               clk,
    input  wire               rst,
    input  wire               in_valid,
    input  wire               frame_start,
    input  wire signed [15:0] in_re,
    input  wire signed [15:0] in_im,
    output wire               out_valid,
    output wire               out_start,
    output wire signed [23:0] out_re,
    output wire signed [23:0] out_im
);
    // Only a frame_start can open a new 64-sample input packet.
    reg [5:0] samples_left;
    wire accept_sample = in_valid && (frame_start || samples_left != 0);
    always @(posedge clk) begin
        if (rst)
            samples_left <= 0;
        else if (accept_sample)
            samples_left <= frame_start ? 6'd63 : samples_left - 1'b1;
    end

    // Q15 storage omits the redundant sign bit over the specified input
    // range. Saturate the positive endpoint, which costs one input LSB.
    wire signed [14:0] sample_re, sample_im;
    function automatic signed [14:0] narrow_input(input signed [15:0] sample);
        case (sample[15:14])
            2'b01: narrow_input = 15'sd16383;
            2'b10: narrow_input = -15'sd16384;
            default: narrow_input = sample[14:0];
        endcase
    endfunction
    assign sample_re = narrow_input(in_re);
    assign sample_im = narrow_input(in_im);

    wire swap_50_valid, swap_41_valid, reversed_valid;
    wire signed [14:0] swap_50_re, swap_50_im, swap_41_re, swap_41_im;
    wire signed [14:0] reversed_re, reversed_im;

    // Bit reversal is three disjoint swaps in the six-bit sample index.
    // Moving this permutation to the DIT input keeps all delays narrow.
    // The first two swaps feed their successor directly; the third registers
    // its output before the first butterfly.
    fft64_index_swap #(.W(15), .HI(5), .LO(0), .REGISTER_OUTPUT(0)) swap_50
        (clk, rst, accept_sample, sample_re, sample_im, swap_50_valid, swap_50_re, swap_50_im);
    fft64_index_swap #(.W(15), .HI(4), .LO(1), .REGISTER_OUTPUT(0)) swap_41
        (clk, rst, swap_50_valid, swap_50_re, swap_50_im, swap_41_valid, swap_41_re, swap_41_im);
    fft64_index_swap #(.W(15), .HI(3), .LO(2)) swap_32
        (clk, rst, swap_41_valid, swap_41_re, swap_41_im, reversed_valid, reversed_re, reversed_im);

    wire fft2_valid, fft4_valid, tw16_valid, fft8_valid, fft16_valid, tw64_valid, fft32_valid;
    wire signed [15:0] fft2_re, fft2_im;
    wire signed [16:0] fft4_re, fft4_im, tw16_re, tw16_im, tw64_re, tw64_im;
    wire signed [17:0] fft8_re, fft8_im, fft32_re, fft32_im;
    wire signed [18:0] fft16_re, fft16_im, bin_re, bin_im;

    // The DIT pairs rotate the odd difference by -j in their first
    // butterfly. A general rotator precedes each of the last two pairs.
    fft64_sdf #(.W(15), .DELAY_LOG(0), .PAIR_FIRST(1)) bf_2
        (clk, rst, reversed_valid, reversed_re, reversed_im, fft2_valid, fft2_re, fft2_im);
    fft64_sdf #(.W(16), .DELAY_LOG(1)) bf_4
        (clk, rst, fft2_valid, fft2_re, fft2_im, fft4_valid, fft4_re, fft4_im);
    // Before the 16-point butterflies, add a rotation guard bit and round Q15 to Q14.
    fft64_twiddle #(.W(17), .SPAN_LOG(4), .DROP(1), .GROW(1)) rotate_16
        (clk, rst, fft4_valid, fft4_re, fft4_im, tw16_valid, tw16_re, tw16_im);
    fft64_sdf #(.W(17), .DELAY_LOG(2), .PAIR_FIRST(1)) bf_8
        (clk, rst, tw16_valid, tw16_re, tw16_im, fft8_valid, fft8_re, fft8_im);
    fft64_sdf #(.W(18), .DELAY_LOG(3)) bf_16
        (clk, rst, fft8_valid, fft8_re, fft8_im, fft16_valid, fft16_re, fft16_im);
    // Before the 64-point butterflies, round Q14 to Q12.
    fft64_twiddle #(.W(19), .SPAN_LOG(6), .DROP(2)) rotate_64
        (clk, rst, fft16_valid, fft16_re, fft16_im, tw64_valid, tw64_re, tw64_im);
    fft64_sdf #(.W(17), .DELAY_LOG(4), .PAIR_FIRST(1)) bf_32
        (clk, rst, tw64_valid, tw64_re, tw64_im, fft32_valid, fft32_re, fft32_im);
    fft64_sdf #(.W(18), .DELAY_LOG(5)) bf_64
        (clk, rst, fft32_valid, fft32_re, fft32_im, out_valid, bin_re, bin_im);

    reg [5:0] output_index;
    always @(posedge clk) begin
        if (rst)
            output_index <= 0;
        else if (out_valid)
            output_index <= output_index + 1'b1;
    end
    assign out_start = out_valid && output_index == 0;
    assign out_re = {{2{bin_re[18]}}, bin_re, 3'b000};
    assign out_im = {{2{bin_im[18]}}, bin_im, 3'b000};
endmodule

module fft64_index_swap #(
    parameter integer W = 16,
    parameter integer HI = 5,
    parameter integer LO = 0,
    parameter bit REGISTER_OUTPUT = 1
) (
    input  wire                clk,
    input  wire                rst,
    input  wire                in_valid,
    input  wire signed [W-1:0] in_re, in_im,
    output wire                out_valid,
    output wire signed [W-1:0] out_re, out_im
);
    localparam integer DELAY = (1 << HI) - (1 << LO);
    reg [HI:0] index;
    reg [DELAY-1:0] delay_valid;
    reg [2*W-1:0] data_delay [0:DELAY-1];

    // The 01 sample arrived DELAY clocks before the 10 sample. At their
    // meeting the late sample takes the output and the early sample makes
    // a second trip through the same delay line. Equal-bit samples go
    // through once. Each exchange is entirely within one contiguous frame.
    wire exchange = in_valid && index[HI] && !index[LO];
    wire [2*W-1:0] older = data_delay[DELAY-1];
    wire [2*W-1:0] forwarded = exchange ? {in_re, in_im} : older;
    wire forwarded_valid = delay_valid[DELAY-1];
    always @(posedge clk) begin
        if (rst) begin
            index <= 0;
            delay_valid <= 0;
        end else begin
            if (in_valid)
                index <= index + 1'b1;
            delay_valid <= {delay_valid[DELAY-2:0], in_valid};
        end
        data_delay[0] <= exchange ? older : {in_re, in_im};
    end
    if (REGISTER_OUTPUT) begin : output_register
        reg valid_reg;
        reg [2*W-1:0] data_reg;
        always @(posedge clk) begin
            valid_reg <= !rst && forwarded_valid;
            data_reg <= forwarded;
        end
        assign out_valid = valid_reg;
        assign {out_re, out_im} = data_reg;
    end else begin : direct_output
        assign out_valid = forwarded_valid;
        assign {out_re, out_im} = forwarded;
    end
    for (genvar i = 1; i < DELAY; i = i + 1) begin : delay_line
        always @(posedge clk)
            data_delay[i] <= data_delay[i-1];
    end
endmodule

module fft64_sdf #(
    parameter integer W = 16,
    parameter integer DELAY_LOG = 5,
    parameter bit PAIR_FIRST = 0
) (
    input  wire                clk,
    input  wire                rst,
    input  wire                in_valid,
    input  wire signed [W-1:0] in_re, in_im,
    output reg                 out_valid,
    output reg signed [W:0]    out_re, out_im
);
    localparam integer DELAY = 1 << DELAY_LOG;
    localparam integer COUNT_W = DELAY_LOG + (PAIR_FIRST ? 2 : 1);
    reg [COUNT_W-1:0] phase;
    reg [DELAY-1:0] delay_valid;
    reg signed [W:0] delay_re [0:DELAY-1];
    reg signed [W:0] delay_im [0:DELAY-1];

    wire butterfly = in_valid && phase[DELAY_LOG];
    wire quarter_turn = PAIR_FIRST && phase[COUNT_W-1];
    wire signed [W:0] input_re = {in_re[W-1], in_re};
    wire signed [W:0] input_im = {in_im[W-1], in_im};
    wire signed [W:0] older_re = delay_re[DELAY-1];
    wire signed [W:0] older_im = delay_im[DELAY-1];
    wire signed [W:0] diff_re = older_re - input_re;
    wire signed [W:0] diff_im = older_im - input_im;
    wire signed [W:0] feedback_re = quarter_turn ? diff_im : diff_re;
    wire signed [W:0] feedback_im = quarter_turn ? input_re - older_re : diff_im;

    always @(posedge clk) begin
        if (rst) begin
            phase <= 0;
            delay_valid <= 0;
            out_valid <= 0;
        end else begin
            if (in_valid)
                phase <= phase + 1'b1;
            delay_valid <= (delay_valid << 1) | {{(DELAY-1){1'b0}}, in_valid};
            out_valid <= delay_valid[DELAY-1];
        end
        out_re <= butterfly ? older_re + input_re : older_re;
        out_im <= butterfly ? older_im + input_im : older_im;
        delay_re[0] <= butterfly ? feedback_re : input_re;
        delay_im[0] <= butterfly ? feedback_im : input_im;
    end
    for (genvar i = 1; i < DELAY; i = i + 1) begin : delay_line
        always @(posedge clk) begin
            delay_re[i] <= delay_re[i-1];
            delay_im[i] <= delay_im[i-1];
        end
    end
endmodule

module fft64_twiddle #(
    parameter integer W = 18,
    parameter integer SPAN_LOG = 6,
    parameter integer DROP = 1,
    parameter integer GROW = 0
) (
    input  wire                     clk,
    input  wire                     rst,
    input  wire                     in_valid,
    input  wire signed [W-1:0]      in_re, in_im,
    output reg                      out_valid,
    output reg signed [W+GROW-DROP-1:0] out_re, out_im
);
    localparam integer F = SPAN_LOG == 4 ? 9 : 10;
    localparam integer COEFF_W = F + 2;
    localparam integer PRODUCT_W = W + COEFF_W;
    localparam integer ROUND_SHIFT = F + DROP;
    localparam integer OUT_W = W + GROW - DROP;
    localparam integer OFFSET_W = SPAN_LOG - 2;
    localparam signed [PRODUCT_W-1:0] BIAS = 1 << (ROUND_SHIFT-1);

    reg [SPAN_LOG-1:0] phase;
    wire [1:0] branch = phase[SPAN_LOG-1 -: 2];
    wire [OFFSET_W-1:0] offset = phase[OFFSET_W-1:0];
    wire [3:0] stride_offset = {offset, {(6-SPAN_LOG){1'b0}}};
    wire [5:0] n = {2'b00, stride_offset};
    reg [5:0] exponent;
    always @* begin
        case (branch)
            2'd1: exponent = n << 1;
            2'd2: exponent = n;
            2'd3: exponent = n + (n << 1);
            default: exponent = 0;
        endcase
    end

    wire [5:0] biased_phase = exponent + 6'd8;
    wire [1:0] quadrant = biased_phase[5:4];
    wire [3:0] reduced_phase = exponent[3:0];
    wire negative_phase = reduced_phase[3];
    wire [3:0] magnitude = negative_phase ? -reduced_phase : reduced_phase;

    // Use the magnitude of the residual angle. The largest coefficient,
    // cos(t)+sin(t), is always in [1,sqrt(2)] so its unity bit is fixed.
    function automatic [31:0] coefficients_16(input [3:0] phase_code);
        case (phase_code)
            4'd0: coefficients_16 = {11'sd512, 11'sd512, 10'sd0};
            4'd4: coefficients_16 = {11'sd669, 11'sd277, 10'sd196};
            4'd8: coefficients_16 = {11'sd724, 11'sd0, 10'sd362};
            default: coefficients_16 = {11'sd512, 11'sd512, 10'sd0};
        endcase
    endfunction

    function automatic [34:0] coefficients_64(input [3:0] phase_code);
        case (phase_code)
            4'd0: coefficients_64 = {12'sd1024, 12'sd1024, 11'sd0};
            4'd1: coefficients_64 = {12'sd1119, 12'sd919, 11'sd100};
            4'd2: coefficients_64 = {12'sd1204, 12'sd804, 11'sd200};
            4'd3: coefficients_64 = {12'sd1277, 12'sd683, 11'sd297};
            4'd4: coefficients_64 = {12'sd1338, 12'sd554, 11'sd392};
            4'd5: coefficients_64 = {12'sd1386, 12'sd420, 11'sd483};
            4'd6: coefficients_64 = {12'sd1420, 12'sd282, 11'sd569};
            4'd7: coefficients_64 = {12'sd1442, 12'sd142, 11'sd650};
            4'd8: coefficients_64 = {12'sd1448, 12'sd0, 11'sd724};
            default: coefficients_64 = {12'sd1024, 12'sd1024, 11'sd0};
        endcase
    endfunction

    wire [2*COEFF_W+F:0] coeff_word;
    if (SPAN_LOG == 4) begin : rom_16
        assign coeff_word = coefficients_16(magnitude);
    end else begin : rom_64
        assign coeff_word = coefficients_64(magnitude);
    end

    reg signed [W-1:0] re_pre, im_pre;
    reg signed [W:0] diff_pre;
    reg signed [COEFF_W-1:0] plus_pre, minus_pre;
    reg signed [F:0] sine_pre;
    reg signed [PRODUCT_W-1:0] re_product, im_product, common_product;
    reg [1:0] quadrant_pre, quadrant_product, quadrant_sum;
    reg add_pre, add_product;
    reg [2:0] valid_pipe;

    // For a positive angle both components subtract (re-im)*sin(t).
    // For a negative angle the common term is (re+im)*sin(t); its sign
    // is negative for the real output and positive for the imaginary one.
    wire signed [W:0] ext_re = {in_re[W-1], in_re};
    wire signed [W:0] ext_im = {in_im[W-1], in_im};
    wire signed [W:0] signed_im = ext_im ^ {(W+1){!negative_phase}};
    wire signed [W:0] diff_or_sum =
        ext_re + signed_im + $signed({{W{1'b0}}, !negative_phase});
    wire signed [PRODUCT_W-1:0] signed_common = common_product ^ {PRODUCT_W{!add_product}};
    wire signed [PRODUCT_W-1:0] re_sum = re_product - common_product + BIAS;
    wire signed [PRODUCT_W-1:0] im_sum =
        im_product + signed_common + BIAS + $signed({{(PRODUCT_W-1){1'b0}}, !add_product});
    reg signed [OUT_W-1:0] re_rounded, im_rounded;

    always @(posedge clk) begin
        if (rst) begin
            phase <= 0;
            valid_pipe <= 0;
            out_valid <= 0;
        end else begin
            if (in_valid)
                phase <= phase + 1'b1;
            valid_pipe <= {valid_pipe[1:0], in_valid};
            out_valid <= valid_pipe[2];
        end

        re_pre <= in_re;
        im_pre <= in_im;
        diff_pre <= diff_or_sum;
        add_pre <= negative_phase;
        {plus_pre, minus_pre, sine_pre} <= coeff_word;
        quadrant_pre <= quadrant;
        re_product <= re_pre * plus_pre;
        im_product <= im_pre * minus_pre;
        common_product <= diff_pre * sine_pre;
        quadrant_product <= quadrant_pre;
        add_product <= add_pre;
        re_rounded <= re_sum[ROUND_SHIFT +: OUT_W];
        im_rounded <= im_sum[ROUND_SHIFT +: OUT_W];
        quadrant_sum <= quadrant_product;

        case (quadrant_sum)
            2'd0: begin out_re <= re_rounded;  out_im <= im_rounded;  end
            2'd1: begin out_re <= im_rounded;  out_im <= -re_rounded; end
            2'd2: begin out_re <= -re_rounded; out_im <= -im_rounded; end
            2'd3: begin out_re <= -im_rounded; out_im <= re_rounded;  end
        endcase
    end
endmodule
