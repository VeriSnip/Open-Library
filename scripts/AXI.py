#!/usr/bin/env python

# AXI.py script creates required AXI5 IOs and logic for Lite, Stream, and Full interfaces.
# It generates two files:
# To call this script in a Verilog file it should follow one of the following patterns:
#   `include "AXI_[ios,signals,logic][_{interface/bus_name}].vs" // AXI-[Lite,Full,Stream] [Manager,Subordinate] {bus_name}
# and
#   `include "AXI_[ios,signals,logic][_{interface_name}].vs" /*
#             AXI-[Lite,Full,Stream] [Manager,Subordinate] {bus_name}
#             AXI-[Lite,Full,Stream] [Manager,Subordinate] {bus_name}
#             AXI-[Lite,Full,Stream] [Manager,Subordinate] {bus_name}
#             ...
#             */
# Notes:
# - {bus_name} is optional. If it is not provided, the script will use the interface name as the bus name.
# - {interface_name} is optional. If it is not provided, the script will use the bus name as the interface name.

from logging import Manager
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
            if bus.type == "AXI-Lite" and bus.node == "Manager":
                  vs_print(WARNING, "AXI-Lite Manager interface not implemented yet.")
                  pass
            elif bus.type == "AXI-Lite" and bus.node == "Subordinate":
                vs_print(INFO, f"Generating AXI-Lite Subordinate {bus.name} interface.")
                prefix = f"AXIL_{bus.name}" if bus.name else "AXIL"
                parameters_content += get_lite_s_parameters(prefix)
                ios_content += get_lite_s_ios(prefix)
                logic_content += get_lite_s_logic(prefix, bus.name)
                signals_content += get_lite_s_signals(prefix)
            elif bus.type == "AXI-Stream" and bus.node == "Manager":
                vs_print(WARNING, "AXI-Stream Manager interface not implemented yet.")
                pass
            elif bus.type == "AXI-Stream" and bus.node == "Subordinate":
                vs_print(WARNING, "AXI-Stream Subordinate interface not implemented yet.")
                pass
            elif bus.type == "AXI-Full" and bus.node == "Manager":
                prefix = f"AXI_M_{bus.name}" if bus.name else "AXI_M"
                parameters_content += get_full_m_parameters(prefix)
                ios_content += get_full_m_ios(prefix)
                signals_content += get_full_m_signals(prefix)
                logic_content += get_full_m_logic(prefix)
                vs_print(INFO, f"Generating AXI-Full Manager {bus.name} interface.")
            elif bus.type == "AXI-Full" and bus.node == "Subordinate":
                vs_print(WARNING, "AXI-Full Subordinate interface not implemented yet.")
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


def get_lite_s_parameters(bus_prefix):
  return f"""    // Generated parameters for AXI-Lite Subordinate
    parameter integer {bus_prefix}_ADDR_WIDTH = 32,
    parameter integer {bus_prefix}_DATA_WIDTH = 32,
    parameter integer {bus_prefix}_ID_W_WIDTH = 1,
    parameter integer {bus_prefix}_ID_R_WIDTH = 1,
"""

def get_lite_s_ios(bus_prefix):
    return f"""    // Generated IOs for AXI-Lite Subordinate
    input wire {bus_prefix}_awvalid_i,
    output reg {bus_prefix}_awready_o,
    input wire [{bus_prefix}_ID_W_WIDTH-1:0] {bus_prefix}_awid_i,
    input wire [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awaddr_i,
    input wire {bus_prefix}_wvalid_i,
    output reg {bus_prefix}_wready_o,
    input wire [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wdata_i,
    input wire [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wstrb_i,
    output reg {bus_prefix}_bvalid_o,
    input wire {bus_prefix}_bready_i,
    output reg [{bus_prefix}_ID_W_WIDTH-1:0] {bus_prefix}_bid_o,
    input wire {bus_prefix}_arvalid_i,
    output reg {bus_prefix}_arready_o,
    input wire [{bus_prefix}_ID_R_WIDTH-1:0] {bus_prefix}_arid_i,
    input wire [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_araddr_i,
    output reg {bus_prefix}_rvalid_o,
    input wire {bus_prefix}_rready_i,
    output reg [{bus_prefix}_ID_R_WIDTH-1:0] {bus_prefix}_rid_o,
    output reg [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_rdata_o,
"""

def get_lite_s_signals(bus_prefix):
    return f"""  // Generated signals for AXI-Lite Subordinate
  reg  [1:0] {bus_prefix}_w_state;
  reg  [1:0] {bus_prefix}_w_state_n;
  reg  {bus_prefix}_awready_n;
  reg  [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awaddr_q;
  reg  [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awaddr_n;
  reg  [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awaddr_sb; // "sb" is an abbreviation for skid buffer
  reg  [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awaddr_sb_n;
  reg  {bus_prefix}_wready_n;
  reg  [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wdata;
  reg  [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wdata_sb;
  reg  [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wdata_sb_n;
  reg  [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wstrb;
  reg  [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wstrb_sb;
  reg  [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wstrb_sb_n;
  reg  {bus_prefix}_bvalid_n;
  reg  [{bus_prefix}_ID_W_WIDTH-1:0] {bus_prefix}_bid_n;
  reg  [{bus_prefix}_ID_W_WIDTH-1:0] {bus_prefix}_bid_sb;
  reg  [{bus_prefix}_ID_W_WIDTH-1:0] {bus_prefix}_bid_sb_n;
  reg  {bus_prefix}_r_state;
  reg  {bus_prefix}_r_state_n;
  reg  {bus_prefix}_arready_n;
  reg  [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_araddr_q;
  reg  [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_araddr_n;
  reg  [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_araddr_sb;
  reg  [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_araddr_sb_n;
  reg  {bus_prefix}_rvalid_n;
  reg  [{bus_prefix}_ID_R_WIDTH-1:0] {bus_prefix}_rid_n;
  reg  [{bus_prefix}_ID_R_WIDTH-1:0] {bus_prefix}_rid_sb;
  reg  [{bus_prefix}_ID_R_WIDTH-1:0] {bus_prefix}_rid_sb_n;
  wire [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_rdata;
  reg  [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_rdata_n;
"""

def get_lite_s_logic(bus_prefix, interface_name=None):
    return f"""  // Generated logic for AXI-Lite Subordinate
  // Write state machine
  always @(*) begin
    // 1. DEFAULT ASSIGNMENTS
    {bus_prefix}_w_state_n   = {bus_prefix}_w_state;
    {bus_prefix}_awready_n   = {bus_prefix}_awready_o;
    {bus_prefix}_awaddr_n    = {bus_prefix}_awaddr_q;
    {bus_prefix}_awaddr_sb_n = {bus_prefix}_awaddr_sb;
    {bus_prefix}_wready_n    = {bus_prefix}_wready_o;
    {bus_prefix}_wdata       = 0;
    {bus_prefix}_wdata_sb_n  = {bus_prefix}_wdata_sb;
    {bus_prefix}_wstrb       = 0;
    {bus_prefix}_wstrb_sb_n  = {bus_prefix}_wstrb_sb;
    {bus_prefix}_bid_n       = {bus_prefix}_bid_o;
    {bus_prefix}_bid_sb_n    = {bus_prefix}_bid_sb;
    {bus_prefix}_bvalid_n    = {bus_prefix}_bvalid_o;
    // 2. STATE MACHINE
    case({bus_prefix}_w_state)
      2'b00: begin
        if ({bus_prefix}_awvalid_i & {bus_prefix}_awready_o & {bus_prefix}_wvalid_i & {bus_prefix}_wready_o) begin
          {bus_prefix}_bvalid_n = 1'b1;
          if ({bus_prefix}_bvalid_o & ~{bus_prefix}_bready_i) begin
            {bus_prefix}_w_state_n = 2'b11;
            {bus_prefix}_awready_n = 1'b0;
            {bus_prefix}_awaddr_sb_n = {bus_prefix}_awaddr_i;
            {bus_prefix}_wready_n = 1'b0;
            {bus_prefix}_wdata_sb_n = {bus_prefix}_wdata_i;
            {bus_prefix}_wstrb_sb_n = {bus_prefix}_wstrb_i;
            {bus_prefix}_bid_sb_n = {bus_prefix}_awid_i;
          end else begin
            {bus_prefix}_awaddr_n = {bus_prefix}_awaddr_i;
            {bus_prefix}_wdata = {bus_prefix}_wdata_i;
            {bus_prefix}_wstrb = {bus_prefix}_wstrb_i;
            {bus_prefix}_bid_n = {bus_prefix}_awid_i;
          end
        end else begin
          if ({bus_prefix}_awvalid_i & {bus_prefix}_awready_o) begin
            {bus_prefix}_w_state_n = 2'b01;
            {bus_prefix}_awready_n = 1'b0;
            {bus_prefix}_awaddr_sb_n = {bus_prefix}_awaddr_i;
            {bus_prefix}_bid_sb_n = {bus_prefix}_awid_i;
          end else if ({bus_prefix}_wvalid_i & {bus_prefix}_wready_o) begin
            {bus_prefix}_w_state_n = 2'b10;
            {bus_prefix}_wready_n = 1'b0;
            {bus_prefix}_wdata_sb_n = {bus_prefix}_wdata_i;
            {bus_prefix}_wstrb_sb_n = {bus_prefix}_wstrb_i;
          end else begin
            {bus_prefix}_awready_n = 1'b1;
            {bus_prefix}_wready_n = 1'b1;
          end
          if ({bus_prefix}_bready_i) begin
            {bus_prefix}_bvalid_n = 1'b0;
          end
        end
      end
      2'b01: begin
        if ({bus_prefix}_wvalid_i & {bus_prefix}_wready_o) begin
          {bus_prefix}_bvalid_n = 1'b1;
          if ({bus_prefix}_bvalid_o & ~{bus_prefix}_bready_i) begin
            {bus_prefix}_w_state_n = 2'b11;
            {bus_prefix}_wready_n = 1'b0;
            {bus_prefix}_wdata_sb_n = {bus_prefix}_wdata_i;
            {bus_prefix}_wstrb_sb_n = {bus_prefix}_wstrb_i;
          end else begin
            {bus_prefix}_w_state_n = 2'b00;
            {bus_prefix}_awready_n = 1'b1;
            {bus_prefix}_awaddr_n = {bus_prefix}_awaddr_sb;
            {bus_prefix}_wdata = {bus_prefix}_wdata_i;
            {bus_prefix}_wstrb = {bus_prefix}_wstrb_i;
            {bus_prefix}_bid_n = {bus_prefix}_bid_sb;
          end
        end else begin
          if ({bus_prefix}_bready_i) begin
            {bus_prefix}_bvalid_n = 1'b0;
          end
        end
      end
      2'b10: begin
        if ({bus_prefix}_awvalid_i & {bus_prefix}_awready_o) begin
          {bus_prefix}_bvalid_n = 1'b1;
          if ({bus_prefix}_bvalid_o & ~{bus_prefix}_bready_i) begin
            {bus_prefix}_w_state_n = 2'b11;
            {bus_prefix}_awready_n = 1'b0;
            {bus_prefix}_awaddr_sb_n = {bus_prefix}_awaddr_i;
            {bus_prefix}_bid_sb_n = {bus_prefix}_awid_i;
          end else begin
            {bus_prefix}_w_state_n = 2'b00;
            {bus_prefix}_awaddr_n = {bus_prefix}_awaddr_i;
            {bus_prefix}_wready_n = 1'b1;
            {bus_prefix}_wdata = {bus_prefix}_wdata_sb;
            {bus_prefix}_wstrb = {bus_prefix}_wstrb_sb;
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
          {bus_prefix}_w_state_n = 2'b00;
          {bus_prefix}_awready_n = 1'b1;
          {bus_prefix}_awaddr_n = {bus_prefix}_awaddr_sb;
          {bus_prefix}_wready_n = 1'b1;
          {bus_prefix}_wdata = {bus_prefix}_wdata_sb;
          {bus_prefix}_wstrb = {bus_prefix}_wstrb_sb;
          {bus_prefix}_bid_n = {bus_prefix}_bid_sb;
        end
      end
      default: ;
    endcase
  end

  // Read state machine
  always @(*) begin
    // 1. DEFAULT ASSIGNMENTS
    {bus_prefix}_r_state_n   = {bus_prefix}_r_state;
    {bus_prefix}_arready_n   = {bus_prefix}_arready_o;
    {bus_prefix}_araddr_n    = {bus_prefix}_araddr_q;
    {bus_prefix}_araddr_sb_n = {bus_prefix}_araddr_sb;
    {bus_prefix}_rvalid_n    = {bus_prefix}_rvalid_o;
    {bus_prefix}_rid_n       = {bus_prefix}_rid_o;
    {bus_prefix}_rid_sb_n    = {bus_prefix}_rid_sb;
    {bus_prefix}_rdata_n     = {bus_prefix}_rdata_o;
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
            {bus_prefix}_rdata_n = {bus_prefix}_rdata;
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
          {bus_prefix}_rid_n = {bus_prefix}_rid_sb;
          {bus_prefix}_rdata_n = {bus_prefix}_rdata;
        end
      end
      default: ;
    endcase
  end

  `include "reg_AXI_bus_prefix_{bus_prefix}_{interface_name}.vs"  /*
    {bus_prefix}_w_state   , 2                        , 0, sync_reset, , _n
    {bus_prefix}_awready_o , 1                        , 0, sync_reset, , _n
    {bus_prefix}_awaddr_q  , {bus_prefix}_ADDR_WIDTH  , 0, sync_reset, , _n
    {bus_prefix}_awaddr_sb , {bus_prefix}_ADDR_WIDTH  , 0, sync_reset, , _n
    {bus_prefix}_wready_o  , 1                        , 0, sync_reset, , _n
    {bus_prefix}_wdata_sb  , {bus_prefix}_DATA_WIDTH  , 0, sync_reset, , _n
    {bus_prefix}_wstrb_sb  , {bus_prefix}_DATA_WIDTH/8, 0, sync_reset, , _n
    {bus_prefix}_bvalid_o  , 1                        , 0, sync_reset, , _n
    {bus_prefix}_bid_o     , {bus_prefix}_ID_W_WIDTH  , 0, sync_reset, , _n
    {bus_prefix}_bid_sb    , {bus_prefix}_ID_W_WIDTH  , 0, sync_reset, , _n
    {bus_prefix}_r_state   , 1                        , 0, sync_reset, , _n
    {bus_prefix}_arready_o , 1                        , 0, sync_reset, , _n
    {bus_prefix}_araddr_q  , {bus_prefix}_ADDR_WIDTH  , 0, sync_reset, , _n
    {bus_prefix}_araddr_sb , {bus_prefix}_ADDR_WIDTH  , 0, sync_reset, , _n
    {bus_prefix}_rvalid_o  , 1                        , 0, sync_reset, , _n
    {bus_prefix}_rdata_o   , {bus_prefix}_DATA_WIDTH  , 0, sync_reset, , _n
    {bus_prefix}_rid_o     , {bus_prefix}_ID_R_WIDTH  , 0, sync_reset, , _n
    {bus_prefix}_rid_sb    , {bus_prefix}_ID_R_WIDTH  , 0, sync_reset, , _n
    */
"""
# I should add global resets to register lists

def get_full_m_parameters(bus_prefix):
    return f"""    // Generated Parameters for AXI-Full Manager
    //parameter string {bus_prefix}_AXI_Transport = "Ready",
    parameter integer {bus_prefix}_ID_W_WIDTH = 1,
    parameter integer {bus_prefix}_ADDR_WIDTH = 32,
    //parameter reg {bus_prefix}_LEN_Present = 1,
    //parameter reg {bus_prefix}_SIZE_Present = 1,
    //parameter reg {bus_prefix}_BURST_Present = 1,
    //parameter reg {bus_prefix}_CACHE_Present = 1,
    //parameter reg {bus_prefix}_PROT_Present = 1,
    //parameter reg {bus_prefix}_QOS_Present = 1,
    parameter integer {bus_prefix}_DATA_WIDTH = 32,
    //parameter reg {bus_prefix}_WSTRB_Present = 1,
    parameter integer {bus_prefix}_BRESP_WIDTH = 2,
    parameter integer {bus_prefix}_ID_R_WIDTH = 1,
"""

def get_full_m_ios(bus_prefix):
    return f"""    // Generated IOs for AXI-Full Manager
    output reg {bus_prefix}_awVALID_o,
    input wire {bus_prefix}_awREADY_i,
    output reg [{bus_prefix}_ID_W_WIDTH-1 : 0] {bus_prefix}_awID_o,
    output reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awADDR_o,
    output reg [7:0] {bus_prefix}_awLEN_o,
    output reg [2:0] {bus_prefix}_awSIZE_o,
    output reg [1:0] {bus_prefix}_awBURST_o,
    output reg  {bus_prefix}_awLOCK_o,
    output reg [3:0] {bus_prefix}_awCACHE_o,
    output reg [2:0] {bus_prefix}_awPROT_o,
    output reg [3:0] {bus_prefix}_awQOS_o,
    output reg {bus_prefix}_wVALID_o,
    input wire {bus_prefix}_wREADY_i,
    output reg [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wDATA_o,
    output reg [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wSTRB_o,
    output reg  {bus_prefix}_wLAST_o,
    input wire {bus_prefix}_bVALID_i,
    output reg {bus_prefix}_bREADY_o,
    input  wire [{bus_prefix}_ID_W_WIDTH-1:0] {bus_prefix}_bID_i,
    input  wire [{bus_prefix}_BRESP_WIDTH-1:0] {bus_prefix}_bRESP_i,
    output reg {bus_prefix}_arVALID_o,
    input wire {bus_prefix}_arREADY_i,
    output reg [{bus_prefix}_ID_R_WIDTH-1 : 0] {bus_prefix}_arID_o,
    output reg [{bus_prefix}_ADDR_WIDTH-1 : 0] {bus_prefix}_arADDR_o,
    output reg [7:0] {bus_prefix}_arLEN_o,
    output reg [2:0] {bus_prefix}_arSIZE_o,
    output reg [1:0] {bus_prefix}_arBURST_o,
    output reg  {bus_prefix}_arLOCK_o,
    output reg [3:0] {bus_prefix}_arCACHE_o,
    output reg [2:0] {bus_prefix}_arPROT_o,
    output reg [3:0] {bus_prefix}_arQOS_o,
    input wire {bus_prefix}_rVALID_i,
    output reg {bus_prefix}_rREADY_o,
    input  wire [{bus_prefix}_ID_R_WIDTH-1:0] {bus_prefix}_rID_i,
    input  wire [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_rDATA_i,
    input  wire [1:0] {bus_prefix}_rRESP_i,
    input  wire {bus_prefix}_rLAST_i,
"""

def get_full_m_signals(bus_prefix):
    return f"""  // Generated signals for AXI-Full Manager
  localparam reg[2:0] ActiveByteLanes = ({bus_prefix}_DATA_WIDTH == 8) ? 3'b000:
                                       ({bus_prefix}_DATA_WIDTH == 16) ? 3'b001:
                                       ({bus_prefix}_DATA_WIDTH == 32) ? 3'b010:
                                       ({bus_prefix}_DATA_WIDTH == 64) ? 3'b011:
                                       ({bus_prefix}_DATA_WIDTH == 128) ? 3'b100:
                                       ({bus_prefix}_DATA_WIDTH == 256) ? 3'b101:
                                       ({bus_prefix}_DATA_WIDTH == 512) ? 3'b110: 3'b111;

  // Read FSM (AR/R sequencing). Command inputs are driven by the control FSM.
  reg [1:0] {bus_prefix}_r_state, {bus_prefix}_r_state_n;
  reg [7:0] {bus_prefix}_r_beat_idx, {bus_prefix}_r_beat_idx_n;
  reg {bus_prefix}_arVALID;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_arADDR;
  reg [7:0] {bus_prefix}_arLEN;
  reg {bus_prefix}_arVALID_n;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_arADDR_n;
  reg [7:0] {bus_prefix}_arLEN_n;
  reg {bus_prefix}_rREADY_n;
  reg {bus_prefix}_r_error, {bus_prefix}_r_error_n;
  wire {bus_prefix}_r_beat;
  wire {bus_prefix}_r_done;
  wire {bus_prefix}_r_idle;

  // Write FSM (AW/W/B sequencing). Beat payload comes from the control FSM.
  reg [1:0] {bus_prefix}_w_state, {bus_prefix}_w_state_n;
  reg [7:0] {bus_prefix}_w_beat_idx, {bus_prefix}_w_beat_idx_n;
  reg {bus_prefix}_awVALID;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awADDR;
  reg [7:0] {bus_prefix}_awLEN;
  reg {bus_prefix}_awVALID_n;
  reg [{bus_prefix}_ADDR_WIDTH-1:0] {bus_prefix}_awADDR_n;
  reg [7:0] {bus_prefix}_awLEN_n;
  reg {bus_prefix}_wVALID;
  reg [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wDATA;
  reg [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wSTRB;
  reg {bus_prefix}_wVALID_n;
  reg [{bus_prefix}_DATA_WIDTH-1:0] {bus_prefix}_wDATA_n;
  reg [{bus_prefix}_DATA_WIDTH/8-1:0] {bus_prefix}_wSTRB_n;
  reg {bus_prefix}_wLAST_n;
  reg {bus_prefix}_bREADY_n;
  reg {bus_prefix}_w_error, {bus_prefix}_w_error_n;
  wire {bus_prefix}_w_beat;
  wire {bus_prefix}_w_done;
  wire {bus_prefix}_w_idle;
"""

def get_full_m_logic(bus_prefix, interface_name=None):
    return f"""  // Generated logic for AXI-Full Manager
  assign {bus_prefix}_r_beat = {bus_prefix}_rVALID_i & {bus_prefix}_rREADY_o;
  assign {bus_prefix}_r_done = {bus_prefix}_r_beat & {bus_prefix}_rLAST_i;
  assign {bus_prefix}_r_idle = ({bus_prefix}_r_state == 2'd0);

  // Read FSM: sequences AR/R with registered channel outputs.
  always @(*) begin
    {bus_prefix}_r_state_n    = {bus_prefix}_r_state;
    {bus_prefix}_r_beat_idx_n = {bus_prefix}_r_beat_idx;
    {bus_prefix}_arVALID_n    = {bus_prefix}_arVALID_o;
    {bus_prefix}_arADDR_n     = {bus_prefix}_arADDR_o;
    {bus_prefix}_arLEN_n      = {bus_prefix}_arLEN_o;
    {bus_prefix}_rREADY_n     = {bus_prefix}_rREADY_o;
    {bus_prefix}_r_error_n    = 1'b0;

    {bus_prefix}_arID_o    = {{{bus_prefix}_ID_R_WIDTH{{1'b0}}}};
    {bus_prefix}_arSIZE_o  = ActiveByteLanes;
    {bus_prefix}_arBURST_o = 2'b01;
    {bus_prefix}_arLOCK_o  = 1'b0;
    {bus_prefix}_arCACHE_o = 4'b0011;
    {bus_prefix}_arPROT_o  = 3'b000;
    {bus_prefix}_arQOS_o   = 4'b0000;

    case ({bus_prefix}_r_state)
      2'd0: begin  // RStIdle
        if ({bus_prefix}_arVALID) begin
          {bus_prefix}_arVALID_n    = 1'b1;
          {bus_prefix}_arADDR_n     = {bus_prefix}_arADDR;
          {bus_prefix}_arLEN_n      = {bus_prefix}_arLEN;
          {bus_prefix}_r_beat_idx_n = 8'h00;
          {bus_prefix}_r_state_n    = 2'd1;
        end
      end
      2'd1: begin  // RStAr
        if ({bus_prefix}_arREADY_i) begin
          {bus_prefix}_arVALID_n    = 1'b0;
          {bus_prefix}_rREADY_n     = 1'b1;
          {bus_prefix}_r_beat_idx_n = 8'h00;
          {bus_prefix}_r_state_n    = 2'd2;
        end
      end
      2'd2: begin  // RStData
        if ({bus_prefix}_r_beat) begin
          if ({bus_prefix}_rRESP_i != 2'b00) {bus_prefix}_r_error_n = 1'b1;
          if ({bus_prefix}_r_done) begin
            {bus_prefix}_rREADY_n  = 1'b0;
            {bus_prefix}_r_state_n = 2'd0;
          end else begin
            {bus_prefix}_r_beat_idx_n = {bus_prefix}_r_beat_idx + 8'h01;
          end
        end
      end
      default: {bus_prefix}_r_state_n = 2'd0;
    endcase
  end

  `include "reg_{bus_prefix}_r_registers.vs"  /*
    {bus_prefix}_r_state, 2, 0, sync_reset, , _n
    {bus_prefix}_r_beat_idx, 8, 0, sync_reset, , _n
    {bus_prefix}_arVALID_o, 1, 0, sync_reset, , _n
    {bus_prefix}_arADDR_o, {bus_prefix}_ADDR_WIDTH, 0, sync_reset, , _n
    {bus_prefix}_arLEN_o, 8, 0, sync_reset, , _n
    {bus_prefix}_rREADY_o, 1, 0, sync_reset, , _n
    {bus_prefix}_r_error, 1, 0, sync_reset, , _n
    */

  assign {bus_prefix}_w_beat = {bus_prefix}_wVALID_o & {bus_prefix}_wREADY_i & ~{bus_prefix}_wLAST_o;
  assign {bus_prefix}_w_done = ({bus_prefix}_w_state == 2'd3) & {bus_prefix}_bVALID_i & {bus_prefix}_bREADY_o;
  assign {bus_prefix}_w_idle = ({bus_prefix}_w_state == 2'd0);

  // Write FSM: sequences AW/W/B with registered channel outputs.
  always @(*) begin
    {bus_prefix}_w_state_n    = {bus_prefix}_w_state;
    {bus_prefix}_w_beat_idx_n = {bus_prefix}_w_beat_idx;
    {bus_prefix}_awVALID_n    = {bus_prefix}_awVALID_o;
    {bus_prefix}_awADDR_n     = {bus_prefix}_awADDR_o;
    {bus_prefix}_awLEN_n      = {bus_prefix}_awLEN_o;
    {bus_prefix}_wVALID_n     = {bus_prefix}_wVALID_o;
    {bus_prefix}_wDATA_n      = {bus_prefix}_wDATA_o;
    {bus_prefix}_wSTRB_n      = {{{bus_prefix}_DATA_WIDTH/8{{1'b0}}}};
    {bus_prefix}_wLAST_n      = {bus_prefix}_wLAST_o;
    {bus_prefix}_bREADY_n     = {bus_prefix}_bREADY_o;
    {bus_prefix}_w_error_n    = 1'b0;

    {bus_prefix}_awID_o    = {{{bus_prefix}_ID_W_WIDTH{{1'b0}}}};
    {bus_prefix}_awSIZE_o  = ActiveByteLanes;
    {bus_prefix}_awBURST_o = 2'b01;
    {bus_prefix}_awLOCK_o  = 1'b0;
    {bus_prefix}_awCACHE_o = 4'b0011;
    {bus_prefix}_awPROT_o  = 3'b000;
    {bus_prefix}_awQOS_o   = 4'b0000;

    case ({bus_prefix}_w_state)
      2'd0: begin  // WStIdle
        if ({bus_prefix}_awVALID) begin
          {bus_prefix}_awVALID_n    = 1'b1;
          {bus_prefix}_awADDR_n     = {bus_prefix}_awADDR;
          {bus_prefix}_awLEN_n      = {bus_prefix}_awLEN;
          {bus_prefix}_w_beat_idx_n = 8'h00;
          {bus_prefix}_w_state_n    = 2'd1;
        end
      end
      2'd1: begin  // WStAw
        if ({bus_prefix}_awREADY_i) begin
          {bus_prefix}_awVALID_n = 1'b0;
          {bus_prefix}_wVALID_n  = {bus_prefix}_wVALID;
          {bus_prefix}_wDATA_n   = {bus_prefix}_wDATA;
          {bus_prefix}_wSTRB_n   = {bus_prefix}_wSTRB;
          {bus_prefix}_wLAST_n   = ({bus_prefix}_w_beat_idx == {bus_prefix}_awLEN_o);
          {bus_prefix}_w_state_n = 2'd2;
        end
      end
      2'd2: begin  // WStData
        if ({bus_prefix}_wVALID_o & {bus_prefix}_wREADY_i) begin
          if ({bus_prefix}_wLAST_o) begin
            {bus_prefix}_wVALID_n  = 1'b0;
            {bus_prefix}_wLAST_n   = 1'b0;
            {bus_prefix}_bREADY_n  = 1'b1;
            {bus_prefix}_w_state_n = 2'd3;
          end else begin
            {bus_prefix}_w_beat_idx_n = {bus_prefix}_w_beat_idx + 8'h01;
            {bus_prefix}_wVALID_n     = {bus_prefix}_wVALID;
            {bus_prefix}_wDATA_n      = {bus_prefix}_wDATA;
            {bus_prefix}_wSTRB_n      = {bus_prefix}_wSTRB;
            {bus_prefix}_wLAST_n      = (({bus_prefix}_w_beat_idx + 8'h01) == {bus_prefix}_awLEN_o);
          end
        end
      end
      2'd3: begin  // WStResp
        if ({bus_prefix}_bVALID_i) begin
          if ({bus_prefix}_bRESP_i != 2'b00) {bus_prefix}_w_error_n = 1'b1;
          {bus_prefix}_bREADY_n  = 1'b0;
          {bus_prefix}_w_state_n = 2'd0;
        end
      end
      default: {bus_prefix}_w_state_n = 2'd0;
    endcase
  end

  `include "reg_{bus_prefix}_w_registers.vs"  /*
    {bus_prefix}_w_state, 2, 0, sync_reset, , _n
    {bus_prefix}_w_beat_idx, 8, 0, sync_reset, , _n
    {bus_prefix}_awVALID_o, 1, 0, sync_reset, , _n
    {bus_prefix}_awADDR_o, {bus_prefix}_ADDR_WIDTH, 0, sync_reset, , _n
    {bus_prefix}_awLEN_o, 8, 0, sync_reset, , _n
    {bus_prefix}_wVALID_o, 1, 0, sync_reset, , _n
    {bus_prefix}_wDATA_o, {bus_prefix}_DATA_WIDTH, 0, sync_reset, , _n
    {bus_prefix}_wSTRB_o, {bus_prefix}_DATA_WIDTH/8, 0, sync_reset, , _n
    {bus_prefix}_wLAST_o, 1, 0, sync_reset, , _n
    {bus_prefix}_bREADY_o, 1, 0, sync_reset, , _n
    {bus_prefix}_w_error, 1, 0, sync_reset, , _n
    */
"""

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
