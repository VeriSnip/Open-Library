#!/usr/bin/env python

# counter.py script creates a Verilog Snippet for a counter.
# To call this script in a Verilog file it should follow the following patterns:
#   `include "counter_{name}.vs" // Counter Width, Enable, Reset

# Default values are: Counter Width = 8 bits; Enable = 1'b1; Reset = 1'b0.

import sys, re

from VeriSnip.vs_colours import *

vs_name_suffix = sys.argv[1].removesuffix(".vs")
vs_name = f"counter_{vs_name_suffix}.vs"


def write_vs(string="", file_name=None):
    with open(file_name, "w") as file:
        file.write(string)


def verilog_string(counter_width, enable, reset):
    verilog_code = f"  // Automatically generated {vs_name_suffix}\n"
    verilog_code += f'  `include "reg_{vs_name_suffix}.vs" // {counter_width}, 0, {reset}, {enable}, {vs_name_suffix}_next\n'
    verilog_code += f'  assign {vs_name_suffix}_next = {vs_name_suffix} + 1;\n'
    return verilog_code


def parse_arguments():
    if len(sys.argv) < 2:
        print_coloured(ERROR, "Not enough arguments.")
        exit(1)

    # Check if any argument contains "//"
    has_double_slash = any("//" in arg for arg in sys.argv[1:])
    if has_double_slash:
        args = sys.argv[2][sys.argv[2].index("//")+2:].split(',')
        if len(args) == 3:
            counter_width = int(args[0].strip())
            enable = args[1].strip()
            reset = args[2].strip()
        elif len(args) == 2:
            counter_width = int(args[0].strip())
            enable = args[1].strip()
            reset = "1'b0"
        elif len(args) == 1:
            counter_width = int(args[0].strip())
            enable = "1'b1"
            reset = "1'b0"
        else:
            print_coloured(ERROR, "Invalid number of arguments.")
            exit(1)
    else:
        print_coloured(ERROR, "Unsuported argument format.")
        exit(1)

    return counter_width, enable, reset


# Check if this script is called directly
if __name__ == "__main__":
    counter_width, enable, reset = parse_arguments()
    vs_content = verilog_string(counter_width, enable, reset)
    write_vs(vs_content, vs_name)
