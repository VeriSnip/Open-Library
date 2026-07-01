`timescale 1ns / 1ps

module AXIL_mem_tb ();

  // Local parameters
  localparam integer ADDR_WIDTH = 32;
  localparam integer DATA_WIDTH = 32;
  localparam integer ID_W_WIDTH = 2;
  localparam integer ID_R_WIDTH = 2;

  // DUT Inputs
  reg clk = 0;

  // Clock generation
  always #5 clk = ~clk;

  initial begin
    $finish;
  end

  // Dump waves
  initial begin
    $dumpfile("bitSerialNNAcel_tb.vcd");
    $dumpvars(0, bitSerialNNAcel_tb);
  end

  AXIL_mem #(
    // Generated parameters for AXI-Lite Slave
    .AXIL_ADDR_WIDTH(),
    .AXIL_DATA_WIDTH(),
    .AXIL_ID_W_WIDTH(),
    .AXIL_ID_R_WIDTH(),
    .ADDR_WIDTH(),
    .DATA_WIDTH()
) DUT (
    // Generated IOs for AXI-Lite Slave
    .AXIL_awvalid_i(),
    .AXIL_awready_o(),
    .AXIL_awid_i(),
    .AXIL_awaddr_i(),
    .AXIL_awprot_i(),
    .AXIL_wvalid_i(),
    .AXIL_wready_o(),
    .AXIL_wdata_i(),
    .AXIL_wstrb_i(),
    .AXIL_bvalid_o(),
    .AXIL_bready_i(),
    .AXIL_bid_o(),
    .AXIL_arvalid_i(),
    .AXIL_arready_o(),
    .AXIL_arid_i(),
    .AXIL_araddr_i(),
    .AXIL_rvalid_o(),
    .AXIL_rready_i(),
    .AXIL_rid_o(),
    .AXIL_rdata_o(),
    // Generic IOs
    .clk_i(),
    .arst_i()
);

endmodule
