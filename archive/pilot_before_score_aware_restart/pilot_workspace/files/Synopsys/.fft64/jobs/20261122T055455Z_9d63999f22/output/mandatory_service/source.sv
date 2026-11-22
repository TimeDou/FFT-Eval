// 3-multiplier (Karatsuba-style) complex multiplier with fixed-point rounding.
//   (pr + j pi) = (ar + j ai) * (wr + j wi)
//   t1 = (ar+ai)*wr ; t2 = ar*(wi-wr) ; t3 = ai*(wr+wi)
//   pr = t1 - t3    ; pi = t1 + t2
// Products carry DW+TWF fractional bits; result is rounded back to Q(DW-1-TWF...)
// i.e. arithmetic shift right by TWF with round-half-up.
module cmul3 #(
    parameter integer DW  = 22,   // data width (signed)
    parameter integer TWB = 14,   // twiddle width (signed)
    parameter integer TWF = 12    // twiddle fractional bits (shift amount)
) (
    input  wire signed [DW-1:0]  ar,
    input  wire signed [DW-1:0]  ai,
    input  wire signed [TWB-1:0] wr,
    input  wire signed [TWB-1:0] wi,
    output wire signed [DW-1:0]  pr,
    output wire signed [DW-1:0]  pi
);
    wire signed [DW:0]   s1 = ar + ai;
    wire signed [TWB:0]  d2 = wi - wr;
    wire signed [TWB:0]  s3 = wr + wi;

    wire signed [DW+TWB:0] t1 = s1 * wr;
    wire signed [DW+TWB:0] t2 = ar * d2;
    wire signed [DW+TWB:0] t3 = ai * s3;

    wire signed [DW+TWB:0] prf = t1 - t3;
    wire signed [DW+TWB:0] pif = t1 + t2;

    wire signed [DW+TWB:0] rnd = {{(DW+TWB-1){1'b0}}, 1'b1} <<< (TWF-1);

    wire signed [DW+TWB:0] prr = (prf + rnd) >>> TWF;
    wire signed [DW+TWB:0] pir = (pif + rnd) >>> TWF;

    assign pr = prr[DW-1:0];
    assign pi = pir[DW-1:0];
endmodule

// ---------------------------------------------------------------------------
// fft64_top : 64-point forward, unscaled, fixed-point complex FFT.
//
// Architecture : folded, memory-based, in-place radix-4 decimation-in-time.
//                One radix-4 butterfly engine + NMULT complex multipliers
//                time-shared over the 48 radix-4 butterflies of the transform.
//   * input  : natural order, written into the array at base-4 digit-reversed
//              addresses (free permutation on the write address).
//   * output : natural frequency order, read out sequentially.
//   * data   : 22-bit signed, 15 fractional bits, additions are exact
//              (|X| <= 32 needs 22 bits), only twiddle products are rounded.
//   * twiddle: 14-bit signed Q12, 1/8-wave symmetric table.
//
// Timing : 64 load cycles + 49*(3+MC) compute cycles + 64 output cycles,
//          where MC = ceil(3/NMULT) is the number of multiplier phases.
// ---------------------------------------------------------------------------
`timescale 1ns/1ps
module fft64_top #(
    parameter integer NMULT = 3
) (
    input  wire                  clk,
    input  wire                  rst,
    input  wire                  in_valid,
    input  wire                  frame_start,
    input  wire signed [15:0]    in_re,
    input  wire signed [15:0]    in_im,
    output wire                  out_valid,
    output wire                  out_start,
    output wire signed [23:0]    out_re,
    output wire signed [23:0]    out_im
);
    localparam integer DW  = 22;   // internal data width (signed, Q15)
    localparam integer TWB = 14;   // twiddle width (signed Q12)
    localparam integer TWF = 12;   // twiddle fractional bits
    localparam integer MC  = (NMULT >= 3) ? 1 : ((NMULT == 2) ? 2 : 3);
    localparam integer SLOTS = 3 + MC;      // slots per butterfly
    localparam integer LASTSLOT = SLOTS - 1;

    localparam [1:0] ST_IDLE = 2'd0, ST_LOAD = 2'd1, ST_COMP = 2'd2, ST_OUT = 2'd3;

    reg [1:0]  st;
    reg [5:0]  lc;      // load counter
    reg [5:0]  bc;      // butterfly counter 0..48
    reg [2:0]  slot;    // slot within butterfly
    reg [5:0]  oc;      // output counter

    // ---------------- memory (64 entries x 2 x 22 bit, 2R2W) ----------------
    reg signed [DW-1:0] mem_re [0:63];
    reg signed [DW-1:0] mem_im [0:63];

    wire [5:0] ra0, ra1, wa0, wa1;
    wire       we0, we1;
    wire signed [DW-1:0] wd0_re, wd0_im, wd1_re, wd1_im;

    wire signed [DW-1:0] rd0_re = mem_re[ra0];
    wire signed [DW-1:0] rd0_im = mem_im[ra0];
    wire signed [DW-1:0] rd1_re = mem_re[ra1];
    wire signed [DW-1:0] rd1_im = mem_im[ra1];

    always @(posedge clk) begin
        if (we0) begin mem_re[wa0] <= wd0_re; mem_im[wa0] <= wd0_im; end
        if (we1) begin mem_re[wa1] <= wd1_re; mem_im[wa1] <= wd1_im; end
    end

    // ---------------- address / twiddle generation -------------------------
    wire [1:0] bs = (bc[5:4] > 2'd2) ? 2'd2 : bc[5:4];
    wire [3:0] bi = bc[3:0];

    wire [5:0] cur_base = (bs == 2'd0) ? {bi, 2'b00} :
                          (bs == 2'd1) ? {bi[3:2], 2'b00, bi[1:0]} :
                                         {2'b00, bi};
    wire [5:0] cur_m    = (bs == 2'd0) ? 6'd1 : ((bs == 2'd1) ? 6'd4 : 6'd16);
    wire [5:0] cur_m2   = {cur_m[4:0], 1'b0};
    wire [5:0] cur_m3   = cur_m + cur_m2;

    wire [5:0] kw = (bs == 2'd0) ? 6'd0 :
                    (bs == 2'd1) ? {bi[1:0], 2'b00} : {2'b00, bi};
    wire [5:0] j1 = kw;
    wire [5:0] j2 = {kw[4:0], 1'b0};
    wire [5:0] j3 = kw + {kw[4:0], 1'b0};

    // ---------------- pipeline registers ------------------------------------
    reg signed [DW-1:0] x0_re, x0_im, x1_re, x1_im, x2_re, x2_im, x3_re, x3_im;
    reg signed [DW-1:0] y0_re, y0_im, y1_re, y1_im, y2_re, y2_im, y3_re, y3_im;
    reg signed [DW-1:0] p1r_reg, p1i_reg, p2r_reg, p2i_reg, p3r_reg, p3i_reg;
    reg [5:0] pbase, pstep;

    wire mult_en = (st == ST_COMP) && (slot >= 3'd2) && (slot <= (3'd1 + MC[2:0]));
    wire [2:0] phase_m = slot - 3'd1;

    // multiplier array
    genvar gi;
    generate
        for (gi = 0; gi < NMULT; gi = gi + 1) begin : g_mul
            wire [2:0] q = ((phase_m - 3'd1) * NMULT) + gi;
            wire qv = mult_en && (q <= 3'd2);
            wire signed [DW-1:0] opr_re = (q == 3'd0) ? x1_re : ((q == 3'd1) ? x2_re : x3_re);
            wire signed [DW-1:0] opr_im = (q == 3'd0) ? x1_im : ((q == 3'd1) ? x2_im : x3_im);
            wire [5:0] jsel = (q == 3'd0) ? j1 : ((q == 3'd1) ? j2 : j3);
            wire signed [TWB-1:0] twr, twi;
            wire signed [DW-1:0]  mre, mim;

            twiddle_gen #(.TWB(TWB)) u_tw (.j(jsel), .wr(twr), .wi(twi));
            cmul3 #(.DW(DW), .TWB(TWB), .TWF(TWF)) u_mul (
                .ar(opr_re), .ai(opr_im), .wr(twr), .wi(twi), .pr(mre), .pi(mim));

            // No reset: every product register is written before it is used.
            always @(posedge clk) begin
                if (qv) begin
                    if (q == 3'd0) begin p1r_reg <= mre; p1i_reg <= mim; end
                    if (q == 3'd1) begin p2r_reg <= mre; p2i_reg <= mim; end
                    if (q == 3'd2) begin p3r_reg <= mre; p3i_reg <= mim; end
                end
            end
        end
    endgenerate

    // ---------------- butterfly datapath ------------------------------------
    wire signed [DW-1:0] t0_re = x0_re + p2r_reg;
    wire signed [DW-1:0] t0_im = x0_im + p2i_reg;
    wire signed [DW-1:0] t1_re = x0_re - p2r_reg;
    wire signed [DW-1:0] t1_im = x0_im - p2i_reg;
    wire signed [DW-1:0] t2_re = p1r_reg + p3r_reg;
    wire signed [DW-1:0] t2_im = p1i_reg + p3i_reg;
    wire signed [DW-1:0] t3_re = p1r_reg - p3r_reg;
    wire signed [DW-1:0] t3_im = p1i_reg - p3i_reg;

    wire signed [DW-1:0] ny0_re = t0_re + t2_re;
    wire signed [DW-1:0] ny0_im = t0_im + t2_im;
    wire signed [DW-1:0] ny2_re = t0_re - t2_re;
    wire signed [DW-1:0] ny2_im = t0_im - t2_im;
    wire signed [DW-1:0] ny1_re = t1_re + t3_im;
    wire signed [DW-1:0] ny1_im = t1_im - t3_re;
    wire signed [DW-1:0] ny3_re = t1_re - t3_im;
    wire signed [DW-1:0] ny3_im = t1_im + t3_re;

    // ---------------- read / write port muxing ------------------------------
    wire [5:0] load_addr = {lc[1:0], lc[3:2], lc[5:4]};   // base-4 digit reversal

    assign ra0 = (st == ST_OUT)  ? oc :
                 (st == ST_COMP) ? ((slot == 3'd1) ? (cur_base + cur_m2) : cur_base) :
                                   load_addr;
    assign ra1 = (st == ST_COMP) ? ((slot == 3'd1) ? (cur_base + cur_m3) : (cur_base + cur_m))
                                 : load_addr;

    assign we0 = ((st == ST_IDLE) && in_valid && frame_start) ||
                 ((st == ST_LOAD) && in_valid) ||
                 ((st == ST_COMP) && (slot <= 3'd1) && (bc != 6'd0));
    assign we1 = ((st == ST_COMP) && (slot <= 3'd1) && (bc != 6'd0));

    wire signed [DW-1:0] in_re_ext = {{(DW-16){in_re[15]}}, in_re};
    wire signed [DW-1:0] in_im_ext = {{(DW-16){in_im[15]}}, in_im};

    assign wa0 = (st == ST_COMP) ? ((slot == 3'd0) ? pbase : (pbase + {pstep[4:0],1'b0}))
                                 : load_addr;
    assign wa1 = (st == ST_COMP) ? ((slot == 3'd0) ? (pbase + pstep)
                                                   : (pbase + {pstep[4:0],1'b0} + pstep))
                                 : load_addr;
    assign wd0_re = (st == ST_COMP) ? ((slot == 3'd0) ? y0_re : y2_re) : in_re_ext;
    assign wd0_im = (st == ST_COMP) ? ((slot == 3'd0) ? y0_im : y2_im) : in_im_ext;
    assign wd1_re = (st == ST_COMP) ? ((slot == 3'd0) ? y1_re : y3_re) : in_re_ext;
    assign wd1_im = (st == ST_COMP) ? ((slot == 3'd0) ? y1_im : y3_im) : in_im_ext;

    // ---------------- control ------------------------------------------------
    always @(posedge clk) begin
        if (rst) begin
            st    <= ST_IDLE;
            lc    <= 6'd0;
            bc    <= 6'd0;
            slot  <= 3'd0;
            oc    <= 6'd0;
        end else begin
            case (st)
                ST_IDLE: begin
                    if (in_valid && frame_start) begin
                        lc <= 6'd1;
                        st <= ST_LOAD;
                    end
                end
                ST_LOAD: begin
                    if (in_valid) begin
                        if (lc == 6'd63) begin
                            st   <= ST_COMP;
                            bc   <= 6'd0;
                            slot <= 3'd0;
                        end else begin
                            lc <= lc + 6'd1;
                        end
                    end
                end
                ST_COMP: begin
                    if (slot == 3'd0) begin
                        x0_re <= rd0_re; x0_im <= rd0_im;
                        x1_re <= rd1_re; x1_im <= rd1_im;
                    end
                    if (slot == 3'd1) begin
                        x2_re <= rd0_re; x2_im <= rd0_im;
                        x3_re <= rd1_re; x3_im <= rd1_im;
                    end
                    if (slot == LASTSLOT[2:0]) begin
                        y0_re <= ny0_re; y0_im <= ny0_im;
                        y1_re <= ny1_re; y1_im <= ny1_im;
                        y2_re <= ny2_re; y2_im <= ny2_im;
                        y3_re <= ny3_re; y3_im <= ny3_im;
                        pbase <= cur_base;
                        pstep <= cur_m;
                        if (bc == 6'd48) begin
                            st <= ST_OUT;
                            oc <= 6'd0;
                        end else begin
                            bc   <= bc + 6'd1;
                            slot <= 3'd0;
                        end
                    end else begin
                        slot <= slot + 3'd1;
                    end
                end
                ST_OUT: begin
                    if (oc == 6'd63) begin
                        st <= ST_IDLE;
                        lc <= 6'd0;
                        oc <= 6'd0;
                    end else begin
                        oc <= oc + 6'd1;
                    end
                end
                default: st <= ST_IDLE;
            endcase
        end
    end

    // ---------------- outputs -------------------------------------------------
    assign out_valid = (st == ST_OUT);
    assign out_start = (st == ST_OUT) && (oc == 6'd0);
    assign out_re    = {{(24-DW){rd0_re[DW-1]}}, rd0_re};
    assign out_im    = {{(24-DW){rd0_im[DW-1]}}, rd0_im};

endmodule

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
