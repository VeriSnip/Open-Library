#!/usr/bin/env python

# mem.py script creates a memory
# To call this script in a Verilog file it should follow one of the following patterns:
#   `include "Mem_{Memory_name}.vs" // Type, Depth, Width, Init_file (optional)
# where Type can be: RAM or ROM. The Init_file is optional, unless you are using a ROM.
# Default values are: Type = None; Depth = None; Width = None; Init_file = None.


import sys

from VeriSnip.vs_colours import *

vs_name_suffix = sys.argv[1].removesuffix(".vs")


class Memory:
    def __init__(self, mem_properties, name):
        self.type = mem_properties[0].strip().upper()
        self.depth = mem_properties[1].strip()
        self.width = mem_properties[2].strip()
        if len(mem_properties) > 3:
            self.init_file = mem_properties[3].strip()
        else:
            self.init_file = ""
        self.name = name
        self.validate()

    def generate_verilog(self):
        memory_signals(self)
        memory_logic(self)
        return

    def validate(self):
        if self.type == "":
            vs_print(ERROR, "You must provide the memory type: RAM or ROM.")
            exit(1)
        if self.type not in ["RAM", "ROM"]:
            vs_print(ERROR, f"Invalid memory type: {self.type}. Use RAM or ROM.")
            exit(1)
        if self.depth == "":
            vs_print(ERROR, "You must provide the memory depth.")
            exit(1)
        if self.width == "":
            vs_print(ERROR, "You must provide the memory width.")
            exit(1)
        if self.type == "ROM" and self.init_file == "":
            vs_print(ERROR, "You must provide an init file for ROM.")
            exit(1)


def addr_width(depth):
    return f"(({depth}) <= 1 ? 0 : $clog2({depth})-1)"


def memory_signals(mem):
    addr_msb = addr_width(mem.depth)
    verilog_code = f"""  // Automatically generated signals for {mem.name} {mem.type} memory
  logic [{mem.width}-1:0] {mem.name} [{mem.depth}];
"""
    if mem.type == "RAM":
        verilog_code += f"  logic [{addr_msb}:0] {mem.name}_w_addr;\n"
    verilog_code += f"  logic [{addr_msb}:0] {mem.name}_r_addr;\n"
    verilog_code += f"  logic [{mem.width}-1:0] {mem.name}_data_out;\n"
    if mem.type == "RAM":
        verilog_code += f"  logic [{mem.width}-1:0] {mem.name}_data_in;\n"
        verilog_code += f"  logic [{mem.width}/8-1:0] {mem.name}_w_en;\n"

    with open(f"Mem_{vs_name_suffix}_signals.vs", "w") as file:
        file.write(verilog_code)
    return


def memory_logic(mem):
    verilog_code = f"  // Automatically generated logic for {mem.name} {mem.type} memory\n"
    if mem.type == "ROM":
        verilog_code += f"  initial begin\n"
        verilog_code += f'    $readmemh("{mem.init_file}", {mem.name});\n'
        verilog_code += f"  end\n\n"
        verilog_code += (
            f"  assign {mem.name}_data_out = {mem.name}[{mem.name}_r_addr];\n\n"
        )
    elif mem.type == "RAM":
        if mem.init_file != "":
            verilog_code += f"""
  initial begin
    $readmemh("{mem.init_file}", {mem.name});
  end
"""
        verilog_code += f"""
  integer {mem.name}_b;
  always_ff @(posedge clk_i) begin
    for ({mem.name}_b = 0; {mem.name}_b < {mem.width} / 8; {mem.name}_b = {mem.name}_b + 1) begin
      if ({mem.name}_w_en[{mem.name}_b]) begin
        {mem.name}[{mem.name}_w_addr][8*{mem.name}_b+:8] <= {mem.name}_data_in[8*{mem.name}_b+:8];
      end
    end
  end
  assign {mem.name}_data_out = {mem.name}[{mem.name}_r_addr];\n
"""
    else:
        vs_print(ERROR, "Invalid memory type.")

    with open(f"Mem_{vs_name_suffix}.vs", "w") as file:
        file.write(verilog_code)
    return


def parse_arguments():
    if len(sys.argv) < 2:
        vs_print(ERROR, "Not enough arguments.")
        exit(1)

    memory_config = sys.argv[2].replace("//", "").strip().split(",")

    return memory_config


# Check if this script is called directly
if __name__ == "__main__":
    mem = Memory(parse_arguments(), vs_name_suffix)
    mem.generate_verilog()
