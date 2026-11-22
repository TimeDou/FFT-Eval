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
