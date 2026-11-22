module rf64x44_1r1w (input clk, input we, input [5:0] wa, input [43:0] d, input [5:0] ra, output [43:0] q);
  reg [43:0] m [0:63];
  always @(posedge clk) if (we) m[wa] <= d;
  assign q = m[ra];
endmodule
module rf32x44_1r1w (input clk, input we, input [4:0] wa, input [43:0] d, input [4:0] ra, output [43:0] q);
  reg [43:0] m [0:31];
  always @(posedge clk) if (we) m[wa] <= d;
  assign q = m[ra];
endmodule
module rf32x44_2r2w (input clk, input wea, input web, input [4:0] wa, input [4:0] wb, input [43:0] da, input [43:0] db, input [4:0] ra, input [4:0] rb, output [43:0] qa, output [43:0] qb);
  reg [43:0] m [0:31];
  always @(posedge clk) begin
    if (wea) m[wa] <= da;
    if (web) m[wb] <= db;
  end
  assign qa = m[ra];
  assign qb = m[rb];
endmodule
module rf64x44_1r1w_banked (input clk, input we, input [5:0] wa, input [43:0] d, input [5:0] ra, output [43:0] q);
  reg [43:0] m0 [0:31]; reg [43:0] m1 [0:31];
  always @(posedge clk) if (we) begin if (wa[5]) m1[wa[4:0]] <= d; else m0[wa[4:0]] <= d; end
  assign q = ra[5] ? m1[ra[4:0]] : m0[ra[4:0]];
endmodule
module rf64x88_1r1w (input clk, input we, input [5:0] wa, input [87:0] d, input [5:0] ra, output [87:0] q);
  reg [87:0] m [0:63];
  always @(posedge clk) if (we) m[wa] <= d;
  assign q = m[ra];
endmodule
module rf64x44_2r2w_indep (input clk, input we, input [5:0] wa, input [43:0] da, input [43:0] db, input [5:0] ra1, input [5:0] ra2, output [43:0] qa, output [43:0] qb);
  reg [43:0] m [0:63];
  always @(posedge clk) if (we) m[wa] <= da;
  assign qa = m[ra1];
  assign qb = m[ra2];
endmodule
// butterfly + 3-mult complex multiply + round, 22-bit
module bfly (input signed [21:0] ur, input signed [21:0] ui, input signed [21:0] vr, input signed [21:0] vi,
             input signed [15:0] wr, input signed [15:0] wi,
             output signed [21:0] ar, output signed [21:0] ai, output signed [21:0] br, output signed [21:0] bi);
  wire signed [22:0] s1 = ur + ui;
  wire signed [22:0] s2 = wi - wr;
  wire signed [22:0] s3 = wr + wi;
  wire signed [38:0] t1 = s1*wr;
  wire signed [38:0] t2 = vr*s2;
  wire signed [38:0] t3 = vi*s3;
  wire signed [38:0] pr = t1 - t3;
  wire signed [38:0] pi = t1 + t2;
  wire signed [22:0] prr = (pr + 39'sd16384) >>> 15;
  wire signed [22:0] pir = (pi + 39'sd16384) >>> 15;
  assign ar = ur + prr[21:0];
  assign ai = ui + pir[21:0];
  assign br = ur - prr[21:0];
  assign bi = ui - pir[21:0];
endmodule
