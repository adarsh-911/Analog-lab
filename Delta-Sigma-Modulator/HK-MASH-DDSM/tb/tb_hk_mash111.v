`timescale  1ns / 1ps

module tb_hk_mash111;

// mash111 Parameters
parameter PERIOD = 10;
// parameter WIDTH  = 24;
parameter WIDTH  = 20;
parameter A_GAIN = 2;
parameter OUT_REG = 1;

// mash111 Inputs
reg   clk                                  = 0 ;
reg   rst_n                                = 0 ;
reg   [WIDTH-1:0]  x_i                     = 0 ;

// mash111 Outputs
wire  [3:0]  y_o                           ;
wire  [WIDTH-1:0]  e_o                     ;


initial
begin
    forever #(PERIOD/2)  clk=~clk;
end

initial
begin
    #(PERIOD*2) rst_n  =  1;
end

integer dout_file;
initial begin
    dout_file=$fopen("mash111-hkefm-data-20bit-a2-reg-new.txt", "w");   
    if(dout_file == 0)begin 
        $display ("can not open the file!");   
        $stop;
    end
end

always @(posedge clk) begin
    $fdisplay(dout_file,"%d",$signed(y_o));    
end    

hk_mash111 #(
    .WIDTH ( WIDTH ),
    .A_GAIN( A_GAIN ),
    .OUT_REG ( OUT_REG ))
 u_hk_mash111 (
    .clk                     ( clk                ),
    .rst_n                   ( rst_n              ),
    .x_i                     ( x_i    [WIDTH-1:0] ),

    .y_o                     ( y_o    [3:0]       ),
    .e_o                     ( e_o    [WIDTH-1:0] )
);

initial
begin
    x_i = 'b10000000000000000000; // Choose according to width
    # (PERIOD*10000);

    $finish;
end

endmodule