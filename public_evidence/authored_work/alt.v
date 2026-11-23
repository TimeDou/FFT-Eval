// Generated R2^3 SDF FFT64 (DIF) with bit-reversal reorder; config:
// {"m": [0, 1, 1, 1, 2, 2, 4], "mA": 1, "mB": 2, "mC": 2, "tb": 10, "k8": 8, "R3": 1, "R4": 1, "R6": 1, "bf_round": [0, 0, 0, 0, 0, 0], "altpol": 1}

module sdf_stage1(input clk, input mode, input signed [15:0] br, input signed [15:0] bi,
  output reg signed [15:0] yr, output reg signed [15:0] yi);
  reg [511:0] dlr, dli;
  wire [15:0] qr = ~dlr[511:496];
  wire [15:0] qi = ~dli[511:496];
  wire signed [15:0] ar = qr[15:0];
  wire signed [15:0] ai = qi[15:0];
  wire signed [15:0] cr = qr[15:0];
  wire signed [15:0] ci = qi[15:0];
  wire signed [31:0] sr = ar + br;
  wire signed [31:0] si = ai + bi;
  wire signed [31:0] dr = ar - br;
  wire signed [31:0] di = ai - bi;
  wire signed [31:0] srq = sr >>> 1;
  wire signed [31:0] siq = si >>> 1;
  wire signed [31:0] drq = dr >>> 1;
  wire signed [31:0] diq = di >>> 1;
  wire [15:0] nr = (mode ? drq[15:0] : br);
  wire [15:0] ni = (mode ? diq[15:0] : bi);
  always @(posedge clk) begin
    dlr <= {~dlr[495:0], nr}; dli <= {~dli[495:0], ni};
    yr <= mode ? srq[15:0] : cr;
    yi <= mode ? siq[15:0] : ci;
  end
endmodule

module sdf_stage2(input clk, input mode, input signed [15:0] br, input signed [15:0] bi,
  output reg signed [16:0] yr, output reg signed [16:0] yi);
  reg [271:0] dlr, dli;
  wire [16:0] qr = ~dlr[271:255];
  wire [16:0] qi = ~dli[271:255];
  wire signed [15:0] ar = qr[15:0];
  wire signed [15:0] ai = qi[15:0];
  wire signed [16:0] cr = qr[16:0];
  wire signed [16:0] ci = qi[16:0];
  wire signed [31:0] sr = ar + br;
  wire signed [31:0] si = ai + bi;
  wire signed [31:0] dr = ar - br;
  wire signed [31:0] di = ai - bi;
  wire signed [31:0] srq = sr >>> 0;
  wire signed [31:0] siq = si >>> 0;
  wire signed [31:0] drq = dr >>> 0;
  wire signed [31:0] diq = di >>> 0;
  wire [16:0] nr = {drq[16:16], (mode ? drq[15:0] : br)};
  wire [16:0] ni = {diq[16:16], (mode ? diq[15:0] : bi)};
  always @(posedge clk) begin
    dlr <= {~dlr[254:0], nr}; dli <= {~dli[254:0], ni};
    yr <= mode ? srq[16:0] : cr;
    yi <= mode ? siq[16:0] : ci;
  end
endmodule

module sdf_stage3(input clk, input mode, input signed [16:0] br, input signed [16:0] bi,
  output reg signed [17:0] yr, output reg signed [17:0] yi);
  reg [143:0] dlr, dli;
  wire [17:0] qr = ~dlr[143:126];
  wire [17:0] qi = ~dli[143:126];
  wire signed [16:0] ar = qr[16:0];
  wire signed [16:0] ai = qi[16:0];
  wire signed [17:0] cr = qr[17:0];
  wire signed [17:0] ci = qi[17:0];
  wire signed [31:0] sr = ar + br;
  wire signed [31:0] si = ai + bi;
  wire signed [31:0] dr = ar - br;
  wire signed [31:0] di = ai - bi;
  wire signed [31:0] srq = sr >>> 0;
  wire signed [31:0] siq = si >>> 0;
  wire signed [31:0] drq = dr >>> 0;
  wire signed [31:0] diq = di >>> 0;
  wire [17:0] nr = {drq[17:17], (mode ? drq[16:0] : br)};
  wire [17:0] ni = {diq[17:17], (mode ? diq[16:0] : bi)};
  always @(posedge clk) begin
    dlr <= {~dlr[125:0], nr}; dli <= {~dli[125:0], ni};
    yr <= mode ? srq[17:0] : cr;
    yi <= mode ? siq[17:0] : ci;
  end
endmodule

module sdf_stage4(input clk, input mode, input signed [16:0] br, input signed [16:0] bi,
  output reg signed [17:0] yr, output reg signed [17:0] yi);
  reg [71:0] dlr, dli;
  wire [17:0] qr = ~dlr[71:54];
  wire [17:0] qi = ~dli[71:54];
  wire signed [16:0] ar = qr[16:0];
  wire signed [16:0] ai = qi[16:0];
  wire signed [17:0] cr = qr[17:0];
  wire signed [17:0] ci = qi[17:0];
  wire signed [31:0] sr = ar + br;
  wire signed [31:0] si = ai + bi;
  wire signed [31:0] dr = ar - br;
  wire signed [31:0] di = ai - bi;
  wire signed [31:0] srq = sr >>> 0;
  wire signed [31:0] siq = si >>> 0;
  wire signed [31:0] drq = dr >>> 0;
  wire signed [31:0] diq = di >>> 0;
  wire [17:0] nr = {drq[17:17], (mode ? drq[16:0] : br)};
  wire [17:0] ni = {diq[17:17], (mode ? diq[16:0] : bi)};
  always @(posedge clk) begin
    dlr <= {~dlr[53:0], nr}; dli <= {~dli[53:0], ni};
    yr <= mode ? srq[17:0] : cr;
    yi <= mode ? siq[17:0] : ci;
  end
endmodule

module sdf_stage5(input clk, input mode, input signed [17:0] br, input signed [17:0] bi,
  output reg signed [18:0] yr, output reg signed [18:0] yi);
  reg [37:0] dlr, dli;
  wire [18:0] qr = ~dlr[37:19];
  wire [18:0] qi = ~dli[37:19];
  wire signed [17:0] ar = qr[17:0];
  wire signed [17:0] ai = qi[17:0];
  wire signed [18:0] cr = qr[18:0];
  wire signed [18:0] ci = qi[18:0];
  wire signed [31:0] sr = ar + br;
  wire signed [31:0] si = ai + bi;
  wire signed [31:0] dr = ar - br;
  wire signed [31:0] di = ai - bi;
  wire signed [31:0] srq = sr >>> 0;
  wire signed [31:0] siq = si >>> 0;
  wire signed [31:0] drq = dr >>> 0;
  wire signed [31:0] diq = di >>> 0;
  wire [18:0] nr = {drq[18:18], (mode ? drq[17:0] : br)};
  wire [18:0] ni = {diq[18:18], (mode ? diq[17:0] : bi)};
  always @(posedge clk) begin
    dlr <= {~dlr[18:0], nr}; dli <= {~dli[18:0], ni};
    yr <= mode ? srq[18:0] : cr;
    yi <= mode ? siq[18:0] : ci;
  end
endmodule

module sdf_stage6(input clk, input mode, input signed [18:0] br, input signed [18:0] bi,
  output reg signed [17:0] yr, output reg signed [17:0] yi);
  reg [18:0] dlr, dli;
  wire [18:0] qr = dlr[18:0];
  wire [18:0] qi = dli[18:0];
  wire signed [18:0] ar = qr[18:0];
  wire signed [18:0] ai = qi[18:0];
  wire signed [17:0] cr = qr[17:0];
  wire signed [17:0] ci = qi[17:0];
  wire signed [31:0] sr = ar + br;
  wire signed [31:0] si = ai + bi;
  wire signed [31:0] dr = ar - br;
  wire signed [31:0] di = ai - bi;
  wire signed [31:0] srq = sr >>> 2;
  wire signed [31:0] siq = si >>> 2;
  wire signed [31:0] drq = dr >>> 2;
  wire signed [31:0] diq = di >>> 2;
  wire [18:0] nr = {br[18:18], (mode ? drq[17:0] : br[17:0])};
  wire [18:0] ni = {bi[18:18], (mode ? diq[17:0] : bi[17:0])};
  always @(posedge clk) begin
    dlr <= nr; dli <= ni;
    yr <= mode ? srq[17:0] : cr;
    yi <= mode ? siq[17:0] : ci;
  end
endmodule

module w8rot3(input clk, input [1:0] sel, input signed [16:0] xr, input signed [16:0] xi,
  output signed [16:0] zr, output signed [16:0] zi);
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
      2'd2: begin or_ = ti; oi = -tr; end
      default: begin or_ = vr; oi = -ur; end
    endcase
  end
  reg signed [16:0] p0r, p0i;
  always @(posedge clk) begin p0r <= or_[16:0]; p0i <= oi[16:0]; end
  assign zr = p0r;
  assign zi = p0i;
endmodule

module w8rot6(input clk, input [1:0] sel, input signed [18:0] xr, input signed [18:0] xi,
  output signed [18:0] zr, output signed [18:0] zi);
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
      2'd2: begin or_ = ti; oi = -tr; end
      default: begin or_ = vr; oi = -ur; end
    endcase
  end
  reg signed [18:0] p0r, p0i;
  always @(posedge clk) begin p0r <= or_[18:0]; p0i <= oi[18:0]; end
  assign zr = p0r;
  assign zi = p0i;
endmodule

module w64mul(input clk, input [5:0] q, input signed [17:0] xr, input signed [17:0] xi,
  output signed [16:0] zr, output signed [16:0] zi);
  reg signed [10:0] C, S;
  reg t0, t16;
  always @(*) begin
    case (q)
      6'd0: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd1: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd2: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd3: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd4: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd5: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd6: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd7: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd8: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd9: begin C = 11'sd946; S = -11'sd392; t0 = 1'b0; t16 = 1'b0; end
      6'd10: begin C = 11'sd724; S = -11'sd724; t0 = 1'b0; t16 = 1'b0; end
      6'd11: begin C = 11'sd392; S = -11'sd946; t0 = 1'b0; t16 = 1'b0; end
      6'd12: begin C = 11'sd0; S = 11'sd0; t0 = 1'b0; t16 = 1'b1; end
      6'd13: begin C = -11'sd392; S = -11'sd946; t0 = 1'b0; t16 = 1'b0; end
      6'd14: begin C = -11'sd724; S = -11'sd724; t0 = 1'b0; t16 = 1'b0; end
      6'd15: begin C = -11'sd946; S = -11'sd392; t0 = 1'b0; t16 = 1'b0; end
      6'd16: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd17: begin C = 11'sd1004; S = -11'sd200; t0 = 1'b0; t16 = 1'b0; end
      6'd18: begin C = 11'sd946; S = -11'sd392; t0 = 1'b0; t16 = 1'b0; end
      6'd19: begin C = 11'sd851; S = -11'sd569; t0 = 1'b0; t16 = 1'b0; end
      6'd20: begin C = 11'sd724; S = -11'sd724; t0 = 1'b0; t16 = 1'b0; end
      6'd21: begin C = 11'sd569; S = -11'sd851; t0 = 1'b0; t16 = 1'b0; end
      6'd22: begin C = 11'sd392; S = -11'sd946; t0 = 1'b0; t16 = 1'b0; end
      6'd23: begin C = 11'sd200; S = -11'sd1004; t0 = 1'b0; t16 = 1'b0; end
      6'd24: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd25: begin C = 11'sd851; S = -11'sd569; t0 = 1'b0; t16 = 1'b0; end
      6'd26: begin C = 11'sd392; S = -11'sd946; t0 = 1'b0; t16 = 1'b0; end
      6'd27: begin C = -11'sd200; S = -11'sd1004; t0 = 1'b0; t16 = 1'b0; end
      6'd28: begin C = -11'sd724; S = -11'sd724; t0 = 1'b0; t16 = 1'b0; end
      6'd29: begin C = -11'sd1004; S = -11'sd200; t0 = 1'b0; t16 = 1'b0; end
      6'd30: begin C = -11'sd946; S = 11'sd392; t0 = 1'b0; t16 = 1'b0; end
      6'd31: begin C = -11'sd569; S = 11'sd851; t0 = 1'b0; t16 = 1'b0; end
      6'd32: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd33: begin C = 11'sd1019; S = -11'sd100; t0 = 1'b0; t16 = 1'b0; end
      6'd34: begin C = 11'sd1004; S = -11'sd200; t0 = 1'b0; t16 = 1'b0; end
      6'd35: begin C = 11'sd980; S = -11'sd297; t0 = 1'b0; t16 = 1'b0; end
      6'd36: begin C = 11'sd946; S = -11'sd392; t0 = 1'b0; t16 = 1'b0; end
      6'd37: begin C = 11'sd903; S = -11'sd483; t0 = 1'b0; t16 = 1'b0; end
      6'd38: begin C = 11'sd851; S = -11'sd569; t0 = 1'b0; t16 = 1'b0; end
      6'd39: begin C = 11'sd792; S = -11'sd650; t0 = 1'b0; t16 = 1'b0; end
      6'd40: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd41: begin C = 11'sd903; S = -11'sd483; t0 = 1'b0; t16 = 1'b0; end
      6'd42: begin C = 11'sd569; S = -11'sd851; t0 = 1'b0; t16 = 1'b0; end
      6'd43: begin C = 11'sd100; S = -11'sd1019; t0 = 1'b0; t16 = 1'b0; end
      6'd44: begin C = -11'sd392; S = -11'sd946; t0 = 1'b0; t16 = 1'b0; end
      6'd45: begin C = -11'sd792; S = -11'sd650; t0 = 1'b0; t16 = 1'b0; end
      6'd46: begin C = -11'sd1004; S = -11'sd200; t0 = 1'b0; t16 = 1'b0; end
      6'd47: begin C = -11'sd980; S = 11'sd297; t0 = 1'b0; t16 = 1'b0; end
      6'd48: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd49: begin C = 11'sd980; S = -11'sd297; t0 = 1'b0; t16 = 1'b0; end
      6'd50: begin C = 11'sd851; S = -11'sd569; t0 = 1'b0; t16 = 1'b0; end
      6'd51: begin C = 11'sd650; S = -11'sd792; t0 = 1'b0; t16 = 1'b0; end
      6'd52: begin C = 11'sd392; S = -11'sd946; t0 = 1'b0; t16 = 1'b0; end
      6'd53: begin C = 11'sd100; S = -11'sd1019; t0 = 1'b0; t16 = 1'b0; end
      6'd54: begin C = -11'sd200; S = -11'sd1004; t0 = 1'b0; t16 = 1'b0; end
      6'd55: begin C = -11'sd483; S = -11'sd903; t0 = 1'b0; t16 = 1'b0; end
      6'd56: begin C = 11'sd0; S = 11'sd0; t0 = 1'b1; t16 = 1'b0; end
      6'd57: begin C = 11'sd792; S = -11'sd650; t0 = 1'b0; t16 = 1'b0; end
      6'd58: begin C = 11'sd200; S = -11'sd1004; t0 = 1'b0; t16 = 1'b0; end
      6'd59: begin C = -11'sd483; S = -11'sd903; t0 = 1'b0; t16 = 1'b0; end
      6'd60: begin C = -11'sd946; S = -11'sd392; t0 = 1'b0; t16 = 1'b0; end
      6'd61: begin C = -11'sd980; S = 11'sd297; t0 = 1'b0; t16 = 1'b0; end
      6'd62: begin C = -11'sd569; S = 11'sd851; t0 = 1'b0; t16 = 1'b0; end
      6'd63: begin C = 11'sd100; S = 11'sd1019; t0 = 1'b0; t16 = 1'b0; end
      default: begin C = 0; S = 0; t0 = 1'b0; t16 = 1'b0; end
    endcase
  end
  wire signed [31:0] pr = xr * C - xi * S;
  wire signed [31:0] pi = xr * S + xi * C;
  wire signed [31:0] prr = (pr + 1024) >>> 11;
  wire signed [31:0] pir = (pi + 1024) >>> 11;
  wire signed [31:0] tr = xr >>> 1;
  wire signed [31:0] ti = xi >>> 1;
  wire signed [31:0] or_ = t0 ? tr : (t16 ? ti : prr);
  wire signed [31:0] oi = t0 ? ti : (t16 ? -tr : pir);
  reg signed [16:0] p0r, p0i;
  always @(posedge clk) begin p0r <= or_[16:0]; p0i <= oi[16:0]; end
  assign zr = p0r;
  assign zi = p0i;
endmodule

module bswap32(input clk, input c, input [35:0] u, output [35:0] v);
  reg [143:0] dl;
  wire [35:0] o = ~dl[143:108];
  wire [35:0] n = c ? o : u;
  always @(posedge clk) dl <= {~dl[107:0], n};
  assign v = c ? u : o;
endmodule

module bswap41(input clk, input c, input [35:0] u, output [35:0] v);
  reg [503:0] dl;
  wire [35:0] o = ~dl[503:468];
  wire [35:0] n = c ? o : u;
  always @(posedge clk) dl <= {~dl[467:0], n};
  assign v = c ? u : o;
endmodule

module bswap50(input clk, input c, input [35:0] u, output [35:0] v);
  reg [1115:0] dl;
  wire [35:0] o = dl[1115:1080];
  wire [35:0] n = c ? o : u;
  always @(posedge clk) dl <= {~dl[1079:0], n};
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
  segctl #(.OFF(0), .TRIG(9), .NB(6)) ctl3(.clk(clk), .rst(rst), .st(st3), .pos(pos3), .nxt(st4));
  reg [0:0] mdp3;
  always @(posedge clk) mdp3 <= pos3[3];
  wire md3 = mdp3[0];
  wire [5:0] pos4; wire st5;
  segctl #(.OFF(0), .TRIG(5), .NB(6)) ctl4(.clk(clk), .rst(rst), .st(st4), .pos(pos4), .nxt(st5));
  reg [0:0] mdp4;
  always @(posedge clk) mdp4 <= pos4[2];
  wire md4 = mdp4[0];
  wire [5:0] pos5; wire st6;
  segctl #(.OFF(0), .TRIG(2), .NB(6)) ctl5(.clk(clk), .rst(rst), .st(st5), .pos(pos5), .nxt(st6));
  wire md5 = pos5[1];
  wire [5:0] pos6; wire st7;
  segctl #(.OFF(0), .TRIG(2), .NB(6)) ctl6(.clk(clk), .rst(rst), .st(st6), .pos(pos6), .nxt(st7));
  reg [0:0] mdp6;
  always @(posedge clk) mdp6 <= pos6[0];
  wire md6 = mdp6[0];
  wire signed [15:0] x0r = in_re >>> 0;
  wire signed [15:0] x0i = in_im >>> 0;
  wire signed [15:0] y1r, y1i;
  sdf_stage1 u_s1(.clk(clk), .mode(md1), .br(x0r), .bi(x0i), .yr(y1r), .yi(y1i));
  wire j2 = pos2[5] & pos2[4];
  wire signed [15:0] b2r = j2 ? y1i : y1r;
  wire signed [15:0] b2i = j2 ? -y1r : y1i;
  wire signed [16:0] y2r, y2i;
  sdf_stage2 u_s2(.clk(clk), .mode(md2), .br(b2r), .bi(b2i), .yr(y2r), .yi(y2i));
  wire [5:0] q3 = pos3;
  wire [1:0] sel3 = q3[3] ? {q3[4], q3[5]} : 2'd0;
  wire signed [16:0] b3r, b3i;
  w8rot3 u_r3(.clk(clk), .sel(sel3), .xr(y2r), .xi(y2i), .zr(b3r), .zi(b3i));
  wire signed [17:0] y3r, y3i;
  sdf_stage3 u_s3(.clk(clk), .mode(md3), .br(b3r), .bi(b3i), .yr(y3r), .yi(y3i));
  wire [5:0] q4 = pos4;
  wire signed [16:0] b4r, b4i;
  w64mul u_m4(.clk(clk), .q(q4), .xr(y3r), .xi(y3i), .zr(b4r), .zi(b4i));
  wire signed [17:0] y4r, y4i;
  sdf_stage4 u_s4(.clk(clk), .mode(md4), .br(b4r), .bi(b4i), .yr(y4r), .yi(y4i));
  wire j5 = pos5[1] & pos5[2];
  wire signed [17:0] b5r = j5 ? y4i : y4r;
  wire signed [17:0] b5i = j5 ? -y4r : y4i;
  wire signed [18:0] y5r, y5i;
  sdf_stage5 u_s5(.clk(clk), .mode(md5), .br(b5r), .bi(b5i), .yr(y5r), .yi(y5i));
  wire [5:0] q6 = pos6;
  wire [1:0] sel6 = q6[0] ? {q6[1], q6[2]} : 2'd0;
  wire signed [18:0] b6r, b6i;
  w8rot6 u_r6(.clk(clk), .sel(sel6), .xr(y5r), .xi(y5i), .zr(b6r), .zi(b6i));
  wire signed [17:0] y6r, y6i;
  sdf_stage6 u_s6(.clk(clk), .mode(md6), .br(b6r), .bi(b6i), .yr(y6r), .yi(y6i));
  wire [3:0] pe32; wire ste41;
  segctl #(.OFF(0), .TRIG(3), .NB(4)) ctl7(.clk(clk), .rst(rst), .st(st7), .pos(pe32), .nxt(ste41));
  wire [4:0] pe41; wire ste50;
  segctl #(.OFF(0), .TRIG(13), .NB(5)) ctl8(.clk(clk), .rst(rst), .st(ste41), .pos(pe41), .nxt(ste50));
  wire [5:0] pe50; wire ostart;
  segctl #(.OFF(0), .TRIG(30), .NB(6)) ctl9(.clk(clk), .rst(rst), .st(ste50), .pos(pe50), .nxt(ostart));
  wire [35:0] r0, r1, r2, r3;
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
  assign out_re = {{2{r3[35]}}, r3[35:18], 4'b0};
  assign out_im = {{2{r3[17]}}, r3[17:0], 4'b0};
endmodule
