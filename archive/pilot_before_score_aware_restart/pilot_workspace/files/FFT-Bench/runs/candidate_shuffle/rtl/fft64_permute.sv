module fft64_permute #(
    parameter integer HIGH_BIT = 5,
    parameter integer LOW_BIT = 0
) (
    input  wire clk,
    input  wire rst,
    input  wire in_valid,
    input  wire [29:0] in_data,
    output reg  out_valid,
    output reg  [29:0] out_data
);
    localparam integer DELTA = (1 << HIGH_BIT) - (1 << LOW_BIT);

    reg [29:0] delay_data [0:2*DELTA-1];
    reg [DELTA-1:0] delay_valid;
    reg [HIGH_BIT:0] index;

    // The output for position k is due DELTA+k cycles after frame start.
    // Swapping the two bits changes the source index by -DELTA, 0 or
    // +DELTA. Read the corresponding tap when that position is due.
    integer tap;
    always @(posedge clk) begin
        delay_data[0] <= in_data;
        for (tap = 1; tap < 2*DELTA; tap = tap + 1)
            delay_data[tap] <= delay_data[tap-1];

        if (index[HIGH_BIT] == index[LOW_BIT])
            out_data <= delay_data[DELTA-1];
        else if (index[HIGH_BIT])
            out_data <= delay_data[2*DELTA-1];
        else
            out_data <= in_data;
    end

    always @(posedge clk) begin
        if (rst) begin
            index <= 0;
            delay_valid <= 0;
            out_valid <= 1'b0;
        end else begin
            delay_valid <= {delay_valid[DELTA-2:0], in_valid};
            out_valid <= delay_valid[DELTA-1];
            if (delay_valid[DELTA-1]) index <= index + 1'b1;
        end
    end
endmodule
