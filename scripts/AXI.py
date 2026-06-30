#!/usr/bin/env python

# AXI.py script creates required AXI5 IOs and logic for Lite, Stream, and Full interfaces.
# It generates two files:
# To call this script in a Verilog file it should follow one of the following patterns:
#   `include "AXI_[ios,signals,logic][_{interface/bus_name}].vs" // AXI-[Lite,Full,Stream] [Master,Slave] {bus_name}
# and
#   `include "AXI_[ios,signals,logic][_{interface_name}].vs" /*
#             AXI-[Lite,Full,Stream] [Master,Slave] {bus_name}
#             AXI-[Lite,Full,Stream] [Master,Slave] {bus_name}
#             AXI-[Lite,Full,Stream] [Master,Slave] {bus_name}
#             ...
#             */
# Notes:
# - {bus_name} is optional. If it is not provided, the script will use the interface name as the bus name.
# - {interface_name} is optional. If it is not provided, the script will use the bus name as the interface name.

import subprocess
import sys
import os
import re
from VeriSnip.vs_colours import *


class AXIConfiguration:
    def __init__(self, configuration):
        configuration = configuration.split(" ")
        self.type = configuration[0]
        self.node = configuration[1]
        self.name = configuration[2]

class AXIInterface:
    def __init__(self, vs_suffix, configurations):
        self.interface_name = vs_suffix
        self.conf_list = configurations.split("\n")
        self.buses = [AXIConfiguration(conf.strip() + " " + self.interface_name) for conf in self.conf_list]

    def generate(self):
        parameters_content = ""
        ios_content = ""
        logic_content = ""
        signals_content = ""

        for bus in self.buses:
            if bus.type == "AXI-Lite":
                vs_print(INFO, f"Generating AXI-Lite {bus.node} {bus.name} interface.")
                prefix = f"AXIL_{bus.name}" if bus.name else "AXIL"
                if bus.node == "Slave":
                    parameters_content += get_lite_slave_parameters(prefix)
                    ios_content += get_lite_slave_ios(prefix)
                    logic_content += get_lite_slave_logic(prefix, bus.name)
                    signals_content += get_lite_slave_signals(prefix)
                else:  # master
                    ios_content += get_lite_master_ios(prefix)
                    logic_content += get_lite_master_logic()
                    signals_content += get_lite_master_signals()
            elif bus.type == "AXI-Stream":
                vs_print(INFO, f"Generating AXI-Stream {bus.node} {bus.name} interface.")
                prefix = f"AXIS_{bus.name}" if bus.name else "AXIS"
                if bus.node == "Slave":
                    ios_content += get_stream_slave_ios(prefix)
                    logic_content += get_stream_slave_logic()
                    signals_content += get_stream_slave_signals()
                else:  # master
                    ios_content += get_stream_master_ios(prefix)
                    logic_content += get_stream_master_logic()
                    signals_content += get_stream_master_signals()
            elif bus.type == "AXI-Full":
                vs_print(INFO, f"Generating AXI-Full {bus.node} {bus.name} interface.")
                prefix = f"AXIF_{bus.name}" if bus.name else "AXIF"
                if bus.node == "Slave":
                    ios_content += get_full_slave_ios(prefix)
                    logic_content += get_full_slave_logic()
                    signals_content += get_full_slave_signals()
                else:  # master
                    ios_content += get_full_master_ios(prefix)
                    logic_content += get_full_master_logic()
                    signals_content += get_full_master_signals()

        name = "_" + self.interface_name if self.interface_name else ""
        if parameters_content:
            write_vs(parameters_content, f"AXI_parameters{name}.vs")
        if ios_content:
            write_vs(ios_content, f"AXI_ios{name}.vs")
        if signals_content:
            write_vs(signals_content, f"AXI_signals{name}.vs")
        if logic_content:
            write_vs(logic_content, f"AXI_logic{name}.vs")
        
        name = " " + self.interface_name if self.interface_name else ""
        vs_print(OK, f"Generated AXI{name} interface.")


def get_lite_slave_parameters(bus_prefix):
  return f"""
  parameter {bus_prefix}_ADDR_WIDTH = 32;
  parameter {bus_prefix}_DATA_WIDTH = 32;
  parameter {bus_prefix}_ID_W_WIDTH = 1;
  parameter {bus_prefix}_ID_R_WIDTH = 1;
"""

def get_lite_slave_signals(bus_prefix):
    return f"""
  // Generated signals for AXI-Lite Slave
  reg [1:0] {bus_prefix}_w_state;
  reg {bus_prefix}_awvalid_q;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awaddr_n;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awaddr_q;
  reg {bus_prefix}_wvalid_q;
  reg [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wdata_n;
  reg [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wdata_q;
  reg [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wstrb_n;
  reg [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wstrb_q;
  reg {bus_prefix}_bvalid_n;
  reg [{bus_prefix}_ID_W_WIDTH-1:0] {bus_prefix}_bid_n;
  reg {bus_prefix}_r_state;
  reg {bus_prefix}_arvalid_q;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_araddr_n;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_araddr_q;
  reg [{bus_prefix}_ID_R_WIDTH-1:0] {bus_prefix}_rid_n;
  reg [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_rdata;
  reg [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_rdata_n;
"""

def get_lite_slave_ios(bus_prefix):
    return f"""
    // AXI5-Lite Slave IOS
    input  wire {bus_prefix}_awvalid_i,
    output  reg {bus_prefix}_awready_o,
    output  reg {bus_prefix}_awready_n,
    input  wire [{bus_prefix}_ID_W_WIDTH-1:0] {bus_prefix}_awid_i,
    input  wire [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awaddr_i,
    output  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awaddr_n,
    input  wire [2:0] {bus_prefix}_awprot_i,
    input  wire {bus_prefix}_wvalid_i,
    output  reg {bus_prefix}_wready_o,
    output  reg {bus_prefix}_wready_n,
    input  wire [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wdata_i,
    input  wire [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wstrb_i,
    output  reg {bus_prefix}_bvalid_o,
    input  wire {bus_prefix}_bready_i,
    output  reg [{bus_prefix}_ID_W_WIDTH-1:0] {bus_prefix}_bid_o,
    output  reg [1:0] {bus_prefix}_bresp_o,
    input  wire {bus_prefix}_arvalid_i,
    output  reg {bus_prefix}_arready_o,
    output  reg {bus_prefix}_arready_n,
    input  wire [{bus_prefix}_ID_R_WIDTH-1:0] {bus_prefix}_arid_i,
    input  wire [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_araddr_i,
    output  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_araddr_n,
    output  reg {bus_prefix}_rvalid_o,
    input  wire {bus_prefix}_rready_i,
    output  reg [{bus_prefix}_ID_R_WIDTH-1:0] {bus_prefix}_rid_o,
    output  reg [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_rdata_o,
    output  reg [1:0] {bus_prefix}_rresp_o,
"""

# TO DO: Fix wready and awready to add backpressure.
def get_lite_slave_logic(bus_prefix, interface_name=None):
    return f"""
  // Automatically generated {bus_prefix} slave logic.
  // Write state machine
  always @(*) begin
    // 1. DEFAULT ASSIGNMENTS (Prevents all latches!)
    {bus_prefix}_w_state_n   = {bus_prefix}_w_state;
    {bus_prefix}_awready_n   = {bus_prefix}_awready_o;
    {bus_prefix}_wready_n    = {bus_prefix}_wready_o;
    {bus_prefix}_wdata_n     = {bus_prefix}_wdata_q;
    {bus_prefix}_wstrb_n     = {bus_prefix}_wstrb_q;
    {bus_prefix}_bid_n       = {bus_prefix}_bid_o;
    {bus_prefix}_bid_queue_n = {bus_prefix}_bid_queue;
    {bus_prefix}_bvalid_n    = {bus_prefix}_bvalid_o;
    // 2. STATE MACHINE
    case({bus_prefix}_w_state)
      2'b00: begin
        {bus_prefix}_awready_n = 1'b1;
        {bus_prefix}_wready_n = 1'b1;
        if ({bus_prefix}_awvalid_i & {bus_prefix}_awready_o & {bus_prefix}_wvalid_i & {bus_prefix}_wready_o) begin
          {bus_prefix}_wdata_n = {bus_prefix}_wdata_i;
          {bus_prefix}_wstrb_n = {bus_prefix}_wstrb_i;
          {bus_prefix}_bvalid_n = 1'b1;
          if ({bus_prefix}_bvalid_o & ~{bus_prefix}_bready_i) begin
            {bus_prefix}_w_state_n = 2'b11;
            {bus_prefix}_awready_n = 1'b0;
            {bus_prefix}_wready_n = 1'b0;
            {bus_prefix}_bid_n = {bus_prefix}_bid_o;
            {bus_prefix}_bid_queue_n = {bus_prefix}_awid_i;
          end else begin
            {bus_prefix}_w_state_n = 2'b00;
            {bus_prefix}_bid_n = {bus_prefix}_awid_i;
          end
        end else begin
          if ({bus_prefix}_awvalid_i & {bus_prefix}_awready_o) begin
            {bus_prefix}_w_state_n = 2'b01;
            {bus_prefix}_awready_n = 1'b0;
          end
          if ({bus_prefix}_wvalid_i & {bus_prefix}_wready_o) begin
            {bus_prefix}_w_state_n = 2'b10;
            {bus_prefix}_wready_n = 1'b0;
          end
          {bus_prefix}_bvalid_n = {bus_prefix}_bready_i ? 1'b0 : {bus_prefix}_bvalid_o;
        end
      end
      2'b01: begin
        if ({bus_prefix}_wvalid_i & {bus_prefix}_wready_o) begin
          {bus_prefix}_wdata_n = {bus_prefix}_wdata_i;
          {bus_prefix}_wstrb_n = {bus_prefix}_wstrb_i;
          {bus_prefix}_bid_n = {bus_prefix}_awid_i;
          {bus_prefix}_bvalid_n = 1'b1;
          if ({bus_prefix}_bvalid_o & ~{bus_prefix}_bready_i) begin
            {bus_prefix}_w_state_n = 2'b11;
            {bus_prefix}_wready_n = 1'b0;
            {bus_prefix}_bid_n = {bus_prefix}_bid_o;
            {bus_prefix}_bid_queue_n = {bus_prefix}_awid_i;
          end else begin
            {bus_prefix}_w_state_n = 2'b00;
            {bus_prefix}_awready_n = 1'b1;
            {bus_prefix}_bid_n = {bus_prefix}_awid_i;
          end
        end else begin
          {bus_prefix}_bvalid_n = {bus_prefix}_bready_i ? 1'b0 : {bus_prefix}_bvalid_o;
        end
      end
      2'b10: begin
        if ({bus_prefix}_awvalid_i & {bus_prefix}_awready_o) begin
          {bus_prefix}_wdata_n = {bus_prefix}_wdata_i;
          {bus_prefix}_wstrb_n = {bus_prefix}_wstrb_i;
          {bus_prefix}_bid_n = {bus_prefix}_awid_i;
          {bus_prefix}_bvalid_n = 1'b1;
          if ({bus_prefix}_bvalid_o & ~{bus_prefix}_bready_i) begin
            {bus_prefix}_w_state_n = 2'b11;
            {bus_prefix}_awready_n = 1'b0;
            {bus_prefix}_bid_n = {bus_prefix}_bid_o;
            {bus_prefix}_bid_queue_n = {bus_prefix}_awid_i;
          end else begin
            {bus_prefix}_w_state_n = 2'b00;
            {bus_prefix}_wready_n = 1'b1;
            {bus_prefix}_bid_n = {bus_prefix}_awid_i;
          end
        end else begin
          {bus_prefix}_bvalid_n = {bus_prefix}_bready_i ? 1'b0 : {bus_prefix}_bvalid_o;
        end
      end
      2'b11: begin
        if ({bus_prefix}_bready_i) begin
          {bus_prefix}_bid_n = {bus_prefix}_bid_queue;
          {bus_prefix}_w_state_n = 2'b00;
          {bus_prefix}_awready_n = 1'b1;
          {bus_prefix}_wready_n = 1'b1;
        end
      end
      default: ;
    endcase
  end
  // Read state machine
  always @(*) begin
    case({bus_prefix}_r_state)
      1'b0: begin
      // Ready to receive address and send back data
        {bus_prefix}_arready_n = 1'b1;
        {bus_prefix}_r_state_n = 1'b0;
        if ({bus_prefix}_arvalid_i & {bus_prefix}_arready_o) begin
          {bus_prefix}_rvalid_n = 1'b1;
          {bus_prefix}_rdata_n = {bus_prefix}_rdata;
          {bus_prefix}_rid_n = {bus_prefix}_arid_i;
          if ({bus_prefix}_rready_i) begin
            {bus_prefix}_r_state_n = 1'b0;
          end else begin
            {bus_prefix}_r_state_n = 1'b1;
            {bus_prefix}_arready_n = 1'b0;
          end
        end
      end
      1'b1: begin
      // Waiting for data to be sent back
        {bus_prefix}_r_state_n = 1'b1;
        if ({bus_prefix}_rready_i) begin
          {bus_prefix}_r_state_n = 1'b0;
          {bus_prefix}_arready_n = 1'b1;
        end
      end
      default: ;
    endcase
  end

  `include "reg_AXI_bus_prefix_{bus_prefix}_{interface_name}.vs"  /*
    {bus_prefix}_w_state, 1, 0, rst_i, , _n
    {bus_prefix}_awvalid_q, 1, 0, rst_i, , _n
    {bus_prefix}_awready_o, 1, 0, rst_i, , _n
    {bus_prefix}_awaddr_q, {bus_prefix}_ADDR_WIDTH, 0, rst_i, , _n
    {bus_prefix}_wvalid_q, 1, 0, rst_i, , _n
    {bus_prefix}_wready_o, 1, 0, rst_i, , _n
    {bus_prefix}_wdata_q, {bus_prefix}_DATA_WIDTH, 0, rst_i, , _n
    {bus_prefix}_wstrb_q, {bus_prefix}_DATA_WIDTH/8, 0, rst_i, , _n
    {bus_prefix}_bvalid_o, 1, 0, rst_i, , _n
    {bus_prefix}_bid_o, {bus_prefix}_ID_W_WIDTH, 0, rst_i, , _n
    {bus_prefix}_bid_queue, 1, 0, rst_i, , _n
    {bus_prefix}_bresp_o, 2, 0, rst_i, , 2'b00
    {bus_prefix}_r_state, 1, 0, rst_i, , _n
    {bus_prefix}_arvalid_q, 1, 0, rst_i, , _n
    {bus_prefix}_arready_o, 1, 0, rst_i, , _n
    {bus_prefix}_araddr_q, {bus_prefix}_ADDR_WIDTH, 0, rst_i, , _n
    {bus_prefix}_rvalid_o, 1, 0, rst_i, , _n
    {bus_prefix}_rid_o, {bus_prefix}_ID_R_WIDTH, 0, rst_i, , _n
    {bus_prefix}_rdata_o, {bus_prefix}_DATA_WIDTH, 0, rst_i, , _n
    {bus_prefix}_rresp_o, 2, 0, rst_i, , 2'b00
    */
"""
# I should add global resets to register lists


def get_lite_master_ios(bus_prefix):
    return f"""
    output wire {bus_prefix}_awvalid_o,
    input  wire {bus_prefix}_awready_i,
    output wire [ADDR_WIDTH-1:0] {bus_prefix}_awaddr_o,
    output wire [2:0] {bus_prefix}_awprot_o,
    output wire {bus_prefix}_wvalid_o,
    input  wire {bus_prefix}_wready_i,
    output wire [DATA_WIDTH-1:0] {bus_prefix}_wdata_o,
    output wire [DATA_WIDTH/8-1:0] {bus_prefix}_wstrb_o,
    input  wire {bus_prefix}_bvalid_i,
    output wire {bus_prefix}_bready_o,
    input  wire [1:0] {bus_prefix}_bresp_i,
    output wire {bus_prefix}_arvalid_o,
    input  wire {bus_prefix}_arready_i,
    output wire [ADDR_WIDTH-1:0] {bus_prefix}_araddr_o,
    output wire [2:0] {bus_prefix}_arprot_o,
    input  wire {bus_prefix}_rvalid_i,
    output wire {bus_prefix}_rready_o,
    input  wire [DATA_WIDTH-1:0] {bus_prefix}_rdata_i,
    input  wire [1:0] {bus_prefix}_rresp_i,
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


def get_stream_slave_ios(bus_prefix):
    return f"""
    input  wire [DATA_WIDTH-1:0] {bus_prefix}_tdata_i,
    input  wire [DATA_WIDTH/8-1:0] {bus_prefix}_tstrb_i,
    input  wire {bus_prefix}_tlast_i,
    input  wire {bus_prefix}_tvalid_i,
    output wire {bus_prefix}_tready_o,
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


def get_stream_master_ios(bus_prefix):
    return f"""
    output wire [DATA_WIDTH-1:0] {bus_prefix}_tdata_o,
    output wire [DATA_WIDTH/8-1:0] {bus_prefix}_tstrb_o,
    output wire {bus_prefix}_tlast_o,
    output wire {bus_prefix}_tvalid_o,
    input  wire {bus_prefix}_tready_i,
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


def get_full_slave_ios(bus_prefix):
    vs_print(ERROR, "Full AXI Slave IOS generation is not implemented yet.")
    return ""


def get_full_slave_logic():
    vs_print(ERROR, "Full AXI Slave logic generation is not implemented yet.")
    return ""


def get_full_slave_signals():
    vs_print(ERROR, "Full AXI Slave signals generation is not implemented yet.")
    return ""


def get_full_master_ios(bus_prefix):
    return f"""
    // AXI-Full Master IOS
    output wire [ADDR_WIDTH-1:0] {bus_prefix}_awaddr_o,
    output wire [7:0] {bus_prefix}_awlen_o,
    output wire [2:0] {bus_prefix}_awsize_o,
    output wire {bus_prefix}_awvalid_o,
    input  wire {bus_prefix}_awready_i,
    output wire [DATA_WIDTH-1:0] {bus_prefix}_wdata_o,
    output wire [DATA_WIDTH/8-1:0] {bus_prefix}_wstrb_o,
    output wire {bus_prefix}_wlast_o,
    output wire {bus_prefix}_wvalid_o,
    input  wire {bus_prefix}_wready_i,
    input  wire [1:0] {bus_prefix}_bresp_i,
    input  wire {bus_prefix}_bvalid_i,
    output wire {bus_prefix}_bready_o,
    output wire {bus_prefix}_arvalid_o,
    input  wire {bus_prefix}_arready_i,
    output wire [ADDR_WIDTH-1:0] {bus_prefix}_araddr_o,
    output wire [7:0] {bus_prefix}_arlen_o,
    output wire [2:0] {bus_prefix}_arsize_o,
    input  wire {bus_prefix}_rvalid_i,
    output wire {bus_prefix}_rready_o,
    input  wire [DATA_WIDTH-1:0] {bus_prefix}_rdata_i,
    input  wire {bus_prefix}_rlast_i,
    input  wire [1:0] {bus_prefix}_rresp_i,
"""


def get_full_master_logic():
    vs_print(WARNING, "Full AXI Master logic generation is not implemented yet.")
    return ""


def get_full_master_signals():
    vs_print(
        WARNING, "Full AXI Master signals generation is not implemented yet."
    )
    return ""


def write_vs(string, file_name):
    with open(file_name, "w") as file:
        file.write(string)


def parse_arguments():
    if len(sys.argv) < 2:
        vs_print(ERROR, "Not enough arguments. Please provide vs_name_suffix.")
        vs_print(INFO, "Usage: python AXI.py <vs_name_suffix>")
        vs_print(INFO, "Example: python AXI.py lite_s")
        exit(1)
    
    vs_name_suffix = sys.argv[1]
    for token in ("ios.vs", "logic.vs", "signals.vs"):
        vs_name_suffix = vs_name_suffix.replace(token, "")
    config_line = sys.argv[2].strip()
    configurations = config_line.replace(",", "").replace("//", "").replace("/*", "").replace("*/", "").strip()
    interface = AXIInterface(vs_name_suffix, configurations)
    return interface


# Check if this script is called directly
if __name__ == "__main__":
    axi_if = parse_arguments()
    axi_if.generate()
