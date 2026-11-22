// ---------------------------------------------------------------------------
// fft64_top : 64-point forward, unscaled, fixed-point complex FFT.
//
// Architecture : folded, memory-based, in-place radix-4 decimation-in-time.
//                One radix-4 butterfly engine with three time-shared complex
//                multipliers drives the 48 radix-4 butterflies of the
//                transform (3 stages x 16 butterflies).
//   * input  : natural order, written into the array at base-4 digit-reversed
//              addresses (permutation is free on the write address).
//   * output : natural frequency order, read out sequentially.
//   * data   : 22-bit signed Q15; all butterfly additions are exact because
//              |X| <= 32, only twiddle products are rounded.
//   * twiddle: 14-bit signed Q12, 1/8-wave symmetric table.
//
// Schedule : 64 load cycles + 49*4 compute cycles + 64 output cycles.
// ---------------------------------------------------------------------------
`timescale 1ns/1ps
module fft64_top (
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

    localparam [1:0] ST_IDLE = 2'd0, ST_LOAD = 2'd1, ST_COMP = 2'd2, ST_OUT = 2'd3;
    localparam [2:0] SLOT_LAST = 3'd3;

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

    // ---- one-butterfly-ahead address / twiddle precompute -------------------
    // Registers break the bc -> address -> memory-mux -> multiplier path.
    wire [5:0] nbc   = bc + 6'd1;
    wire [1:0] nbs   = (nbc[5:4] > 2'd2) ? 2'd2 : nbc[5:4];
    wire [3:0] nbi   = nbc[3:0];
    wire [5:0] nbase = (nbs == 2'd0) ? {nbi, 2'b00} :
                       (nbs == 2'd1) ? {nbi[3:2], 2'b00, nbi[1:0]} : {2'b00, nbi};
    wire [5:0] nm    = (nbs == 2'd0) ? 6'd1 : ((nbs == 2'd1) ? 6'd4 : 6'd16);
    wire [5:0] nkw   = (nbs == 2'd0) ? 6'd0 :
                       (nbs == 2'd1) ? {nbi[1:0], 2'b00} : {2'b00, nbi};

    reg [5:0] a0_r, a1_r, a2_r, a3_r;
    wire [5:0] nkw2 = {nkw[4:0], 1'b0};
    wire [5:0] nkw3 = nkw + {nkw[4:0], 1'b0};
    wire signed [TWB-1:0] nw1r, nw1i, nw2r, nw2i, nw3r, nw3i;
    reg  signed [TWB-1:0] w1r_r, w1i_r, w2r_r, w2i_r, w3r_r, w3i_r;

    // ---------------- pipeline registers ------------------------------------
    reg signed [DW-1:0] x0_re, x0_im, x1_re, x1_im, x2_re, x2_im, x3_re, x3_im;
    reg signed [DW-1:0] y0_re, y0_im, y1_re, y1_im, y2_re, y2_im, y3_re, y3_im;
    reg signed [DW-1:0] p1_re, p1_im, p2_re, p2_im, p3_re, p3_im;
    reg [5:0] pbase, pstep;

    wire mult_en = (st == ST_COMP) && (slot == 3'd2);

    // three complex multipliers, one per twiddle bank
    wire signed [TWB-1:0] w1r, w1i, w2r, w2i, w3r, w3i;
    wire signed [DW-1:0]  m1r, m1i, m2r, m2i, m3r, m3i;

    twiddle_gen #(.TWB(TWB)) u_tw1 (.j(nkw),  .wr(nw1r), .wi(nw1i));
    twiddle_gen #(.TWB(TWB)) u_tw2 (.j(nkw2), .wr(nw2r), .wi(nw2i));
    twiddle_gen #(.TWB(TWB)) u_tw3 (.j(nkw3), .wr(nw3r), .wi(nw3i));
    assign w1r = w1r_r; assign w1i = w1i_r;
    assign w2r = w2r_r; assign w2i = w2i_r;
    assign w3r = w3r_r; assign w3i = w3i_r;

    cmul3 #(.DW(DW), .TWB(TWB), .TWF(TWF)) u_m1 (.ar(x1_re), .ai(x1_im), .wr(w1r), .wi(w1i), .pr(m1r), .pi(m1i));
    cmul3 #(.DW(DW), .TWB(TWB), .TWF(TWF)) u_m2 (.ar(x2_re), .ai(x2_im), .wr(w2r), .wi(w2i), .pr(m2r), .pi(m2i));
    cmul3 #(.DW(DW), .TWB(TWB), .TWF(TWF)) u_m3 (.ar(x3_re), .ai(x3_im), .wr(w3r), .wi(w3i), .pr(m3r), .pi(m3i));

    always @(posedge clk) begin
        if (mult_en) begin
            p1_re <= m1r; p1_im <= m1i;
            p2_re <= m2r; p2_im <= m2i;
            p3_re <= m3r; p3_im <= m3i;
        end
    end

    // ---------------- butterfly datapath ------------------------------------
    wire signed [DW-1:0] t0_re = x0_re + p2_re;
    wire signed [DW-1:0] t0_im = x0_im + p2_im;
    wire signed [DW-1:0] t1_re = x0_re - p2_re;
    wire signed [DW-1:0] t1_im = x0_im - p2_im;
    wire signed [DW-1:0] t2_re = p1_re + p3_re;
    wire signed [DW-1:0] t2_im = p1_im + p3_im;
    wire signed [DW-1:0] t3_re = p1_re - p3_re;
    wire signed [DW-1:0] t3_im = p1_im - p3_im;

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
                 (st == ST_COMP) ? ((slot == 3'd1) ? a2_r : a0_r) : load_addr;
    assign ra1 = (st == ST_COMP) ? ((slot == 3'd1) ? a3_r : a1_r) : load_addr;

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
                            a0_r <= 6'd0; a1_r <= 6'd1; a2_r <= 6'd2; a3_r <= 6'd3;
                            w1r_r <= 14'sd4096; w1i_r <= 14'sd0;
                            w2r_r <= 14'sd4096; w2i_r <= 14'sd0;
                            w3r_r <= 14'sd4096; w3i_r <= 14'sd0;
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
                    if (slot == SLOT_LAST) begin
                        y0_re <= ny0_re; y0_im <= ny0_im;
                        y1_re <= ny1_re; y1_im <= ny1_im;
                        y2_re <= ny2_re; y2_im <= ny2_im;
                        y3_re <= ny3_re; y3_im <= ny3_im;
                        pbase <= cur_base;
                        pstep <= cur_m;
                        a0_r  <= nbase;
                        a1_r  <= nbase + nm;
                        a2_r  <= nbase + {nm[4:0], 1'b0};
                        a3_r  <= nbase + {nm[4:0], 1'b0} + nm;
                        w1r_r <= nw1r; w1i_r <= nw1i;
                        w2r_r <= nw2r; w2i_r <= nw2i;
                        w3r_r <= nw3r; w3i_r <= nw3i;
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
