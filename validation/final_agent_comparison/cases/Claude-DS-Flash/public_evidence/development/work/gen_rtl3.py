#!/usr/bin/env python3
"""fft64_top generator v2: R2SDF 64-pt FFT, balanced twiddle mux, registered coefficients."""
import math, sys
N=64; NS=6
Ms=[N//2**(s+1) for s in range(NS)]
CFRAC=int(sys.argv[1]) if len(sys.argv)>1 else 10
CW=2+CFRAC                     # coefficient width (Q2.CFRAC, includes sign)
OUTDIR=sys.argv[2] if len(sys.argv)>2 else '../submission/rtl'
RAMW=int(sys.argv[3]) if len(sys.argv)>3 else 22
L0=69; LAST=L0+63; C=L0+64

def cval(v):
    return ("-14'sd%d"%(-v)) if v<0 else ("14'sd%d"%v)
def clit(v):
    return ("-%d'sd%d"%(CW,-v)) if v<0 else ("%d'sd%d"%(CW,v))

def table(M):
    t=[]
    for j in range(M):
        a=-2*math.pi*j/(2*M)
        t.append((int(round(math.cos(a)*(1<<CFRAC))), int(round(math.sin(a)*(1<<CFRAC)))))
    return t

L=[];A=L.append
A("// fft64_top : streaming radix-2 single-path delay-feedback (R2SDF) 64-point")
A("// forward unscaled complex FFT (DIF), natural-order input and output.")
A("// Signed fixed point, 15 fractional bits externally; per-stage width growth.")
A("// Generated file.")
A("`default_nettype none")
A("module fft64_top (")
A("    input  wire               clk,")
A("    input  wire               rst,")
A("    input  wire               in_valid,")
A("    input  wire               frame_start,")
A("    input  wire signed [15:0] in_re,")
A("    input  wire signed [15:0] in_im,")
A("    output wire               out_valid,")
A("    output wire               out_start,")
A("    output wire signed [23:0] out_re,")
A("    output wire signed [23:0] out_im")
A(");")
A(f"  localparam integer LAST = {LAST};")
A(f"  localparam integer COFF = {C};")
A("")
A("  reg  [7:0] sc;")
A("  reg        busy;")
A("  wire       start = in_valid & frame_start;")
A("  wire [7:0] sc_nxt = start ? 8'd1 : (busy ? ((sc==LAST[7:0]) ? 8'd0 : sc+8'd1) : 8'd0);")
A("")
A("  always @(posedge clk) begin")
A("    if (rst) begin busy <= 1'b0; sc <= 8'd0; end")
A("    else if (start) begin busy <= 1'b1; sc <= 8'd1; end")
A("    else if (busy) begin")
A("      if (sc == LAST[7:0]) begin busy <= 1'b0; sc <= 8'd0; end")
A("      else sc <= sc + 8'd1;")
A("    end")
A("  end")
A("")
A("  reg [7:0] cp1,cp2,cp3,cp4,cp5,cp6;")
A("  always @(posedge clk) begin")
A("    cp1 <= sc; cp2 <= cp1; cp3 <= cp2; cp4 <= cp3; cp5 <= cp4; cp6 <= cp5;")
A("  end")
A("  wire signed [15:0] din_re = in_valid ? in_re : 16'sd0;")
A("  wire signed [15:0] din_im = in_valid ? in_im : 16'sd0;")
A("")

def coef_mux_tree(name, idx, M):
    """emit a balanced 2:1 mux tree selecting (cre,cim) constants by idx (idxw bits)."""
    t=table(M)
    idxw=max(1,(M-1).bit_length())
    if M==1:
        A(f"  wire signed [{CW-1}:0] {name}_re = {clit(t[0][0])};")
        A(f"  wire signed [{CW-1}:0] {name}_im = {clit(t[0][1])};")
        return
    # level 0 constants
    for j,(re,im) in enumerate(t):
        A(f"  wire signed [{CW-1}:0] {name}_c{j}_re = {clit(re)};")
        A(f"  wire signed [{CW-1}:0] {name}_c{j}_im = {clit(im)};")
    cur=[f"{name}_c{j}" for j in range(M)]
    lvl=0
    while len(cur)>1:
        nxt=[]
        for k in range(len(cur)//2):
            sel=f"{idx}[{lvl}]"
            nn=f"{name}_m{lvl}_{k}"
            A(f"  wire signed [{CW-1}:0] {nn}_re = {sel} ? {cur[2*k+1]}_re : {cur[2*k]}_re;")
            A(f"  wire signed [{CW-1}:0] {nn}_im = {sel} ? {cur[2*k+1]}_im : {cur[2*k]}_im;")
            nxt.append(nn)
        cur=nxt; lvl+=1
    A(f"  wire signed [{CW-1}:0] {name}_re = {cur[0]}_re;")
    A(f"  wire signed [{CW-1}:0] {name}_im = {cur[0]}_im;")

sig_in_re="din_re"; sig_in_im="din_im"
for s in range(1,NS+1):
    M=Ms[s-1]; W=15+s; Wo=W+1
    ctl = "sc" if s==1 else f"cp{s-1}"
    phbit = 6-s; idxw=max(1,(M-1).bit_length())
    A(f"  // ---------------- stage {s}: M={M} W={W} ----------------")
    A(f"  reg  signed [{Wo-1}:0] dly{s}_re [0:{M-1}];")
    A(f"  reg  signed [{Wo-1}:0] dly{s}_im [0:{M-1}];")
    A(f"  wire signed [{Wo-1}:0] do{s}_re = dly{s}_re[{M-1}];")
    A(f"  wire signed [{Wo-1}:0] do{s}_im = dly{s}_im[{M-1}];")
    A(f"  wire ph{s} = {ctl}[{phbit}];")
    if M==1:
        A(f"  wire [{idxw-1}:0] ix{s} = 1'b0;")
    else:
        A(f"  wire [{idxw-1}:0] ix{s} = {ctl}[{idxw-1}:0];")
    if s<=3:
        pre = {1:"sc_nxt", 2:"sc", 3:"cp1"}[s]
        if M==1:
            preidx="1'b0"
        else:
            A(f"  wire [{idxw-1}:0] px{s} = {pre}[{idxw-1}:0];")
            preidx=f"px{s}"
        coef_mux_tree(f"pc{s}", preidx, M)
        A(f"  reg signed [{CW-1}:0] cr{s}, ci{s};")
        A("  always @(posedge clk) begin")
        A(f"    if (rst) begin cr{s} <= {CW}'sd{1<<CFRAC}; ci{s} <= {CW}'sd0; end")
        A(f"    else begin cr{s} <= pc{s}_re; ci{s} <= pc{s}_im; end")
        A("  end")
    else:
        coef_mux_tree(f"pc{s}", f"ix{s}", M)
        A(f"  wire signed [{CW-1}:0] cr{s} = pc{s}_re;")
        A(f"  wire signed [{CW-1}:0] ci{s} = pc{s}_im;")
    A(f"  wire signed [{W-1}:0] i{s}_re = {sig_in_re};")
    A(f"  wire signed [{W-1}:0] i{s}_im = {sig_in_im};")
    A(f"  wire signed [{Wo}:0] su{s}_re = do{s}_re + i{s}_re;")
    A(f"  wire signed [{Wo}:0] su{s}_im = do{s}_im + i{s}_im;")
    A(f"  wire signed [{Wo}:0] df{s}_re = do{s}_re - i{s}_re;")
    A(f"  wire signed [{Wo}:0] df{s}_im = do{s}_im - i{s}_im;")
    A(f"  wire signed [{Wo-1}:0] dr{s}_re = df{s}_re[{Wo-1}:0];")
    A(f"  wire signed [{Wo-1}:0] dr{s}_im = df{s}_im[{Wo-1}:0];")
    A(f"  wire signed [{Wo+CW-1}:0] pr{s} = dr{s}_re * cr{s};")
    A(f"  wire signed [{Wo+CW-1}:0] pi{s} = dr{s}_im * ci{s};")
    A(f"  wire signed [{Wo+CW-1}:0] qr{s} = dr{s}_re * ci{s};")
    A(f"  wire signed [{Wo+CW-1}:0] qi{s} = dr{s}_im * cr{s};")
    A(f"  wire signed [{Wo+CW}:0] zr{s}_f = {{pr{s}[{Wo+CW-1}],pr{s}}} - {{pi{s}[{Wo+CW-1}],pi{s}}} + {1<<(CFRAC-1)};")
    A(f"  wire signed [{Wo+CW}:0] zi{s}_f = {{qr{s}[{Wo+CW-1}],qr{s}}} + {{qi{s}[{Wo+CW-1}],qi{s}}} + {1<<(CFRAC-1)};")
    A(f"  wire signed [{Wo-1}:0] zr{s} = zr{s}_f[{Wo-1+CFRAC}:{CFRAC}];")
    A(f"  wire signed [{Wo-1}:0] zi{s} = zi{s}_f[{Wo-1+CFRAC}:{CFRAC}];")
    A(f"  wire signed [{Wo-1}:0] nx{s}_re = ph{s} ? zr{s} : do{s}_re;")
    A(f"  wire signed [{Wo-1}:0] nx{s}_im = ph{s} ? zi{s} : do{s}_im;")
    A(f"  wire signed [{Wo-1}:0] wr{s}_re = ph{s} ? su{s}_re[{Wo-1}:0] : {{i{s}_re[{W-1}],i{s}_re}};")
    A(f"  wire signed [{Wo-1}:0] wr{s}_im = ph{s} ? su{s}_im[{Wo-1}:0] : {{i{s}_im[{W-1}],i{s}_im}};")
    A(f"  reg  signed [{Wo-1}:0] o{s}_re, o{s}_im;")
    A(f"  integer k{s};")
    A(f"  wire [{Wo-1}:0] rstmask{s} = {{ {Wo} {{~rst}} }};")
    A(f"  always @(posedge clk) begin")
    A(f"    for (k{s}={M-1}; k{s}>0; k{s}=k{s}-1) begin")
    A(f"      dly{s}_re[k{s}] <= dly{s}_re[k{s}-1] & rstmask{s};")
    A(f"      dly{s}_im[k{s}] <= dly{s}_im[k{s}-1] & rstmask{s};")
    A(f"    end")
    A(f"    dly{s}_re[0] <= wr{s}_re & rstmask{s};")
    A(f"    dly{s}_im[0] <= wr{s}_im & rstmask{s};")
    A(f"    o{s}_re <= nx{s}_re & rstmask{s};")
    A(f"    o{s}_im <= nx{s}_im & rstmask{s};")
    A("  end")
    A("")
    sig_in_re=f"o{s}_re"; sig_in_im=f"o{s}_im"

A("  // ---------------- output reorder buffer ----------------")
A(f"  reg signed [{RAMW-1}:0] rb_re [0:63];")
A(f"  reg signed [{RAMW-1}:0] rb_im [0:63];")
A("  wire       wr_en = (cp6 >= 8'd63) && (cp6 <= 8'd126);")
A("  wire [5:0] wt  = cp6[5:0] - 6'd63;")
A("  wire [5:0] wad = ~{wt[0],wt[1],wt[2],wt[3],wt[4],wt[5]};")
A("")
A(f"  reg [COFF:0] arm_sr;")
A("  always @(posedge clk) begin")
A("    if (rst) arm_sr <= 0;")
A("    else     arm_sr <= {arm_sr[COFF-1:0], start};")
A("  end")
A("  wire emit_arm = arm_sr[COFF];")
A("")
A("  reg        emit;")
A("  reg [5:0]  eidx;")
A("  always @(posedge clk) begin")
A("    if (rst) begin emit <= 1'b0; eidx <= 6'd0; end")
A("    else if (emit_arm) begin emit <= 1'b1; eidx <= 6'd0; end")
A("    else if (emit) begin")
A("      if (eidx == 6'd63) emit <= 1'b0;")
A("      else eidx <= eidx + 6'd1;")
A("    end")
A("  end")
A("")
A("  always @(posedge clk) if (wr_en) begin")
A(f"    rb_re[wad] <= o{NS}_re[{RAMW-1}:0];")
A(f"    rb_im[wad] <= o{NS}_im[{RAMW-1}:0];")
A("  end")
A("")
A("  assign out_valid = emit;")
A("  assign out_start = emit & (eidx == 6'd0);")
A(f"  wire signed [{RAMW-1}:0] rd_re = rb_re[eidx];")
A(f"  wire signed [{RAMW-1}:0] rd_im = rb_im[eidx];")
A("  assign out_re = {{%d{rd_re[%d]}}, rd_re};"%(24-RAMW,RAMW-1))
A("  assign out_im = {{%d{rd_im[%d]}}, rd_im};"%(24-RAMW,RAMW-1))
A("endmodule")
A("`default_nettype wire")
open(OUTDIR+"/fft64_top.sv","w").write("\n".join(L)+"\n")
print("wrote",OUTDIR+"/fft64_top.sv",len(L),"lines")
