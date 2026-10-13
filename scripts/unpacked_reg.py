#!/usr/bin/env python

# unpacked_reg.py generates registers for unpacked arrays, updated in a single always block.
# To call this script in a Verilog file, use the following pattern:
#   `include "unpacked_reg_{list_name}.vs" /* [reset = <rst>,] [clock = <clk>]
#     Name, Size, [DIM0][DIM1], Reset_value, Reg_reset, Reg_enable, Reg_next
#     */
# Reg_next is indexed like the register; Reg_reset and Reg_enable are scalars. Other fields follow reg.py.
# Only synchronous, active-high resets are supported.

import sys, re

from VeriSnip.vs_colours import *
from reg import register, write_vs, parse_global_header

vs_name_suffix = sys.argv[1].removesuffix(".vs")
vs_name = f"unpacked_reg_{vs_name_suffix}.vs"


class array_register(register):
    def __init__(self, reg_properties):
        reg_properties = [reg_property.strip() for reg_property in reg_properties]
        if len(reg_properties) < 7:
            vs_print(ERROR, f"Not enough arguments for array register {reg_properties[0]}.")
            exit(1)
        self.dimensions = re.findall(r"\[([^\[\]]+)\]", reg_properties.pop(2))
        if not self.dimensions:
            vs_print(ERROR, f"Array register {reg_properties[0]} has no dimensions.")
            exit(1)
        super().__init__(reg_properties)


def reg_description(reg_list, clock="clk_i", global_rst=None):
    verilog_code = f"  // Automatically generated array register {vs_name_suffix}\n"
    for reg in reg_list:
        if global_rst is not None and reg.rst is not None:
            verilog_code += f"  wire {reg.name}_int_rst = {global_rst} | {reg.rst};\n"
            reg.rst = f"{reg.name}_int_rst"
        elif global_rst is not None:
            reg.rst = global_rst
    verilog_code += f"  always @(posedge {clock}) begin\n"
    for reg in reg_list:
        indices = [f"k{depth}" for depth in range(len(reg.dimensions))]
        index = "".join(f"[{k}]" for k in indices)
        indent = "    "
        verilog_code += f"{indent}// Register {reg.signal}\n"
        for k, dimension in zip(indices, reg.dimensions):
            verilog_code += f"{indent}for (int {k} = 0; {k} < {dimension}; {k}++) begin\n"
            indent += "  "
        if reg.rst is not None:
            verilog_code += f"{indent}if ({reg.rst}) begin\n"
            verilog_code += f"{indent}  {reg.signal}{index} <= {reg.rst_val};\n"
            verilog_code += f"{indent}end else "
            verilog_code += f"if ({reg.en}) begin\n" if reg.en is not None else "begin\n"
            verilog_code += f"{indent}  {reg.signal}{index} <= {reg.next}{index};\n"
            verilog_code += f"{indent}end\n"
        elif reg.en is not None:
            verilog_code += f"{indent}if ({reg.en}) begin\n"
            verilog_code += f"{indent}  {reg.signal}{index} <= {reg.next}{index};\n"
            verilog_code += f"{indent}end\n"
        else:
            verilog_code += f"{indent}{reg.signal}{index} <= {reg.next}{index};\n"
        for _ in reg.dimensions:
            indent = indent[:-2]
            verilog_code += f"{indent}end\n"
    verilog_code += "  end\n"

    return verilog_code


def parse_arguments():
    if len(sys.argv) < 3:
        vs_print(ERROR, "Not enough arguments.")
        exit(1)

    comment = sys.argv[2].replace("/*", "").replace("*/", "").strip()
    lines = [line.strip() for line in comment.split("\n") if line.strip()]
    clock, global_rst, lines = parse_global_header(lines)

    # Split the string by commas outside of any type of braces
    reg_list = [array_register(re.split(r",(?![^{}[\]()]*[}\])])", description)) for description in lines]
    return reg_list, clock, global_rst


# Check if this script is called directly
if __name__ == "__main__":
    reg_list, clock, global_rst = parse_arguments()
    write_vs(reg_description(reg_list, clock, global_rst), vs_name)
