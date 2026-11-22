module fft64_twiddle #(
    parameter integer WIDTH = 18,
    parameter integer LOG_SPAN = 4
) (
    input  wire clk,
    input  wire rst,
    input  wire in_valid,
    input  wire signed [WIDTH-1:0] in_re,
    input  wire signed [WIDTH-1:0] in_im,
    output reg  out_valid,
    output reg  signed [WIDTH-1:0] out_re,
    output reg  signed [WIDTH-1:0] out_im
);
    localparam integer FRACTION = 12;
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

    // The first quadrant of sin(2*pi*k/64), rounded to 12 fraction bits.
    function automatic signed [COEFF_WIDTH-1:0] sine(input [5:0] angle);
        reg [4:0] index;
        reg [12:0] magnitude;
        begin
            index = angle[4] ? (5'd16 - {1'b0, angle[3:0]})
                             : {1'b0, angle[3:0]};
            case (index)
                5'd0:  magnitude = 13'd0;
                5'd1:  magnitude = 13'd401;
                5'd2:  magnitude = 13'd799;
                5'd3:  magnitude = 13'd1189;
                5'd4:  magnitude = 13'd1567;
                5'd5:  magnitude = 13'd1931;
                5'd6:  magnitude = 13'd2276;
                5'd7:  magnitude = 13'd2598;
                5'd8:  magnitude = 13'd2896;
                5'd9:  magnitude = 13'd3166;
                5'd10: magnitude = 13'd3406;
                5'd11: magnitude = 13'd3612;
                5'd12: magnitude = 13'd3784;
                5'd13: magnitude = 13'd3920;
                5'd14: magnitude = 13'd4017;
                5'd15: magnitude = 13'd4076;
                5'd16: magnitude = 13'd4096;
                default: magnitude = 13'd0;
            endcase
            sine = angle[5] ? -$signed({1'b0, magnitude}) : $signed({1'b0, magnitude});
        end
    endfunction

    function automatic signed [WIDTH-1:0] round_even(input signed [PRODUCT_WIDTH:0] x);
        reg increment;
        begin
            increment = x[FRACTION-1] && ((|x[FRACTION-2:0]) || x[FRACTION]);
            round_even = x[FRACTION +: WIDTH] + {{(WIDTH-1){1'b0}}, increment};
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
