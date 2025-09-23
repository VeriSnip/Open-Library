#!/usr/bin/env python

# mem.py script creates a memory
# To call this script in a Verilog file it should follow one of the following patterns:
#   `include "mem_{Mem_name}.vs" // Type, Depth, Width, Init_file (optional)
# where Type can be: RAM or ROM. The Init_file is optional, unless you are using a ROM.
# Default values are: Type = None; Depth = None; Width = None; Init_file = None.


import sys, re

from VeriSnip.vs_colours import *

vs_name_suffix = sys.argv[1].removesuffix(".vs")
vs_name = f"mem_{vs_name_suffix}.vs"


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
            print_coloured(ERROR, "You must provide the memory type: RAM or ROM.")
            exit(1)
        if self.type not in ["RAM", "ROM"]:
            print_coloured(ERROR, f"Invalid memory type: {self.type}. Use RAM or ROM.")
            exit(1)
        if self.depth == "":
            print_coloured(ERROR, "You must provide the memory depth.")
            exit(1)
        if self.width == "":
            print_coloured(ERROR, "You must provide the memory width.")
            exit(1)
        if self.type == "ROM" and self.init_file == "":
            print_coloured(ERROR, "You must provide an init file for ROM.")
            exit(1)


def memory_signals(mem):
    verilog_code = f"// Automatically generated signals for {mem.name} memory\n"
    verilog_code += f"reg [{mem.width}-1:0] {mem.name} [{mem.depth}];\n"
    verilog_code += f"wire [$clog2({mem.depth})-1:0] {mem.name}_addr;\n"
    verilog_code += f"wire [{mem.width}-1:0] {mem.name}_data_out;\n"
    verilog_code += f"wire {mem.name}_read_en;\n"
    if mem.type is "RAM":
        verilog_code += f"wire [{mem.width}-1:0] {mem.name}_data_in;\n"
        verilog_code += f"wire {mem.name}_write_en;\n"

    generated_signals_file = f"{sys.argv[4]}_generated_signals.vs"
    with open(generated_signals_file, "a") as file:
        file.write(verilog_code)
    return


def memory_logic(mem):
    verilog_code = f"// Automatically generated logic for {mem.name} memory\n"
    if mem.type == "ROM":
        verilog_code += f"  initial begin\n"
        verilog_code += f'    $readmemh("{mem.init_file}", {mem.name});\n'
        verilog_code += f"  end\n\n"
        verilog_code += (
            f"  assign {mem.name}_data_out = {mem.name}[{mem.name}_addr];\n\n"
        )
    elif mem.type == "RAM":
        if mem.init_file != "":
            verilog_code += f"  initial begin\n"
            verilog_code += f'    $readmemh("{mem.init_file}", {mem.name});\n'
            verilog_code += f"  end\n\n"
        verilog_code += f"  always @(posedge clk) begin\n"
        verilog_code += f"    if ({mem.name}_write_en) begin\n"
        verilog_code += f"      {mem.name}[{mem.name}_addr] <= {mem.name}_data_in;\n"
        verilog_code += f"    end\n"
        verilog_code += f"  end\n\n"
        verilog_code += (
            f"  assign {mem.name}_data_out = {mem.name}[{mem.name}_addr];\n\n"
        )
    else:
        print_coloured(ERROR, "Invalid memory type.")

    with open(vs_name, "w") as file:
        file.write(verilog_code)
    return


def parse_arguments():
    if len(sys.argv) < 2:
        print_coloured(ERROR, "Not enough arguments.")
        exit(1)

    memory_config = sys.argv[2].replace("//", "").strip().split(",")

    return memory_config


# Check if this script is called directly
if __name__ == "__main__":
    mem = Memory(parse_arguments(), vs_name_suffix)
    mem.generate_verilog()
