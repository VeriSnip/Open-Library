`timescale 1ps / 1ps

/*
  AXI-Lite memory
  This module was mostly created to test the AXI-Lite interface. But it may also work as a memory with an AXI-Lite interface in some projects.
*/
module AXIL_mem #(
    `include "AXI_parameters.vs"  // VS_NO_GENERATE
    parameter integer ADDR_WIDTH = 32,
    parameter integer DATA_WIDTH = 32
) (
    `include "AXI_ios.vs"  // AXI-Lite Subordinate
    // Generic IOs
    input wire clk_i,
    input wire arst_i
);
  // ============================================================================
  // Signal Declarations
  // ============================================================================
  `include "AXI_signals.vs"  // VS_NO_GENERATE
  reg [DATA_WIDTH-1:0] memory[2**ADDR_WIDTH];
  reg sync_reset;

  // ============================================================================
  // Logic
  // ============================================================================
  integer b;
  always @(posedge clk_i) begin
    // AXI write transaction -> write memory
    // Word-aligned index (drop byte-offset bits)
    for (b = 0; b < AXIL_DATA_WIDTH / 8; b = b + 1) begin
      if (AXIL_wstrb[b]) begin
        memory[AXIL_awaddr_n[ADDR_WIDTH-1:$clog2(AXIL_DATA_WIDTH/8)]][8*b+:8] <=
            AXIL_wdata[8*b+:8];
      end
    end
  end
  // AXI read transaction -> sample memory data
  assign AXIL_rdata = memory[AXIL_araddr_n[ADDR_WIDTH-1:$clog2(AXIL_DATA_WIDTH/8)]];

  `include "synchronous_reset_from_async.vs"

  `include "AXI_logic.vs"  // VS_NO_GENERATE

endmodule
