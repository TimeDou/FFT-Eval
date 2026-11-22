// Folded radix-2 DIF, parity-banked complete storage. All memories map to flops.
module fft64_top (
 input wire clk, rst, in_valid, frame_start,
 input wire signed [15:0] in_re, in_im,
 output reg out_valid, out_start,
 output reg signed [23:0] out_re, out_im
);
 localparam W=20, DROP=2, TF=13;
 localparam IDLE=0, LOAD=1, CALC=2, SEND=3;
 reg [1:0] state;
 reg [5:0] icnt, ocnt;
 reg [4:0] bc;
 reg [2:0] stage;
 reg signed [W-1:0] re0[0:31], im0[0:31], re1[0:31], im1[0:31];
 reg [5:0] ia, ib;
 always @* begin
   case(stage)
   0: ia={bc,1'b0};
   1: ia={bc[4:1],1'b0,bc[0]};
   2: ia={bc[4:2],1'b0,bc[1:0]};
   3: ia={bc[4:3],1'b0,bc[2:0]};
   4: ia={bc[4],1'b0,bc[3:0]};
   default: ia={1'b0,bc};
   endcase
   ib=ia^(6'b1<<stage);
 end
 wire bank_a=^ia;
 wire [4:0] ra0=bank_a ? ib[4:0] : ia[4:0];
 wire [4:0] ra1=bank_a ? ia[4:0] : ib[4:0];
 wire signed [W-1:0] ar=bank_a?re1[ra1]:re0[ra0];
 wire signed [W-1:0] ai=bank_a?im1[ra1]:im0[ra0];
 wire signed [W-1:0] br=bank_a?re0[ra0]:re1[ra1];
 wire signed [W-1:0] bi=bank_a?im0[ra0]:im1[ra1];
 wire signed [W-1:0] sr=ar+br, si=ai+bi, dr=ar-br, di=ai-bi;
 wire [4:0] exponent=(ia[4:0] << (5-stage));
 reg signed [TF+1:0] wr,wi;
 always @* begin
   wr=0;wi=0;
   case(exponent)
      5'd0: begin wr=15'sd8192; wi=15'sd0; end
      5'd1: begin wr=15'sd8153; wi=-15'sd803; end
      5'd2: begin wr=15'sd8035; wi=-15'sd1598; end
      5'd3: begin wr=15'sd7839; wi=-15'sd2378; end
      5'd4: begin wr=15'sd7568; wi=-15'sd3135; end
      5'd5: begin wr=15'sd7225; wi=-15'sd3862; end
      5'd6: begin wr=15'sd6811; wi=-15'sd4551; end
      5'd7: begin wr=15'sd6333; wi=-15'sd5197; end
      5'd8: begin wr=15'sd5793; wi=-15'sd5793; end
      5'd9: begin wr=15'sd5197; wi=-15'sd6333; end
      5'd10: begin wr=15'sd4551; wi=-15'sd6811; end
      5'd11: begin wr=15'sd3862; wi=-15'sd7225; end
      5'd12: begin wr=15'sd3135; wi=-15'sd7568; end
      5'd13: begin wr=15'sd2378; wi=-15'sd7839; end
      5'd14: begin wr=15'sd1598; wi=-15'sd8035; end
      5'd15: begin wr=15'sd803; wi=-15'sd8153; end
      5'd16: begin wr=15'sd0; wi=-15'sd8192; end
      5'd17: begin wr=-15'sd803; wi=-15'sd8153; end
      5'd18: begin wr=-15'sd1598; wi=-15'sd8035; end
      5'd19: begin wr=-15'sd2378; wi=-15'sd7839; end
      5'd20: begin wr=-15'sd3135; wi=-15'sd7568; end
      5'd21: begin wr=-15'sd3862; wi=-15'sd7225; end
      5'd22: begin wr=-15'sd4551; wi=-15'sd6811; end
      5'd23: begin wr=-15'sd5197; wi=-15'sd6333; end
      5'd24: begin wr=-15'sd5793; wi=-15'sd5793; end
      5'd25: begin wr=-15'sd6333; wi=-15'sd5197; end
      5'd26: begin wr=-15'sd6811; wi=-15'sd4551; end
      5'd27: begin wr=-15'sd7225; wi=-15'sd3862; end
      5'd28: begin wr=-15'sd7568; wi=-15'sd3135; end
      5'd29: begin wr=-15'sd7839; wi=-15'sd2378; end
      5'd30: begin wr=-15'sd8035; wi=-15'sd1598; end
      5'd31: begin wr=-15'sd8153; wi=-15'sd803; end
   endcase
 end
 wire signed [W+TF+1:0] rr=dr*wr, ii=di*wi, ri=dr*wi, ir=di*wr;
 wire signed [W+TF+2:0] tr=$signed(rr)-$signed(ii);
 wire signed [W+TF+2:0] ti=$signed(ri)+$signed(ir);
 wire signed [W-1:0] xr=exponent==0 ? dr : exponent==16 ? di : (tr >>> TF);
 wire signed [W-1:0] xi=exponent==0 ? di : exponent==16 ? -dr : (ti >>> TF);
 wire [5:0] ip=(state==IDLE)?6'd0:icnt;
 wire ibank=^ip;
 wire [5:0] op={ocnt[0],ocnt[1],ocnt[2],ocnt[3],ocnt[4],ocnt[5]};
 wire signed [W-1:0] yr=(^op)?re1[op[4:0]]:re0[op[4:0]];
 wire signed [W-1:0] yi=(^op)?im1[op[4:0]]:im0[op[4:0]];
 // Storage is intentionally not reset; control prevents reads before writes.
 always @(posedge clk) begin
   if(!rst) begin
     if((state==IDLE && in_valid && frame_start)||(state==LOAD && in_valid)) begin
       if(ibank) begin re1[ip[4:0]] <= $signed(in_re) >>> DROP; im1[ip[4:0]] <= $signed(in_im) >>> DROP; end
       else begin re0[ip[4:0]] <= $signed(in_re) >>> DROP; im0[ip[4:0]] <= $signed(in_im) >>> DROP; end
     end else if(state==CALC) begin
       if(bank_a) begin
         re1[ra1]<=sr; im1[ra1]<=si; re0[ra0]<=xr; im0[ra0]<=xi;
       end else begin
         re0[ra0]<=sr; im0[ra0]<=si; re1[ra1]<=xr; im1[ra1]<=xi;
       end
     end
   end
 end
 always @(posedge clk) begin
   if(rst) begin
     state<=IDLE;icnt<=0;ocnt<=0;bc<=0;stage<=5;
     out_valid<=0;out_start<=0;
   end else begin
     out_valid<=0;out_start<=0;
     case(state)
       IDLE: if(in_valid && frame_start) begin state<=LOAD;icnt<=1;end
       LOAD: if(in_valid) begin
         icnt<=icnt+1'b1;
         if(icnt==63) begin state<=CALC;stage<=5;bc<=0;end
       end
       CALC: begin
         bc<=bc+1'b1;
         if(bc==31) begin
           stage<=stage-1'b1;
           if(stage==0) begin state<=SEND;ocnt<=0;end
         end
       end
       SEND: begin
         out_valid<=1;out_start<=ocnt==0;
         out_re<=$signed(yr) * (1<<DROP);out_im<=$signed(yi) * (1<<DROP);
         ocnt<=ocnt+1'b1;
         if(ocnt==63) state<=IDLE;
       end
     endcase
   end
 end
endmodule
