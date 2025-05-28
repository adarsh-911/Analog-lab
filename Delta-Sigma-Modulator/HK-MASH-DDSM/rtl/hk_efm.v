`timescale  1ns / 1ps

module hk_efm #(
    parameter WIDTH = 24,
    parameter A_GAIN = 1,
    parameter OUT_REG = 0
) (
    input clk,
    input rst_n,

    input [WIDTH-1:0] x_i,
    output y_o,
    output [WIDTH-1:0] e_o
);

    wire [WIDTH:0] sum;
    reg [WIDTH:0] sum_r;

    assign sum = x_i + sum_r[WIDTH-1:0] + {A_GAIN{sum_r[WIDTH]}};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_r <= 'b0;
        end else begin
            sum_r <= sum;
        end
    end

    assign y_o = sum_r[WIDTH];

    generate
        if (OUT_REG) begin
            assign e_o = sum_r[WIDTH-1:0];
        end else begin
            assign e_o = sum[WIDTH-1:0];
        end
    endgenerate

endmodule