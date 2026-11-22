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

    reg [27:0] samples [0:49];
    reg [5:0] write_index, read_index, read_delay;
    reg [3:0] write_frame, read_frame;

    function automatic [5:0] reverse6(input [5:0] index);
        reverse6 = {index[0], index[1], index[2], index[3], index[4], index[5]};
    endfunction

    // At II=64, every write from cycle 50 onward reuses the slot read
    // on the same edge. The first 50 writes of the next frame therefore
    // permute those 50 slots. This table assigns frame-zero addresses
    // in groups arranged along the cycles of that permutation.
    function automatic [5:0] base_address(input [5:0] index);
        case (index)
            6'd0, 6'd50:             base_address = 6'd0;
            6'd28:                   base_address = 6'd1;
            6'd21:                   base_address = 6'd2;
            6'd49:                   base_address = 6'd3;
            6'd44, 6'd63:            base_address = 6'd4;
            6'd23:                   base_address = 6'd5;
            6'd41:                   base_address = 6'd6;
            6'd36, 6'd59:            base_address = 6'd7;
            6'd19:                   base_address = 6'd8;
            6'd33:                   base_address = 6'd9;
            6'd16, 6'd52, 6'd61:     base_address = 6'd10;
            6'd30:                   base_address = 6'd11;
            6'd13:                   base_address = 6'd12;
            6'd8, 6'd54:             base_address = 6'd13;
            6'd26:                   base_address = 6'd14;
            6'd5:                    base_address = 6'd15;
            6'd1:                    base_address = 6'd16;
            6'd20, 6'd60:            base_address = 6'd17;
            6'd17:                   base_address = 6'd18;
            6'd12, 6'd62:            base_address = 6'd19;
            6'd22:                   base_address = 6'd20;
            6'd9:                    base_address = 6'd21;
            6'd4, 6'd58:             base_address = 6'd22;
            6'd18:                   base_address = 6'd23;
            6'd27:                   base_address = 6'd24;
            6'd37:                   base_address = 6'd25;
            6'd32, 6'd51:            base_address = 6'd26;
            6'd29:                   base_address = 6'd27;
            6'd48, 6'd53:            base_address = 6'd28;
            6'd31:                   base_address = 6'd29;
            6'd45:                   base_address = 6'd30;
            6'd40, 6'd55:            base_address = 6'd31;
            6'd3:                    base_address = 6'd32;
            6'd34:                   base_address = 6'd33;
            6'd6:                    base_address = 6'd34;
            6'd10:                   base_address = 6'd35;
            6'd7:                    base_address = 6'd36;
            6'd42:                   base_address = 6'd37;
            6'd11:                   base_address = 6'd38;
            6'd38:                   base_address = 6'd39;
            6'd15:                   base_address = 6'd40;
            6'd46:                   base_address = 6'd41;
            6'd24, 6'd56, 6'd57:     base_address = 6'd42;
            6'd25:                   base_address = 6'd43;
            6'd39:                   base_address = 6'd44;
            6'd43:                   base_address = 6'd45;
            6'd2:                    base_address = 6'd46;
            6'd14:                   base_address = 6'd47;
            6'd35:                   base_address = 6'd48;
            6'd47:                   base_address = 6'd49;
            default: base_address = 6'd0;
        endcase
    endfunction

    function automatic [5:0] address(input [5:0] index, input [3:0] frame);
        reg [5:0] base;
        reg [3:0] position;
        begin
            base = base_address(index);
            position = base[3:0] + frame;
            // The groups have lengths 16, 8, 8, seven 2s and four 1s.
            // Only the bits belonging to a group's position wrap.
            address = {base[5:4],
                       (base < 6'd16) ? position[3]   : base[3],
                       (base < 6'd32) ? position[2:1] : base[2:1],
                       (base < 6'd46) ? position[0]   : base[0]};
        end
    endfunction

    wire start_write = in_valid && frame_start && (write_index == 6'd0);
    wire writing = in_valid && (start_write || (write_index != 6'd0));
    wire reading = (read_delay == 6'd1) || (read_index != 6'd0);
    wire [5:0] write_address = address(write_index, write_frame);
    wire [5:0] read_address = address(reverse6(read_index), read_frame);

    // A longer input gap moves the later frame's writes away from the
    // earlier reads. The same allocation works at every legal II.
    always @(posedge clk) begin
        if (rst) begin
            write_index <= 6'd0;
            read_index <= 6'd0;
            read_delay <= 6'd0;
            write_frame <= 4'd0;
            read_frame <= 4'd0;
            out_valid <= 1'b0;
        end else begin
            if (writing) begin
                write_index <= write_index + 6'd1;
                if (write_index == 6'd63) write_frame <= write_frame + 4'd1;
            end
            if (reading) begin
                read_index <= read_index + 6'd1;
                if (read_index == 6'd63) read_frame <= read_frame + 4'd1;
            end
            if (start_write) read_delay <= READ_DELAY;
            else if (read_delay != 6'd0) read_delay <= read_delay - 6'd1;
            out_valid <= reading;
        end
        if (writing) samples[write_address] <= {in_re, in_im};
        {out_re, out_im} <= samples[read_address];
    end
endmodule
