`timescale 1ns / 1ps

module axi_manager_test #(
    `include "AXI_parameters.vs"  // VS_NO_GENERATE
) (
    `include "AXI_ios.vs"  // VS_NO_GENERATE

    // User read command
    input  logic                              AXI_M_usr_cmd_rd_valid_i,
    output logic                              AXI_M_usr_cmd_rd_ready_o,
    input  logic [AXI_M_ADDR_WIDTH-1:0]       AXI_M_usr_cmd_rd_addr_i,
    input  logic [7:0]                        AXI_M_usr_cmd_rd_len_i,
    input  logic [2:0]                        AXI_M_usr_cmd_rd_size_i,
    input  logic [1:0]                        AXI_M_usr_cmd_rd_burst_i,
    input  logic [AXI_M_ID_R_WIDTH-1:0]       AXI_M_usr_cmd_rd_id_i,

    // User read data
    output logic                              AXI_M_usr_rd_data_valid_o,
    input  logic                              AXI_M_usr_rd_data_ready_i,
    output logic [AXI_M_DATA_WIDTH-1:0]       AXI_M_usr_rd_data_o,
    output logic [1:0]                        AXI_M_usr_rd_resp_o,
    output logic [AXI_M_ID_R_WIDTH-1:0]       AXI_M_usr_rd_id_o,
    output logic                              AXI_M_usr_rd_last_o,

    // User write command
    input  logic                              AXI_M_usr_cmd_wr_valid_i,
    output logic                              AXI_M_usr_cmd_wr_ready_o,
    input  logic [AXI_M_ADDR_WIDTH-1:0]       AXI_M_usr_cmd_wr_addr_i,
    input  logic [7:0]                        AXI_M_usr_cmd_wr_len_i,
    input  logic [2:0]                        AXI_M_usr_cmd_wr_size_i,
    input  logic [1:0]                        AXI_M_usr_cmd_wr_burst_i,
    input  logic [AXI_M_ID_W_WIDTH-1:0]       AXI_M_usr_cmd_wr_id_i,

    // User write data
    input  logic                              AXI_M_usr_wr_data_valid_i,
    output logic                              AXI_M_usr_wr_data_ready_o,
    input  logic [AXI_M_DATA_WIDTH-1:0]       AXI_M_usr_wr_data_i,
    input  logic [AXI_M_DATA_WIDTH/8-1:0]     AXI_M_usr_wr_strb_i,

    // User write response
    output logic                              AXI_M_usr_wr_resp_valid_o,
    input  logic                              AXI_M_usr_wr_resp_ready_i,
    output logic [AXI_M_ID_W_WIDTH-1:0]       AXI_M_usr_wr_resp_id_o,
    output logic [AXI_M_BRESP_WIDTH-1:0]      AXI_M_usr_wr_resp_o,

    input logic clk_i,
    input logic arstn_i
);

  `include "AXI_signals.vs"  // VS_NO_GENERATE

  logic sync_reset;
  `include "synchronize_reset_axi_manager_test.vs"  // arstn_i (active-low), sync_reset (active-high)

  `include "AXI_logic.vs"  /*
      AXI-Full Manager
    */

  // ---------------------------------------------------------------------------
  // Tie wrapper IOs to the generated user ports
  // ---------------------------------------------------------------------------
  assign AXI_M_usr_cmd_rd_valid     = AXI_M_usr_cmd_rd_valid_i;
  assign AXI_M_usr_cmd_rd_ready_o   = AXI_M_usr_cmd_rd_ready;
  assign AXI_M_usr_cmd_rd_addr      = AXI_M_usr_cmd_rd_addr_i;
  assign AXI_M_usr_cmd_rd_len       = AXI_M_usr_cmd_rd_len_i;
  assign AXI_M_usr_cmd_rd_size      = AXI_M_usr_cmd_rd_size_i;
  assign AXI_M_usr_cmd_rd_burst     = AXI_M_usr_cmd_rd_burst_i;
  assign AXI_M_usr_cmd_rd_id        = AXI_M_usr_cmd_rd_id_i;

  assign AXI_M_usr_rd_data_valid_o  = AXI_M_usr_rd_data_valid;
  assign AXI_M_usr_rd_data_ready    = AXI_M_usr_rd_data_ready_i;
  assign AXI_M_usr_rd_data_o        = AXI_M_usr_rd_data;
  assign AXI_M_usr_rd_resp_o        = AXI_M_usr_rd_resp;
  assign AXI_M_usr_rd_id_o          = AXI_M_usr_rd_id;
  assign AXI_M_usr_rd_last_o        = AXI_M_usr_rd_last;

  assign AXI_M_usr_cmd_wr_valid     = AXI_M_usr_cmd_wr_valid_i;
  assign AXI_M_usr_cmd_wr_ready_o   = AXI_M_usr_cmd_wr_ready;
  assign AXI_M_usr_cmd_wr_addr      = AXI_M_usr_cmd_wr_addr_i;
  assign AXI_M_usr_cmd_wr_len       = AXI_M_usr_cmd_wr_len_i;
  assign AXI_M_usr_cmd_wr_size      = AXI_M_usr_cmd_wr_size_i;
  assign AXI_M_usr_cmd_wr_burst     = AXI_M_usr_cmd_wr_burst_i;
  assign AXI_M_usr_cmd_wr_id        = AXI_M_usr_cmd_wr_id_i;

  assign AXI_M_usr_wr_data_valid    = AXI_M_usr_wr_data_valid_i;
  assign AXI_M_usr_wr_data_ready_o  = AXI_M_usr_wr_data_ready;
  assign AXI_M_usr_wr_data          = AXI_M_usr_wr_data_i;
  assign AXI_M_usr_wr_strb          = AXI_M_usr_wr_strb_i;

  assign AXI_M_usr_wr_resp_valid_o  = AXI_M_usr_wr_resp_valid;
  assign AXI_M_usr_wr_resp_ready    = AXI_M_usr_wr_resp_ready_i;
  assign AXI_M_usr_wr_resp_id_o     = AXI_M_usr_wr_resp_id;
  assign AXI_M_usr_wr_resp_o        = AXI_M_usr_wr_resp;

endmodule
