`timescale  1ns / 1ps

module hk_mash111 #(
    parameter WIDTH = 9,
    parameter A_GAIN = 2,
    parameter OUT_REG = 1
) (
    input clk,
    input rst_n,
    

    input [WIDTH-1:0] x_i,
    output [3:0] y_o,
    output [WIDTH-1:0] e_o
);

    wire [WIDTH-1:0] x_i_1;
    wire [WIDTH-1:0] e_o_1;
    wire y_o_1;
    wire [WIDTH-1:0] x_i_2;
    wire [WIDTH-1:0] e_o_2;
    wire y_o_2;
    wire [WIDTH-1:0] x_i_3;
    wire [WIDTH-1:0] e_o_3;
    wire y_o_3;

    wire y1_i;
    wire y2_i;
    wire y3_i;

    assign x_i_1 = x_i;
    assign x_i_2 = e_o_1;
    assign x_i_3 = e_o_2;

    assign e_o = e_o_3;

    hk_efm #(
        .WIDTH ( WIDTH ),
        .A_GAIN( A_GAIN ),
        .OUT_REG ( OUT_REG ))
    u_hk_efm_1 (
        .clk                     ( clk     ),
        .rst_n                   ( rst_n   ),
        .x_i                     ( x_i_1   ),

        .y_o                     ( y_o_1   ),
        .e_o                     ( e_o_1   )
    );

    hk_efm #(
        .WIDTH ( WIDTH ),
        .A_GAIN( A_GAIN ),
        .OUT_REG ( OUT_REG ))
    u_hk_efm_2 (
        .clk                     ( clk     ),
        .rst_n                   ( rst_n   ),
        .x_i                     ( x_i_2   ),

        .y_o                     ( y_o_2   ),
        .e_o                     ( e_o_2   )
    );

    hk_efm #(
        .WIDTH ( WIDTH ),
        .A_GAIN( A_GAIN ),
        .OUT_REG ( OUT_REG ))
    u_hk_efm_3 (
        .clk                     ( clk     ),
        .rst_n                   ( rst_n   ),
        .x_i                     ( x_i_3   ),

        .y_o                     ( y_o_3   ),
        .e_o                     ( e_o_3   )
    );

    ncl #(
        .OUT_REG ( 1 ))
    u_ncl (
        .clk                     ( clk     ),
        .rst_n                   ( rst_n   ),
        .y1_i                    ( y1_i    ),
        .y2_i                    ( y2_i    ),
        .y3_i                    ( y3_i    ),

        .y_o                     ( y_o     )
    );

    generate
        if (OUT_REG) begin
            wire y1_reg_0;
            wire y1_reg_1;
            wire y2_reg_0;
            dff #(
                .WIDTH     ( 1 ),
                .WITH_RST  ( 0 ),
                .RST_VALUE ( 0 ))
            u0_dff (
                .clk                     ( clk    ),
                .rst_n                   ( rst_n  ),
                .D                       ( y_o_1   ),

                .Q                       ( y1_reg_0 )
            );
            dff #(
                .WIDTH     ( 1 ),
                .WITH_RST  ( 0 ),
                .RST_VALUE ( 0 ))
            u1_dff (
                .clk                     ( clk    ),
                .rst_n                   ( rst_n  ),
                .D                       ( y1_reg_0   ),

                .Q                       ( y1_reg_1 )
            );
            dff #(
                .WIDTH     ( 1 ),
                .WITH_RST  ( 0 ),
                .RST_VALUE ( 0 ))
            u2_dff (
                .clk                     ( clk    ),
                .rst_n                   ( rst_n  ),
                .D                       ( y_o_2   ),

                .Q                       ( y2_reg_0 )
            );
            assign y1_i = y1_reg_1;
            assign y2_i = y2_reg_0;
            assign y3_i = y_o_3;
        end else begin
            assign y1_i = y_o_1;
            assign y2_i = y_o_2;
            assign y3_i = y_o_3;
        end
    endgenerate
    
endmodule