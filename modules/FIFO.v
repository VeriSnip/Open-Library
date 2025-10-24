`timescale 1ns / 1ps

module FIFO #(
    parameter integer WIDTH = 8,
    parameter integer DEPTH = 16
) (
    input wire clk_i,
    input wire rst_i,

    // Write port
    input wire             wr_en_i,
    input wire [WIDTH-1:0] wr_data_i,

    // Read port
    input  wire             rd_en_i,
    output reg  [WIDTH-1:0] rd_data_o,

    output wire empty_o,
    output wire full_o
);
  wire tunnel_en;
  wire int_wr_en;
  wire int_rd_en;

  assign tunnel_en = wr_en_i & rd_en_i & empty_o;
  assign int_wr_en = wr_en_i & (~full_o | rd_en_i) & ~tunnel_en;
  assign int_rd_en = rd_en_i & ~empty_o;

  generate
    if (DEPTH == 1) begin : gen_one_depth_fifo
      // Storage
      reg [WIDTH-1:0] mem;
      reg wptr;  // wrap flag
      reg rptr;

      assign full_o  = (wptr ^ rptr);
      assign empty_o = (wptr ~^ rptr);

      always_ff @(posedge clk_i) begin
        if (rst_i) begin
          wptr <= 1'b0;
          rptr <= 1'b0;
        end else begin
          if (int_wr_en) begin
            mem  <= wr_data_i;
            wptr <= wptr + 1;
          end
          if (int_rd_en) begin
            rptr <= rptr + 1;
          end
        end
      end

      always_comb begin
        if (tunnel_en) rd_data_o = wr_data_i;
        else rd_data_o = mem;
      end
    end else begin : gen_fifo
      localparam int ADDR_W = $clog2(DEPTH);

      // Storage
      reg [WIDTH-1:0] mem[DEPTH];
      reg [ADDR_W:0] wptr;  // MSB is wrap flag
      reg [ADDR_W:0] rptr;

      assign full_o  = (wptr[ADDR_W] ^ rptr[ADDR_W]) & (wptr[ADDR_W-1:0] == rptr[ADDR_W-1:0]);
      assign empty_o = (wptr == rptr);

      always_ff @(posedge clk_i) begin
        if (rst_i) begin
          wptr <= '0;
          rptr <= '0;
        end else begin
          if (int_wr_en) begin
            mem[wptr[ADDR_W-1:0]] <= wr_data_i;
            wptr <= wptr + 1;
          end
          if (int_rd_en) begin
            rptr <= rptr + 1;
          end
        end
      end

      always @(*) begin
        if (tunnel_en) rd_data_o = wr_data_i;
        else rd_data_o = mem[rptr[ADDR_W-1:0]];
      end
    end
  endgenerate
endmodule
