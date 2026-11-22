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
