"""RTL generator + bit-exact integer model for an R2^3 SDF FFT64 (DIF) with
Garrido-style bit-reversal output reordering.

Datapath points carry (width, lsb) where lsb is the exponent of the LSB in
units of 2^-15.  Every RTL arithmetic step has an identical numpy model.
"""
import json
import math
import sys
import numpy as np

BOUND = dict(inp=16384, s1=32768, s2=65536, w8a=79109, s3=158218, w64=166350,
             s4=332700, s5=665399, w8b=667008, s6=1334016)

DEFAULT = dict(m=[0, 1, 1, 1, 2, 2, 4], mA=1, mB=2, mC=2, tb=10, k8=8,
               R3=1, R4=1, R6=1, bf_round=[0, 0, 0, 0, 0, 0], tw_opt=None)


def width_for(bound, m):
    b = bound / (1 << m) * 1.001 + 2
    w = 2
    while (1 << (w - 1)) - 1 < b:
        w += 1
    return w


def twiddle_consts(cfg):
    tbl = twiddles(cfg)
    W = {}
    for e in range(64):
        if e == 0:
            W[e] = 1.0 + 0j
        elif e == 16:
            W[e] = -1j
        else:
            W[e] = (tbl[e][0] + 1j * tbl[e][1]) / (1 << cfg['tb'])
    return dict(K8=k8const(cfg) / (1 << cfg['k8']), W=W)


def formats(cfg):
    if cfg.get('exact_widths'):
        import widths
        m = cfg['m']
        lsb = dict(inp=m[0], s1=m[1], s2=m[2], w8a=cfg['mA'], s3=m[3], w64=cfg['mB'],
                   s4=m[4], s5=m[5], w8b=cfg['mC'], s6=m[6])
        modes = dict(inp='floor', w8a='mult', w64='mult', w8b='mult')
        for i, p in enumerate(['s1', 's2', 's3', 's4', 's5', 's6']):
            modes[p] = 'round' if cfg['bf_round'][i] else 'floor'
        res = widths.analyze(cfg, lsb, modes, twiddle_consts(cfg),
                             in_hi=16383 if cfg.get('clamp15') else 16384)
        f = {p: (r['width'], r['lsb']) for p, r in res.items()}
        f['inp'] = (min(f['inp'][0], 16), f['inp'][1])
        return f
    m = cfg['m']
    f = dict(inp=(width_for(BOUND['inp'], m[0]), m[0]))
    f['s1'] = (width_for(BOUND['s1'], m[1]), m[1])
    f['s2'] = (width_for(BOUND['s2'], m[2]), m[2])
    f['w8a'] = (width_for(BOUND['w8a'], cfg['mA']), cfg['mA'])
    f['s3'] = (width_for(BOUND['s3'], m[3]), m[3])
    f['w64'] = (width_for(BOUND['w64'], cfg['mB']), cfg['mB'])
    f['s4'] = (width_for(BOUND['s4'], m[4]), m[4])
    f['s5'] = (width_for(BOUND['s5'], m[5]), m[5])
    f['w8b'] = (width_for(BOUND['w8b'], cfg['mC']), cfg['mC'])
    f['s6'] = (width_for(BOUND['s6'], m[6]), m[6])
    if f['inp'][0] > 16:
        f['inp'] = (16, m[0])
    f['j2'] = f['s1']
    f['j5'] = f['s4']
    return f


STAGE_IN = ['inp', 'j2', 'w8a', 'w64', 'j5', 'w8b']
STAGE_OUT = ['s1', 's2', 's3', 's4', 's5', 's6']
P = np.arange(64)
BIT = lambda p, b: (p >> b) & 1
BITREV = np.array([int(f'{p:06b}'[::-1], 2) for p in range(64)])


def twiddles(cfg):
    tb = cfg['tb']
    tbl = {}
    for e in range(64):
        a = -2 * np.pi * e / 64
        tbl[e] = (int(np.rint(np.cos(a) * (1 << tb))), int(np.rint(np.sin(a) * (1 << tb))))
    if cfg.get('tw_opt'):
        for k, v in cfg['tw_opt'].items():
            tbl[int(k)] = tuple(v)
    return tbl


def tw_index(p):
    return (p & 7) * (BIT(p, 5) + 2 * BIT(p, 4) + 4 * BIT(p, 3))


def w8_sel(p, seg):
    if seg == 3:
        return BIT(p, 3) * (BIT(p, 5) + 2 * BIT(p, 4))
    return BIT(p, 0) * (BIT(p, 2) + 2 * BIT(p, 1))


def jrot_cond(p, seg):
    if seg == 2:
        return BIT(p, 5) & BIT(p, 4)
    return BIT(p, 1) & BIT(p, 2)


def k8const(cfg):
    return int(round((1 << cfg['k8']) / math.sqrt(2)))


# ----------------------------------------------------------------- model
def fl(v, k):
    return v >> k if k > 0 else v


def rnd(v, k):
    return (v + (1 << (k - 1))) >> k if k > 0 else v


def model(x, cfg):
    f = formats(cfg)
    re = x[..., 0].astype(np.int64)
    im = x[..., 1].astype(np.int64)
    if cfg.get('clamp15'):
        re, im = np.minimum(re, 16383), np.minimum(im, 16383)
    sh0 = f['inp'][1]
    re, im = fl(re, sh0), fl(im, sh0)
    K = k8const(cfg)
    k8 = cfg['k8']
    tbl = twiddles(cfg)
    tb = cfg['tb']
    for s in range(1, 7):
        fi, fo = f[STAGE_IN[s - 1]], f[STAGE_OUT[s - 1]]
        sh = fo[1] - fi[1]
        assert sh >= 0
        b = 6 - s
        D = 1 << b
        lo = P[(P >> b) & 1 == 0]
        hi = lo + D
        a_r, a_i, b_r, b_i = re[:, lo], im[:, lo], re[:, hi], im[:, hi]
        q = rnd if cfg['bf_round'][s - 1] else fl
        nre = np.empty_like(re)
        nim = np.empty_like(im)
        nre[:, lo] = q(a_r + b_r, sh)
        nim[:, lo] = q(a_i + b_i, sh)
        nre[:, hi] = q(a_r - b_r, sh)
        nim[:, hi] = q(a_i - b_i, sh)
        re, im = nre, nim
        if s in (1, 4):
            c = jrot_cond(P, 2 if s == 1 else 5).astype(bool)
            re, im = np.where(c, im, re), np.where(c, -re, im)
        elif s in (2, 5):
            fin = f[STAGE_OUT[s - 1]]
            fout = f['w8a' if s == 2 else 'w8b']
            d = fout[1] - fin[1]
            assert d >= 0
            sel = w8_sel(P, 3 if s == 2 else 6)
            u = re + im
            v = im - re
            ur = rnd(u * K, k8 + d)
            vr = rnd(v * K, k8 + d)
            tr, ti = fl(re, d), fl(im, d)
            re, im = (np.select([sel == 0, sel == 1, sel == 2, sel == 3], [tr, ur, ti, vr]),
                      np.select([sel == 0, sel == 1, sel == 2, sel == 3], [ti, vr, -tr, -ur]))
        elif s == 3:
            fin, fout = f['s3'], f['w64']
            d = fout[1] - fin[1]
            assert d >= 0
            e = tw_index(P)
            C = np.array([tbl[int(k)][0] for k in e])
            S = np.array([tbl[int(k)][1] for k in e])
            pr = re * C - im * S
            pi = re * S + im * C
            tr, ti = fl(re, d), fl(im, d)
            t0 = e == 0
            t16 = e == 16
            re, im = (np.where(t0, tr, np.where(t16, ti, rnd(pr, tb + d))),
                      np.where(t0, ti, np.where(t16, -tr, rnd(pi, tb + d))))
    out = np.empty(x.shape, dtype=np.int64)
    m6 = f['s6'][1]
    out[:, BITREV, 0] = re << m6
    out[:, BITREV, 1] = im << m6
    return out


def storage_bits(cfg):
    f = formats(cfg)
    tot = 0
    for s in range(1, 7):
        D = 1 << (6 - s)
        wd = max(f[STAGE_IN[s - 1]][0], f[STAGE_OUT[s - 1]][0])
        tot += D * wd + f[STAGE_OUT[s - 1]][0]  # delay line + out reg
    tot += cfg['R3'] * f['w8a'][0] + cfg['R4'] * f['w64'][0] + cfg['R6'] * f['w8b'][0]
    tot += 49 * f['s6'][0]
    return 2 * tot


# ------------------------------------------------------------------- RTL
def sv_const(v, w):
    return f"-{w}'sd{-v}" if v < 0 else f"{w}'sd{v}"


def noreg_set(cfg):
    s = set(cfg.get('noreg', []))
    if cfg.get('noreg6'):
        s.add(6)
    return s


def gen_rtl(cfg):
    f = formats(cfg)
    K = k8const(cfg)
    k8 = cfg['k8']
    tb = cfg['tb']
    tbl = twiddles(cfg)
    L = []
    A = L.append
    A('// Generated R2^3 SDF FFT64 (DIF) with bit-reversal reorder; config:')
    A('// ' + json.dumps({k: v for k, v in cfg.items() if k != 'tw_opt'}))
    A('')

    # ---------------- SDF butterfly stage modules
    for s in range(1, 7):
        WI, mi = f[STAGE_IN[s - 1]]
        WO, mo = f[STAGE_OUT[s - 1]]
        WD = max(WI, WO)
        D = 1 << (6 - s)
        sh = mo - mi
        rq = cfg['bf_round'][s - 1] and sh > 0
        neg = cfg.get('negmerge') and s >= 2
        noreg = s in noreg_set(cfg)
        ports = ', input ngi' if neg else ''
        A(f'module sdf_stage{s}(input clk, input mode{ports}, input signed [{WI-1}:0] br, input signed [{WI-1}:0] bi,')
        A(f'  output {"" if noreg else "reg "}signed [{WO-1}:0] yr, output {"" if noreg else "reg "}signed [{WO-1}:0] yi);')
        A(f'  reg [{WD*D-1}:0] dlr, dli;')
        inv_out = '~' if (cfg.get('altpol') and (D - 1) % 2 == 1) else ''
        A(f'  wire [{WD-1}:0] qr = {inv_out}dlr[{WD*D-1}:{WD*(D-1)}];')
        A(f'  wire [{WD-1}:0] qi = {inv_out}dli[{WD*D-1}:{WD*(D-1)}];')
        A(f'  wire signed [{WI-1}:0] ar = qr[{WI-1}:0];')
        A(f'  wire signed [{WI-1}:0] ai = qi[{WI-1}:0];')
        A(f'  wire signed [{WO-1}:0] cr = qr[{WO-1}:0];')
        A(f'  wire signed [{WO-1}:0] ci = qi[{WO-1}:0];')
        A('  wire signed [31:0] sr = ar + br;')
        A('  wire signed [31:0] dr = ar - br;')
        if neg and cfg.get('negxor'):
            # conditional negation of b_i folded into both adders:
            # ngi=1: sum_i = a_i - b_i, diff_i = a_i + b_i (XOR + carry-in)
            A(f'  wire [{WI-1}:0] bxi = bi ^ {{{WI}{{ngi}}}};')
            A("  wire signed [31:0] si = ai + $signed(bxi) + $signed({1'b0, ngi});")
            A("  wire signed [31:0] di = ai + $signed(~bxi) + $signed({1'b0, ~ngi});")
        else:
            A('  wire signed [31:0] si = ai + bi;')
            A('  wire signed [31:0] di = ai - bi;')
        if rq:
            h = 1 << (sh - 1)
            A(f'  wire signed [31:0] srq = (sr + {h}) >>> {sh};')
            A(f'  wire signed [31:0] siq = (si + {h}) >>> {sh};')
            A(f'  wire signed [31:0] drq = (dr + {h}) >>> {sh};')
            A(f'  wire signed [31:0] diq = (di + {h}) >>> {sh};')
        else:
            A(f'  wire signed [31:0] srq = sr >>> {sh};')
            A(f'  wire signed [31:0] siq = si >>> {sh};')
            A(f'  wire signed [31:0] drq = dr >>> {sh};')
            A(f'  wire signed [31:0] diq = di >>> {sh};')
        # delay-line input: low bits muxed, upper bits belong only to the wider format
        def din(dq, bb):
            if WI == WO:
                return f'(mode ? {dq}[{WO-1}:0] : {bb})'
            if WI > WO:
                return f'{{{bb}[{WI-1}:{WO}], (mode ? {dq}[{WO-1}:0] : {bb}[{WO-1}:0])}}'
            return f'{{{dq}[{WO-1}:{WI}], (mode ? {dq}[{WI-1}:0] : {bb})}}'
        if neg and not cfg.get('negxor'):
            # b_i arrives un-negated; ngi=1 (only ever in mode 1) means b_i is
            # really -bi: then sum_i = a_i - bi and diff_i = a_i + bi.
            A('  wire signed [31:0] siq2 = ngi ? diq : siq;')
            A('  wire signed [31:0] diq2 = ngi ? siq : diq;')
        else:
            A('  wire signed [31:0] siq2 = siq;')
            A('  wire signed [31:0] diq2 = diq;')
        A(f'  wire [{WD-1}:0] nr = {din("drq", "br")};')
        A(f'  wire [{WD-1}:0] ni = {din("diq2", "bi")};')
        if noreg:
            A(f'  assign yr = mode ? srq[{WO-1}:0] : cr;')
            A(f'  assign yi = mode ? siq2[{WO-1}:0] : ci;')
        A('  always @(posedge clk) begin')
        if D == 1:
            A('    dlr <= nr; dli <= ni;')
        else:
            ap = '~' if cfg.get('altpol') else ''
            A(f'    dlr <= {{{ap}dlr[{WD*(D-1)-1}:0], nr}}; dli <= {{{ap}dli[{WD*(D-1)-1}:0], ni}};')
        if not noreg:
            A(f'    yr <= mode ? srq[{WO-1}:0] : cr;')
            A(f'    yi <= mode ? siq2[{WO-1}:0] : ci;')
        A('  end')
        A('endmodule')
        A('')

    # ---------------- W8 rotators
    for seg, src, dst, R in [(3, 's2', 'w8a', cfg['R3']), (6, 's5', 'w8b', cfg['R6'])]:
        WI, mi = f[src]
        WO, mo = f[dst]
        d = mo - mi
        negm = cfg.get('negmerge')
        A(f'module w8rot{seg}(input clk, input [1:0] sel, input signed [{WI-1}:0] xr, input signed [{WI-1}:0] xi,')
        A(f'  output signed [{WO-1}:0] zr, output signed [{WO-1}:0] zi' + (', output zn);' if negm else ');'))
        if cfg.get('w8pipe'):
            assert negm and R >= 2
            # cycle 1: (U,V) = mult ? (xr+xi, xi-xr) : (xr, xi)   -- narrow cut
            # cycle 2: X,Y = mult ? rnd(K*U), rnd(K*V) : U>>d, V>>d ; swap if sel[1]
            A(f'  wire signed [{WI}:0] u = xr + xi;')
            A(f'  wire signed [{WI}:0] v = xi - xr;')
            A(f'  reg signed [{WI}:0] U, V; reg m1, s1;')
            if cfg.get('w8pipe') == 2:
                # swap folded into the cycle-1 select (one 4:1 mux), so cycle 2
                # is only constant multiply + round + one 2:1 mux
                A('  always @(posedge clk) begin')
                A('    case (sel)')
                A('      2\'d0: begin U <= xr; V <= xi; end')
                A('      2\'d1: begin U <= u;  V <= v;  end')
                A('      2\'d2: begin U <= xi; V <= xr; end')
                A('      default: begin U <= v; V <= u; end')
                A('    endcase')
                A('    m1 <= sel[0]; s1 <= sel[1];')
                A('  end')
            else:
                A('  always @(posedge clk) begin')
                A('    U <= sel[0] ? u : xr; V <= sel[0] ? v : xi; m1 <= sel[0]; s1 <= sel[1];')
                A('  end')
            A(f'  wire signed [31:0] ur = (U * {K} + {1 << (k8 + d - 1)}) >>> {k8 + d};')
            A(f'  wire signed [31:0] vr = (V * {K} + {1 << (k8 + d - 1)}) >>> {k8 + d};')
            A(f'  wire signed [31:0] X = m1 ? ur : (U >>> {d});')
            A(f'  wire signed [31:0] Y = m1 ? vr : (V >>> {d});')
            if cfg.get('w8pipe') == 2:
                prev_r, prev_i, prev_n = f'X[{WO-1}:0]', f'Y[{WO-1}:0]', 's1'
            else:
                prev_r, prev_i, prev_n = f'(s1 ? Y[{WO-1}:0] : X[{WO-1}:0])', f'(s1 ? X[{WO-1}:0] : Y[{WO-1}:0])', 's1'
            for k in range(R - 1):
                A(f'  reg signed [{WO-1}:0] p{k}r, p{k}i; reg p{k}n;')
                A(f'  always @(posedge clk) begin p{k}r <= {prev_r}; p{k}i <= {prev_i}; p{k}n <= {prev_n}; end')
                prev_r, prev_i, prev_n = f'p{k}r', f'p{k}i', f'p{k}n'
            A(f'  assign zr = {prev_r};')
            A(f'  assign zi = {prev_i};')
            A(f'  assign zn = {prev_n};')
            A('endmodule')
            A('')
            continue
        A('  wire signed [31:0] u = xr + xi;')
        A('  wire signed [31:0] v = xi - xr;')
        A(f'  wire signed [31:0] ur = (u * {K} + {1 << (k8 + d - 1)}) >>> {k8 + d};')
        A(f'  wire signed [31:0] vr = (v * {K} + {1 << (k8 + d - 1)}) >>> {k8 + d};')
        A(f'  wire signed [31:0] tr = xr >>> {d};')
        A(f'  wire signed [31:0] ti = xi >>> {d};')
        A('  reg signed [31:0] or_, oi;')
        A('  always @(*) begin')
        A('    case (sel)')
        A('      2\'d0: begin or_ = tr; oi = ti; end')
        A('      2\'d1: begin or_ = ur; oi = vr; end')
        if negm:
            A('      2\'d2: begin or_ = ti; oi = tr; end')
            A('      default: begin or_ = vr; oi = ur; end')
        else:
            A('      2\'d2: begin or_ = ti; oi = -tr; end')
            A('      default: begin or_ = vr; oi = -ur; end')
        A('    endcase')
        A('  end')
        prev_r, prev_i, prev_n = f'or_[{WO-1}:0]', f'oi[{WO-1}:0]', 'sel[1]'
        for k in range(R):
            A(f'  reg signed [{WO-1}:0] p{k}r, p{k}i; reg p{k}n;')
            A(f'  always @(posedge clk) begin p{k}r <= {prev_r}; p{k}i <= {prev_i}; p{k}n <= {prev_n}; end')
            prev_r, prev_i, prev_n = f'p{k}r', f'p{k}i', f'p{k}n'
        A(f'  assign zr = {prev_r};')
        A(f'  assign zi = {prev_i};')
        if negm:
            A(f'  assign zn = {prev_n};')
        A('endmodule')
        A('')

    # ---------------- W64 twiddle multiplier
    WI, mi = f['s3']
    WO, mo = f['w64']
    d = mo - mi
    R = cfg['R4']
    negm = cfg.get('negmerge')
    A(f'module w64mul(input clk, input [5:0] q, input signed [{WI-1}:0] xr, input signed [{WI-1}:0] xi,')
    A(f'  output signed [{WO-1}:0] zr, output signed [{WO-1}:0] zi' + (', output zn);' if negm else ');'))
    gauss = cfg.get('w64gauss')
    if gauss:
        A(f'  reg signed [{tb}:0] C; reg signed [{tb+1}:0] CpS, SmC;')
    else:
        A(f'  reg signed [{tb}:0] C, S;')
    A('  reg t0, t16;')
    A('  always @(*) begin')
    A('    case (q)')
    for p in range(64):
        e = int(tw_index(p))
        c, s_ = tbl[e] if e not in (0, 16) else (0, 0)
        if gauss:
            A(f"      6'd{p}: begin C = {sv_const(c, tb+1)}; CpS = {sv_const(c + s_, tb+2)}; SmC = {sv_const(s_ - c, tb+2)}; t0 = 1'b{int(e == 0)}; t16 = 1'b{int(e == 16)}; end")
        else:
            A(f"      6'd{p}: begin C = {sv_const(c, tb+1)}; S = {sv_const(s_, tb+1)}; t0 = 1'b{int(e == 0)}; t16 = 1'b{int(e == 16)}; end")
    if gauss:
        A("      default: begin C = 0; CpS = 0; SmC = 0; t0 = 1'b0; t16 = 1'b0; end")
    else:
        A("      default: begin C = 0; S = 0; t0 = 1'b0; t16 = 1'b0; end")
    A('    endcase')
    A('  end')
    if gauss:
        A(f'  wire signed [{WI}:0] xs = xr + xi;')
        A('  wire signed [31:0] tt = xs * C;')
        A('  wire signed [31:0] pr = tt - xi * CpS;')
        A('  wire signed [31:0] pi = tt + xr * SmC;')
    else:
        A('  wire signed [31:0] pr = xr * C - xi * S;')
        A('  wire signed [31:0] pi = xr * S + xi * C;')
    A(f'  wire signed [31:0] prr = (pr + {1 << (tb + d - 1)}) >>> {tb + d};')
    A(f'  wire signed [31:0] pir = (pi + {1 << (tb + d - 1)}) >>> {tb + d};')
    A(f'  wire signed [31:0] tr = xr >>> {d};')
    A(f'  wire signed [31:0] ti = xi >>> {d};')
    A('  wire signed [31:0] or_ = t0 ? tr : (t16 ? ti : prr);')
    A('  wire signed [31:0] oi = t0 ? ti : (t16 ? ' + ('tr' if negm else '-tr') + ' : pir);')
    prev_r, prev_i, prev_n = f'or_[{WO-1}:0]', f'oi[{WO-1}:0]', 't16'
    for k in range(R):
        A(f'  reg signed [{WO-1}:0] p{k}r, p{k}i; reg p{k}n;')
        A(f'  always @(posedge clk) begin p{k}r <= {prev_r}; p{k}i <= {prev_i}; p{k}n <= {prev_n}; end')
        prev_r, prev_i, prev_n = f'p{k}r', f'p{k}i', f'p{k}n'
    A(f'  assign zr = {prev_r};')
    A(f'  assign zi = {prev_i};')
    if negm:
        A(f'  assign zn = {prev_n};')
    A('endmodule')
    A('')

    # ---------------- bit-swap reorder circuits
    W6 = f['s6'][0]
    for (i, j) in [(2, 3), (1, 4), (0, 5)]:
        Ls = (1 << j) - (1 << i)
        A(f'module bswap{j}{i}(input clk, input c, input [{2*W6-1}:0] u, output [{2*W6-1}:0] v);')
        A(f'  reg [{2*W6*Ls-1}:0] dl;')
        inv_out = '~' if (cfg.get('altpol') and (Ls - 1) % 2 == 1) else ''
        A(f'  wire [{2*W6-1}:0] o = {inv_out}dl[{2*W6*Ls-1}:{2*W6*(Ls-1)}];')
        A(f'  wire [{2*W6-1}:0] n = c ? o : u;')
        if Ls == 1:
            A('  always @(posedge clk) dl <= n;')
        else:
            ap = '~' if cfg.get('altpol') else ''
            A(f'  always @(posedge clk) dl <= {{{ap}dl[{2*W6*(Ls-1)-1}:0], n}};')
        A('  assign v = c ? u : o;')
        A('endmodule')
        A('')

    # ---------------- segment controller
    A('module segctl #(parameter OFF = 0, parameter TRIG = 0, parameter NB = 6) (')
    A('  input clk, input rst, input st, output [NB-1:0] pos, output reg nxt);')
    A('  localparam [NB-1:0] OFFV = OFF;')
    A('  localparam [NB-1:0] TRIGV = TRIG;')
    A('  reg [NB-1:0] cnt;')
    A('  reg pend;')
    A('  assign pos = st ? OFFV : cnt;')
    A('  wire hit = pend & (pos == TRIGV);')
    A('  always @(posedge clk) begin')
    A('    cnt <= pos + 1\'b1;')
    A('    if (rst) begin pend <= 1\'b0; nxt <= 1\'b0; end')
    A('    else begin nxt <= hit; pend <= st | (pend & ~hit); end')
    A('  end')
    A('endmodule')
    A('')

    if cfg.get('regctl'):
        # Registered-position controller: 'ste' is asserted one cycle before
        # position 0; 'nxe' (the next segment's early start) at pos == TRIG.
        A('module rsegctl #(parameter TRIG = 0, parameter NB = 6) (')
        A('  input clk, input rst, input ste, output [NB-1:0] pos, output nxe);')
        A('  localparam [NB-1:0] TRIGV = TRIG;')
        A('  reg [NB-1:0] cnt;')
        A('  reg pend;')
        A('  assign pos = cnt;')
        A('  assign nxe = pend & (cnt == TRIGV);')
        A('  always @(posedge clk) begin')
        A("    cnt <= ste ? {NB{1'b0}} : cnt + 1'b1;")
        A("    if (rst) pend <= 1'b0;")
        A('    else pend <= ste | (pend & ~nxe);')
        A('  end')
        A('endmodule')
        A('')
        # Input segment: position from the frame_start port, early trigger out.
        A('module segctl1 #(parameter TRIG = 0) (input clk, input rst, input st, output [5:0] pos, output hit);')
        A('  localparam [5:0] TRIGV = TRIG;')
        A('  reg [5:0] cnt;')
        A('  reg pend;')
        A("  assign pos = st ? 6'd0 : cnt;")
        A('  assign hit = pend & (pos == TRIGV);')
        A('  always @(posedge clk) begin')
        A("    cnt <= pos + 1'b1;")
        A("    if (rst) pend <= 1'b0;")
        A('    else pend <= st | (pend & ~hit);')
        A('  end')
        A('endmodule')
        A('')

    # ---------------- top
    W = {k: v[0] for k, v in f.items()}
    m6 = f['s6'][1]
    A('module fft64_top(input wire clk, input wire rst, input wire in_valid, input wire frame_start,')
    A('  input wire signed [15:0] in_re, input wire signed [15:0] in_im,')
    A('  output wire out_valid, output wire out_start, output wire signed [23:0] out_re, output wire signed [23:0] out_im);')
    A('  wire st1 = in_valid & frame_start;')
    R3, R4, R6 = cfg['R3'], cfg['R4'], cfg['R6']
    segs = [(1, 0, 32, 6), (2, 0, 16, 6), (3, R3, 8, 6), (4, R4, 4, 6), (5, 0, 2, 3), (6, R6, 1, 3)]
    for s, R, D, nb in segs:
        trig = R + D - (1 if s in noreg_set(cfg) else 0)
        assert trig >= 1
        if not cfg.get('smallctl') or trig >= (1 << nb):
            nb = 6
        A(f'  wire [5:0] pos{s}; wire st{s+1};')
        if cfg.get('regctl'):
            if s == 1:
                A(f'  segctl1 #(.TRIG({trig})) ctl1(.clk(clk), .rst(rst), .st(st1), .pos(pos1), .hit(st2));')
            elif nb == 6:
                A(f'  rsegctl #(.TRIG({trig}), .NB(6)) ctl{s}(.clk(clk), .rst(rst), .ste(st{s}), .pos(pos{s}), .nxe(st{s+1}));')
            else:
                A(f'  wire [{nb-1}:0] pss{s};')
                A(f'  rsegctl #(.TRIG({trig}), .NB({nb})) ctl{s}(.clk(clk), .rst(rst), .ste(st{s}), .pos(pss{s}), .nxe(st{s+1}));')
                A(f"  assign pos{s} = {{{6-nb}'b0, pss{s}}};")
        elif nb == 6:
            A(f'  segctl #(.OFF(0), .TRIG({trig}), .NB(6)) ctl{s}(.clk(clk), .rst(rst), .st(st{s}), .pos(pos{s}), .nxt(st{s+1}));')
        else:
            A(f'  wire [{nb-1}:0] pss{s};')
            A(f'  segctl #(.OFF(0), .TRIG({trig}), .NB({nb})) ctl{s}(.clk(clk), .rst(rst), .st(st{s}), .pos(pss{s}), .nxt(st{s+1}));')
            A(f"  assign pos{s} = {{{6-nb}'b0, pss{s}}};")
        b = D.bit_length() - 1
        if R == 0:
            A(f'  wire md{s} = pos{s}[{b}];')
        else:
            A(f'  reg [{R-1}:0] mdp{s};')
            A(f'  always @(posedge clk) mdp{s} <= ' + (f'pos{s}[{b}];' if R == 1 else f'{{mdp{s}[{R-2}:0], pos{s}[{b}]}};'))
            A(f'  wire md{s} = mdp{s}[{R-1}];')
    # input
    if cfg.get('clamp15'):
        A('  wire signed [14:0] cin_re = {in_re[15], in_re[13:0] | {14{in_re[14] & ~in_re[15]}}};')
        A('  wire signed [14:0] cin_im = {in_im[15], in_im[13:0] | {14{in_im[14] & ~in_im[15]}}};')
        A(f'  wire signed [{W["inp"]-1}:0] x0r = cin_re >>> {f["inp"][1]};')
        A(f'  wire signed [{W["inp"]-1}:0] x0i = cin_im >>> {f["inp"][1]};')
    else:
        A(f'  wire signed [{W["inp"]-1}:0] x0r = in_re >>> {f["inp"][1]};')
        A(f'  wire signed [{W["inp"]-1}:0] x0i = in_im >>> {f["inp"][1]};')
    # stage 1
    A(f'  wire signed [{W["s1"]-1}:0] y1r, y1i;')
    A('  sdf_stage1 u_s1(.clk(clk), .mode(md1), .br(x0r), .bi(x0i), .yr(y1r), .yi(y1i));')
    # seg2: -j
    A('  wire j2 = pos2[5] & pos2[4];')
    A(f'  wire signed [{W["j2"]-1}:0] b2r = j2 ? y1i : y1r;')
    if cfg.get('negmerge'):
        A(f'  wire signed [{W["j2"]-1}:0] b2i = j2 ? y1r : y1i;')
    else:
        A(f'  wire signed [{W["j2"]-1}:0] b2i = j2 ? -y1r : y1i;')
    A(f'  wire signed [{W["s2"]-1}:0] y2r, y2i;')
    ng = '.ngi(j2), ' if cfg.get('negmerge') else ''
    A(f'  sdf_stage2 u_s2(.clk(clk), .mode(md2), {ng}.br(b2r), .bi(b2i), .yr(y2r), .yi(y2i));')
    # seg3: W8 on position q = pos3 + R3
    A('  wire [5:0] q3 = pos3;')
    A('  wire [1:0] sel3 = q3[3] ? {q3[4], q3[5]} : 2\'d0;')
    A(f'  wire signed [{W["w8a"]-1}:0] b3r, b3i; wire n3;')
    zn = ', .zn(n3)' if cfg.get('negmerge') else ''
    A(f'  w8rot3 u_r3(.clk(clk), .sel(sel3), .xr(y2r), .xi(y2i), .zr(b3r), .zi(b3i){zn});')
    A(f'  wire signed [{W["s3"]-1}:0] y3r, y3i;')
    ng = '.ngi(n3), ' if cfg.get('negmerge') else ''
    A(f'  sdf_stage3 u_s3(.clk(clk), .mode(md3), {ng}.br(b3r), .bi(b3i), .yr(y3r), .yi(y3i));')
    # seg4: W64
    A('  wire [5:0] q4 = pos4;')
    A(f'  wire signed [{W["w64"]-1}:0] b4r, b4i; wire n4;')
    zn = ', .zn(n4)' if cfg.get('negmerge') else ''
    A(f'  w64mul u_m4(.clk(clk), .q(q4), .xr(y3r), .xi(y3i), .zr(b4r), .zi(b4i){zn});')
    A(f'  wire signed [{W["s4"]-1}:0] y4r, y4i;')
    ng = '.ngi(n4), ' if cfg.get('negmerge') else ''
    A(f'  sdf_stage4 u_s4(.clk(clk), .mode(md4), {ng}.br(b4r), .bi(b4i), .yr(y4r), .yi(y4i));')
    # seg5: -j
    A('  wire j5 = pos5[1] & pos5[2];')
    A(f'  wire signed [{W["j5"]-1}:0] b5r = j5 ? y4i : y4r;')
    if cfg.get('negmerge'):
        A(f'  wire signed [{W["j5"]-1}:0] b5i = j5 ? y4r : y4i;')
    else:
        A(f'  wire signed [{W["j5"]-1}:0] b5i = j5 ? -y4r : y4i;')
    A(f'  wire signed [{W["s5"]-1}:0] y5r, y5i;')
    ng = '.ngi(j5), ' if cfg.get('negmerge') else ''
    A(f'  sdf_stage5 u_s5(.clk(clk), .mode(md5), {ng}.br(b5r), .bi(b5i), .yr(y5r), .yi(y5i));')
    # seg6: W8
    A('  wire [5:0] q6 = pos6;')
    A('  wire [1:0] sel6 = q6[0] ? {q6[1], q6[2]} : 2\'d0;')
    A(f'  wire signed [{W["w8b"]-1}:0] b6r, b6i; wire n6;')
    zn = ', .zn(n6)' if cfg.get('negmerge') else ''
    A(f'  w8rot6 u_r6(.clk(clk), .sel(sel6), .xr(y5r), .xi(y5i), .zr(b6r), .zi(b6i){zn});')
    A(f'  wire signed [{W["s6"]-1}:0] y6r, y6i;')
    ng = '.ngi(n6), ' if cfg.get('negmerge') else ''
    A(f'  sdf_stage6 u_s6(.clk(clk), .mode(md6), {ng}.br(b6r), .bi(b6i), .yr(y6r), .yi(y6i));')
    # reorder chain
    if cfg.get('regctl'):
        A('  wire [3:0] pe32; wire ste41;')
        A('  rsegctl #(.TRIG(3), .NB(4)) ctl7(.clk(clk), .rst(rst), .ste(st7), .pos(pe32), .nxe(ste41));')
        A('  wire [4:0] pe41; wire ste50;')
        A('  rsegctl #(.TRIG(13), .NB(5)) ctl8(.clk(clk), .rst(rst), .ste(ste41), .pos(pe41), .nxe(ste50));')
        A('  wire [5:0] pe50; wire oste; reg ostart;')
        A('  rsegctl #(.TRIG(30), .NB(6)) ctl9(.clk(clk), .rst(rst), .ste(ste50), .pos(pe50), .nxe(oste));')
        A("  always @(posedge clk) ostart <= rst ? 1'b0 : oste;")
    else:
        A('  wire [3:0] pe32; wire ste41;')
        A('  segctl #(.OFF(0), .TRIG(3), .NB(4)) ctl7(.clk(clk), .rst(rst), .st(st7), .pos(pe32), .nxt(ste41));')
        A('  wire [4:0] pe41; wire ste50;')
        A('  segctl #(.OFF(0), .TRIG(13), .NB(5)) ctl8(.clk(clk), .rst(rst), .st(ste41), .pos(pe41), .nxt(ste50));')
        A('  wire [5:0] pe50; wire ostart;')
        A('  segctl #(.OFF(0), .TRIG(30), .NB(6)) ctl9(.clk(clk), .rst(rst), .st(ste50), .pos(pe50), .nxt(ostart));')
    A(f'  wire [{2*W6-1}:0] r0, r1, r2, r3;')
    A('  assign r0 = {y6r, y6i};')
    A('  bswap32 u_b32(.clk(clk), .c(pe32[3] & ~pe32[2]), .u(r0), .v(r1));')
    A('  bswap41 u_b41(.clk(clk), .c(pe41[4] & ~pe41[1]), .u(r1), .v(r2));')
    A('  bswap50 u_b50(.clk(clk), .c(pe50[5] & ~pe50[0]), .u(r2), .v(r3));')
    # output control
    A('  reg ovr; reg [5:0] oc;')
    A('  always @(posedge clk) begin')
    A('    if (rst) ovr <= 1\'b0;')
    A('    else if (ostart) ovr <= 1\'b1;')
    A('    else if (oc == 6\'d63) ovr <= 1\'b0;')
    A('    oc <= ostart ? 6\'d1 : oc + 6\'d1;')
    A('  end')
    A('  assign out_valid = ostart | ovr;')
    A('  assign out_start = ostart;')
    pad = 24 - W6 - m6
    zeros = f", {m6}'b0" if m6 > 0 else ''
    A(f'  assign out_re = {{{{{pad}{{r3[{2*W6-1}]}}}}, r3[{2*W6-1}:{W6}]{zeros}}};')
    A(f'  assign out_im = {{{{{pad}{{r3[{W6-1}]}}}}, r3[{W6-1}:0]{zeros}}};')
    A('endmodule')
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    cfg = dict(DEFAULT)
    if len(sys.argv) > 2:
        cfg.update(json.loads(open(sys.argv[2]).read()))
    out = sys.argv[1] if len(sys.argv) > 1 else 'fft64_top.v'
    open(out, 'w').write(gen_rtl(cfg))
    print('formats', formats(cfg))
    print('storage bits', storage_bits(cfg))
