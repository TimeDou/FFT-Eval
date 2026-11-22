// ---------------------------------------------------------------------------
// Twiddle-factor generation for W64^j = exp(-j*2*pi*j/64), j in 0..63.
// Uses the 1/8-wave symmetry: only table entries j = 0..8 are stored.
//   jj = j mod 16, q = j div 16
//   jj <= 8 : base = t[jj]
//   jj >  8 : base = (-j) * conj(t[16-jj]) = (-t.im, -t.re)
//   result  = base * (-j)^q
// ---------------------------------------------------------------------------
module twiddle_gen #(
    parameter integer TWB = 14
) (
    input  wire [5:0]            j,
    output wire signed [TWB-1:0] wr,
    output wire signed [TWB-1:0] wi
);
    reg signed [TWB-1:0] tre, tim;
    wire [3:0] jj = j[3:0];
    wire [1:0] qd = j[5:4];
    wire       mir = (jj > 4'd8);
    wire [4:0] tref = mir ? (5'd16 - {1'b0, jj}) : {1'b0, jj};

    always @* begin
        case (tref)
            5'd0: begin tre = 14'sd4096;  tim = 14'sd0;     end
            5'd1: begin tre = 14'sd4076;  tim = -14'sd401;  end
            5'd2: begin tre = 14'sd4017;  tim = -14'sd799;  end
            5'd3: begin tre = 14'sd3920;  tim = -14'sd1189; end
            5'd4: begin tre = 14'sd3784;  tim = -14'sd1567; end
            5'd5: begin tre = 14'sd3612;  tim = -14'sd1931; end
            5'd6: begin tre = 14'sd3406;  tim = -14'sd2276; end
            5'd7: begin tre = 14'sd3166;  tim = -14'sd2598; end
            5'd8: begin tre = 14'sd2896;  tim = -14'sd2896; end
            default: begin tre = 14'sd0; tim = 14'sd0; end
        endcase
    end

    wire signed [TWB-1:0] b_re = mir ? -tim : tre;
    wire signed [TWB-1:0] b_im = mir ? -tre : tim;

    assign wr = (qd == 2'd0) ? b_re :
                (qd == 2'd1) ? b_im :
                (qd == 2'd2) ? -b_re : -b_im;
    assign wi = (qd == 2'd0) ? b_im :
                (qd == 2'd1) ? -b_re :
                (qd == 2'd2) ? -b_im : b_re;
endmodule
