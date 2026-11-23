// Generated R2^3 SDF FFT64 (DIF) with bit-reversal reorder; config:
// {"m": [0, 1, 1, 2, 2, 3, 5], "mA": 1, "mB": 2, "mC": 3, "tb": 9, "k8": 8, "R3": 4, "R4": 5, "R6": 4, "bf_round": [0, 0, 0, 0, 0, 1], "altpol": 1, "exact_widths": 1, "clamp15": 1, "negmerge": 1, "noreg6": 1, "smallctl": 1}

module sdf_stage1(input clk, input mode, input signed [14:0] br, input signed [14:0] bi,
  output reg signed [14:0] yr, output reg signed [14:0] yi);
  reg [479:0] dlr, dli;
  wire [14:0] qr = ~dlr[479:465];
  wire [14:0] qi = ~dli[479:465];
  wire signed [14:0] ar = qr[14:0];
  wire signed [14:0] ai = qi[14:0];
  wire signed [14:0] cr = qr[14:0];
  wire signed [14:0] ci = qi[14:0];
  wire signed [31:0] sr = ar + br;
  wire signed [31:0] dr = ar - br;
  wire signed [31:0] si = ai + bi;
  wire signed [31:0] di = ai - bi;
  wire signed [31:0] srq = sr >>> 1;
  wire signed [31:0] siq = si >>> 1;
  wire signed [31:0] drq = dr >>> 1;
  wire signed [31:0] diq = di >>> 1;
  wire signed [31:0] siq2 = siq;
  wire signed [31:0] diq2 = diq;
  wire [14:0] nr = (mode ? drq[14:0] : br);
  wire [14:0] ni = (mode ? diq2[14:0] : bi);
  always @(posedge clk) begin
    dlr <= {~dlr[464:0], nr}; dli <= {~dli[464:0], ni};
    yr <= mode ? srq[14:0] : cr;
    yi <= mode ? siq2[14:0] : ci;
  end
endmodule

module sdf_stage2(input clk, input mode, input ngi, input signed [15:0] br, input signed [15:0] bi,
  output reg signed [15:0] yr, output reg signed [15:0] yi);
  reg [255:0] dlr, dli;
  wire [15:0] qr = ~dlr[255:240];
  wire [15:0] qi = ~dli[255:240];
  wire signed [15:0] ar = qr[15:0];
  wire signed [15:0] ai = qi[15:0];
  wire signed [15:0] cr = qr[15:0];
  wire signed [15:0] ci = qi[15:0];
  wire signed [31:0] sr = ar + br;
  wire signed [31:0] dr = ar - br;
  wire signed [31:0] si = ai + bi;
  wire signed [31:0] di = ai - bi;
  wire signed [31:0] srq = sr >>> 0;
  wire signed [31:0] siq = si >>> 0;
  wire signed [31:0] drq = dr >>> 0;
  wire signed [31:0] diq = di >>> 0;
  wire signed [31:0] siq2 = ngi ? diq : siq;
  wire signed [31:0] diq2 = ngi ? siq : diq;
  wire [15:0] nr = (mode ? drq[15:0] : br);
  wire [15:0] ni = (mode ? diq2[15:0] : bi);
  always @(posedge clk) begin
    dlr <= {~dlr[239:0], nr}; dli <= {~dli[239:0], ni};
    yr <= mode ? srq[15:0] : cr;
    yi <= mode ? siq2[15:0] : ci;
  end
endmodule

module sdf_stage3(input clk, input mode, input ngi, input signed [16:0] br, input signed [16:0] bi,
  output reg signed [16:0] yr, output reg signed [16:0] yi);
  reg [135:0] dlr, dli;
  wire [16:0] qr = ~dlr[135:119];
  wire [16:0] qi = ~dli[135:119];
  wire signed [16:0] ar = qr[16:0];
  wire signed [16:0] ai = qi[16:0];
  wire signed [16:0] cr = qr[16:0];
  wire signed [16:0] ci = qi[16:0];
  wire signed [31:0] sr = ar + br;
  wire signed [31:0] dr = ar - br;
  wire signed [31:0] si = ai + bi;
  wire signed [31:0] di = ai - bi;
  wire signed [31:0] srq = sr >>> 1;
  wire signed [31:0] siq = si >>> 1;
  wire signed [31:0] drq = dr >>> 1;
  wire signed [31:0] diq = di >>> 1;
  wire signed [31:0] siq2 = ngi ? diq : siq;
  wire signed [31:0] diq2 = ngi ? siq : diq;
  wire [16:0] nr = (mode ? drq[16:0] : br);
  wire [16:0] ni = (mode ? diq2[16:0] : bi);
  always @(posedge clk) begin
    dlr <= {~dlr[118:0], nr}; dli <= {~dli[118:0], ni};
    yr <= mode ? srq[16:0] : cr;
    yi <= mode ? siq2[16:0] : ci;
  end
endmodule

module sdf_stage4(input clk, input mode, input ngi, input signed [16:0] br, input signed [16:0] bi,
  output reg signed [17:0] yr, output reg signed [17:0] yi);
  reg [71:0] dlr, dli;
  wire [17:0] qr = ~dlr[71:54];
  wire [17:0] qi = ~dli[71:54];
  wire signed [16:0] ar = qr[16:0];
  wire signed [16:0] ai = qi[16:0];
  wire signed [17:0] cr = qr[17:0];
  wire signed [17:0] ci = qi[17:0];
  wire signed [31:0] sr = ar + br;
  wire signed [31:0] dr = ar - br;
  wire signed [31:0] si = ai + bi;
  wire signed [31:0] di = ai - bi;
  wire signed [31:0] srq = sr >>> 0;
  wire signed [31:0] siq = si >>> 0;
  wire signed [31:0] drq = dr >>> 0;
  wire signed [31:0] diq = di >>> 0;
  wire signed [31:0] siq2 = ngi ? diq : siq;
  wire signed [31:0] diq2 = ngi ? siq : diq;
  wire [17:0] nr = {drq[17:17], (mode ? drq[16:0] : br)};
  wire [17:0] ni = {diq2[17:17], (mode ? diq2[16:0] : bi)};
  always @(posedge clk) begin
    dlr <= {~dlr[53:0], nr}; dli <= {~dli[53:0], ni};
    yr <= mode ? srq[17:0] : cr;
    yi <= mode ? siq2[17:0] : ci;
  end
endmodule

module sdf_stage5(input clk, input mode, input ngi, input signed [17:0] br, input signed [17:0] bi,
  output reg signed [17:0] yr, output reg signed [17:0] yi);
  reg [35:0] dlr, dli;
  wire [17:0] qr = ~dlr[35:18];
  wire [17:0] qi = ~dli[35:18];
  wire signed [17:0] ar = qr[17:0];
  wire signed [17:0] ai = qi[17:0];
  wire signed [17:0] cr = qr[17:0];
  wire signed [17:0] ci = qi[17:0];
  wire signed [31:0] sr = ar + br;
  wire signed [31:0] dr = ar - br;
  wire signed [31:0] si = ai + bi;
  wire signed [31:0] di = ai - bi;
  wire signed [31:0] srq = sr >>> 1;
  wire signed [31:0] siq = si >>> 1;
  wire signed [31:0] drq = dr >>> 1;
  wire signed [31:0] diq = di >>> 1;
  wire signed [31:0] siq2 = ngi ? diq : siq;
  wire signed [31:0] diq2 = ngi ? siq : diq;
  wire [17:0] nr = (mode ? drq[17:0] : br);
  wire [17:0] ni = (mode ? diq2[17:0] : bi);
  always @(posedge clk) begin
    dlr <= {~dlr[17:0], nr}; dli <= {~dli[17:0], ni};
    yr <= mode ? srq[17:0] : cr;
    yi <= mode ? siq2[17:0] : ci;
  end
endmodule

module sdf_stage6(input clk, input mode, input ngi, input signed [17:0] br, input signed [17:0] bi,
  output signed [16:0] yr, output signed [16:0] yi);
  reg [17:0] dlr, dli;
  wire [17:0] qr = dlr[17:0];
  wire [17:0] qi = dli[17:0];
  wire signed [17:0] ar = qr[17:0];
  wire signed [17:0] ai = qi[17:0];
  wire signed [16:0] cr = qr[16:0];
  wire signed [16:0] ci = qi[16:0];
  wire signed [31:0] sr = ar + br;
  wire signed [31:0] dr = ar - br;
  wire signed [31:0] si = ai + bi;
  wire signed [31:0] di = ai - bi;
  wire signed [31:0] srq = (sr + 2) >>> 2;
  wire signed [31:0] siq = (si + 2) >>> 2;
  wire signed [31:0] drq = (dr + 2) >>> 2;
  wire signed [31:0] diq = (di + 2) >>> 2;
  wire signed [31:0] siq2 = ngi ? diq : siq;
  wire signed [31:0] diq2 = ngi ? siq : diq;
  wire [17:0] nr = {br[17:17], (mode ? drq[16:0] : br[16:0])};
  wire [17:0] ni = {bi[17:17], (mode ? diq2[16:0] : bi[16:0])};
  assign yr = mode ? srq[16:0] : cr;
  assign yi = mode ? siq2[16:0] : ci;
  always @(posedge clk) begin
    dlr <= nr; dli <= ni;
  end
endmodule

module w8rot3(input clk, input [1:0] sel, input signed [15:0] xr, input signed [15:0] xi,
  output signed [16:0] zr, output signed [16:0] zi, output zn);
  wire signed [31:0] u = xr + xi;
  wire signed [31:0] v = xi - xr;
  wire signed [31:0] ur = (u * 181 + 128) >>> 8;
  wire signed [31:0] vr = (v * 181 + 128) >>> 8;
  wire signed [31:0] tr = xr >>> 0;
  wire signed [31:0] ti = xi >>> 0;
  reg signed [31:0] or_, oi;
  always @(*) begin
    case (sel)
      2'd0: begin or_ = tr; oi = ti; end
      2'd1: begin or_ = ur; oi = vr; end
      2'd2: begin or_ = ti; oi = tr; end
      default: begin or_ = vr; oi = ur; end
    endcase
  end
  reg signed [16:0] p0r, p0i; reg p0n;
  always @(posedge clk) begin p0r <= or_[16:0]; p0i <= oi[16:0]; p0n <= sel[1]; end
  reg signed [16:0] p1r, p1i; reg p1n;
  always @(posedge clk) begin p1r <= p0r; p1i <= p0i; p1n <= p0n; end
  reg signed [16:0] p2r, p2i; reg p2n;
  always @(posedge clk) begin p2r <= p1r; p2i <= p1i; p2n <= p1n; end
  reg signed [16:0] p3r, p3i; reg p3n;
  always @(posedge clk) begin p3r <= p2r; p3i <= p2i; p3n <= p2n; end
  assign zr = p3r;
  assign zi = p3i;
  assign zn = p3n;
endmodule

module w8rot6(input clk, input [1:0] sel, input signed [17:0] xr, input signed [17:0] xi,
  output signed [17:0] zr, output signed [17:0] zi, output zn);
  wire signed [31:0] u = xr + xi;
  wire signed [31:0] v = xi - xr;
  wire signed [31:0] ur = (u * 181 + 128) >>> 8;
  wire signed [31:0] vr = (v * 181 + 128) >>> 8;
  wire signed [31:0] tr = xr >>> 0;
  wire signed [31:0] ti = xi >>> 0;
  reg signed [31:0] or_, oi;
  always @(*) begin
    case (sel)
      2'd0: begin or_ = tr; oi = ti; end
      2'd1: begin or_ = ur; oi = vr; end
      2'd2: begin or_ = ti; oi = tr; end
      default: begin or_ = vr; oi = ur; end
    endcase
  end
  reg signed [17:0] p0r, p0i; reg p0n;
  always @(posedge clk) begin p0r <= or_[17:0]; p0i <= oi[17:0]; p0n <= sel[1]; end
  reg signed [17:0] p1r, p1i; reg p1n;
  always @(posedge clk) begin p1r <= p0r; p1i <= p0i; p1n <= p0n; end
  reg signed [17:0] p2r, p2i; reg p2n;
  always @(posedge clk) begin p2r <= p1r; p2i <= p1i; p2n <= p1n; end
  reg signed [17:0] p3r, p3i; reg p3n;
  always @(posedge clk) begin p3r <= p2r; p3i <= p2i; p3n <= p2n; end
  assign zr = p3r;
  assign zi = p3i;
  assign zn = p3n;
endmodule

module w64mul(input clk, input [5:0] q, input signed [16:0] xr, input signed [16:0] xi,
  output signed [16:0] zr, output signed [16:0] zi, output zn);
  reg signed [9:0] C, S;
  reg t0, t16;
  always @(*) begin
    case (q)
      6'd0: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd1: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd2: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd3: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd4: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd5: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd6: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd7: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd8: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd9: begin C = 10'sd473; S = -10'sd196; t0 = 1'b0; t16 = 1'b0; end
      6'd10: begin C = 10'sd362; S = -10'sd362; t0 = 1'b0; t16 = 1'b0; end
      6'd11: begin C = 10'sd196; S = -10'sd473; t0 = 1'b0; t16 = 1'b0; end
      6'd12: begin C = 10'sd0; S = 10'sd0; t0 = 1'b0; t16 = 1'b1; end
      6'd13: begin C = -10'sd196; S = -10'sd473; t0 = 1'b0; t16 = 1'b0; end
      6'd14: begin C = -10'sd362; S = -10'sd362; t0 = 1'b0; t16 = 1'b0; end
      6'd15: begin C = -10'sd473; S = -10'sd196; t0 = 1'b0; t16 = 1'b0; end
      6'd16: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd17: begin C = 10'sd502; S = -10'sd100; t0 = 1'b0; t16 = 1'b0; end
      6'd18: begin C = 10'sd473; S = -10'sd196; t0 = 1'b0; t16 = 1'b0; end
      6'd19: begin C = 10'sd426; S = -10'sd284; t0 = 1'b0; t16 = 1'b0; end
      6'd20: begin C = 10'sd362; S = -10'sd362; t0 = 1'b0; t16 = 1'b0; end
      6'd21: begin C = 10'sd284; S = -10'sd426; t0 = 1'b0; t16 = 1'b0; end
      6'd22: begin C = 10'sd196; S = -10'sd473; t0 = 1'b0; t16 = 1'b0; end
      6'd23: begin C = 10'sd100; S = -10'sd502; t0 = 1'b0; t16 = 1'b0; end
      6'd24: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd25: begin C = 10'sd426; S = -10'sd284; t0 = 1'b0; t16 = 1'b0; end
      6'd26: begin C = 10'sd196; S = -10'sd473; t0 = 1'b0; t16 = 1'b0; end
      6'd27: begin C = -10'sd100; S = -10'sd502; t0 = 1'b0; t16 = 1'b0; end
      6'd28: begin C = -10'sd362; S = -10'sd362; t0 = 1'b0; t16 = 1'b0; end
      6'd29: begin C = -10'sd502; S = -10'sd100; t0 = 1'b0; t16 = 1'b0; end
      6'd30: begin C = -10'sd473; S = 10'sd196; t0 = 1'b0; t16 = 1'b0; end
      6'd31: begin C = -10'sd284; S = 10'sd426; t0 = 1'b0; t16 = 1'b0; end
      6'd32: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd33: begin C = 10'sd510; S = -10'sd50; t0 = 1'b0; t16 = 1'b0; end
      6'd34: begin C = 10'sd502; S = -10'sd100; t0 = 1'b0; t16 = 1'b0; end
      6'd35: begin C = 10'sd490; S = -10'sd149; t0 = 1'b0; t16 = 1'b0; end
      6'd36: begin C = 10'sd473; S = -10'sd196; t0 = 1'b0; t16 = 1'b0; end
      6'd37: begin C = 10'sd452; S = -10'sd241; t0 = 1'b0; t16 = 1'b0; end
      6'd38: begin C = 10'sd426; S = -10'sd284; t0 = 1'b0; t16 = 1'b0; end
      6'd39: begin C = 10'sd396; S = -10'sd325; t0 = 1'b0; t16 = 1'b0; end
      6'd40: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd41: begin C = 10'sd452; S = -10'sd241; t0 = 1'b0; t16 = 1'b0; end
      6'd42: begin C = 10'sd284; S = -10'sd426; t0 = 1'b0; t16 = 1'b0; end
      6'd43: begin C = 10'sd50; S = -10'sd510; t0 = 1'b0; t16 = 1'b0; end
      6'd44: begin C = -10'sd196; S = -10'sd473; t0 = 1'b0; t16 = 1'b0; end
      6'd45: begin C = -10'sd396; S = -10'sd325; t0 = 1'b0; t16 = 1'b0; end
      6'd46: begin C = -10'sd502; S = -10'sd100; t0 = 1'b0; t16 = 1'b0; end
      6'd47: begin C = -10'sd490; S = 10'sd149; t0 = 1'b0; t16 = 1'b0; end
      6'd48: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd49: begin C = 10'sd490; S = -10'sd149; t0 = 1'b0; t16 = 1'b0; end
      6'd50: begin C = 10'sd426; S = -10'sd284; t0 = 1'b0; t16 = 1'b0; end
      6'd51: begin C = 10'sd325; S = -10'sd396; t0 = 1'b0; t16 = 1'b0; end
      6'd52: begin C = 10'sd196; S = -10'sd473; t0 = 1'b0; t16 = 1'b0; end
      6'd53: begin C = 10'sd50; S = -10'sd510; t0 = 1'b0; t16 = 1'b0; end
      6'd54: begin C = -10'sd100; S = -10'sd502; t0 = 1'b0; t16 = 1'b0; end
      6'd55: begin C = -10'sd241; S = -10'sd452; t0 = 1'b0; t16 = 1'b0; end
      6'd56: begin C = 10'sd0; S = 10'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd57: begin C = 10'sd396; S = -10'sd325; t0 = 1'b0; t16 = 1'b0; end
      6'd58: begin C = 10'sd100; S = -10'sd502; t0 = 1'b0; t16 = 1'b0; end
      6'd59: begin C = -10'sd241; S = -10'sd452; t0 = 1'b0; t16 = 1'b0; end
      6'd60: begin C = -10'sd473; S = -10'sd196; t0 = 1'b0; t16 = 1'b0; end
      6'd61: begin C = -10'sd490; S = 10'sd149; t0 = 1'b0; t16 = 1'b0; end
      6'd62: begin C = -10'sd284; S = 10'sd426; t0 = 1'b0; t16 = 1'b0; end
      6'd63: begin C = 10'sd50; S = 10'sd510; t0 = 1'b0; t16 = 1'b0; end
      default: begin C = 0; S = 0; t0 = 1'b0; t16 = 1'b0; end
    endcase
  end
  wire signed [31:0] pr = xr * C - xi * S;
  wire signed [31:0] pi = xr * S + xi * C;
  wire signed [31:0] prr = (pr + 256) >>> 9;
  wire signed [31:0] pir = (pi + 256) >>> 9;
  wire signed [31:0] tr = xr >>> 0;
  wire signed [31:0] ti = xi >>> 0;
  wire signed [31:0] or_ = t0 ? tr : (t16 ? ti : prr);
  wire signed [31:0] oi = t0 ? ti : (t16 ? tr : pir);
  reg signed [16:0] p0r, p0i; reg p0n;
  always @(posedge clk) begin p0r <= or_[16:0]; p0i <= oi[16:0]; p0n <= t16; end
  reg signed [16:0] p1r, p1i; reg p1n;
  always @(posedge clk) begin p1r <= p0r; p1i <= p0i; p1n <= p0n; end
  reg signed [16:0] p2r, p2i; reg p2n;
  always @(posedge clk) begin p2r <= p1r; p2i <= p1i; p2n <= p1n; end
  reg signed [16:0] p3r, p3i; reg p3n;
  always @(posedge clk) begin p3r <= p2r; p3i <= p2i; p3n <= p2n; end
  reg signed [16:0] p4r, p4i; reg p4n;
  always @(posedge clk) begin p4r <= p3r; p4i <= p3i; p4n <= p3n; end
  assign zr = p4r;
  assign zi = p4i;
  assign zn = p4n;
endmodule

module bswap32(input clk, input c, input [33:0] u, output [33:0] v);
  reg [135:0] dl;
  wire [33:0] o = ~dl[135:102];
  wire [33:0] n = c ? o : u;
  always @(posedge clk) dl <= {~dl[101:0], n};
  assign v = c ? u : o;
endmodule

module bswap41(input clk, input c, input [33:0] u, output [33:0] v);
  reg [475:0] dl;
  wire [33:0] o = ~dl[475:442];
  wire [33:0] n = c ? o : u;
  always @(posedge clk) dl <= {~dl[441:0], n};
  assign v = c ? u : o;
endmodule

module bswap50(input clk, input c, input [33:0] u, output [33:0] v);
  reg [1053:0] dl;
  wire [33:0] o = dl[1053:1020];
  wire [33:0] n = c ? o : u;
  always @(posedge clk) dl <= {~dl[1019:0], n};
  assign v = c ? u : o;
endmodule

module segctl #(parameter OFF = 0, parameter TRIG = 0, parameter NB = 6) (
  input clk, input rst, input st, output [NB-1:0] pos, output reg nxt);
  localparam [NB-1:0] OFFV = OFF;
  localparam [NB-1:0] TRIGV = TRIG;
  reg [NB-1:0] cnt;
  reg pend;
  assign pos = st ? OFFV : cnt;
  wire hit = pend & (pos == TRIGV);
  always @(posedge clk) begin
    cnt <= pos + 1'b1;
    if (rst) begin pend <= 1'b0; nxt <= 1'b0; end
    else begin nxt <= hit; pend <= st | (pend & ~hit); end
  end
endmodule

module fft64_top(input wire clk, input wire rst, input wire in_valid, input wire frame_start,
  input wire signed [15:0] in_re, input wire signed [15:0] in_im,
  output wire out_valid, output wire out_start, output wire signed [23:0] out_re, output wire signed [23:0] out_im);
  wire st1 = in_valid & frame_start;
  wire [5:0] pos1; wire st2;
  segctl #(.OFF(0), .TRIG(32), .NB(6)) ctl1(.clk(clk), .rst(rst), .st(st1), .pos(pos1), .nxt(st2));
  wire md1 = pos1[5];
  wire [5:0] pos2; wire st3;
  segctl #(.OFF(0), .TRIG(16), .NB(6)) ctl2(.clk(clk), .rst(rst), .st(st2), .pos(pos2), .nxt(st3));
  wire md2 = pos2[4];
  wire [5:0] pos3; wire st4;
  segctl #(.OFF(0), .TRIG(12), .NB(6)) ctl3(.clk(clk), .rst(rst), .st(st3), .pos(pos3), .nxt(st4));
  reg [3:0] mdp3;
  always @(posedge clk) mdp3 <= {mdp3[2:0], pos3[3]};
  wire md3 = mdp3[3];
  wire [5:0] pos4; wire st5;
  segctl #(.OFF(0), .TRIG(9), .NB(6)) ctl4(.clk(clk), .rst(rst), .st(st4), .pos(pos4), .nxt(st5));
  reg [4:0] mdp4;
  always @(posedge clk) mdp4 <= {mdp4[3:0], pos4[2]};
  wire md4 = mdp4[4];
  wire [5:0] pos5; wire st6;
  wire [2:0] pss5;
  segctl #(.OFF(0), .TRIG(2), .NB(3)) ctl5(.clk(clk), .rst(rst), .st(st5), .pos(pss5), .nxt(st6));
  assign pos5 = {3'b0, pss5};
  wire md5 = pos5[1];
  wire [5:0] pos6; wire st7;
  wire [2:0] pss6;
  segctl #(.OFF(0), .TRIG(4), .NB(3)) ctl6(.clk(clk), .rst(rst), .st(st6), .pos(pss6), .nxt(st7));
  assign pos6 = {3'b0, pss6};
  reg [3:0] mdp6;
  always @(posedge clk) mdp6 <= {mdp6[2:0], pos6[0]};
  wire md6 = mdp6[3];
  wire signed [14:0] cin_re = {in_re[15], in_re[13:0] | {14{in_re[14] & ~in_re[15]}}};
  wire signed [14:0] cin_im = {in_im[15], in_im[13:0] | {14{in_im[14] & ~in_im[15]}}};
  wire signed [14:0] x0r = cin_re >>> 0;
  wire signed [14:0] x0i = cin_im >>> 0;
  wire signed [14:0] y1r, y1i;
  sdf_stage1 u_s1(.clk(clk), .mode(md1), .br(x0r), .bi(x0i), .yr(y1r), .yi(y1i));
  wire j2 = pos2[5] & pos2[4];
  wire signed [15:0] b2r = j2 ? y1i : y1r;
  wire signed [15:0] b2i = j2 ? y1r : y1i;
  wire signed [15:0] y2r, y2i;
  sdf_stage2 u_s2(.clk(clk), .mode(md2), .ngi(j2), .br(b2r), .bi(b2i), .yr(y2r), .yi(y2i));
  wire [5:0] q3 = pos3;
  wire [1:0] sel3 = q3[3] ? {q3[4], q3[5]} : 2'd0;
  wire signed [16:0] b3r, b3i; wire n3;
  w8rot3 u_r3(.clk(clk), .sel(sel3), .xr(y2r), .xi(y2i), .zr(b3r), .zi(b3i), .zn(n3));
  wire signed [16:0] y3r, y3i;
  sdf_stage3 u_s3(.clk(clk), .mode(md3), .ngi(n3), .br(b3r), .bi(b3i), .yr(y3r), .yi(y3i));
  wire [5:0] q4 = pos4;
  wire signed [16:0] b4r, b4i; wire n4;
  w64mul u_m4(.clk(clk), .q(q4), .xr(y3r), .xi(y3i), .zr(b4r), .zi(b4i), .zn(n4));
  wire signed [17:0] y4r, y4i;
  sdf_stage4 u_s4(.clk(clk), .mode(md4), .ngi(n4), .br(b4r), .bi(b4i), .yr(y4r), .yi(y4i));
  wire j5 = pos5[1] & pos5[2];
  wire signed [17:0] b5r = j5 ? y4i : y4r;
  wire signed [17:0] b5i = j5 ? y4r : y4i;
  wire signed [17:0] y5r, y5i;
  sdf_stage5 u_s5(.clk(clk), .mode(md5), .ngi(j5), .br(b5r), .bi(b5i), .yr(y5r), .yi(y5i));
  wire [5:0] q6 = pos6;
  wire [1:0] sel6 = q6[0] ? {q6[1], q6[2]} : 2'd0;
  wire signed [17:0] b6r, b6i; wire n6;
  w8rot6 u_r6(.clk(clk), .sel(sel6), .xr(y5r), .xi(y5i), .zr(b6r), .zi(b6i), .zn(n6));
  wire signed [16:0] y6r, y6i;
  sdf_stage6 u_s6(.clk(clk), .mode(md6), .ngi(n6), .br(b6r), .bi(b6i), .yr(y6r), .yi(y6i));
  wire [3:0] pe32; wire ste41;
  segctl #(.OFF(0), .TRIG(3), .NB(4)) ctl7(.clk(clk), .rst(rst), .st(st7), .pos(pe32), .nxt(ste41));
  wire [4:0] pe41; wire ste50;
  segctl #(.OFF(0), .TRIG(13), .NB(5)) ctl8(.clk(clk), .rst(rst), .st(ste41), .pos(pe41), .nxt(ste50));
  wire [5:0] pe50; wire ostart;
  segctl #(.OFF(0), .TRIG(30), .NB(6)) ctl9(.clk(clk), .rst(rst), .st(ste50), .pos(pe50), .nxt(ostart));
  wire [33:0] r0, r1, r2, r3;
  assign r0 = {y6r, y6i};
  bswap32 u_b32(.clk(clk), .c(pe32[3] & ~pe32[2]), .u(r0), .v(r1));
  bswap41 u_b41(.clk(clk), .c(pe41[4] & ~pe41[1]), .u(r1), .v(r2));
  bswap50 u_b50(.clk(clk), .c(pe50[5] & ~pe50[0]), .u(r2), .v(r3));
  reg ovr; reg [5:0] oc;
  always @(posedge clk) begin
    if (rst) ovr <= 1'b0;
    else if (ostart) ovr <= 1'b1;
    else if (oc == 6'd63) ovr <= 1'b0;
    oc <= ostart ? 6'd1 : oc + 6'd1;
  end
  assign out_valid = ostart | ovr;
  assign out_start = ostart;
  assign out_re = {{2{r3[33]}}, r3[33:17], 5'b0};
  assign out_im = {{2{r3[16]}}, r3[16:0], 5'b0};
endmodule
