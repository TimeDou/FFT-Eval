module fft64_reorder (
    input  wire clk,
    input  wire rst,
    input  wire in_valid,
    input  wire frame_start,
    input  wire signed [14:0] in_re,
    input  wire signed [14:0] in_im,
    output wire out_valid,
    output wire signed [14:0] out_re,
    output wire signed [14:0] out_im
);
    reg [5:0] input_index;
    wire accept = in_valid && (frame_start || (input_index != 6'd0));
    always @(posedge clk) begin
        if (rst) input_index <= 6'd0;
        else if (accept) input_index <= input_index + 6'd1;
    end

    // Three independent index-bit swaps implement six-bit reversal.
    wire valid_outer, valid_middle;
    wire [29:0] data_outer, data_middle;
    fft64_permute #(.HIGH_BIT(5), .LOW_BIT(0)) swap_outer (
        .clk(clk), .rst(rst), .in_valid(accept), .in_data({in_re, in_im}),
        .out_valid(valid_outer), .out_data(data_outer)
    );
    fft64_permute #(.HIGH_BIT(4), .LOW_BIT(1)) swap_middle (
        .clk(clk), .rst(rst), .in_valid(valid_outer), .in_data(data_outer),
        .out_valid(valid_middle), .out_data(data_middle)
    );
    fft64_permute #(.HIGH_BIT(3), .LOW_BIT(2)) swap_inner (
        .clk(clk), .rst(rst), .in_valid(valid_middle), .in_data(data_middle),
        .out_valid(out_valid), .out_data({out_re, out_im})
    );
endmodule
