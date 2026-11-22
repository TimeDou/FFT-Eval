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

    wire valid_a, valid_b, valid_c;
    wire signed [15:0] a_re, a_im, b_re, b_im, c_re, c_im;

    // Bit reversal is three disjoint swaps in the six-bit sample index.
    // Moving this permutation to the DIT input keeps all delays narrow.
    fft64_index_swap #(.W(16), .HI(5), .LO(0)) swap_50
        (clk, rst, accept_sample, in_re, in_im, valid_a, a_re, a_im);
    fft64_index_swap #(.W(16), .HI(4), .LO(1)) swap_41
        (clk, rst, valid_a, a_re, a_im, valid_b, b_re, b_im);
    fft64_index_swap #(.W(16), .HI(3), .LO(2)) swap_32
        (clk, rst, valid_b, b_re, b_im, valid_c, c_re, c_im);

    wire valid_d, valid_e, valid_f, valid_g, valid_h, valid_i, valid_j;
    wire signed [16:0] d_re, d_im;
    wire signed [17:0] e_re, e_im, f_re, f_im;
    wire signed [18:0] g_re, g_im;
    wire signed [19:0] h_re, h_im, i_re, i_im;
    wire signed [20:0] j_re, j_im;
    wire signed [21:0] bin_re, bin_im;

    // Radix-2 squared DIT is the transpose of the DIF factorization:
    // twiddle first, apply the quarter-turn to the odd difference, then
    // combine the two halves. The bit-reversed input becomes natural bins.
    fft64_sdf #(.W(16), .DELAY_LOG(0), .PAIR_FIRST(1)) bf_a
        (clk, rst, valid_c, c_re, c_im, valid_d, d_re, d_im);
    fft64_sdf #(.W(17), .DELAY_LOG(1)) bf_b
        (clk, rst, valid_d, d_re, d_im, valid_e, e_re, e_im);
    fft64_twiddle #(.W(18), .SPAN_LOG(4)) rotate_b
        (clk, rst, valid_e, e_re, e_im, valid_f, f_re, f_im);
    fft64_sdf #(.W(18), .DELAY_LOG(2), .PAIR_FIRST(1)) bf_c
        (clk, rst, valid_f, f_re, f_im, valid_g, g_re, g_im);
    fft64_sdf #(.W(19), .DELAY_LOG(3)) bf_d
        (clk, rst, valid_g, g_re, g_im, valid_h, h_re, h_im);
    fft64_twiddle #(.W(20), .SPAN_LOG(6)) rotate_d
        (clk, rst, valid_h, h_re, h_im, valid_i, i_re, i_im);
    fft64_sdf #(.W(20), .DELAY_LOG(4), .PAIR_FIRST(1)) bf_e
        (clk, rst, valid_i, i_re, i_im, valid_j, j_re, j_im);
    fft64_sdf #(.W(21), .DELAY_LOG(5)) bf_f
        (clk, rst, valid_j, j_re, j_im, out_valid, bin_re, bin_im);

    reg [5:0] output_index;
    always @(posedge clk) begin
        if (rst)
            output_index <= 0;
        else if (out_valid)
            output_index <= output_index + 1'b1;
    end
    assign out_start = out_valid && output_index == 0;
    assign out_re = {{2{bin_re[21]}}, bin_re};
    assign out_im = {{2{bin_im[21]}}, bin_im};
endmodule

module fft64_index_swap #(
    parameter integer W = 16,
    parameter integer HI = 5,
    parameter integer LO = 0
) (
    input  wire                clk,
    input  wire                rst,
    input  wire                in_valid,
    input  wire signed [W-1:0] in_re, in_im,
    output reg                 out_valid,
    output reg signed [W-1:0]  out_re, out_im
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
    always @(posedge clk) begin
        if (rst) begin
            index <= 0;
            delay_valid <= 0;
            out_valid <= 0;
        end else begin
            if (in_valid)
                index <= index + 1'b1;
            delay_valid <= {delay_valid[DELAY-2:0], in_valid};
            out_valid <= delay_valid[DELAY-1];
        end
        data_delay[0] <= exchange ? older : {in_re, in_im};
        {out_re, out_im} <= exchange ? {in_re, in_im} : older;
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
    parameter integer SPAN_LOG = 6
) (
    input  wire                clk,
    input  wire                rst,
    input  wire                in_valid,
    input  wire signed [W-1:0] in_re, in_im,
    output reg                 out_valid,
    output reg signed [W-1:0]  out_re, out_im
);
    localparam integer F = 12;
    localparam integer COEF_W = F + 2;
    localparam integer PRODUCT_W = W + COEF_W;
    localparam integer OFFSET_W = SPAN_LOG - 2;
    localparam signed [PRODUCT_W:0] BIAS = 1 << (F-1);

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

    // Rounded cos and sin of 2*pi*exponent/64 in Q12. The exponent is
    // determined solely by the stage and the position within the FFT block.
    function automatic [2*COEF_W-1:0] coefficients(input [5:0] k);
        case (k)
            6'd0: coefficients = {14'sd4096, 14'sd0};
            6'd1: coefficients = {14'sd4076, 14'sd401};
            6'd2: coefficients = {14'sd4017, 14'sd799};
            6'd3: coefficients = {14'sd3920, 14'sd1189};
            6'd4: coefficients = {14'sd3784, 14'sd1567};
            6'd5: coefficients = {14'sd3612, 14'sd1931};
            6'd6: coefficients = {14'sd3406, 14'sd2276};
            6'd7: coefficients = {14'sd3166, 14'sd2598};
            6'd8: coefficients = {14'sd2896, 14'sd2896};
            6'd9: coefficients = {14'sd2598, 14'sd3166};
            6'd10: coefficients = {14'sd2276, 14'sd3406};
            6'd11: coefficients = {14'sd1931, 14'sd3612};
            6'd12: coefficients = {14'sd1567, 14'sd3784};
            6'd13: coefficients = {14'sd1189, 14'sd3920};
            6'd14: coefficients = {14'sd799, 14'sd4017};
            6'd15: coefficients = {14'sd401, 14'sd4076};
            6'd16: coefficients = {14'sd0, 14'sd4096};
            6'd17: coefficients = {-14'sd401, 14'sd4076};
            6'd18: coefficients = {-14'sd799, 14'sd4017};
            6'd19: coefficients = {-14'sd1189, 14'sd3920};
            6'd20: coefficients = {-14'sd1567, 14'sd3784};
            6'd21: coefficients = {-14'sd1931, 14'sd3612};
            6'd22: coefficients = {-14'sd2276, 14'sd3406};
            6'd23: coefficients = {-14'sd2598, 14'sd3166};
            6'd24: coefficients = {-14'sd2896, 14'sd2896};
            6'd25: coefficients = {-14'sd3166, 14'sd2598};
            6'd26: coefficients = {-14'sd3406, 14'sd2276};
            6'd27: coefficients = {-14'sd3612, 14'sd1931};
            6'd28: coefficients = {-14'sd3784, 14'sd1567};
            6'd29: coefficients = {-14'sd3920, 14'sd1189};
            6'd30: coefficients = {-14'sd4017, 14'sd799};
            6'd31: coefficients = {-14'sd4076, 14'sd401};
            6'd32: coefficients = {-14'sd4096, 14'sd0};
            6'd33: coefficients = {-14'sd4076, -14'sd401};
            6'd34: coefficients = {-14'sd4017, -14'sd799};
            6'd35: coefficients = {-14'sd3920, -14'sd1189};
            6'd36: coefficients = {-14'sd3784, -14'sd1567};
            6'd37: coefficients = {-14'sd3612, -14'sd1931};
            6'd38: coefficients = {-14'sd3406, -14'sd2276};
            6'd39: coefficients = {-14'sd3166, -14'sd2598};
            6'd40: coefficients = {-14'sd2896, -14'sd2896};
            6'd41: coefficients = {-14'sd2598, -14'sd3166};
            6'd42: coefficients = {-14'sd2276, -14'sd3406};
            6'd43: coefficients = {-14'sd1931, -14'sd3612};
            6'd44: coefficients = {-14'sd1567, -14'sd3784};
            6'd45: coefficients = {-14'sd1189, -14'sd3920};
            default: coefficients = 0;
        endcase
    endfunction

    wire signed [COEF_W-1:0] cosine, sine;
    assign {cosine, sine} = coefficients(exponent);

    reg products_valid;
    reg signed [PRODUCT_W-1:0] re_cos, im_sin, im_cos, re_sin;
    wire signed [PRODUCT_W:0] rotated_re = re_cos + im_sin + BIAS;
    wire signed [PRODUCT_W:0] rotated_im = im_cos - re_sin + BIAS;
    always @(posedge clk) begin
        if (rst) begin
            phase <= 0;
            products_valid <= 0;
            out_valid <= 0;
        end else begin
            if (in_valid)
                phase <= phase + 1'b1;
            products_valid <= in_valid;
            out_valid <= products_valid;
        end
        re_cos <= in_re * cosine;
        im_sin <= in_im * sine;
        im_cos <= in_im * cosine;
        re_sin <= in_re * sine;
        out_re <= rotated_re[F +: W];
        out_im <= rotated_im[F +: W];
    end
endmodule

