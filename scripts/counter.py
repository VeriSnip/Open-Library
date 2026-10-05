#!/usr/bin/env python

# counter.py script creates a Verilog Snippet for a counter.
# To call this script in a Verilog file it should follow the following patterns:
#   `include "counter_{name}.vs" // Counter Width, Enable, Reset, Reset Value, Direction

# Default values are: Counter Width = 8 bits; Enable = 1'b1; Reset = 1'b0; Reset Value = 0;
# Direction = up. Direction is either "up" (increment) or "down" (decrement).

import sys, re

from VeriSnip.vs_colours import *

vs_name_suffix = sys.argv[1].removesuffix(".vs")
vs_name = f"counter_{vs_name_suffix}.vs"


def write_vs(string="", file_name=None):
    with open(file_name, "w") as file:
        file.write(string)


def verilog_string(counter_width, enable, reset, reset_value, direction):
    operator = "-" if direction == "down" else "+"
    verilog_code = f"  // Automatically generated {vs_name_suffix}\n"
    verilog_code += f'  `include "reg_{vs_name_suffix}.vs" // {counter_width}, {reset_value}, {reset}, {enable}, {vs_name_suffix}_next\n'
    verilog_code += f'  assign {vs_name_suffix}_next = {vs_name_suffix} {operator} 1;\n'
    return verilog_code


def parse_arguments():
    if len(sys.argv) < 2:
        vs_print(ERROR, "Not enough arguments.")
        exit(1)

    # Check if any argument contains "//"
    has_double_slash = any("//" in arg for arg in sys.argv[1:])
    if not has_double_slash:
        vs_print(ERROR, "Unsuported argument format.")
        exit(1)

    # Split the string by commas outside of any type of braces
    args = re.split(r",(?![^{}[\]()]*[}\])])", sys.argv[2][sys.argv[2].index("//")+2:])
    args = [arg.strip() for arg in args]
    if len(args) > 5:
        vs_print(ERROR, "Invalid number of arguments.")
        exit(1)

    defaults = ["8", "1'b1", "1'b0", "0", "up"]
    counter_width, enable, reset, reset_value, direction = [
        arg if arg != "" else default
        for arg, default in zip(args + [""] * (5 - len(args)), defaults)
    ]
    if direction not in ("up", "down"):
        vs_print(ERROR, f"Invalid direction '{direction}'. Expected 'up' or 'down'.")
        exit(1)

    return counter_width, enable, reset, reset_value, direction


# Check if this script is called directly
if __name__ == "__main__":
    vs_content = verilog_string(*parse_arguments())
    write_vs(vs_content, vs_name)
