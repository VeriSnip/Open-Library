#!/usr/bin/env python

# unpacked_reg.py script creates registers for unpacked arrays of parameter-dependent size.
# Every array register is updated element by element inside a for loop, so a whole array
# costs a single always block instead of one per element (e.g. per generate iteration).
# To call this script in a Verilog file it should follow one of the following patterns:
#   `include "unpacked_reg_{Reg_name}.vs" // Size, Dimensions, Reset Value, Reg_reset, Reg_enable, Reg_next
# and
#   `include "unpacked_reg_{list_name}.vs" /*
#             Reg_name0, Size, Dimensions, Reset Value, Reg_reset, Reg_enable, Reg_next
#             Reg_name1, Size, Dimensions, Reset Value, Reg_reset, Reg_enable, Reg_next
#             ...
#             */
# Dimensions are the unpacked array sizes, e.g. [SA_HEIGHT][SA_WIDTH].
# Reg_next is an array indexed like the register; Reg_reset and Reg_enable are scalars.
# Remaining fields and defaults follow reg.py.

import sys, re

from VeriSnip.vs_colours import *
from reg import register, write_vs

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


def reg_description(reg_list):
    verilog_code = f"  // Automatically generated array register {vs_name_suffix}\n"
    verilog_code += "  always @(posedge clk_i) begin\n"
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

    if "//" in sys.argv[2]:
        registers_description = [f'{vs_name_suffix}, {sys.argv[2][sys.argv[2].index("//")+2:]}']
    else:
        registers_description = [line for line in sys.argv[2].split("\n") if line.strip()]

    # Split the string by commas outside of any type of braces
    return [
        array_register(re.split(r",(?![^{}[\]()]*[}\])])", description))
        for description in registers_description
    ]


# Check if this script is called directly
if __name__ == "__main__":
    write_vs(reg_description(parse_arguments()), vs_name)
