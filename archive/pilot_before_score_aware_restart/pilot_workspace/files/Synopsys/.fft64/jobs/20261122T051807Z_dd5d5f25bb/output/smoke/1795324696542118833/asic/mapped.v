/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Expert(TM) in wire load mode
// Version   : L-2016.03-SP1
// Date      : Sun Nov 22 13:19:08 2026
/////////////////////////////////////////////////////////////


module fft64_top ( clk, rst, in_valid, frame_start, in_re, in_im, out_valid, 
        out_start, out_re, out_im );
  input [15:0] in_re;
  input [15:0] in_im;
  output [23:0] out_re;
  output [23:0] out_im;
  input clk, rst, in_valid, frame_start;
  output out_valid, out_start;
  wire   n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, n16,
         n17, n18, n19, n20, n21, n22, n23, n24, n25, n26, n27, n28, n29, n30,
         n31, n32, n33, n34, n35, n36, n37, n38, n55, n56, n57, n58, n59, n60,
         n61, n62, n63, n64, n65, n66, n67, n68, n69, n70, n71, n72, n73, n74,
         n75, n76, n77, n78, n79, n80, n81, n82, n83, n84, n85, n86, n87;

  DFFHQNx1_ASAP7_75t_R out_im_reg_14_ ( .D(n87), .CLK(clk), .QN(out_im[14]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_13_ ( .D(n86), .CLK(clk), .QN(out_im[13]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_12_ ( .D(n85), .CLK(clk), .QN(out_im[12]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_11_ ( .D(n84), .CLK(clk), .QN(out_im[11]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_10_ ( .D(n83), .CLK(clk), .QN(out_im[10]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_9_ ( .D(n82), .CLK(clk), .QN(out_im[9]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_8_ ( .D(n81), .CLK(clk), .QN(out_im[8]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_7_ ( .D(n80), .CLK(clk), .QN(out_im[7]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_6_ ( .D(n79), .CLK(clk), .QN(out_im[6]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_5_ ( .D(n78), .CLK(clk), .QN(out_im[5]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_4_ ( .D(n77), .CLK(clk), .QN(out_im[4]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_3_ ( .D(n76), .CLK(clk), .QN(out_im[3]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_2_ ( .D(n75), .CLK(clk), .QN(out_im[2]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_1_ ( .D(n74), .CLK(clk), .QN(out_im[1]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_0_ ( .D(n73), .CLK(clk), .QN(out_im[0]) );
  DFFHQNx1_ASAP7_75t_R out_valid_reg ( .D(n72), .CLK(clk), .QN(out_valid) );
  DFFHQNx1_ASAP7_75t_R out_start_reg ( .D(n3), .CLK(clk), .QN(out_start) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_14_ ( .D(n71), .CLK(clk), .QN(out_re[14]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_13_ ( .D(n70), .CLK(clk), .QN(out_re[13]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_12_ ( .D(n69), .CLK(clk), .QN(out_re[12]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_11_ ( .D(n68), .CLK(clk), .QN(out_re[11]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_10_ ( .D(n67), .CLK(clk), .QN(out_re[10]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_9_ ( .D(n66), .CLK(clk), .QN(out_re[9]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_8_ ( .D(n65), .CLK(clk), .QN(out_re[8]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_7_ ( .D(n64), .CLK(clk), .QN(out_re[7]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_6_ ( .D(n63), .CLK(clk), .QN(out_re[6]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_5_ ( .D(n62), .CLK(clk), .QN(out_re[5]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_4_ ( .D(n61), .CLK(clk), .QN(out_re[4]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_3_ ( .D(n60), .CLK(clk), .QN(out_re[3]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_2_ ( .D(n59), .CLK(clk), .QN(out_re[2]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_1_ ( .D(n58), .CLK(clk), .QN(out_re[1]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_0_ ( .D(n57), .CLK(clk), .QN(out_re[0]) );
  DFFHQNx1_ASAP7_75t_R out_im_reg_15_ ( .D(n56), .CLK(clk), .QN(out_im[16]) );
  DFFHQNx1_ASAP7_75t_R out_re_reg_15_ ( .D(n55), .CLK(clk), .QN(out_re[16]) );
  INVxp33_ASAP7_75t_R U38 ( .A(out_im[16]), .Y(n37) );
  NAND2xp33_ASAP7_75t_R U39 ( .A(in_re[3]), .B(n38), .Y(n16) );
  NAND2xp33_ASAP7_75t_R U40 ( .A(in_im[1]), .B(n38), .Y(n34) );
  INVxp33_ASAP7_75t_R U41 ( .A(n37), .Y(out_im[15]) );
  INVxp33_ASAP7_75t_R U42 ( .A(n37), .Y(out_im[21]) );
  INVxp33_ASAP7_75t_R U43 ( .A(out_re[16]), .Y(n36) );
  INVxp33_ASAP7_75t_R U44 ( .A(n36), .Y(out_re[17]) );
  INVxp33_ASAP7_75t_R U45 ( .A(n36), .Y(out_re[18]) );
  INVxp33_ASAP7_75t_R U46 ( .A(n36), .Y(out_re[19]) );
  INVxp33_ASAP7_75t_R U47 ( .A(n36), .Y(out_re[20]) );
  INVxp33_ASAP7_75t_R U48 ( .A(n36), .Y(out_re[21]) );
  INVxp33_ASAP7_75t_R U49 ( .A(n36), .Y(out_re[22]) );
  INVxp33_ASAP7_75t_R U50 ( .A(n36), .Y(out_re[23]) );
  INVxp33_ASAP7_75t_R U51 ( .A(n36), .Y(out_re[15]) );
  INVxp33_ASAP7_75t_R U52 ( .A(n37), .Y(out_im[17]) );
  INVxp33_ASAP7_75t_R U53 ( .A(n37), .Y(out_im[18]) );
  INVxp33_ASAP7_75t_R U54 ( .A(n37), .Y(out_im[19]) );
  INVxp33_ASAP7_75t_R U55 ( .A(n37), .Y(out_im[20]) );
  INVxp33_ASAP7_75t_R U56 ( .A(n37), .Y(out_im[22]) );
  INVxp33_ASAP7_75t_R U57 ( .A(n37), .Y(out_im[23]) );
  INVxp33_ASAP7_75t_R U58 ( .A(rst), .Y(n38) );
  NAND2xp33_ASAP7_75t_R U59 ( .A(in_re[15]), .B(n38), .Y(n4) );
  NAND2xp33_ASAP7_75t_R U60 ( .A(in_im[13]), .B(n38), .Y(n22) );
  NAND2xp33_ASAP7_75t_R U61 ( .A(in_im[11]), .B(n38), .Y(n24) );
  NAND2xp33_ASAP7_75t_R U62 ( .A(in_im[10]), .B(n38), .Y(n25) );
  NAND2xp33_ASAP7_75t_R U63 ( .A(in_im[9]), .B(n38), .Y(n26) );
  NAND2xp33_ASAP7_75t_R U64 ( .A(in_im[8]), .B(n38), .Y(n27) );
  NAND2xp33_ASAP7_75t_R U65 ( .A(in_im[7]), .B(n38), .Y(n28) );
  NAND2xp33_ASAP7_75t_R U66 ( .A(in_im[6]), .B(n38), .Y(n29) );
  NAND2xp33_ASAP7_75t_R U67 ( .A(in_im[12]), .B(n38), .Y(n23) );
  NAND2xp33_ASAP7_75t_R U68 ( .A(in_im[4]), .B(n38), .Y(n31) );
  NAND2xp33_ASAP7_75t_R U69 ( .A(in_im[3]), .B(n38), .Y(n32) );
  NAND2xp33_ASAP7_75t_R U70 ( .A(in_im[2]), .B(n38), .Y(n33) );
  NAND2xp33_ASAP7_75t_R U71 ( .A(in_im[0]), .B(n38), .Y(n35) );
  NAND2xp33_ASAP7_75t_R U72 ( .A(in_valid), .B(n38), .Y(n2) );
  NAND2xp33_ASAP7_75t_R U73 ( .A(in_im[5]), .B(n38), .Y(n30) );
  NAND2xp33_ASAP7_75t_R U74 ( .A(in_im[14]), .B(n38), .Y(n21) );
  NAND2xp33_ASAP7_75t_R U75 ( .A(in_re[14]), .B(n38), .Y(n5) );
  NAND2xp33_ASAP7_75t_R U76 ( .A(in_re[13]), .B(n38), .Y(n6) );
  NAND2xp33_ASAP7_75t_R U77 ( .A(in_re[12]), .B(n38), .Y(n7) );
  NAND2xp33_ASAP7_75t_R U78 ( .A(in_re[11]), .B(n38), .Y(n8) );
  NAND2xp33_ASAP7_75t_R U79 ( .A(in_re[10]), .B(n38), .Y(n9) );
  NAND2xp33_ASAP7_75t_R U80 ( .A(in_re[9]), .B(n38), .Y(n10) );
  NAND2xp33_ASAP7_75t_R U81 ( .A(in_re[8]), .B(n38), .Y(n11) );
  NAND2xp33_ASAP7_75t_R U82 ( .A(in_re[7]), .B(n38), .Y(n12) );
  NAND2xp33_ASAP7_75t_R U83 ( .A(in_re[6]), .B(n38), .Y(n13) );
  NAND2xp33_ASAP7_75t_R U84 ( .A(in_re[5]), .B(n38), .Y(n14) );
  NAND2xp33_ASAP7_75t_R U85 ( .A(in_re[4]), .B(n38), .Y(n15) );
  NAND2xp33_ASAP7_75t_R U86 ( .A(in_re[2]), .B(n38), .Y(n17) );
  NAND2xp33_ASAP7_75t_R U87 ( .A(in_re[1]), .B(n38), .Y(n18) );
  NAND2xp33_ASAP7_75t_R U88 ( .A(in_re[0]), .B(n38), .Y(n19) );
  NAND2xp33_ASAP7_75t_R U89 ( .A(in_im[15]), .B(n38), .Y(n20) );
  NAND3xp33_ASAP7_75t_R U90 ( .A(in_valid), .B(frame_start), .C(n38), .Y(n3)
         );
  HB1xp67_ASAP7_75t_R U91 ( .A(n4), .Y(n55) );
  HB1xp67_ASAP7_75t_R U92 ( .A(n20), .Y(n56) );
  HB1xp67_ASAP7_75t_R U93 ( .A(n19), .Y(n57) );
  HB1xp67_ASAP7_75t_R U94 ( .A(n18), .Y(n58) );
  HB1xp67_ASAP7_75t_R U95 ( .A(n17), .Y(n59) );
  HB1xp67_ASAP7_75t_R U96 ( .A(n16), .Y(n60) );
  HB1xp67_ASAP7_75t_R U97 ( .A(n15), .Y(n61) );
  HB1xp67_ASAP7_75t_R U98 ( .A(n14), .Y(n62) );
  HB1xp67_ASAP7_75t_R U99 ( .A(n13), .Y(n63) );
  HB1xp67_ASAP7_75t_R U100 ( .A(n12), .Y(n64) );
  HB1xp67_ASAP7_75t_R U101 ( .A(n11), .Y(n65) );
  HB1xp67_ASAP7_75t_R U102 ( .A(n10), .Y(n66) );
  HB1xp67_ASAP7_75t_R U103 ( .A(n9), .Y(n67) );
  HB1xp67_ASAP7_75t_R U104 ( .A(n8), .Y(n68) );
  HB1xp67_ASAP7_75t_R U105 ( .A(n7), .Y(n69) );
  HB1xp67_ASAP7_75t_R U106 ( .A(n6), .Y(n70) );
  HB1xp67_ASAP7_75t_R U107 ( .A(n5), .Y(n71) );
  HB1xp67_ASAP7_75t_R U108 ( .A(n2), .Y(n72) );
  HB1xp67_ASAP7_75t_R U109 ( .A(n35), .Y(n73) );
  HB1xp67_ASAP7_75t_R U110 ( .A(n34), .Y(n74) );
  HB1xp67_ASAP7_75t_R U111 ( .A(n33), .Y(n75) );
  HB1xp67_ASAP7_75t_R U112 ( .A(n32), .Y(n76) );
  HB1xp67_ASAP7_75t_R U113 ( .A(n31), .Y(n77) );
  HB1xp67_ASAP7_75t_R U114 ( .A(n30), .Y(n78) );
  HB1xp67_ASAP7_75t_R U115 ( .A(n29), .Y(n79) );
  HB1xp67_ASAP7_75t_R U116 ( .A(n28), .Y(n80) );
  HB1xp67_ASAP7_75t_R U117 ( .A(n27), .Y(n81) );
  HB1xp67_ASAP7_75t_R U118 ( .A(n26), .Y(n82) );
  HB1xp67_ASAP7_75t_R U119 ( .A(n25), .Y(n83) );
  HB1xp67_ASAP7_75t_R U120 ( .A(n24), .Y(n84) );
  HB1xp67_ASAP7_75t_R U121 ( .A(n23), .Y(n85) );
  HB1xp67_ASAP7_75t_R U122 ( .A(n22), .Y(n86) );
  HB1xp67_ASAP7_75t_R U123 ( .A(n21), .Y(n87) );
endmodule

