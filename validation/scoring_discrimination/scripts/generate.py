"""Original RTL emitters: block-scheduled R2SDF and folded in-place R2.

All arithmetic is synthesizable; no third-party FFT RTL is included.
"""
from pathlib import Path
import json,math,argparse

ROOT=Path(__file__).resolve().parents[1]
PORTS='input wire clk,input wire rst,input wire in_valid,input wire frame_start,input wire signed [15:0] in_re,in_im,output reg out_valid,output reg out_start,output reg signed [23:0] out_re,out_im'

def qfun(name,iw,ow,shift,mode):
    start=f'function automatic signed [{ow-1}:0] {name};input signed [{iw-1}:0] x;'
    if shift<=0:return start+f'reg signed [{ow-1}:0] e;begin e=x;{name}=e<<<{-shift};end endfunction\n'
    inc='0'
    if mode=='rne':inc=f'((x[{shift-1}:0]>{shift}\'d{1<<(shift-1)}) || ((x[{shift-1}:0]=={shift}\'d{1<<(shift-1)}) && b[0]))'
    if mode=='zero':inc=f'(x[{iw-1}] && (x[{shift-1}:0]!={shift}\'d0))'
    # Keep the signed quotient at least as wide as the return value. Otherwise
    # mixing a signed narrow quotient with an unsigned one-bit rounding flag
    # can zero-extend negative values when the function widens its output.
    return start+f'reg signed [{max(iw,ow)}:0] b;begin b=x>>>{shift};{name}=b+{inc};end endfunction\n'

def romfun(name,t,count=32,stride=1,aw=5):
    out=f'function automatic signed [{t+1}:0] {name};input [{aw-1}:0] j;begin case(j)\n'
    for j in range(count):
        a=-2*math.pi*j*stride/64;v=round((math.cos(a)if name.endswith('r')else math.sin(a))*(1<<t))
        out+=f"{aw}'d{j}:{name}="+('-'if v<0 else'')+f"{t+2}'sd{abs(v)};\n"
    return out+f'default:{name}=0;endcase end endfunction\n'

def rotate(name,dw,ow,t,p,mode):
    pw=dw-p;prod=pw+t+2;acc=prod+1
    s=f'module {name}(input signed[{dw-1}:0] dr,di,input signed[{t+1}:0] wr,wi,input[4:0] index,output signed[{ow-1}:0] vr,vi);\n'
    s+=qfun('preq',dw,pw,p,mode)+qfun('postq',acc,ow,t-p,mode)
    s+=f'wire signed[{pw-1}:0] ar=preq(dr),ai=preq(di);wire signed[{prod-1}:0] p0=ar*wr,p1=ai*wi,p2=ar*wi,p3=ai*wr;\n'
    s+=f'wire signed[{acc-1}:0] rr=$signed({{p0[{prod-1}],p0}})-$signed({{p1[{prod-1}],p1}}),ii=$signed({{p2[{prod-1}],p2}})+$signed({{p3[{prod-1}],p3}});\n'
    s+="assign vr=index==0?dr:index==16?di:postq(rr);assign vi=index==0?di:index==16?-dr:postq(ii);endmodule\n"
    return s

def sdf(cfg):
    ds=cfg.get('drops',[0]*6);ts=cfg.get('twiddles',[16]*6);ps=cfg.get('pre',[0]*6);mode=cfg.get('rounding','rne')
    s='';prevw=16;prevd=0;offset=0
    for st in range(6):
        h=32>>st;iw=16+st-ds[st];ow=iw+1;t=ts[st];p=ps[st]
        if h>=4:s+=rotate(f'rot{st}',ow,ow,t,p,mode)
        s+=f'module stage{st}(input clk,rst,input[15:0] tick,input signed[{prevw-1}:0] ir,ii,output reg signed[{ow-1}:0] yr,yi);\n'
        s+=qfun('iq',prevw,iw,ds[st]-prevd,mode)
        aw=max(1,int(math.log2(h)))
        s+=f'wire[{int(math.log2(h))}:0] phase=tick-16\'d{offset};wire bf=phase[{int(math.log2(h))}];\n'
        s+=f'wire signed[{iw-1}:0] xr=iq(ir),xi=iq(ii);reg signed[{ow-1}:0] br[0:{h-1}],bi[0:{h-1}];integer n;\n'
        s+=f'wire signed[{ow-1}:0] ar=br[0],ai=bi[0],sr=ar+xr,si=ai+xi,dr=ar-xr,di=ai-xi;wire signed[{ow-1}:0] vr,vi;\n'
        if h>=4:
            s+=romfun('cr',t,h,1<<st,aw)+romfun('ci',t,h,1<<st,aw)
            s+=f'wire[{aw-1}:0] j=phase[{aw-1}:0];wire[4:0] idx={{j,{st}\'b0}};'if st else f'wire[{aw-1}:0] j=phase[{aw-1}:0];wire[4:0] idx=j;'
            s+=f'rot{st} rot(dr,di,cr(j),ci(j),idx,vr,vi);\n'
        elif h==2:s+='assign vr=phase[0]?di:dr;assign vi=phase[0]?-dr:di;\n'
        else:s+='assign vr=dr;assign vi=di;\n'
        s+=f'always @(posedge clk)begin if(rst)begin yr<=0;yi<=0;for(n=0;n<{h};n=n+1)begin br[n]<=0;bi[n]<=0;end end else begin\n'
        if h>1:s+=f'for(n=0;n<{h-1};n=n+1)begin br[n]<=br[n+1];bi[n]<=bi[n+1];end\n'
        s+=f'br[{h-1}]<=bf?vr:$signed(xr);bi[{h-1}]<=bf?vi:$signed(xi);yr<=bf?sr:br[0];yi<=bf?si:bi[0];end end endmodule\n'
        prevw=ow;prevd=ds[st];offset+=h+1
    s+=f'module fft64_top({PORTS});reg[15:0] epoch;reg started;wire[15:0] tick=frame_start?16\'d0:epoch;integer k;\n'
    s+="always @(posedge clk)if(rst)begin epoch<=0;started<=0;end else if(frame_start)begin epoch<=1;started<=1;end else if(started)epoch <= (epoch < 16'd256) ? (epoch + 16'd1) : epoch;\n"
    s+='wire signed[15:0] r0=in_valid?in_re:16\'sd0,i0=in_valid?in_im:16\'sd0;\n'
    for st in range(6):
        w=17+st-ds[st]
        s+=f'wire signed[{w-1}:0] r{st+1},i{st+1};stage{st} u{st}(clk,rst,tick,r{st},i{st},r{st+1},i{st+1});\n'
    cap=69;out=133;w=22-ds[-1]
    s+=f'reg signed[{w-1}:0] rr[0:63],ri[0:63];wire[5:0] ci=tick-16\'d{cap},oi=tick-16\'d{out};wire[5:0] rev={{ci[0],ci[1],ci[2],ci[3],ci[4],ci[5]}};\n'
    s+=f'always @(posedge clk)begin if(rst)begin out_valid<=0;out_start<=0;out_re<=0;out_im<=0;for(k=0;k<64;k=k+1)begin rr[k]<=0;ri[k]<=0;end end else begin out_valid<=0;out_start<=0;if(started && tick>={cap} && tick<{cap+64})begin rr[rev]<=r6;ri[rev]<=i6;end\n'
    s+=f'if(started && tick>={out} && tick<{out+64})begin out_valid<=1;out_start<=tick=={out};out_re<=$signed({{{{{24-w}{{rr[oi][{w-1}]}}}},rr[oi]}})<<<{ds[-1]};out_im<=$signed({{{{{24-w}{{ri[oi][{w-1}]}}}},ri[oi]}})<<<{ds[-1]};end end end endmodule\n'
    return s

def folded(cfg):
    d=cfg.get('drop',0);t=cfg.get('twiddle',16);p=cfg.get('mul_drop',0);mode=cfg.get('rounding','rne');cut=cfg.get('pipeline',False);w=22-d;dw=w+1
    s=rotate('frot',dw,w,t,p,mode)+f'module fft64_top({PORTS});\n'
    s+=f'localparam W={w};reg signed[W-1:0] mr[0:63],mi[0:63];reg[2:0] state,stage;reg[5:0] ic,oc;reg[4:0] bidx;reg[5:0] a,b;reg[4:0] tidx;integer n;\n'
    s+=qfun('iq',16,w,d,mode)+romfun('cr',t)+romfun('ci',t)
    s+='always @* begin a=0;b=0;tidx=0;case(stage)\n'
    for st in range(6):
        hlog=5-st;h=1<<hlog
        s+=f"3'd{st}:begin a=((bidx>>{hlog})<<{hlog+1}) | (bidx & 5'd{h-1});b=a+6'd{h};tidx=(bidx & 5'd{h-1})<<{st};end\n"
    s+='default:begin a=0;b=0;tidx=0;end endcase end\n'
    s+=f'wire signed[{dw-1}:0] dr=$signed(mr[a])-$signed(mr[b]),di=$signed(mi[a])-$signed(mi[b]);wire signed[W-1:0] sr=mr[a]+mr[b],si=mi[a]+mi[b];wire signed[W-1:0] vr,vi;wire[5:0] oaddr={{oc[0],oc[1],oc[2],oc[3],oc[4],oc[5]}};\n'
    if cut:
        s+=f'reg pending;reg[5:0] pa,pb;reg[4:0] pi;reg signed[W-1:0] psr,psi;reg signed[{dw-1}:0] pdr,pdi;reg signed[{t+1}:0] pwr,pwi;frot rot(pdr,pdi,pwr,pwi,pi,vr,vi);\n'
    else:s+='frot rot(dr,di,cr(tidx),ci(tidx),tidx,vr,vi);\n'
    s+='always @(posedge clk)begin if(rst)begin state<=0;stage<=0;ic<=0;oc<=0;bidx<=0;out_valid<=0;out_start<=0;out_re<=0;out_im<=0;for(n=0;n<64;n=n+1)begin mr[n]<=0;mi[n]<=0;end\n'
    if cut:s+='pending<=0;pa<=0;pb<=0;pi<=0;psr<=0;psi<=0;pdr<=0;pdi<=0;pwr<=0;pwi<=0;\n'
    s+='end else begin out_valid<=0;out_start<=0;\n'
    if cut:s+='pending<=0;if(pending)begin mr[pa]<=psr;mi[pa]<=psi;mr[pb]<=vr;mi[pb]<=vi;end\n'
    s+='case(state)\n0:if(in_valid && frame_start)begin mr[0]<=iq(in_re);mi[0]<=iq(in_im);ic<=1;state<=1;end\n1:if(in_valid)begin mr[ic]<=iq(in_re);mi[ic]<=iq(in_im);if(ic==63)begin state<=2;stage<=0;bidx<=0;end else ic<=ic+1;end\n2:begin\n'
    if cut:s+='pending<=1;pa<=a;pb<=b;pi<=tidx;psr<=sr;psi<=si;pdr<=dr;pdi<=di;pwr<=cr(tidx);pwi<=ci(tidx);if(bidx==31)begin bidx<=0;state<=4;end else bidx<=bidx+1;\n'
    else:s+='mr[a]<=sr;mi[a]<=si;mr[b]<=vr;mi[b]<=vi;if(bidx==31)begin bidx<=0;if(stage==5)begin state<=3;oc<=0;end else stage<=stage+1;end else bidx<=bidx+1;\n'
    s+='end\n'
    if cut:s+='4:begin if(stage==5)begin state<=3;oc<=0;end else begin stage<=stage+1;state<=2;end end\n'
    s+=f'3:begin out_valid<=1;out_start<=oc==0;out_re<=$signed({{{{{24-w}{{mr[oaddr][{w-1}]}}}},mr[oaddr]}})<<<{d};out_im<=$signed({{{{{24-w}{{mi[oaddr][{w-1}]}}}},mi[oaddr]}})<<<{d};if(oc==63)state<=0;else oc<=oc+1;end\ndefault:state<=0;endcase end end endmodule\n'
    return s

def folded_banked(cfg):
    """Exact XOR-parity banking: each R2 pair differs in exactly one bit."""
    d=cfg.get('drop',0);t=cfg.get('twiddle',16);p=cfg.get('mul_drop',0);mode=cfg.get('rounding','rne');w=22-d;dw=w+1
    s=rotate('frot',dw,w,t,p,mode)
    s+=f'''module parity_mem(input clk,rst,input[5:0] ra,rb,wa,wb,input ena,enb,input signed[{w-1}:0] dra,dia,drb,dib,output signed[{w-1}:0] ar,ai,br,bi);
reg signed[{w-1}:0] r0[0:31],i0[0:31],r1[0:31],i1[0:31];integer k;
wire ba=^ra,bwa=^wa,bwb=^wb;
wire[4:0] a0=ba?rb[5:1]:ra[5:1],a1=ba?ra[5:1]:rb[5:1];
wire signed[{w-1}:0] qr0=r0[a0],qi0=i0[a0],qr1=r1[a1],qi1=i1[a1];
assign ar=ba?qr1:qr0;assign ai=ba?qi1:qi0;assign br=ba?qr0:qr1;assign bi=ba?qi0:qi1;
wire e0=(ena&&!bwa)||(enb&&!bwb),e1=(ena&&bwa)||(enb&&bwb);
wire takea0=ena&&!bwa,takea1=ena&&bwa;
wire[4:0] w0=takea0?wa[5:1]:wb[5:1],w1=takea1?wa[5:1]:wb[5:1];
wire signed[{w-1}:0] wr0=takea0?dra:drb,wi0=takea0?dia:dib,wr1=takea1?dra:drb,wi1=takea1?dia:dib;
always @(posedge clk)if(rst)begin for(k=0;k<32;k=k+1)begin r0[k]<=0;i0[k]<=0;r1[k]<=0;i1[k]<=0;end end else begin
if(e0)begin r0[w0]<=wr0;i0[w0]<=wi0;end if(e1)begin r1[w1]<=wr1;i1[w1]<=wi1;end end endmodule
'''
    s+=f'module fft64_top({PORTS});localparam W={w};reg[2:0] state,stage;reg[5:0] ic,oc;reg[4:0] bidx;reg[5:0] a,b;reg[4:0] tidx;\n'
    s+=qfun('iq',16,w,d,mode)+romfun('cr',t)+romfun('ci',t)
    s+='always @* begin a=0;b=0;tidx=0;case(stage)\n'
    for st in range(6):
        hl=5-st;h=1<<hl;s+=f"3'd{st}:begin a=((bidx>>{hl})<<{hl+1})|(bidx&5'd{h-1});b=a+6'd{h};tidx=(bidx&5'd{h-1})<<{st};end\n"
    s+='default:begin a=0;b=0;tidx=0;end endcase end\n'
    s+=f'''wire[5:0] oaddr={{oc[0],oc[1],oc[2],oc[3],oc[4],oc[5]}},ra=state==3?oaddr:a;
wire signed[W-1:0] ar,ai,br,bi;
wire signed[W-1:0] sr=ar+br,si=ai+bi;
wire signed[W-1:0] vr,vi;
wire signed[{dw-1}:0] dr=$signed(ar)-$signed(br),di=$signed(ai)-$signed(bi);
frot rot(dr,di,cr(tidx),ci(tidx),tidx,vr,vi);
wire load=(state==0&&in_valid&&frame_start)||(state==1&&in_valid),compute=state==2;
wire[5:0] wa=load?(state==0?6'd0:ic):a;
wire signed[W-1:0] wr=load?iq(in_re):sr,wi=load?iq(in_im):si;
parity_mem mem(clk,rst,ra,b,wa,b,load||compute,compute,wr,wi,vr,vi,ar,ai,br,bi);
always @(posedge clk)begin if(rst)begin state<=0;stage<=0;ic<=0;oc<=0;bidx<=0;out_valid<=0;out_start<=0;out_re<=0;out_im<=0;end else begin
out_valid<=0;out_start<=0;case(state)
0:if(in_valid&&frame_start)begin ic<=1;state<=1;end
1:if(in_valid)begin if(ic==63)begin state<=2;stage<=0;bidx<=0;end else ic<=ic+1;end
2:begin if(bidx==31)begin bidx<=0;if(stage==5)begin state<=3;oc<=0;end else stage<=stage+1;end else bidx<=bidx+1;end
3:begin out_valid<=1;out_start<=oc==0;
out_re<=$signed({{{{{24-w}{{ar[{w-1}]}}}},ar}})<<<{d};out_im<=$signed({{{{{24-w}{{ai[{w-1}]}}}},ai}})<<<{d};
if(oc==63)state<=0;else oc<=oc+1;end
default:state<=0;endcase end end endmodule
'''
    return s

def emit(cfg,path):
    path=Path(path);path.mkdir(parents=True,exist_ok=True)
    if cfg['architecture']=='folded':src=folded_banked(cfg)if cfg.get('banked')else folded(cfg)
    elif cfg['architecture']=='sdf':src=sdf(cfg)
    else:raise ValueError(cfg)
    (path/'rtl').mkdir(exist_ok=True)
    (path/'rtl/fft64_top.sv').write_text('// Original FFT64 implementation; no ALS.\n'+src)
    (path/'design_config.json').write_text(json.dumps(dict(top='fft64_top',rtl=['rtl/fft64_top.sv'],config=cfg),indent=2)+'\n')
    return src

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();emit(json.loads(Path(a.config).read_text()),a.output)
