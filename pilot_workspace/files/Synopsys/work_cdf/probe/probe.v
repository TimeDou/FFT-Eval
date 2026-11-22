// Area calibration probes for ASAP7 mapping
module mul16 (input signed [15:0] a, input signed [15:0] b, output signed [31:0] p);
  assign p = a*b;
endmodule
module mul22x16 (input signed [21:0] a, input signed [15:0] b, output signed [37:0] p);
  assign p = a*b;
endmodule
module mul22x22 (input signed [21:0] a, input signed [21:0] b, output signed [43:0] p);
  assign p = a*b;
endmodule
module cplxmul (input signed [21:0] ar, input signed [21:0] ai,
                input signed [15:0] br, input signed [15:0] bi,
                output signed [37:0] pr, output signed [37:0] pi);
  assign pr = ar*br - ai*bi;
  assign pi = ar*bi + ai*br;
endmodule
module cplxmul3 (input signed [21:0] ar, input signed [21:0] ai,
                 input signed [15:0] br, input signed [15:0] bi,
                 output signed [37:0] pr, output signed [37:0] pi);
  wire signed [21:0] t1, t2, t3;
  assign t1 = (ar+ai)*br;
  assign t2 = ar*(bi-br);
  assign t3 = ai*(br+bi);
  assign pr = t1 - t3;
  assign pi = t1 + t2;
endmodule
module add22 (input signed [21:0] a, input signed [21:0] b, output signed [21:0] s);
  assign s = a+b;
endmodule
module regs44 (input clk, input [43:0] d, output reg [43:0] q);
  always @(posedge clk) q <= d;
endmodule
// 64-word x 44-bit register file, 2 read ports, 2 write ports
module rf64x44 (input clk, input wea, input web, input [5:0] ra, input [5:0] rb, input [5:0] wa, input [5:0] wb,
                input [43:0] da, input [43:0] db, output [43:0] qa, output [43:0] qb);
  reg [43:0] m [0:63];
  integer i;
  always @(posedge clk) begin
    if (wea) m[wa] <= da;
    if (web) m[wb] <= db;
  end
  assign qa = m[ra];
  assign qb = m[rb];
endmodule
// 57-word x 44-bit shift register with per-word enable
module sr57x44 (input clk, input en, input [43:0] di, output [43:0] q);
  reg [43:0] s [0:56];
  integer i;
  always @(posedge clk) if (en) begin
    for (i=56;i>0;i=i-1) s[i] <= s[i-1];
    s[0] <= di;
  end
  assign q = s[56];
endmodule
module mux64x44 (input [43:0] d0,d1,d2,d3,d4,d5,d6,d7,d8,d9,d10,d11,d12,d13,d14,d15,
                 input [5:0] sel, output reg [43:0] q);
  reg [43:0] mem [0:63];
  always @* q = mem[sel];
endmodule
