#!/usr/bin/env python

# AXI.py script creates required AXI IOs and logic for Lite and Stream interfaces.
# It generates two files:
#   - AXI_{vs_name_suffix}_ios.vs
#   - AXI_{vs_name_suffix}_logic.vs
# The vs_name_suffix can be: lite_s, lite_m, stream_s, stream_m.

import subprocess
import sys
import os
from VeriSnip.vs_build import (
    find_verilog_and_scripts,
    find_filename_in_list,
)
from VeriSnip.vs_colours import *


class AXIInterface:
    def __init__(self, vs_name_suffix):
        self.vs_name_suffix = vs_name_suffix
        try:
            if "stream_s" in vs_name_suffix:
                self.type = "stream"
                self.node_type = "slave"
            elif "stream_m" in vs_name_suffix:
                self.type = "stream"
                self.node_type = "master"
            elif "lite_s" in vs_name_suffix:
                self.type = "lite"
                self.node_type = "slave"
            elif "lite_m" in vs_name_suffix:
                self.type = "lite"
                self.node_type = "master"
            elif "s" in vs_name_suffix:
                self.type = "full"
                self.node_type = "slave"
            elif "m" in vs_name_suffix:
                self.type = "full"
                self.node_type = "master"
            else:
                raise ValueError
        except ValueError:
            vs_print(ERROR, f"Invalid vs_name_suffix: {vs_name_suffix}")
            exit(1)

        if self.type not in ["lite", "stream"]:
            vs_print(ERROR, f"Invalid AXI type: {self.type}")
            exit(1)

    def generate(self, last_ios=False):
        ios_content = ""
        logic_content = ""
        signals_content = ""

        if self.type == "lite":
            if self.node_type == "slave":
                ios_content = get_lite_slave_ios(last_ios)
                logic_content = get_lite_slave_logic(self.vs_name_suffix)
                signals_content = get_lite_slave_signals()
            else:  # master
                ios_content = get_lite_master_ios(last_ios)
                logic_content = get_lite_master_logic()
                signals_content = get_lite_master_signals()
        else:  # stream
            if self.node_type == "slave":
                ios_content = get_stream_slave_ios(last_ios)
                logic_content = get_stream_slave_logic()
                signals_content = get_stream_slave_signals()
            else:  # master
                ios_content = get_stream_master_ios(last_ios)
                logic_content = get_stream_master_logic()
                signals_content = get_stream_master_signals()

        if ios_content:
            write_vs(ios_content, f"AXI_{self.vs_name_suffix}_ios.vs")
        if logic_content:
            write_vs(logic_content, f"AXI_{self.vs_name_suffix}_logic.vs")
        if signals_content:
            with open(f"{sys.argv[4]}_generated_signals.vs", "a") as f:
                f.write("// AXI Signals\n")
                f.write(signals_content)


def get_lite_slave_ios(last_ios=False):
    return f"""
    input  wire AXIL_awvalid_i,
    output wire AXIL_awready_o,
    input  wire [ADDR_WIDTH-1:0] AXIL_awaddr_i,
    input  wire [2:0] AXIL_awprot_i,
    input  wire AXIL_wvalid_i,
    output wire AXIL_wready_o,
    input  wire [DATA_WIDTH-1:0] AXIL_wdata_i,
    input  wire [DATA_WIDTH/8-1:0] AXIL_wstrb_i,
    output  reg AXIL_bvalid_o,
    input  wire AXIL_bready_i,
    output wire [1:0] AXIL_bresp_o,
    input  wire AXIL_arvalid_i,
    output wire AXIL_arready_o,
    input  wire [ADDR_WIDTH-1:0] AXIL_araddr_i,
    input  wire [2:0] AXIL_arprot_i,
    output  reg AXIL_rvalid_o,
    input  wire AXIL_rready_i,
    output  reg [DATA_WIDTH-1:0] AXIL_rdata_o,
    output wire [1:0] AXIL_rresp_o{',' if last_ios else ''}
"""


def get_lite_slave_logic(vs_name_suffix=None):
    return f"""
  // Automatically generated AXIL slave logic.
  assign AXIL_awready_o = 1'b1;
  assign AXIL_wready_o = 1'b1;
  assign AXIL_arready_o = 1'b1;
  assign AXIL_bresp_o = 2'b00;
  assign AXIL_rresp_o = 2'b00;

  assign w_address = AXIL_awvalid_i ? AXIL_awaddr_i : AXIL_awaddr_q;
  assign w_data = AXIL_wvalid_i ? AXIL_wdata_i : AXIL_wdata_q;
  assign w_enable = (AXIL_awvalid_i & AXIL_wvalid_i) | (AXIL_awvalid_i & AXIL_wvalid_q) | (AXIL_awvalid_q & AXIL_wvalid_i);
  assign r_address = AXIL_arvalid_i ? AXIL_araddr_i : AXIL_araddr_q;
  assign r_enable = AXIL_arvalid_i;
  assign AXIL_rvalid_e = AXIL_arvalid_i | AXIL_rready_i;

  `include "reg_AXI_{vs_name_suffix}.vs"  /*
    AXIL_awvalid_q, 1, 0, w_enable, AXIL_awvalid_i, AXIL_awvalid_i
    AXIL_awaddr_q, ADDR_WIDTH, 0, , AXIL_awvalid_i, AXIL_awaddr_i
    AXIL_wvalid_q, 1, 0, w_enable, AXIL_wvalid_i, AXIL_wvalid_i
    AXIL_wdata_q, DATA_WIDTH, 0, , AXIL_wvalid_i, AXIL_wdata_i
    AXIL_araddr_q, ADDR_WIDTH, 0, , AXIL_arvalid_i, AXIL_araddr_i
    AXIL_bvalid_o, 1, 0, , , w_enable
    AXIL_rvalid_o, 1, 0, , _e, r_enable
    AXIL_rdata_o, DATA_WIDTH, 0, , , r_data
    */
"""


def get_lite_slave_signals():
    return """
  // Additional signals for AXI-Lite Slave
  reg AXIL_awvalid_q;
  reg [ADDR_WIDTH-1:0] AXIL_awaddr_q;
  reg AXIL_wvalid_q;
  reg [DATA_WIDTH-1:0] AXIL_wdata_q;
  reg [ADDR_WIDTH-1:0] AXIL_araddr_q;
  wire AXIL_rvalid_e;
  wire [DATA_WIDTH-1:0] r_data;
  wire [ADDR_WIDTH-1:0] w_address;
  wire [DATA_WIDTH-1:0] w_data;
  wire w_enable;
  wire [ADDR_WIDTH-1:0] r_address;
  wire r_enable;
"""


def get_lite_master_ios(last_ios=False):
    return f"""
    output wire AXIL_awvalid_o,
    input  wire AXIL_awready_i,
    output wire [ADDR_WIDTH-1:0] AXIL_awaddr_o,
    output wire [2:0] AXIL_awprot_o,
    output wire AXIL_wvalid_o,
    input  wire AXIL_wready_i,
    output wire [DATA_WIDTH-1:0] AXIL_wdata_o,
    output wire [DATA_WIDTH/8-1:0] AXIL_wstrb_o,
    input  wire AXIL_bvalid_i,
    output wire AXIL_bready_o,
    input  wire [1:0] AXIL_bresp_i,
    output wire AXIL_arvalid_o,
    input  wire AXIL_arready_i,
    output wire [ADDR_WIDTH-1:0] AXIL_araddr_o,
    output wire [2:0] AXIL_arprot_o,
    input  wire AXIL_rvalid_i,
    output wire AXIL_rready_o,
    input  wire [DATA_WIDTH-1:0] AXIL_rdata_i,
    input  wire [1:0] AXIL_rresp_i{',' if last_ios else ''}
"""


def get_lite_master_logic():
    vs_print(ERROR, "AXI-Lite Master logic generation is not implemented yet.")
    return ""


def get_lite_master_signals():
    vs_print(
        INFO,
        "AXI-Lite Master signals generation is not implemented yet, generating empty file.",
    )
    return ""


def get_stream_slave_ios(last_ios=False):
    return f"""
    input  wire [DATA_WIDTH-1:0] AXIS_tdata_i,
    input  wire [DATA_WIDTH/8-1:0] AXIS_tstrb_i,
    input  wire AXIS_tlast_i,
    input  wire AXIS_tvalid_i,
    output wire AXIS_tready_o{',' if last_ios else ''}
"""


def get_stream_slave_logic():
    vs_print(
        WARNING,
        "AXI-Stream Slave logic generation is not implemented yet, generating empty file.",
    )
    return ""


def get_stream_slave_signals():
    vs_print(
        WARNING,
        "AXI-Stream Slave signals generation is not implemented yet, generating empty file.",
    )
    return ""


def get_stream_master_ios(last_ios=False):
    return f"""
    output wire [DATA_WIDTH-1:0] AXIS_tdata_o,
    output wire [DATA_WIDTH/8-1:0] AXIS_tstrb_o,
    output wire AXIS_tlast_o,
    output wire AXIS_tvalid_o,
    input  wire AXIS_tready_i{',' if last_ios else ''}
"""


def get_stream_master_logic():
    vs_print(
        WARNING,
        "AXI-Stream Master logic generation is not implemented yet, generating empty file.",
    )
    return ""


def get_stream_master_signals():
    vs_print(
        WARNING,
        "AXI-Stream Master signals generation is not implemented yet, generating empty file.",
    )
    return ""


def get_burst_slave_ios(last_ios=False):
    vs_print(ERROR, "Burst AXI Slave IOS generation is not implemented yet.")
    return ""


def get_burst_slave_logic():
    vs_print(ERROR, "Burst AXI Slave logic generation is not implemented yet.")
    return ""


def get_burst_slave_signals():
    vs_print(ERROR, "Burst AXI Slave signals generation is not implemented yet.")
    return ""


def get_burst_master_ios(last_ios=False):
    return f"""
    // AXI master interface
    input wire                          aclk,
    input wire                          areset,

    output wire [C_ADDR_WIDTH-1:0]      awaddr,
    output wire [7:0]                   awlen,
    output wire [2:0]                   awsize,
    output wire                         awvalid,
    input wire                          awready,

    output wire [C_DATA_WIDTH-1:0]      wdata,
    output wire [C_DATA_WIDTH/8-1:0]    wstrb,
    output wire                         wlast,
    output wire                         wvalid,
    input wire                          wready,

    input wire [1:0]                    bresp,
    input wire                          bvalid,
    output wire                         bready,
    output wire                         arvalid,
    input  wire                         arready,
    output wire [C_ADDR_WIDTH-1:0]      araddr,
    output wire [C_ID_WIDTH-1:0]        arid,
    output wire [7:0]                   arlen,
    output wire [2:0]                   arsize,
    input  wire                         rvalid,
    output wire                         rready,
    input  wire [C_DATA_WIDTH - 1:0]    rdata,
    input  wire                         rlast,
    input  wire [C_ID_WIDTH - 1:0]      rid,
    input  wire [1:0]                   rresp,
"""


def get_burst_master_logic():
    vs_print(WARNING, "Full AXI Master logic generation is not implemented yet.")
    return ""


def get_burst_master_signals():
    vs_print(
        WARNING, "Full AXI Master signals generation is not implemented yet."
    )
    return ""


def write_vs(string, file_name):
    with open(file_name, "w") as file:
        file.write(string)
    vs_print(OK, f"Generated {file_name}")


def parse_arguments():
    if len(sys.argv) < 2:
        vs_print(ERROR, "Not enough arguments. Please provide vs_name_suffix.")
        vs_print(INFO, "Usage: python AXI.py <vs_name_suffix>")
        vs_print(INFO, "Example: python AXI.py lite_s")
        exit(1)

    vs_name_suffix = sys.argv[1].replace("_ios.vs", "").replace("_logic.vs", "")
    last_ios = len(sys.argv) > 2 and sys.argv[2] == ","

    return AXIInterface(vs_name_suffix), last_ios


# Check if this script is called directly
if __name__ == "__main__":
    axi_if, last_ios = parse_arguments()
    axi_if.generate(last_ios)
