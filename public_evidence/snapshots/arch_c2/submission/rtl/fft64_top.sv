// fft64_top : streaming radix-2 single-path delay-feedback (R2SDF) 64-point
// forward unscaled complex FFT (DIF), natural-order input and output.
// Signed fixed point, 15 fractional bits externally; per-stage width growth.
// Generated file.
`default_nettype none
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
  localparam integer LAST = 132;
  localparam integer COFF = 133;

  reg  [7:0] sc;
  reg        busy;
  wire       start = in_valid & frame_start;
  wire [7:0] sc_nxt = start ? 8'd1 : (busy ? ((sc==LAST[7:0]) ? 8'd0 : sc+8'd1) : 8'd0);

  always @(posedge clk) begin
    if (rst) begin busy <= 1'b0; sc <= 8'd0; end
    else if (start) begin busy <= 1'b1; sc <= 8'd1; end
    else if (busy) begin
      if (sc == LAST[7:0]) begin busy <= 1'b0; sc <= 8'd0; end
      else sc <= sc + 8'd1;
    end
  end

  reg [7:0] cp1,cp2,cp3,cp4,cp5,cp6;
  always @(posedge clk) begin
    cp1 <= sc; cp2 <= cp1; cp3 <= cp2; cp4 <= cp3; cp5 <= cp4; cp6 <= cp5;
  end
  wire signed [15:0] din_re = in_valid ? in_re : 16'sd0;
  wire signed [15:0] din_im = in_valid ? in_im : 16'sd0;

  // ---------------- stage 1: M=32 W=16 ----------------
  reg  signed [16:0] dly1_re [0:31];
  reg  signed [16:0] dly1_im [0:31];
  wire signed [16:0] do1_re = dly1_re[31];
  wire signed [16:0] do1_im = dly1_im[31];
  wire ph1 = sc[5];
  wire [4:0] ix1 = sc[4:0];
  wire [4:0] px1 = sc_nxt[4:0];
  wire signed [11:0] pc1_c0_re = 12'sd1024;
  wire signed [11:0] pc1_c0_im = 12'sd0;
  wire signed [11:0] pc1_c1_re = 12'sd1019;
  wire signed [11:0] pc1_c1_im = -12'sd100;
  wire signed [11:0] pc1_c2_re = 12'sd1004;
  wire signed [11:0] pc1_c2_im = -12'sd200;
  wire signed [11:0] pc1_c3_re = 12'sd980;
  wire signed [11:0] pc1_c3_im = -12'sd297;
  wire signed [11:0] pc1_c4_re = 12'sd946;
  wire signed [11:0] pc1_c4_im = -12'sd392;
  wire signed [11:0] pc1_c5_re = 12'sd903;
  wire signed [11:0] pc1_c5_im = -12'sd483;
  wire signed [11:0] pc1_c6_re = 12'sd851;
  wire signed [11:0] pc1_c6_im = -12'sd569;
  wire signed [11:0] pc1_c7_re = 12'sd792;
  wire signed [11:0] pc1_c7_im = -12'sd650;
  wire signed [11:0] pc1_c8_re = 12'sd724;
  wire signed [11:0] pc1_c8_im = -12'sd724;
  wire signed [11:0] pc1_c9_re = 12'sd650;
  wire signed [11:0] pc1_c9_im = -12'sd792;
  wire signed [11:0] pc1_c10_re = 12'sd569;
  wire signed [11:0] pc1_c10_im = -12'sd851;
  wire signed [11:0] pc1_c11_re = 12'sd483;
  wire signed [11:0] pc1_c11_im = -12'sd903;
  wire signed [11:0] pc1_c12_re = 12'sd392;
  wire signed [11:0] pc1_c12_im = -12'sd946;
  wire signed [11:0] pc1_c13_re = 12'sd297;
  wire signed [11:0] pc1_c13_im = -12'sd980;
  wire signed [11:0] pc1_c14_re = 12'sd200;
  wire signed [11:0] pc1_c14_im = -12'sd1004;
  wire signed [11:0] pc1_c15_re = 12'sd100;
  wire signed [11:0] pc1_c15_im = -12'sd1019;
  wire signed [11:0] pc1_c16_re = 12'sd0;
  wire signed [11:0] pc1_c16_im = -12'sd1024;
  wire signed [11:0] pc1_c17_re = -12'sd100;
  wire signed [11:0] pc1_c17_im = -12'sd1019;
  wire signed [11:0] pc1_c18_re = -12'sd200;
  wire signed [11:0] pc1_c18_im = -12'sd1004;
  wire signed [11:0] pc1_c19_re = -12'sd297;
  wire signed [11:0] pc1_c19_im = -12'sd980;
  wire signed [11:0] pc1_c20_re = -12'sd392;
  wire signed [11:0] pc1_c20_im = -12'sd946;
  wire signed [11:0] pc1_c21_re = -12'sd483;
  wire signed [11:0] pc1_c21_im = -12'sd903;
  wire signed [11:0] pc1_c22_re = -12'sd569;
  wire signed [11:0] pc1_c22_im = -12'sd851;
  wire signed [11:0] pc1_c23_re = -12'sd650;
  wire signed [11:0] pc1_c23_im = -12'sd792;
  wire signed [11:0] pc1_c24_re = -12'sd724;
  wire signed [11:0] pc1_c24_im = -12'sd724;
  wire signed [11:0] pc1_c25_re = -12'sd792;
  wire signed [11:0] pc1_c25_im = -12'sd650;
  wire signed [11:0] pc1_c26_re = -12'sd851;
  wire signed [11:0] pc1_c26_im = -12'sd569;
  wire signed [11:0] pc1_c27_re = -12'sd903;
  wire signed [11:0] pc1_c27_im = -12'sd483;
  wire signed [11:0] pc1_c28_re = -12'sd946;
  wire signed [11:0] pc1_c28_im = -12'sd392;
  wire signed [11:0] pc1_c29_re = -12'sd980;
  wire signed [11:0] pc1_c29_im = -12'sd297;
  wire signed [11:0] pc1_c30_re = -12'sd1004;
  wire signed [11:0] pc1_c30_im = -12'sd200;
  wire signed [11:0] pc1_c31_re = -12'sd1019;
  wire signed [11:0] pc1_c31_im = -12'sd100;
  wire signed [11:0] pc1_m0_0_re = px1[0] ? pc1_c1_re : pc1_c0_re;
  wire signed [11:0] pc1_m0_0_im = px1[0] ? pc1_c1_im : pc1_c0_im;
  wire signed [11:0] pc1_m0_1_re = px1[0] ? pc1_c3_re : pc1_c2_re;
  wire signed [11:0] pc1_m0_1_im = px1[0] ? pc1_c3_im : pc1_c2_im;
  wire signed [11:0] pc1_m0_2_re = px1[0] ? pc1_c5_re : pc1_c4_re;
  wire signed [11:0] pc1_m0_2_im = px1[0] ? pc1_c5_im : pc1_c4_im;
  wire signed [11:0] pc1_m0_3_re = px1[0] ? pc1_c7_re : pc1_c6_re;
  wire signed [11:0] pc1_m0_3_im = px1[0] ? pc1_c7_im : pc1_c6_im;
  wire signed [11:0] pc1_m0_4_re = px1[0] ? pc1_c9_re : pc1_c8_re;
  wire signed [11:0] pc1_m0_4_im = px1[0] ? pc1_c9_im : pc1_c8_im;
  wire signed [11:0] pc1_m0_5_re = px1[0] ? pc1_c11_re : pc1_c10_re;
  wire signed [11:0] pc1_m0_5_im = px1[0] ? pc1_c11_im : pc1_c10_im;
  wire signed [11:0] pc1_m0_6_re = px1[0] ? pc1_c13_re : pc1_c12_re;
  wire signed [11:0] pc1_m0_6_im = px1[0] ? pc1_c13_im : pc1_c12_im;
  wire signed [11:0] pc1_m0_7_re = px1[0] ? pc1_c15_re : pc1_c14_re;
  wire signed [11:0] pc1_m0_7_im = px1[0] ? pc1_c15_im : pc1_c14_im;
  wire signed [11:0] pc1_m0_8_re = px1[0] ? pc1_c17_re : pc1_c16_re;
  wire signed [11:0] pc1_m0_8_im = px1[0] ? pc1_c17_im : pc1_c16_im;
  wire signed [11:0] pc1_m0_9_re = px1[0] ? pc1_c19_re : pc1_c18_re;
  wire signed [11:0] pc1_m0_9_im = px1[0] ? pc1_c19_im : pc1_c18_im;
  wire signed [11:0] pc1_m0_10_re = px1[0] ? pc1_c21_re : pc1_c20_re;
  wire signed [11:0] pc1_m0_10_im = px1[0] ? pc1_c21_im : pc1_c20_im;
  wire signed [11:0] pc1_m0_11_re = px1[0] ? pc1_c23_re : pc1_c22_re;
  wire signed [11:0] pc1_m0_11_im = px1[0] ? pc1_c23_im : pc1_c22_im;
  wire signed [11:0] pc1_m0_12_re = px1[0] ? pc1_c25_re : pc1_c24_re;
  wire signed [11:0] pc1_m0_12_im = px1[0] ? pc1_c25_im : pc1_c24_im;
  wire signed [11:0] pc1_m0_13_re = px1[0] ? pc1_c27_re : pc1_c26_re;
  wire signed [11:0] pc1_m0_13_im = px1[0] ? pc1_c27_im : pc1_c26_im;
  wire signed [11:0] pc1_m0_14_re = px1[0] ? pc1_c29_re : pc1_c28_re;
  wire signed [11:0] pc1_m0_14_im = px1[0] ? pc1_c29_im : pc1_c28_im;
  wire signed [11:0] pc1_m0_15_re = px1[0] ? pc1_c31_re : pc1_c30_re;
  wire signed [11:0] pc1_m0_15_im = px1[0] ? pc1_c31_im : pc1_c30_im;
  wire signed [11:0] pc1_m1_0_re = px1[1] ? pc1_m0_1_re : pc1_m0_0_re;
  wire signed [11:0] pc1_m1_0_im = px1[1] ? pc1_m0_1_im : pc1_m0_0_im;
  wire signed [11:0] pc1_m1_1_re = px1[1] ? pc1_m0_3_re : pc1_m0_2_re;
  wire signed [11:0] pc1_m1_1_im = px1[1] ? pc1_m0_3_im : pc1_m0_2_im;
  wire signed [11:0] pc1_m1_2_re = px1[1] ? pc1_m0_5_re : pc1_m0_4_re;
  wire signed [11:0] pc1_m1_2_im = px1[1] ? pc1_m0_5_im : pc1_m0_4_im;
  wire signed [11:0] pc1_m1_3_re = px1[1] ? pc1_m0_7_re : pc1_m0_6_re;
  wire signed [11:0] pc1_m1_3_im = px1[1] ? pc1_m0_7_im : pc1_m0_6_im;
  wire signed [11:0] pc1_m1_4_re = px1[1] ? pc1_m0_9_re : pc1_m0_8_re;
  wire signed [11:0] pc1_m1_4_im = px1[1] ? pc1_m0_9_im : pc1_m0_8_im;
  wire signed [11:0] pc1_m1_5_re = px1[1] ? pc1_m0_11_re : pc1_m0_10_re;
  wire signed [11:0] pc1_m1_5_im = px1[1] ? pc1_m0_11_im : pc1_m0_10_im;
  wire signed [11:0] pc1_m1_6_re = px1[1] ? pc1_m0_13_re : pc1_m0_12_re;
  wire signed [11:0] pc1_m1_6_im = px1[1] ? pc1_m0_13_im : pc1_m0_12_im;
  wire signed [11:0] pc1_m1_7_re = px1[1] ? pc1_m0_15_re : pc1_m0_14_re;
  wire signed [11:0] pc1_m1_7_im = px1[1] ? pc1_m0_15_im : pc1_m0_14_im;
  wire signed [11:0] pc1_m2_0_re = px1[2] ? pc1_m1_1_re : pc1_m1_0_re;
  wire signed [11:0] pc1_m2_0_im = px1[2] ? pc1_m1_1_im : pc1_m1_0_im;
  wire signed [11:0] pc1_m2_1_re = px1[2] ? pc1_m1_3_re : pc1_m1_2_re;
  wire signed [11:0] pc1_m2_1_im = px1[2] ? pc1_m1_3_im : pc1_m1_2_im;
  wire signed [11:0] pc1_m2_2_re = px1[2] ? pc1_m1_5_re : pc1_m1_4_re;
  wire signed [11:0] pc1_m2_2_im = px1[2] ? pc1_m1_5_im : pc1_m1_4_im;
  wire signed [11:0] pc1_m2_3_re = px1[2] ? pc1_m1_7_re : pc1_m1_6_re;
  wire signed [11:0] pc1_m2_3_im = px1[2] ? pc1_m1_7_im : pc1_m1_6_im;
  wire signed [11:0] pc1_m3_0_re = px1[3] ? pc1_m2_1_re : pc1_m2_0_re;
  wire signed [11:0] pc1_m3_0_im = px1[3] ? pc1_m2_1_im : pc1_m2_0_im;
  wire signed [11:0] pc1_m3_1_re = px1[3] ? pc1_m2_3_re : pc1_m2_2_re;
  wire signed [11:0] pc1_m3_1_im = px1[3] ? pc1_m2_3_im : pc1_m2_2_im;
  wire signed [11:0] pc1_m4_0_re = px1[4] ? pc1_m3_1_re : pc1_m3_0_re;
  wire signed [11:0] pc1_m4_0_im = px1[4] ? pc1_m3_1_im : pc1_m3_0_im;
  wire signed [11:0] pc1_re = pc1_m4_0_re;
  wire signed [11:0] pc1_im = pc1_m4_0_im;
  reg signed [11:0] cr1, ci1;
  always @(posedge clk) begin
    if (rst) begin cr1 <= 12'sd1024; ci1 <= 12'sd0; end
    else begin cr1 <= pc1_re; ci1 <= pc1_im; end
  end
  wire signed [15:0] i1_re = din_re;
  wire signed [15:0] i1_im = din_im;
  wire signed [17:0] su1_re = do1_re + i1_re;
  wire signed [17:0] su1_im = do1_im + i1_im;
  wire signed [17:0] df1_re = do1_re - i1_re;
  wire signed [17:0] df1_im = do1_im - i1_im;
  wire signed [16:0] dr1_re = df1_re[16:0];
  wire signed [16:0] dr1_im = df1_im[16:0];
  wire signed [28:0] pr1 = dr1_re * cr1;
  wire signed [28:0] pi1 = dr1_im * ci1;
  wire signed [28:0] qr1 = dr1_re * ci1;
  wire signed [28:0] qi1 = dr1_im * cr1;
  wire signed [29:0] zr1_f = {pr1[28],pr1} - {pi1[28],pi1} + 512;
  wire signed [29:0] zi1_f = {qr1[28],qr1} + {qi1[28],qi1} + 512;
  wire signed [16:0] zr1 = zr1_f[26:10];
  wire signed [16:0] zi1 = zi1_f[26:10];
  wire signed [16:0] nx1_re = ph1 ? zr1 : do1_re;
  wire signed [16:0] nx1_im = ph1 ? zi1 : do1_im;
  wire signed [16:0] wr1_re = ph1 ? su1_re[16:0] : {i1_re[15],i1_re};
  wire signed [16:0] wr1_im = ph1 ? su1_im[16:0] : {i1_im[15],i1_im};
  reg  signed [16:0] o1_re, o1_im;
  integer k1;
  wire [16:0] rstmask1 = { 17 {~rst} };
  always @(posedge clk) begin
    for (k1=31; k1>0; k1=k1-1) begin
      dly1_re[k1] <= dly1_re[k1-1] & rstmask1;
      dly1_im[k1] <= dly1_im[k1-1] & rstmask1;
    end
    dly1_re[0] <= wr1_re & rstmask1;
    dly1_im[0] <= wr1_im & rstmask1;
    o1_re <= nx1_re & rstmask1;
    o1_im <= nx1_im & rstmask1;
  end

  // ---------------- stage 2: M=16 W=17 ----------------
  reg  signed [17:0] dly2_re [0:15];
  reg  signed [17:0] dly2_im [0:15];
  wire signed [17:0] do2_re = dly2_re[15];
  wire signed [17:0] do2_im = dly2_im[15];
  wire ph2 = cp1[4];
  wire [3:0] ix2 = cp1[3:0];
  wire [3:0] px2 = sc[3:0];
  wire signed [11:0] pc2_c0_re = 12'sd1024;
  wire signed [11:0] pc2_c0_im = 12'sd0;
  wire signed [11:0] pc2_c1_re = 12'sd1004;
  wire signed [11:0] pc2_c1_im = -12'sd200;
  wire signed [11:0] pc2_c2_re = 12'sd946;
  wire signed [11:0] pc2_c2_im = -12'sd392;
  wire signed [11:0] pc2_c3_re = 12'sd851;
  wire signed [11:0] pc2_c3_im = -12'sd569;
  wire signed [11:0] pc2_c4_re = 12'sd724;
  wire signed [11:0] pc2_c4_im = -12'sd724;
  wire signed [11:0] pc2_c5_re = 12'sd569;
  wire signed [11:0] pc2_c5_im = -12'sd851;
  wire signed [11:0] pc2_c6_re = 12'sd392;
  wire signed [11:0] pc2_c6_im = -12'sd946;
  wire signed [11:0] pc2_c7_re = 12'sd200;
  wire signed [11:0] pc2_c7_im = -12'sd1004;
  wire signed [11:0] pc2_c8_re = 12'sd0;
  wire signed [11:0] pc2_c8_im = -12'sd1024;
  wire signed [11:0] pc2_c9_re = -12'sd200;
  wire signed [11:0] pc2_c9_im = -12'sd1004;
  wire signed [11:0] pc2_c10_re = -12'sd392;
  wire signed [11:0] pc2_c10_im = -12'sd946;
  wire signed [11:0] pc2_c11_re = -12'sd569;
  wire signed [11:0] pc2_c11_im = -12'sd851;
  wire signed [11:0] pc2_c12_re = -12'sd724;
  wire signed [11:0] pc2_c12_im = -12'sd724;
  wire signed [11:0] pc2_c13_re = -12'sd851;
  wire signed [11:0] pc2_c13_im = -12'sd569;
  wire signed [11:0] pc2_c14_re = -12'sd946;
  wire signed [11:0] pc2_c14_im = -12'sd392;
  wire signed [11:0] pc2_c15_re = -12'sd1004;
  wire signed [11:0] pc2_c15_im = -12'sd200;
  wire signed [11:0] pc2_m0_0_re = px2[0] ? pc2_c1_re : pc2_c0_re;
  wire signed [11:0] pc2_m0_0_im = px2[0] ? pc2_c1_im : pc2_c0_im;
  wire signed [11:0] pc2_m0_1_re = px2[0] ? pc2_c3_re : pc2_c2_re;
  wire signed [11:0] pc2_m0_1_im = px2[0] ? pc2_c3_im : pc2_c2_im;
  wire signed [11:0] pc2_m0_2_re = px2[0] ? pc2_c5_re : pc2_c4_re;
  wire signed [11:0] pc2_m0_2_im = px2[0] ? pc2_c5_im : pc2_c4_im;
  wire signed [11:0] pc2_m0_3_re = px2[0] ? pc2_c7_re : pc2_c6_re;
  wire signed [11:0] pc2_m0_3_im = px2[0] ? pc2_c7_im : pc2_c6_im;
  wire signed [11:0] pc2_m0_4_re = px2[0] ? pc2_c9_re : pc2_c8_re;
  wire signed [11:0] pc2_m0_4_im = px2[0] ? pc2_c9_im : pc2_c8_im;
  wire signed [11:0] pc2_m0_5_re = px2[0] ? pc2_c11_re : pc2_c10_re;
  wire signed [11:0] pc2_m0_5_im = px2[0] ? pc2_c11_im : pc2_c10_im;
  wire signed [11:0] pc2_m0_6_re = px2[0] ? pc2_c13_re : pc2_c12_re;
  wire signed [11:0] pc2_m0_6_im = px2[0] ? pc2_c13_im : pc2_c12_im;
  wire signed [11:0] pc2_m0_7_re = px2[0] ? pc2_c15_re : pc2_c14_re;
  wire signed [11:0] pc2_m0_7_im = px2[0] ? pc2_c15_im : pc2_c14_im;
  wire signed [11:0] pc2_m1_0_re = px2[1] ? pc2_m0_1_re : pc2_m0_0_re;
  wire signed [11:0] pc2_m1_0_im = px2[1] ? pc2_m0_1_im : pc2_m0_0_im;
  wire signed [11:0] pc2_m1_1_re = px2[1] ? pc2_m0_3_re : pc2_m0_2_re;
  wire signed [11:0] pc2_m1_1_im = px2[1] ? pc2_m0_3_im : pc2_m0_2_im;
  wire signed [11:0] pc2_m1_2_re = px2[1] ? pc2_m0_5_re : pc2_m0_4_re;
  wire signed [11:0] pc2_m1_2_im = px2[1] ? pc2_m0_5_im : pc2_m0_4_im;
  wire signed [11:0] pc2_m1_3_re = px2[1] ? pc2_m0_7_re : pc2_m0_6_re;
  wire signed [11:0] pc2_m1_3_im = px2[1] ? pc2_m0_7_im : pc2_m0_6_im;
  wire signed [11:0] pc2_m2_0_re = px2[2] ? pc2_m1_1_re : pc2_m1_0_re;
  wire signed [11:0] pc2_m2_0_im = px2[2] ? pc2_m1_1_im : pc2_m1_0_im;
  wire signed [11:0] pc2_m2_1_re = px2[2] ? pc2_m1_3_re : pc2_m1_2_re;
  wire signed [11:0] pc2_m2_1_im = px2[2] ? pc2_m1_3_im : pc2_m1_2_im;
  wire signed [11:0] pc2_m3_0_re = px2[3] ? pc2_m2_1_re : pc2_m2_0_re;
  wire signed [11:0] pc2_m3_0_im = px2[3] ? pc2_m2_1_im : pc2_m2_0_im;
  wire signed [11:0] pc2_re = pc2_m3_0_re;
  wire signed [11:0] pc2_im = pc2_m3_0_im;
  reg signed [11:0] cr2, ci2;
  always @(posedge clk) begin
    if (rst) begin cr2 <= 12'sd1024; ci2 <= 12'sd0; end
    else begin cr2 <= pc2_re; ci2 <= pc2_im; end
  end
  wire signed [16:0] i2_re = o1_re;
  wire signed [16:0] i2_im = o1_im;
  wire signed [18:0] su2_re = do2_re + i2_re;
  wire signed [18:0] su2_im = do2_im + i2_im;
  wire signed [18:0] df2_re = do2_re - i2_re;
  wire signed [18:0] df2_im = do2_im - i2_im;
  wire signed [17:0] dr2_re = df2_re[17:0];
  wire signed [17:0] dr2_im = df2_im[17:0];
  wire signed [29:0] pr2 = dr2_re * cr2;
  wire signed [29:0] pi2 = dr2_im * ci2;
  wire signed [29:0] qr2 = dr2_re * ci2;
  wire signed [29:0] qi2 = dr2_im * cr2;
  wire signed [30:0] zr2_f = {pr2[29],pr2} - {pi2[29],pi2} + 512;
  wire signed [30:0] zi2_f = {qr2[29],qr2} + {qi2[29],qi2} + 512;
  wire signed [17:0] zr2 = zr2_f[27:10];
  wire signed [17:0] zi2 = zi2_f[27:10];
  wire signed [17:0] nx2_re = ph2 ? zr2 : do2_re;
  wire signed [17:0] nx2_im = ph2 ? zi2 : do2_im;
  wire signed [17:0] wr2_re = ph2 ? su2_re[17:0] : {i2_re[16],i2_re};
  wire signed [17:0] wr2_im = ph2 ? su2_im[17:0] : {i2_im[16],i2_im};
  reg  signed [17:0] o2_re, o2_im;
  integer k2;
  wire [17:0] rstmask2 = { 18 {~rst} };
  always @(posedge clk) begin
    for (k2=15; k2>0; k2=k2-1) begin
      dly2_re[k2] <= dly2_re[k2-1] & rstmask2;
      dly2_im[k2] <= dly2_im[k2-1] & rstmask2;
    end
    dly2_re[0] <= wr2_re & rstmask2;
    dly2_im[0] <= wr2_im & rstmask2;
    o2_re <= nx2_re & rstmask2;
    o2_im <= nx2_im & rstmask2;
  end

  // ---------------- stage 3: M=8 W=18 ----------------
  reg  signed [18:0] dly3_re [0:7];
  reg  signed [18:0] dly3_im [0:7];
  wire signed [18:0] do3_re = dly3_re[7];
  wire signed [18:0] do3_im = dly3_im[7];
  wire ph3 = cp2[3];
  wire [2:0] ix3 = cp2[2:0];
  wire [2:0] px3 = cp1[2:0];
  wire signed [11:0] pc3_c0_re = 12'sd1024;
  wire signed [11:0] pc3_c0_im = 12'sd0;
  wire signed [11:0] pc3_c1_re = 12'sd946;
  wire signed [11:0] pc3_c1_im = -12'sd392;
  wire signed [11:0] pc3_c2_re = 12'sd724;
  wire signed [11:0] pc3_c2_im = -12'sd724;
  wire signed [11:0] pc3_c3_re = 12'sd392;
  wire signed [11:0] pc3_c3_im = -12'sd946;
  wire signed [11:0] pc3_c4_re = 12'sd0;
  wire signed [11:0] pc3_c4_im = -12'sd1024;
  wire signed [11:0] pc3_c5_re = -12'sd392;
  wire signed [11:0] pc3_c5_im = -12'sd946;
  wire signed [11:0] pc3_c6_re = -12'sd724;
  wire signed [11:0] pc3_c6_im = -12'sd724;
  wire signed [11:0] pc3_c7_re = -12'sd946;
  wire signed [11:0] pc3_c7_im = -12'sd392;
  wire signed [11:0] pc3_m0_0_re = px3[0] ? pc3_c1_re : pc3_c0_re;
  wire signed [11:0] pc3_m0_0_im = px3[0] ? pc3_c1_im : pc3_c0_im;
  wire signed [11:0] pc3_m0_1_re = px3[0] ? pc3_c3_re : pc3_c2_re;
  wire signed [11:0] pc3_m0_1_im = px3[0] ? pc3_c3_im : pc3_c2_im;
  wire signed [11:0] pc3_m0_2_re = px3[0] ? pc3_c5_re : pc3_c4_re;
  wire signed [11:0] pc3_m0_2_im = px3[0] ? pc3_c5_im : pc3_c4_im;
  wire signed [11:0] pc3_m0_3_re = px3[0] ? pc3_c7_re : pc3_c6_re;
  wire signed [11:0] pc3_m0_3_im = px3[0] ? pc3_c7_im : pc3_c6_im;
  wire signed [11:0] pc3_m1_0_re = px3[1] ? pc3_m0_1_re : pc3_m0_0_re;
  wire signed [11:0] pc3_m1_0_im = px3[1] ? pc3_m0_1_im : pc3_m0_0_im;
  wire signed [11:0] pc3_m1_1_re = px3[1] ? pc3_m0_3_re : pc3_m0_2_re;
  wire signed [11:0] pc3_m1_1_im = px3[1] ? pc3_m0_3_im : pc3_m0_2_im;
  wire signed [11:0] pc3_m2_0_re = px3[2] ? pc3_m1_1_re : pc3_m1_0_re;
  wire signed [11:0] pc3_m2_0_im = px3[2] ? pc3_m1_1_im : pc3_m1_0_im;
  wire signed [11:0] pc3_re = pc3_m2_0_re;
  wire signed [11:0] pc3_im = pc3_m2_0_im;
  reg signed [11:0] cr3, ci3;
  always @(posedge clk) begin
    if (rst) begin cr3 <= 12'sd1024; ci3 <= 12'sd0; end
    else begin cr3 <= pc3_re; ci3 <= pc3_im; end
  end
  wire signed [17:0] i3_re = o2_re;
  wire signed [17:0] i3_im = o2_im;
  wire signed [19:0] su3_re = do3_re + i3_re;
  wire signed [19:0] su3_im = do3_im + i3_im;
  wire signed [19:0] df3_re = do3_re - i3_re;
  wire signed [19:0] df3_im = do3_im - i3_im;
  wire signed [18:0] dr3_re = df3_re[18:0];
  wire signed [18:0] dr3_im = df3_im[18:0];
  wire signed [30:0] pr3 = dr3_re * cr3;
  wire signed [30:0] pi3 = dr3_im * ci3;
  wire signed [30:0] qr3 = dr3_re * ci3;
  wire signed [30:0] qi3 = dr3_im * cr3;
  wire signed [31:0] zr3_f = {pr3[30],pr3} - {pi3[30],pi3} + 512;
  wire signed [31:0] zi3_f = {qr3[30],qr3} + {qi3[30],qi3} + 512;
  wire signed [18:0] zr3 = zr3_f[28:10];
  wire signed [18:0] zi3 = zi3_f[28:10];
  wire signed [18:0] nx3_re = ph3 ? zr3 : do3_re;
  wire signed [18:0] nx3_im = ph3 ? zi3 : do3_im;
  wire signed [18:0] wr3_re = ph3 ? su3_re[18:0] : {i3_re[17],i3_re};
  wire signed [18:0] wr3_im = ph3 ? su3_im[18:0] : {i3_im[17],i3_im};
  reg  signed [18:0] o3_re, o3_im;
  integer k3;
  wire [18:0] rstmask3 = { 19 {~rst} };
  always @(posedge clk) begin
    for (k3=7; k3>0; k3=k3-1) begin
      dly3_re[k3] <= dly3_re[k3-1] & rstmask3;
      dly3_im[k3] <= dly3_im[k3-1] & rstmask3;
    end
    dly3_re[0] <= wr3_re & rstmask3;
    dly3_im[0] <= wr3_im & rstmask3;
    o3_re <= nx3_re & rstmask3;
    o3_im <= nx3_im & rstmask3;
  end

  // ---------------- stage 4: M=4 W=19 ----------------
  reg  signed [19:0] dly4_re [0:3];
  reg  signed [19:0] dly4_im [0:3];
  wire signed [19:0] do4_re = dly4_re[3];
  wire signed [19:0] do4_im = dly4_im[3];
  wire ph4 = cp3[2];
  wire [1:0] ix4 = cp3[1:0];
  wire signed [11:0] pc4_c0_re = 12'sd1024;
  wire signed [11:0] pc4_c0_im = 12'sd0;
  wire signed [11:0] pc4_c1_re = 12'sd724;
  wire signed [11:0] pc4_c1_im = -12'sd724;
  wire signed [11:0] pc4_c2_re = 12'sd0;
  wire signed [11:0] pc4_c2_im = -12'sd1024;
  wire signed [11:0] pc4_c3_re = -12'sd724;
  wire signed [11:0] pc4_c3_im = -12'sd724;
  wire signed [11:0] pc4_m0_0_re = ix4[0] ? pc4_c1_re : pc4_c0_re;
  wire signed [11:0] pc4_m0_0_im = ix4[0] ? pc4_c1_im : pc4_c0_im;
  wire signed [11:0] pc4_m0_1_re = ix4[0] ? pc4_c3_re : pc4_c2_re;
  wire signed [11:0] pc4_m0_1_im = ix4[0] ? pc4_c3_im : pc4_c2_im;
  wire signed [11:0] pc4_m1_0_re = ix4[1] ? pc4_m0_1_re : pc4_m0_0_re;
  wire signed [11:0] pc4_m1_0_im = ix4[1] ? pc4_m0_1_im : pc4_m0_0_im;
  wire signed [11:0] pc4_re = pc4_m1_0_re;
  wire signed [11:0] pc4_im = pc4_m1_0_im;
  wire signed [11:0] cr4 = pc4_re;
  wire signed [11:0] ci4 = pc4_im;
  wire signed [18:0] i4_re = o3_re;
  wire signed [18:0] i4_im = o3_im;
  wire signed [20:0] su4_re = do4_re + i4_re;
  wire signed [20:0] su4_im = do4_im + i4_im;
  wire signed [20:0] df4_re = do4_re - i4_re;
  wire signed [20:0] df4_im = do4_im - i4_im;
  wire signed [19:0] dr4_re = df4_re[19:0];
  wire signed [19:0] dr4_im = df4_im[19:0];
  wire signed [31:0] pr4 = dr4_re * cr4;
  wire signed [31:0] pi4 = dr4_im * ci4;
  wire signed [31:0] qr4 = dr4_re * ci4;
  wire signed [31:0] qi4 = dr4_im * cr4;
  wire signed [32:0] zr4_f = {pr4[31],pr4} - {pi4[31],pi4} + 512;
  wire signed [32:0] zi4_f = {qr4[31],qr4} + {qi4[31],qi4} + 512;
  wire signed [19:0] zr4 = zr4_f[29:10];
  wire signed [19:0] zi4 = zi4_f[29:10];
  wire signed [19:0] nx4_re = ph4 ? zr4 : do4_re;
  wire signed [19:0] nx4_im = ph4 ? zi4 : do4_im;
  wire signed [19:0] wr4_re = ph4 ? su4_re[19:0] : {i4_re[18],i4_re};
  wire signed [19:0] wr4_im = ph4 ? su4_im[19:0] : {i4_im[18],i4_im};
  reg  signed [19:0] o4_re, o4_im;
  integer k4;
  wire [19:0] rstmask4 = { 20 {~rst} };
  always @(posedge clk) begin
    for (k4=3; k4>0; k4=k4-1) begin
      dly4_re[k4] <= dly4_re[k4-1] & rstmask4;
      dly4_im[k4] <= dly4_im[k4-1] & rstmask4;
    end
    dly4_re[0] <= wr4_re & rstmask4;
    dly4_im[0] <= wr4_im & rstmask4;
    o4_re <= nx4_re & rstmask4;
    o4_im <= nx4_im & rstmask4;
  end

  // ---------------- stage 5: M=2 W=20 ----------------
  reg  signed [20:0] dly5_re [0:1];
  reg  signed [20:0] dly5_im [0:1];
  wire signed [20:0] do5_re = dly5_re[1];
  wire signed [20:0] do5_im = dly5_im[1];
  wire ph5 = cp4[1];
  wire [0:0] ix5 = cp4[0:0];
  wire signed [11:0] pc5_c0_re = 12'sd1024;
  wire signed [11:0] pc5_c0_im = 12'sd0;
  wire signed [11:0] pc5_c1_re = 12'sd0;
  wire signed [11:0] pc5_c1_im = -12'sd1024;
  wire signed [11:0] pc5_m0_0_re = ix5[0] ? pc5_c1_re : pc5_c0_re;
  wire signed [11:0] pc5_m0_0_im = ix5[0] ? pc5_c1_im : pc5_c0_im;
  wire signed [11:0] pc5_re = pc5_m0_0_re;
  wire signed [11:0] pc5_im = pc5_m0_0_im;
  wire signed [11:0] cr5 = pc5_re;
  wire signed [11:0] ci5 = pc5_im;
  wire signed [19:0] i5_re = o4_re;
  wire signed [19:0] i5_im = o4_im;
  wire signed [21:0] su5_re = do5_re + i5_re;
  wire signed [21:0] su5_im = do5_im + i5_im;
  wire signed [21:0] df5_re = do5_re - i5_re;
  wire signed [21:0] df5_im = do5_im - i5_im;
  wire signed [20:0] dr5_re = df5_re[20:0];
  wire signed [20:0] dr5_im = df5_im[20:0];
  wire signed [32:0] pr5 = dr5_re * cr5;
  wire signed [32:0] pi5 = dr5_im * ci5;
  wire signed [32:0] qr5 = dr5_re * ci5;
  wire signed [32:0] qi5 = dr5_im * cr5;
  wire signed [33:0] zr5_f = {pr5[32],pr5} - {pi5[32],pi5} + 512;
  wire signed [33:0] zi5_f = {qr5[32],qr5} + {qi5[32],qi5} + 512;
  wire signed [20:0] zr5 = zr5_f[30:10];
  wire signed [20:0] zi5 = zi5_f[30:10];
  wire signed [20:0] nx5_re = ph5 ? zr5 : do5_re;
  wire signed [20:0] nx5_im = ph5 ? zi5 : do5_im;
  wire signed [20:0] wr5_re = ph5 ? su5_re[20:0] : {i5_re[19],i5_re};
  wire signed [20:0] wr5_im = ph5 ? su5_im[20:0] : {i5_im[19],i5_im};
  reg  signed [20:0] o5_re, o5_im;
  integer k5;
  wire [20:0] rstmask5 = { 21 {~rst} };
  always @(posedge clk) begin
    for (k5=1; k5>0; k5=k5-1) begin
      dly5_re[k5] <= dly5_re[k5-1] & rstmask5;
      dly5_im[k5] <= dly5_im[k5-1] & rstmask5;
    end
    dly5_re[0] <= wr5_re & rstmask5;
    dly5_im[0] <= wr5_im & rstmask5;
    o5_re <= nx5_re & rstmask5;
    o5_im <= nx5_im & rstmask5;
  end

  // ---------------- stage 6: M=1 W=21 ----------------
  reg  signed [21:0] dly6_re [0:0];
  reg  signed [21:0] dly6_im [0:0];
  wire signed [21:0] do6_re = dly6_re[0];
  wire signed [21:0] do6_im = dly6_im[0];
  wire ph6 = cp5[0];
  wire [0:0] ix6 = 1'b0;
  wire signed [11:0] pc6_re = 12'sd1024;
  wire signed [11:0] pc6_im = 12'sd0;
  wire signed [11:0] cr6 = pc6_re;
  wire signed [11:0] ci6 = pc6_im;
  wire signed [20:0] i6_re = o5_re;
  wire signed [20:0] i6_im = o5_im;
  wire signed [22:0] su6_re = do6_re + i6_re;
  wire signed [22:0] su6_im = do6_im + i6_im;
  wire signed [22:0] df6_re = do6_re - i6_re;
  wire signed [22:0] df6_im = do6_im - i6_im;
  wire signed [21:0] dr6_re = df6_re[21:0];
  wire signed [21:0] dr6_im = df6_im[21:0];
  wire signed [33:0] pr6 = dr6_re * cr6;
  wire signed [33:0] pi6 = dr6_im * ci6;
  wire signed [33:0] qr6 = dr6_re * ci6;
  wire signed [33:0] qi6 = dr6_im * cr6;
  wire signed [34:0] zr6_f = {pr6[33],pr6} - {pi6[33],pi6} + 512;
  wire signed [34:0] zi6_f = {qr6[33],qr6} + {qi6[33],qi6} + 512;
  wire signed [21:0] zr6 = zr6_f[31:10];
  wire signed [21:0] zi6 = zi6_f[31:10];
  wire signed [21:0] nx6_re = ph6 ? zr6 : do6_re;
  wire signed [21:0] nx6_im = ph6 ? zi6 : do6_im;
  wire signed [21:0] wr6_re = ph6 ? su6_re[21:0] : {i6_re[20],i6_re};
  wire signed [21:0] wr6_im = ph6 ? su6_im[21:0] : {i6_im[20],i6_im};
  reg  signed [21:0] o6_re, o6_im;
  integer k6;
  wire [21:0] rstmask6 = { 22 {~rst} };
  always @(posedge clk) begin
    for (k6=0; k6>0; k6=k6-1) begin
      dly6_re[k6] <= dly6_re[k6-1] & rstmask6;
      dly6_im[k6] <= dly6_im[k6-1] & rstmask6;
    end
    dly6_re[0] <= wr6_re & rstmask6;
    dly6_im[0] <= wr6_im & rstmask6;
    o6_re <= nx6_re & rstmask6;
    o6_im <= nx6_im & rstmask6;
  end

  // ---------------- output reorder buffer ----------------
  reg signed [21:0] rb_re [0:63];
  reg signed [21:0] rb_im [0:63];
  wire       wr_en = (cp6 >= 8'd63) && (cp6 <= 8'd126);
  wire [5:0] wt  = cp6[5:0] - 6'd63;
  wire [5:0] wad = ~{wt[0],wt[1],wt[2],wt[3],wt[4],wt[5]};

  reg [COFF:0] arm_sr;
  always @(posedge clk) begin
    if (rst) arm_sr <= 0;
    else     arm_sr <= {arm_sr[COFF-1:0], start};
  end
  wire emit_arm = arm_sr[COFF];

  reg        emit;
  reg [5:0]  eidx;
  always @(posedge clk) begin
    if (rst) begin emit <= 1'b0; eidx <= 6'd0; end
    else if (emit_arm) begin emit <= 1'b1; eidx <= 6'd0; end
    else if (emit) begin
      if (eidx == 6'd63) emit <= 1'b0;
      else eidx <= eidx + 6'd1;
    end
  end

  always @(posedge clk) if (wr_en) begin
    rb_re[wad] <= o6_re[21:0];
    rb_im[wad] <= o6_im[21:0];
  end

  assign out_valid = emit;
  assign out_start = emit & (eidx == 6'd0);
  wire signed [21:0] rd_re = rb_re[eidx];
  wire signed [21:0] rd_im = rb_im[eidx];
  assign out_re = {{2{rd_re[21]}}, rd_re};
  assign out_im = {{2{rd_im[21]}}, rd_im};
endmodule
`default_nettype wire
