`timescale 1ps / 1ps

/*
  Module to test the AXI interface generator
*/
module AXI_test #(
    `include "AXI_parameters.vs"  // VS_NO_GENERATE
    parameter integer ADDR_WIDTH = 32,
    parameter integer DATA_WIDTH = 32
) (
    `include "AXI_ios.vs"  // VS_NO_GENERATE
    // bitSANN IOs
    input wire clk_i,
    input wire arst_i
);
  // ============================================================================
  // Signal Declarations
  // ============================================================================
  `include "AXI_signals.vs"  // VS_NO_GENERATE
  reg [DATA_WIDTH-1:0] testing_data[2**ADDR_WIDTH];
  reg [DATA_WIDTH-1:0] w_data;

  // ============================================================================
  // Logic
  // ============================================================================
  always @(posedge clk_i) begin
    // AXI write transaction -> write memory
    testing_data[AXIL_awaddr_n[ADDR_WIDTH-1:$clog2(AXIL_DATA_WIDTH/8)]] <= w_data;
  end

  integer b;
  always @(*) begin
    // Word-aligned index (drop byte-offset bits)
    for (b = 0; b < AXIL_DATA_WIDTH / 8; b = b + 1) begin
      if (AXIL_wstrb_q[b]) begin
        w_data[8*b+:8] = AXIL_wdata_q[8*b+:8];
      end
    end
    // AXI read transaction -> sample memory data
    AXIL_rdata = testing_data[AXIL_araddr_q[ADDR_WIDTH-1:$clog2(AXIL_DATA_WIDTH/8)]];
  end

  `include "synchronous_reset_from_async.vs"

  `include "AXI_logic.vs"  /*
      AXI-Lite Slave
    */

endmodule
