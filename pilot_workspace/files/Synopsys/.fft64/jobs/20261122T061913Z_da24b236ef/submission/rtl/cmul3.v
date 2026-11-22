// 3-multiplier (Karatsuba-style) complex multiplier with fixed-point rounding.
//   (pr + j pi) = (ar + j ai) * (wr + j wi)
//   t1 = (ar+ai)*wr ; t2 = ar*(wi-wr) ; t3 = ai*(wr+wi)
//   pr = t1 - t3    ; pi = t1 + t2
// The three operand pre-sums (arpai, wmwr, wpwi) are supplied by pipeline
// registers so that only the array multiplier and the rounding adder remain
// on the critical path.  Results carry TWF extra fractional bits and are
// rounded back with round-half-up.
module cmul3 #(
    parameter integer DW  = 22,   // data width (signed)
    parameter integer TWB = 14,   // twiddle width (signed)
    parameter integer TWF = 12    // twiddle fractional bits (shift amount)
) (
    input  wire signed [DW-1:0]    ar,
    input  wire signed [DW-1:0]    ai,
    input  wire signed [DW:0]      arpai,
    input  wire signed [TWB-1:0]   wr,
    input  wire signed [TWB-1:0]   wi,
    input  wire signed [TWB:0]     wmwr,
    input  wire signed [TWB:0]     wpwi,
    output wire signed [DW-1:0]    pr,
    output wire signed [DW-1:0]    pi
);
    wire signed [DW+TWB:0] t1 = arpai * wr;
    wire signed [DW+TWB:0] t2 = ar * wmwr;
    wire signed [DW+TWB:0] t3 = ai * wpwi;

    wire signed [DW+TWB:0] prf = t1 - t3;
    wire signed [DW+TWB:0] pif = t1 + t2;

    wire signed [DW+TWB:0] rnd = {{(DW+TWB-1){1'b0}}, 1'b1} <<< (TWF-1);

    wire signed [DW+TWB:0] prr = (prf + rnd) >>> TWF;
    wire signed [DW+TWB:0] pir = (pif + rnd) >>> TWF;

    assign pr = prr[DW-1:0];
    assign pi = pir[DW-1:0];
endmodule
