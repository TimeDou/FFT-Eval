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

  // ---------------- frame control ----------------
  reg  [7:0] sc;
  reg        busy;
  wire       start = in_valid & frame_start;

  always @(posedge clk) begin
    if (rst) begin
      busy <= 1'b0;
      sc   <= 8'd0;
    end else if (start) begin
      busy <= 1'b1;
      sc   <= 8'd1;
    end else if (busy) begin
      if (sc == LAST[7:0]) begin busy <= 1'b0; sc <= 8'd0; end
      else sc <= sc + 8'd1;
    end
  end

  // pipeline of the position counter, aligned with the datapath registers
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
  reg signed [13:0] cr1, ci1;
  always @* case (ix1)
    5'd0: begin cr1 = 14'sd4096; ci1 = 14'sd0; end
    5'd1: begin cr1 = 14'sd4076; ci1 = -14'sd401; end
    5'd2: begin cr1 = 14'sd4017; ci1 = -14'sd799; end
    5'd3: begin cr1 = 14'sd3920; ci1 = -14'sd1189; end
    5'd4: begin cr1 = 14'sd3784; ci1 = -14'sd1567; end
    5'd5: begin cr1 = 14'sd3612; ci1 = -14'sd1931; end
    5'd6: begin cr1 = 14'sd3406; ci1 = -14'sd2276; end
    5'd7: begin cr1 = 14'sd3166; ci1 = -14'sd2598; end
    5'd8: begin cr1 = 14'sd2896; ci1 = -14'sd2896; end
    5'd9: begin cr1 = 14'sd2598; ci1 = -14'sd3166; end
    5'd10: begin cr1 = 14'sd2276; ci1 = -14'sd3406; end
    5'd11: begin cr1 = 14'sd1931; ci1 = -14'sd3612; end
    5'd12: begin cr1 = 14'sd1567; ci1 = -14'sd3784; end
    5'd13: begin cr1 = 14'sd1189; ci1 = -14'sd3920; end
    5'd14: begin cr1 = 14'sd799; ci1 = -14'sd4017; end
    5'd15: begin cr1 = 14'sd401; ci1 = -14'sd4076; end
    5'd16: begin cr1 = 14'sd0; ci1 = -14'sd4096; end
    5'd17: begin cr1 = -14'sd401; ci1 = -14'sd4076; end
    5'd18: begin cr1 = -14'sd799; ci1 = -14'sd4017; end
    5'd19: begin cr1 = -14'sd1189; ci1 = -14'sd3920; end
    5'd20: begin cr1 = -14'sd1567; ci1 = -14'sd3784; end
    5'd21: begin cr1 = -14'sd1931; ci1 = -14'sd3612; end
    5'd22: begin cr1 = -14'sd2276; ci1 = -14'sd3406; end
    5'd23: begin cr1 = -14'sd2598; ci1 = -14'sd3166; end
    5'd24: begin cr1 = -14'sd2896; ci1 = -14'sd2896; end
    5'd25: begin cr1 = -14'sd3166; ci1 = -14'sd2598; end
    5'd26: begin cr1 = -14'sd3406; ci1 = -14'sd2276; end
    5'd27: begin cr1 = -14'sd3612; ci1 = -14'sd1931; end
    5'd28: begin cr1 = -14'sd3784; ci1 = -14'sd1567; end
    5'd29: begin cr1 = -14'sd3920; ci1 = -14'sd1189; end
    5'd30: begin cr1 = -14'sd4017; ci1 = -14'sd799; end
    5'd31: begin cr1 = -14'sd4076; ci1 = -14'sd401; end
    default: begin cr1 = 14'sd4096; ci1 = 14'sd0; end
  endcase
  wire signed [15:0] i1_re = din_re;
  wire signed [15:0] i1_im = din_im;
  wire signed [17:0] su1_re = do1_re + i1_re;
  wire signed [17:0] su1_im = do1_im + i1_im;
  wire signed [17:0] df1_re = do1_re - i1_re;
  wire signed [17:0] df1_im = do1_im - i1_im;
  wire signed [16:0] dr1_re = df1_re[16:0];
  wire signed [16:0] dr1_im = df1_im[16:0];
  wire signed [30:0] pr1 = dr1_re * cr1;
  wire signed [30:0] pi1 = dr1_im * ci1;
  wire signed [30:0] qr1 = dr1_re * ci1;
  wire signed [30:0] qi1 = dr1_im * cr1;
  wire signed [31:0] zr1_f = {pr1[30],pr1} - {pi1[30],pi1} + 2048;
  wire signed [31:0] zi1_f = {qr1[30],qr1} + {qi1[30],qi1} + 2048;
  wire signed [16:0] zr1 = zr1_f[28:12];
  wire signed [16:0] zi1 = zi1_f[28:12];
  wire signed [16:0] nx1_re = ph1 ? zr1 : do1_re;
  wire signed [16:0] nx1_im = ph1 ? zi1 : do1_im;
  wire signed [16:0] wr1_re = ph1 ? su1_re[16:0] : {i1_re[15],i1_re};
  wire signed [16:0] wr1_im = ph1 ? su1_im[16:0] : {i1_im[15],i1_im};
  reg  signed [16:0] o1_re, o1_im;
  integer k1;
  always @(posedge clk) begin
    if (rst) begin
      for (k1=0; k1<32; k1=k1+1) begin
        dly1_re[k1] <= 17'sd0; dly1_im[k1] <= 17'sd0;
      end
      o1_re <= 17'sd0; o1_im <= 17'sd0;
    end else begin
      for (k1=31; k1>0; k1=k1-1) begin
        dly1_re[k1] <= dly1_re[k1-1];
        dly1_im[k1] <= dly1_im[k1-1];
      end
      dly1_re[0] <= wr1_re;
      dly1_im[0] <= wr1_im;
      o1_re <= nx1_re;
      o1_im <= nx1_im;
    end
  end

  // ---------------- stage 2: M=16 W=17 ----------------
  reg  signed [17:0] dly2_re [0:15];
  reg  signed [17:0] dly2_im [0:15];
  wire signed [17:0] do2_re = dly2_re[15];
  wire signed [17:0] do2_im = dly2_im[15];
  wire ph2 = cp1[4];
  wire [3:0] ix2 = cp1[3:0];
  reg signed [13:0] cr2, ci2;
  always @* case (ix2)
    4'd0: begin cr2 = 14'sd4096; ci2 = 14'sd0; end
    4'd1: begin cr2 = 14'sd4017; ci2 = -14'sd799; end
    4'd2: begin cr2 = 14'sd3784; ci2 = -14'sd1567; end
    4'd3: begin cr2 = 14'sd3406; ci2 = -14'sd2276; end
    4'd4: begin cr2 = 14'sd2896; ci2 = -14'sd2896; end
    4'd5: begin cr2 = 14'sd2276; ci2 = -14'sd3406; end
    4'd6: begin cr2 = 14'sd1567; ci2 = -14'sd3784; end
    4'd7: begin cr2 = 14'sd799; ci2 = -14'sd4017; end
    4'd8: begin cr2 = 14'sd0; ci2 = -14'sd4096; end
    4'd9: begin cr2 = -14'sd799; ci2 = -14'sd4017; end
    4'd10: begin cr2 = -14'sd1567; ci2 = -14'sd3784; end
    4'd11: begin cr2 = -14'sd2276; ci2 = -14'sd3406; end
    4'd12: begin cr2 = -14'sd2896; ci2 = -14'sd2896; end
    4'd13: begin cr2 = -14'sd3406; ci2 = -14'sd2276; end
    4'd14: begin cr2 = -14'sd3784; ci2 = -14'sd1567; end
    4'd15: begin cr2 = -14'sd4017; ci2 = -14'sd799; end
    default: begin cr2 = 14'sd4096; ci2 = 14'sd0; end
  endcase
  wire signed [16:0] i2_re = o1_re;
  wire signed [16:0] i2_im = o1_im;
  wire signed [18:0] su2_re = do2_re + i2_re;
  wire signed [18:0] su2_im = do2_im + i2_im;
  wire signed [18:0] df2_re = do2_re - i2_re;
  wire signed [18:0] df2_im = do2_im - i2_im;
  wire signed [17:0] dr2_re = df2_re[17:0];
  wire signed [17:0] dr2_im = df2_im[17:0];
  wire signed [31:0] pr2 = dr2_re * cr2;
  wire signed [31:0] pi2 = dr2_im * ci2;
  wire signed [31:0] qr2 = dr2_re * ci2;
  wire signed [31:0] qi2 = dr2_im * cr2;
  wire signed [32:0] zr2_f = {pr2[31],pr2} - {pi2[31],pi2} + 2048;
  wire signed [32:0] zi2_f = {qr2[31],qr2} + {qi2[31],qi2} + 2048;
  wire signed [17:0] zr2 = zr2_f[29:12];
  wire signed [17:0] zi2 = zi2_f[29:12];
  wire signed [17:0] nx2_re = ph2 ? zr2 : do2_re;
  wire signed [17:0] nx2_im = ph2 ? zi2 : do2_im;
  wire signed [17:0] wr2_re = ph2 ? su2_re[17:0] : {i2_re[16],i2_re};
  wire signed [17:0] wr2_im = ph2 ? su2_im[17:0] : {i2_im[16],i2_im};
  reg  signed [17:0] o2_re, o2_im;
  integer k2;
  always @(posedge clk) begin
    if (rst) begin
      for (k2=0; k2<16; k2=k2+1) begin
        dly2_re[k2] <= 18'sd0; dly2_im[k2] <= 18'sd0;
      end
      o2_re <= 18'sd0; o2_im <= 18'sd0;
    end else begin
      for (k2=15; k2>0; k2=k2-1) begin
        dly2_re[k2] <= dly2_re[k2-1];
        dly2_im[k2] <= dly2_im[k2-1];
      end
      dly2_re[0] <= wr2_re;
      dly2_im[0] <= wr2_im;
      o2_re <= nx2_re;
      o2_im <= nx2_im;
    end
  end

  // ---------------- stage 3: M=8 W=18 ----------------
  reg  signed [18:0] dly3_re [0:7];
  reg  signed [18:0] dly3_im [0:7];
  wire signed [18:0] do3_re = dly3_re[7];
  wire signed [18:0] do3_im = dly3_im[7];
  wire ph3 = cp2[3];
  wire [2:0] ix3 = cp2[2:0];
  reg signed [13:0] cr3, ci3;
  always @* case (ix3)
    3'd0: begin cr3 = 14'sd4096; ci3 = 14'sd0; end
    3'd1: begin cr3 = 14'sd3784; ci3 = -14'sd1567; end
    3'd2: begin cr3 = 14'sd2896; ci3 = -14'sd2896; end
    3'd3: begin cr3 = 14'sd1567; ci3 = -14'sd3784; end
    3'd4: begin cr3 = 14'sd0; ci3 = -14'sd4096; end
    3'd5: begin cr3 = -14'sd1567; ci3 = -14'sd3784; end
    3'd6: begin cr3 = -14'sd2896; ci3 = -14'sd2896; end
    3'd7: begin cr3 = -14'sd3784; ci3 = -14'sd1567; end
    default: begin cr3 = 14'sd4096; ci3 = 14'sd0; end
  endcase
  wire signed [17:0] i3_re = o2_re;
  wire signed [17:0] i3_im = o2_im;
  wire signed [19:0] su3_re = do3_re + i3_re;
  wire signed [19:0] su3_im = do3_im + i3_im;
  wire signed [19:0] df3_re = do3_re - i3_re;
  wire signed [19:0] df3_im = do3_im - i3_im;
  wire signed [18:0] dr3_re = df3_re[18:0];
  wire signed [18:0] dr3_im = df3_im[18:0];
  wire signed [32:0] pr3 = dr3_re * cr3;
  wire signed [32:0] pi3 = dr3_im * ci3;
  wire signed [32:0] qr3 = dr3_re * ci3;
  wire signed [32:0] qi3 = dr3_im * cr3;
  wire signed [33:0] zr3_f = {pr3[32],pr3} - {pi3[32],pi3} + 2048;
  wire signed [33:0] zi3_f = {qr3[32],qr3} + {qi3[32],qi3} + 2048;
  wire signed [18:0] zr3 = zr3_f[30:12];
  wire signed [18:0] zi3 = zi3_f[30:12];
  wire signed [18:0] nx3_re = ph3 ? zr3 : do3_re;
  wire signed [18:0] nx3_im = ph3 ? zi3 : do3_im;
  wire signed [18:0] wr3_re = ph3 ? su3_re[18:0] : {i3_re[17],i3_re};
  wire signed [18:0] wr3_im = ph3 ? su3_im[18:0] : {i3_im[17],i3_im};
  reg  signed [18:0] o3_re, o3_im;
  integer k3;
  always @(posedge clk) begin
    if (rst) begin
      for (k3=0; k3<8; k3=k3+1) begin
        dly3_re[k3] <= 19'sd0; dly3_im[k3] <= 19'sd0;
      end
      o3_re <= 19'sd0; o3_im <= 19'sd0;
    end else begin
      for (k3=7; k3>0; k3=k3-1) begin
        dly3_re[k3] <= dly3_re[k3-1];
        dly3_im[k3] <= dly3_im[k3-1];
      end
      dly3_re[0] <= wr3_re;
      dly3_im[0] <= wr3_im;
      o3_re <= nx3_re;
      o3_im <= nx3_im;
    end
  end

  // ---------------- stage 4: M=4 W=19 ----------------
  reg  signed [19:0] dly4_re [0:3];
  reg  signed [19:0] dly4_im [0:3];
  wire signed [19:0] do4_re = dly4_re[3];
  wire signed [19:0] do4_im = dly4_im[3];
  wire ph4 = cp3[2];
  wire [1:0] ix4 = cp3[1:0];
  reg signed [13:0] cr4, ci4;
  always @* case (ix4)
    2'd0: begin cr4 = 14'sd4096; ci4 = 14'sd0; end
    2'd1: begin cr4 = 14'sd2896; ci4 = -14'sd2896; end
    2'd2: begin cr4 = 14'sd0; ci4 = -14'sd4096; end
    2'd3: begin cr4 = -14'sd2896; ci4 = -14'sd2896; end
    default: begin cr4 = 14'sd4096; ci4 = 14'sd0; end
  endcase
  wire signed [18:0] i4_re = o3_re;
  wire signed [18:0] i4_im = o3_im;
  wire signed [20:0] su4_re = do4_re + i4_re;
  wire signed [20:0] su4_im = do4_im + i4_im;
  wire signed [20:0] df4_re = do4_re - i4_re;
  wire signed [20:0] df4_im = do4_im - i4_im;
  wire signed [19:0] dr4_re = df4_re[19:0];
  wire signed [19:0] dr4_im = df4_im[19:0];
  wire signed [33:0] pr4 = dr4_re * cr4;
  wire signed [33:0] pi4 = dr4_im * ci4;
  wire signed [33:0] qr4 = dr4_re * ci4;
  wire signed [33:0] qi4 = dr4_im * cr4;
  wire signed [34:0] zr4_f = {pr4[33],pr4} - {pi4[33],pi4} + 2048;
  wire signed [34:0] zi4_f = {qr4[33],qr4} + {qi4[33],qi4} + 2048;
  wire signed [19:0] zr4 = zr4_f[31:12];
  wire signed [19:0] zi4 = zi4_f[31:12];
  wire signed [19:0] nx4_re = ph4 ? zr4 : do4_re;
  wire signed [19:0] nx4_im = ph4 ? zi4 : do4_im;
  wire signed [19:0] wr4_re = ph4 ? su4_re[19:0] : {i4_re[18],i4_re};
  wire signed [19:0] wr4_im = ph4 ? su4_im[19:0] : {i4_im[18],i4_im};
  reg  signed [19:0] o4_re, o4_im;
  integer k4;
  always @(posedge clk) begin
    if (rst) begin
      for (k4=0; k4<4; k4=k4+1) begin
        dly4_re[k4] <= 20'sd0; dly4_im[k4] <= 20'sd0;
      end
      o4_re <= 20'sd0; o4_im <= 20'sd0;
    end else begin
      for (k4=3; k4>0; k4=k4-1) begin
        dly4_re[k4] <= dly4_re[k4-1];
        dly4_im[k4] <= dly4_im[k4-1];
      end
      dly4_re[0] <= wr4_re;
      dly4_im[0] <= wr4_im;
      o4_re <= nx4_re;
      o4_im <= nx4_im;
    end
  end

  // ---------------- stage 5: M=2 W=20 ----------------
  reg  signed [20:0] dly5_re [0:1];
  reg  signed [20:0] dly5_im [0:1];
  wire signed [20:0] do5_re = dly5_re[1];
  wire signed [20:0] do5_im = dly5_im[1];
  wire ph5 = cp4[1];
  wire [0:0] ix5 = cp4[0:0];
  reg signed [13:0] cr5, ci5;
  always @* case (ix5)
    1'd0: begin cr5 = 14'sd4096; ci5 = 14'sd0; end
    1'd1: begin cr5 = 14'sd0; ci5 = -14'sd4096; end
    default: begin cr5 = 14'sd4096; ci5 = 14'sd0; end
  endcase
  wire signed [19:0] i5_re = o4_re;
  wire signed [19:0] i5_im = o4_im;
  wire signed [21:0] su5_re = do5_re + i5_re;
  wire signed [21:0] su5_im = do5_im + i5_im;
  wire signed [21:0] df5_re = do5_re - i5_re;
  wire signed [21:0] df5_im = do5_im - i5_im;
  wire signed [20:0] dr5_re = df5_re[20:0];
  wire signed [20:0] dr5_im = df5_im[20:0];
  wire signed [34:0] pr5 = dr5_re * cr5;
  wire signed [34:0] pi5 = dr5_im * ci5;
  wire signed [34:0] qr5 = dr5_re * ci5;
  wire signed [34:0] qi5 = dr5_im * cr5;
  wire signed [35:0] zr5_f = {pr5[34],pr5} - {pi5[34],pi5} + 2048;
  wire signed [35:0] zi5_f = {qr5[34],qr5} + {qi5[34],qi5} + 2048;
  wire signed [20:0] zr5 = zr5_f[32:12];
  wire signed [20:0] zi5 = zi5_f[32:12];
  wire signed [20:0] nx5_re = ph5 ? zr5 : do5_re;
  wire signed [20:0] nx5_im = ph5 ? zi5 : do5_im;
  wire signed [20:0] wr5_re = ph5 ? su5_re[20:0] : {i5_re[19],i5_re};
  wire signed [20:0] wr5_im = ph5 ? su5_im[20:0] : {i5_im[19],i5_im};
  reg  signed [20:0] o5_re, o5_im;
  integer k5;
  always @(posedge clk) begin
    if (rst) begin
      for (k5=0; k5<2; k5=k5+1) begin
        dly5_re[k5] <= 21'sd0; dly5_im[k5] <= 21'sd0;
      end
      o5_re <= 21'sd0; o5_im <= 21'sd0;
    end else begin
      for (k5=1; k5>0; k5=k5-1) begin
        dly5_re[k5] <= dly5_re[k5-1];
        dly5_im[k5] <= dly5_im[k5-1];
      end
      dly5_re[0] <= wr5_re;
      dly5_im[0] <= wr5_im;
      o5_re <= nx5_re;
      o5_im <= nx5_im;
    end
  end

  // ---------------- stage 6: M=1 W=21 ----------------
  reg  signed [21:0] dly6_re [0:0];
  reg  signed [21:0] dly6_im [0:0];
  wire signed [21:0] do6_re = dly6_re[0];
  wire signed [21:0] do6_im = dly6_im[0];
  wire ph6 = cp5[0];
  wire ix6 = 1'b0;
  reg signed [13:0] cr6, ci6;
  always @* case (ix6)
    default: begin cr6 = 14'sd4096; ci6 = 14'sd0; end
  endcase
  wire signed [20:0] i6_re = o5_re;
  wire signed [20:0] i6_im = o5_im;
  wire signed [22:0] su6_re = do6_re + i6_re;
  wire signed [22:0] su6_im = do6_im + i6_im;
  wire signed [22:0] df6_re = do6_re - i6_re;
  wire signed [22:0] df6_im = do6_im - i6_im;
  wire signed [21:0] dr6_re = df6_re[21:0];
  wire signed [21:0] dr6_im = df6_im[21:0];
  wire signed [35:0] pr6 = dr6_re * cr6;
  wire signed [35:0] pi6 = dr6_im * ci6;
  wire signed [35:0] qr6 = dr6_re * ci6;
  wire signed [35:0] qi6 = dr6_im * cr6;
  wire signed [36:0] zr6_f = {pr6[35],pr6} - {pi6[35],pi6} + 2048;
  wire signed [36:0] zi6_f = {qr6[35],qr6} + {qi6[35],qi6} + 2048;
  wire signed [21:0] zr6 = zr6_f[33:12];
  wire signed [21:0] zi6 = zi6_f[33:12];
  wire signed [21:0] nx6_re = ph6 ? zr6 : do6_re;
  wire signed [21:0] nx6_im = ph6 ? zi6 : do6_im;
  wire signed [21:0] wr6_re = ph6 ? su6_re[21:0] : {i6_re[20],i6_re};
  wire signed [21:0] wr6_im = ph6 ? su6_im[21:0] : {i6_im[20],i6_im};
  reg  signed [21:0] o6_re, o6_im;
  integer k6;
  always @(posedge clk) begin
    if (rst) begin
      for (k6=0; k6<1; k6=k6+1) begin
        dly6_re[k6] <= 22'sd0; dly6_im[k6] <= 22'sd0;
      end
      o6_re <= 22'sd0; o6_im <= 22'sd0;
    end else begin
      for (k6=0; k6>0; k6=k6-1) begin
        dly6_re[k6] <= dly6_re[k6-1];
        dly6_im[k6] <= dly6_im[k6-1];
      end
      dly6_re[0] <= wr6_re;
      dly6_im[0] <= wr6_im;
      o6_re <= nx6_re;
      o6_im <= nx6_im;
    end
  end

  // ---------------- output reorder: bit-reversal frame buffer ----------------
  reg signed [21:0] rb_re [0:63];
  reg signed [21:0] rb_im [0:63];
  wire       wr_en = (cp6 >= 8'd63) && (cp6 <= 8'd126);
  wire [5:0] wt  = cp6[5:0] - 6'd63;
  wire [5:0] wad = ~{wt[0],wt[1],wt[2],wt[3],wt[4],wt[5]};

  // emission arm: shift register delays the frame start by COFF cycles
  reg [COFF:0] arm_sr;
  always @(posedge clk) begin
    if (rst) arm_sr <= 0;
    else     arm_sr <= {arm_sr[COFF-1:0], start};
  end
  wire emit_arm = arm_sr[COFF];

  reg        emit;
  reg [5:0]  eidx;
  always @(posedge clk) begin
    if (rst) begin
      emit <= 1'b0; eidx <= 6'd0;
    end else if (emit_arm) begin
      emit <= 1'b1; eidx <= 6'd0;
    end else if (emit) begin
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
