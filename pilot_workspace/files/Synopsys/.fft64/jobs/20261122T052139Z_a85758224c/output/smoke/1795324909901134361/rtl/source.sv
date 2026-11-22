module fft64_top(
 input wire clk,rst,in_valid,frame_start,
 input wire signed [15:0] in_re,in_im,
 output reg out_valid,out_start,
 output reg signed [23:0] out_re,out_im);
 always @(posedge clk) begin
  if(rst) begin out_valid<=0;out_start<=0;out_re<=0;out_im<=0;end
  else begin
   out_valid<=in_valid;out_start<=in_valid && frame_start;
   out_re<={{8{in_re[15]}},in_re};out_im<={{8{in_im[15]}},in_im};
  end
 end
endmodule
