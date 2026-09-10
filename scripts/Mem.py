#!/usr/bin/env python

# mem.py script creates a memory
# To call this script in a Verilog file it should follow one of the following patterns:
#   `include "Mem_{Memory_name}.vs" // Type, Depth, Width, Init_file (optional)
# where Type can be: distributed RAM, BRAM, URAM, or ROM.
# The Init_file is optional for distributed RAM and BRAM, required for ROM,
# and not allowed for URAM (UltraRAM cannot be initialized from a file).
# Default values are: Type = None; Depth = None; Width = None; Init_file = None.


import sys

from VeriSnip.vs_colours import *

vs_name_suffix = sys.argv[1].removesuffix(".vs")

# Maps the include-comment type to (kind, style).
# kind is RAM or ROM; style selects the inference template.
VALID_TYPES = {
    "DISTRIBUTED RAM": ("RAM", "DISTRIBUTED"),
    "BRAM": ("RAM", "BRAM"),
    "URAM": ("RAM", "URAM"),
    "ROM": ("ROM", "DISTRIBUTED"),
}
VALID_TYPE_HELP = "distributed RAM, BRAM, URAM, or ROM"


class Memory:
    def __init__(self, mem_properties, name):
        self.type = " ".join(mem_properties[0].strip().upper().split())
        self.kind = ""
        self.style = ""
        self.depth = mem_properties[1].strip() if len(mem_properties) > 1 else ""
        self.width = mem_properties[2].strip() if len(mem_properties) > 2 else ""
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
            vs_print(ERROR, f"You must provide the memory type: {VALID_TYPE_HELP}.")
            exit(1)
        if self.type == "RAM":
            vs_print(
                ERROR,
                "Invalid memory type: RAM. Use distributed RAM, BRAM, or URAM.",
            )
            exit(1)
        if self.type not in VALID_TYPES:
            vs_print(
                ERROR,
                f"Invalid memory type: {self.type}. Use {VALID_TYPE_HELP}.",
            )
            exit(1)
        self.kind, self.style = VALID_TYPES[self.type]
        if self.depth == "":
            vs_print(ERROR, "You must provide the memory depth.")
            exit(1)
        if self.width == "":
            vs_print(ERROR, "You must provide the memory width.")
            exit(1)
        if self.kind == "ROM" and self.init_file == "":
            vs_print(ERROR, "You must provide an init file for ROM.")
            exit(1)
        if self.style == "URAM" and self.init_file != "":
            vs_print(
                ERROR,
                "URAM cannot use an init file. UltraRAM is not initialized from a memory file.",
            )
            exit(1)


def _type_label(mem):
    return mem.type.replace("DISTRIBUTED RAM", "distributed RAM")


def _init_block(mem):
    if mem.init_file == "":
        return ""
    return f"""
  initial begin
    $readmemh("{mem.init_file}", {mem.name});
  end
"""


def _byte_enable_write(mem):
    return f"""    for ({mem.name}_b = 0; {mem.name}_b < {mem.width} / 8; {mem.name}_b = {mem.name}_b + 1) begin
      if ({mem.name}_w_en[{mem.name}_b]) begin
        {mem.name}[{mem.name}_w_addr][8*{mem.name}_b+:8] <= {mem.name}_data_in[8*{mem.name}_b+:8];
      end
    end"""


def memory_signals(mem):
    address_width = f"{mem.name}AddrWidth"
    ram_attr = ""
    if mem.style == "URAM":
        ram_attr = '  (* ram_style = "ultra" *)\n'
    verilog_code = f"""  // Automatically generated signals for {mem.name} {_type_label(mem)} memory
  localparam integer {address_width} = (({mem.depth}==1) ? 1 : $clog2({mem.depth}));
{ram_attr}  logic [{mem.width}-1:0] {mem.name} [{mem.depth}];
"""
    if mem.kind == "RAM":
        verilog_code += f"  logic [{address_width}-1:0] {mem.name}_w_addr;\n"
    verilog_code += f"  logic [{address_width}-1:0] {mem.name}_r_addr;\n"
    verilog_code += f"  logic [{mem.width}-1:0] {mem.name}_data_out;\n"
    if mem.kind == "RAM":
        verilog_code += f"  logic [{mem.width}-1:0] {mem.name}_data_in;\n"
        verilog_code += f"  logic [{mem.width}/8-1:0] {mem.name}_w_en;\n"

    with open(f"Mem_{vs_name_suffix}_signals.vs", "w") as file:
        file.write(verilog_code)
    return


def memory_logic(mem):
    verilog_code = f"  // Automatically generated logic for {mem.name} {_type_label(mem)} memory\n"
    if mem.kind == "ROM":
        verilog_code += f"  initial begin\n"
        verilog_code += f'    $readmemh("{mem.init_file}", {mem.name});\n'
        verilog_code += f"  end\n\n"
        verilog_code += (
            f"  assign {mem.name}_data_out = {mem.name}[{mem.name}_r_addr];\n\n"
        )
    elif mem.style == "DISTRIBUTED":
        verilog_code += _init_block(mem)
        verilog_code += f"""
  integer {mem.name}_b;
  always_ff @(posedge clk_i) begin
{_byte_enable_write(mem)}
  end
  assign {mem.name}_data_out = {mem.name}[{mem.name}_r_addr];\n
"""
    elif mem.style in ("BRAM", "URAM"):
        verilog_code += _init_block(mem)
        ram_attr = ""
        if mem.style == "URAM":
            ram_attr = '  (* ram_style = "ultra" *)\n'
        verilog_code += f"""
  integer {mem.name}_b;
{ram_attr}  always_ff @(posedge clk_i) begin
    {mem.name}_data_out <= {mem.name}[{mem.name}_r_addr];
{_byte_enable_write(mem)}
  end
"""
    else:
        vs_print(ERROR, "Invalid memory type.")
        exit(1)

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
