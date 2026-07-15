`timescale 1ns / 1ps

/*
Synchronous FIFO module
*/
module FIFO #(
    parameter integer WIDTH = 8,
    parameter integer DEPTH = 16
) (
    input logic clk_i,
    input logic rst_i,

    // Write port
    input logic             wr_en_i,
    input logic [WIDTH-1:0] wr_data_i,

    // Read port
    input  logic             rd_en_i,
    output logic [WIDTH-1:0] rd_data_o,

    output logic empty_o,
    output logic full_o
);

  localparam integer AddrWidth = $clog2(DEPTH);

  logic tunnel_en;
  logic int_wr_en;
  logic int_rd_en;
  logic [WIDTH-1:0] rd_data_n;
  logic empty_n, full_n;
  logic [AddrWidth:0] wptr, wptr_n;  // MSB is wrap flag
  logic [AddrWidth:0] rptr, rptr_n;
  logic [WIDTH-1:0] mem[DEPTH];

  /*
  Logic for the FIFO
  */

  assign tunnel_en = wr_en_i & rd_en_i & empty_o;
  assign int_wr_en = wr_en_i & (~full_o | rd_en_i) & ~tunnel_en;
  assign int_rd_en = rd_en_i & ~empty_o;

  always_comb begin
    if (int_wr_en) begin
      wptr_n = wptr + 1;
    end else begin
      wptr_n = wptr;
    end
    if (int_rd_en) begin
      rptr_n = rptr + 1;
    end else begin
      rptr_n = rptr;
    end
  end

  // The following block could be replaced by a VeriSnip register file.
  always_ff @(posedge clk_i) begin
    if (rst_i) begin
      rd_data_o <= WIDTH'(0);
      empty_o <= 1'b1;
      full_o <= 1'b0;
      wptr <= {(AddrWidth + 1) {1'b0}};
      rptr <= {(AddrWidth + 1) {1'b0}};
    end else begin
      rd_data_o <= rd_data_n;
      empty_o <= empty_n;
      full_o <= full_n;
      wptr <= wptr_n;
      rptr <= rptr_n;
    end
  end

  generate
    if (DEPTH == 1) begin : gen_one_depth_fifo

      assign full_n  = (wptr_n ^ rptr_n);
      assign empty_n = (wptr_n ~^ rptr_n);
      always_comb begin
        if (tunnel_en) begin
          rd_data_n = wr_data_i;
        end else begin
          rd_data_n = mem[0];
        end
      end
      always_ff @(posedge clk_i) begin
        if (int_wr_en) begin
          mem[0] <= wr_data_i;
        end else begin
          mem[0] <= mem[0];
        end
      end

    end else begin : gen_fifo

      assign full_n  = (wptr_n[AddrWidth] ^ rptr_n[AddrWidth]) &
                       (wptr_n[AddrWidth-1:0] == rptr_n[AddrWidth-1:0]);
      assign empty_n = (wptr_n == rptr_n);
      always_comb begin
        if (tunnel_en) begin
          rd_data_n = wr_data_i;
        end else begin
          rd_data_n = mem[rptr[AddrWidth-1:0]];
        end
      end
      always_ff @(posedge clk_i) begin
        if (int_wr_en) begin
          mem[wptr[AddrWidth-1:0]] <= wr_data_i;
        end else begin
          mem[wptr[AddrWidth-1:0]] <= mem[wptr[AddrWidth-1:0]];
        end
      end

    end
  endgenerate
endmodule
