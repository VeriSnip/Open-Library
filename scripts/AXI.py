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
                    vs_print(WARNING, "AXI-Lite master interface not implemented yet.")
                    pass
            elif bus.type == "AXI-Stream":
                vs_print(WARNING, "AXI-Stream interface not implemented yet.")
                pass
            elif bus.type == "AXI-Full":
                vs_print(WARNING, "AXI-Full interface not implemented yet.")
                pass
            else:
                vs_print(ERROR, f"Unknown AXI type: {bus.type}")
                exit(1)

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
  return f"""    // Generated parameters for AXI-Lite Slave
    parameter {bus_prefix}_ADDR_WIDTH = 32,
    parameter {bus_prefix}_DATA_WIDTH = 32,
    parameter {bus_prefix}_ID_W_WIDTH = 1,
    parameter {bus_prefix}_ID_R_WIDTH = 1,
"""

def get_lite_slave_ios(bus_prefix):
    return f"""    // Generated IOs for AXI-Lite Slave
    input  wire {bus_prefix}_awvalid_i,
    output  reg {bus_prefix}_awready_o,
    input  wire [{bus_prefix}_ID_W_WIDTH-1:0] {bus_prefix}_awid_i,
    input  wire [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awaddr_i,
    input  wire [2:0] {bus_prefix}_awprot_i,
    input  wire {bus_prefix}_wvalid_i,
    output  reg {bus_prefix}_wready_o,
    input  wire [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wdata_i,
    input  wire [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wstrb_i,
    output  reg {bus_prefix}_bvalid_o,
    input  wire {bus_prefix}_bready_i,
    output  reg [{bus_prefix}_ID_W_WIDTH-1:0] {bus_prefix}_bid_o,
    input  wire {bus_prefix}_arvalid_i,
    output  reg {bus_prefix}_arready_o,
    input  wire [{bus_prefix}_ID_R_WIDTH-1:0] {bus_prefix}_arid_i,
    input  wire [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_araddr_i,
    output  reg {bus_prefix}_rvalid_o,
    input  wire {bus_prefix}_rready_i,
    output  reg [{bus_prefix}_ID_R_WIDTH-1:0] {bus_prefix}_rid_o,
    output  reg [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_rdata_o,
"""

def get_lite_slave_signals(bus_prefix):
    return f"""  // Generated signals for AXI-Lite Slave
  reg [1:0] {bus_prefix}_w_state;
  reg [1:0] {bus_prefix}_w_state_n;
  reg {bus_prefix}_awready_n;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awaddr_q;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awaddr_n;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awaddr_sb; // "sb" is an abbreviation for skid buffer
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awaddr_sb_n;
  reg {bus_prefix}_wready_n;
  reg [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wdata_q;
  reg [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wdata_n;
  reg [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wdata_sb;
  reg [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wdata_sb_n;
  reg [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wstrb_q;
  reg [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wstrb_n;
  reg [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wstrb_sb;
  reg [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wstrb_sb_n;
  reg {bus_prefix}_bvalid_n;
  reg [{bus_prefix}_ID_W_WIDTH-1:0] {bus_prefix}_bid_n;
  reg [{bus_prefix}_ID_W_WIDTH-1:0] {bus_prefix}_bid_sb;
  reg [{bus_prefix}_ID_W_WIDTH-1:0] {bus_prefix}_bid_sb_n;
  reg {bus_prefix}_r_state;
  reg {bus_prefix}_r_state_n;
  reg {bus_prefix}_arready_n;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_araddr_q;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_araddr_n;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_araddr_sb;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_araddr_sb_n;
  reg [{bus_prefix}_ID_R_WIDTH-1:0] {bus_prefix}_rid_n;
  reg [{bus_prefix}_ID_R_WIDTH-1:0] {bus_prefix}_rid_sb;
  reg [{bus_prefix}_ID_R_WIDTH-1:0] {bus_prefix}_rid_sb_n;
"""

# TO DO: Fix wready and awready to add backpressure.
def get_lite_slave_logic(bus_prefix, interface_name=None):
    return f"""  // Generated logic for AXI-Lite Slave
  // Write state machine
  always @(*) begin
    // 1. DEFAULT ASSIGNMENTS
    {bus_prefix}_w_state_n   = {bus_prefix}_w_state;
    {bus_prefix}_awready_n   = {bus_prefix}_awready_o;
    {bus_prefix}_awaddr_n    = {bus_prefix}_awaddr_q;
    {bus_prefix}_awaddr_sb_n = {bus_prefix}_awaddr_sb;
    {bus_prefix}_wready_n    = {bus_prefix}_wready_o;
    {bus_prefix}_wdata_n     = {bus_prefix}_wdata_q;
    {bus_prefix}_wdata_sb_n  = {bus_prefix}_wdata_sb;
    {bus_prefix}_wstrb_n     = {bus_prefix}_wstrb_q;
    {bus_prefix}_wstrb_sb_n  = {bus_prefix}_wstrb_sb;
    {bus_prefix}_bid_n       = {bus_prefix}_bid_o;
    {bus_prefix}_bid_sb_n    = {bus_prefix}_bid_sb;
    {bus_prefix}_bvalid_n    = {bus_prefix}_bvalid_o;
    // 2. STATE MACHINE
    case({bus_prefix}_w_state)
      2'b00: begin
        if ({bus_prefix}_awvalid_i & {bus_prefix}_awready_o & {bus_prefix}_wvalid_i & {bus_prefix}_wready_o) begin
          {bus_prefix}_awaddr_n = {bus_prefix}_awaddr_i;
          {bus_prefix}_wdata_n = {bus_prefix}_wdata_i;
          {bus_prefix}_wstrb_n = {bus_prefix}_wstrb_i;
          {bus_prefix}_bvalid_n = 1'b1;
          if ({bus_prefix}_bvalid_o & ~{bus_prefix}_bready_i) begin
            {bus_prefix}_w_state_n = 2'b11;
            {bus_prefix}_awready_n = 1'b0;
            {bus_prefix}_wready_n = 1'b0;
            {bus_prefix}_bid_n = {bus_prefix}_bid_o;
            {bus_prefix}_bid_sb_n = {bus_prefix}_awid_i;
          end else begin
            {bus_prefix}_w_state_n = 2'b00;
            {bus_prefix}_bid_n = {bus_prefix}_awid_i;
            {bus_prefix}_awready_n = 1'b1;
            {bus_prefix}_wready_n = 1'b1;
          end
        end else begin
          if ({bus_prefix}_awvalid_i & {bus_prefix}_awready_o) begin
            {bus_prefix}_w_state_n = 2'b01;
            {bus_prefix}_awready_n = 1'b0;
            {bus_prefix}_awaddr_sb_n = {bus_prefix}_awaddr_i;
          end else if ({bus_prefix}_wvalid_i & {bus_prefix}_wready_o) begin
            {bus_prefix}_w_state_n = 2'b10;
            {bus_prefix}_wready_n = 1'b0;
            {bus_prefix}_wdata_sb_n = {bus_prefix}_wdata_i;
            {bus_prefix}_wstrb_sb_n = {bus_prefix}_wstrb_i;
          end
          if ({bus_prefix}_bready_i) begin
            {bus_prefix}_bvalid_n = 1'b0;
          end
          {bus_prefix}_awready_n = 1'b1;
          {bus_prefix}_wready_n = 1'b1;
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
            {bus_prefix}_bid_sb_n = {bus_prefix}_awid_i;
          end else begin
            {bus_prefix}_w_state_n = 2'b00;
            {bus_prefix}_awready_n = 1'b1;
            {bus_prefix}_bid_n = {bus_prefix}_awid_i;
          end
        end else begin
          if ({bus_prefix}_bready_i) begin
            {bus_prefix}_bvalid_n = 1'b0;
          end
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
            {bus_prefix}_bid_sb_n = {bus_prefix}_awid_i;
          end else begin
            {bus_prefix}_w_state_n = 2'b00;
            {bus_prefix}_wready_n = 1'b1;
            {bus_prefix}_bid_n = {bus_prefix}_awid_i;
          end
        end else begin
          if ({bus_prefix}_bready_i) begin
            {bus_prefix}_bvalid_n = 1'b0;
          end
        end
      end
      2'b11: begin
        if ({bus_prefix}_bready_i) begin
          {bus_prefix}_bid_n = {bus_prefix}_bid_sb;
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
    // 1. DEFAULT ASSIGNMENTS
    {bus_prefix}_r_state_n = {bus_prefix}_r_state;
    {bus_prefix}_arready_n  = {bus_prefix}_arready_o;
    {bus_prefix}_araddr_n = {bus_prefix}_araddr_q;
    {bus_prefix}_araddr_sb_n = {bus_prefix}_araddr_sb;
    {bus_prefix}_rvalid_n = {bus_prefix}_rvalid_o;
    {bus_prefix}_rid_n = {bus_prefix}_rid_o;
    {bus_prefix}_rid_sb_n = {bus_prefix}_rid_sb;
    // 2. STATE MACHINE
    case({bus_prefix}_r_state)
      1'b0: begin
      // Ready to receive address and send back data
        if ({bus_prefix}_arvalid_i & {bus_prefix}_arready_o) begin
          {bus_prefix}_rvalid_n = 1'b1;
          if ({bus_prefix}_rvalid_o & ~{bus_prefix}_rready_i) begin
            {bus_prefix}_r_state_n = 1'b1;
            {bus_prefix}_arready_n = 1'b0;
            {bus_prefix}_araddr_sb_n = {bus_prefix}_araddr_i;
            {bus_prefix}_rid_sb_n = {bus_prefix}_arid_i;
          end else begin
            {bus_prefix}_araddr_n = {bus_prefix}_araddr_i;
            {bus_prefix}_rid_n = {bus_prefix}_arid_i;
          end
        end else begin
          if ({bus_prefix}_rready_i) begin
            {bus_prefix}_rvalid_n = 1'b0;
          end
          {bus_prefix}_arready_n = 1'b1;
        end
      end
      1'b1: begin
      // Waiting for data to be sent back
        if ({bus_prefix}_rready_i) begin
          {bus_prefix}_r_state_n = 1'b0;
          {bus_prefix}_arready_n = 1'b1;
          {bus_prefix}_araddr_n = {bus_prefix}_araddr_sb;
          {bus_prefix}_rid_n = {bus_prefix}_arid_sb;
        end
      end
      default: ;
    endcase
  end

  `include "reg_AXI_bus_prefix_{bus_prefix}_{interface_name}.vs"  /*
    {bus_prefix}_w_state, 1, 0, rst, , _n
    {bus_prefix}_awready_o, 1, 0, rst, , _n
    {bus_prefix}_awaddr_q, {bus_prefix}_ADDR_WIDTH, 0, rst, , _n
    {bus_prefix}_wready_o, 1, 0, rst, , _n
    {bus_prefix}_wdata_q, {bus_prefix}_DATA_WIDTH, 0, rst, , _n
    {bus_prefix}_wstrb_q, {bus_prefix}_DATA_WIDTH/8, 0, rst, , _n
    {bus_prefix}_bvalid_o, 1, 0, rst, , _n
    {bus_prefix}_bid_o, {bus_prefix}_ID_W_WIDTH, 0, rst, , _n
    {bus_prefix}_bid_skid_buffer, {bus_prefix}_ID_W_WIDTH, 0, rst, , _n
    {bus_prefix}_r_state, 1, 0, rst, , _n
    {bus_prefix}_arready_o, 1, 0, rst, , _n
    {bus_prefix}_araddr_q, {bus_prefix}_ADDR_WIDTH, 0, rst, , _n
    {bus_prefix}_araddr_sb, {bus_prefix}_ADDR_WIDTH, 0, rst, , _n
    {bus_prefix}_rvalid_o, 1, 0, rst, , _n
    {bus_prefix}_rid_o, {bus_prefix}_ID_R_WIDTH, 0, rst, , _n
    {bus_prefix}_rid_sb, {bus_prefix}_ID_R_WIDTH, 0, rst, , _n
    */
"""
# I should add global resets to register lists


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
