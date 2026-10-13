#!/usr/bin/env python

# reg.py generates a list of registers.
# To call this script in a Verilog file, use the following pattern:
#   `include "reg_{list_name}.vs" /* [reset = <rst>,] [clock = <clk>]
#     Name, Size, Reset_value, Reg_reset, Reg_enable, Reg_next
#     */
# Defaults: clock = clk_i, no global reset, Size = 1, Reset_value = 0, no Reg_reset/Reg_enable, Reg_next = {Name}_n.
# A register with a global and a custom reset gets {Name}_int_rst = global | custom.
# Only synchronous, active-high resets are supported.

import sys, re

from VeriSnip.vs_colours import *

vs_name_suffix = sys.argv[1].removesuffix(".vs")
vs_name = f"reg_{vs_name_suffix}.vs"


class register:
    def __init__(self, reg_properties):
        self.name = ""
        self.signal = ""
        self.size = ""
        self.rst_val = ""
        self.rst = ""
        self.en = ""
        self.next = ""

        reg_properties = [reg_property.strip() for reg_property in reg_properties]
        # TO DO: function that parses reg_properties and is able to organize its values in a list
        try:
            self.set_reg_name(reg_properties[0])
            self.set_reg_size(reg_properties[1])
            self.set_reg_rst_val(reg_properties[2])
            self.set_reg_rst(reg_properties[3])
            self.set_reg_en(reg_properties[4])
            self.set_reg_next(reg_properties[5])
        except IndexError:
            vs_print(ERROR, f"Not enough arguments for register {reg_properties[0]}.")
            exit(1)

    def set_reg_name(self, reg_name):
        if "name=" in reg_name:
            reg_name = reg_name.split("name=")[1]
        if reg_name == "":
            vs_print(ERROR, "You should give a name to the register.")
            exit(1)
        else:
            self.name = reg_name
        self.signal = self.name
        for suffix in ["_q", "_r", "_reg", "_o"]:
            if self.name.endswith(suffix):
                self.name = self.name.rsplit(suffix)[0]
                break

    def set_reg_size(self, reg_size):
        if "size=" in reg_size:
            reg_size = reg_size.split("=")[1]
        if reg_size == "":
            self.size = "1"
        else:
            self.size = reg_size

    def set_reg_rst_val(self, reg_rst_val):
        if "rst_val=" in reg_rst_val:
            reg_rst_val = reg_rst_val.split("=")[1]
        if reg_rst_val == "" or reg_rst_val == "0":
            if self.size != "1":
                self.rst_val = "{" + self.size + "{1'b0}}"
            else:
                self.rst_val = "1'b0"
        elif reg_rst_val.isdigit():
            self.rst_val = f"'d{reg_rst_val}"
        else:
            self.rst_val = reg_rst_val

    def set_reg_rst(self, reg_rst):
        if "rst=" in reg_rst:
            reg_rst = reg_rst.split("=")[1]
        if (reg_rst == "") or (reg_rst == "None") or (reg_rst == "1'b0"):
            self.rst = None
        elif reg_rst.startswith("_"):
            self.rst = f"{self.name}{reg_rst}"
        else:
            self.rst = reg_rst

    def set_reg_en(self, reg_en):
        if "en=" in reg_en:
            reg_en = reg_en.split("=")[1]
        if (reg_en == "") or (reg_en == "None") or (reg_en == "1'b1"):
            self.en = None
        elif reg_en.startswith("_"):
            self.en = f"{self.name}{reg_en}"
        else:
            self.en = reg_en

    def set_reg_next(self, reg_next):
        if "next=" in reg_next:
            reg_next = reg_next.split("=")[1]
        if reg_next == "":
            self.next = f"{self.name}_n"
        elif reg_next.startswith("_"):
            self.next = f"{self.name}{reg_next}"
        else:
            self.next = reg_next


def write_vs(string="", file_name="reg.vs"):
    with open(file_name, "w") as file:
        file.write(string)


def parse_global_header(lines):
    """Parse an optional 'reset = <rst>, clock = <clk>' first line.

    Returns (clock, reset, remaining_lines). Lines whose every comma separated part is a
    reset/clock assignment are a header; anything else is a register description.
    """
    clock = "clk_i"
    reset = None
    if not lines:
        return clock, reset, lines
    parts = [part.strip() for part in lines[0].split(",")]
    assignments = [part.split("=", 1) if "=" in part else None for part in parts]
    keys = ("reset", "rst", "clock", "clk")
    if not all(a is not None and a[0].strip().lower() in keys for a in assignments):
        return clock, reset, lines
    for key, value in assignments:
        key, value = key.strip().lower(), value.strip()
        if key in ("reset", "rst"):
            reset = value if value not in ("", "None") else None
        else:
            clock = value
    return clock, reset, lines[1:]


def reg_description(reg_list, clock="clk_i", global_rst=None):
    verilog_code = f"  // Automatically generated register {vs_name_suffix}\n"
    for reg in reg_list:
        if global_rst is not None and reg.rst is not None:
            verilog_code += f"  wire {reg.name}_int_rst = {global_rst} | {reg.rst};\n"
            reg.rst = f"{reg.name}_int_rst"
        elif global_rst is not None:
            reg.rst = global_rst
    verilog_code += f"  always @(posedge {clock}) begin\n"
    for reg in reg_list:
        verilog_code += f"    // Register {reg.signal}\n"
        if (reg.rst is not None) and (reg.en is not None):
            verilog_code += f"    if ({reg.rst}) begin\n"
            verilog_code += f"      {reg.signal} <= {reg.rst_val};\n"
            verilog_code += f"    end else if ({reg.en}) begin\n"
            verilog_code += f"      {reg.signal} <= {reg.next};\n"
            verilog_code += f"    end\n"
        elif reg.rst is not None:
            verilog_code += f"    if ({reg.rst}) begin\n"
            verilog_code += f"      {reg.signal} <= {reg.rst_val};\n"
            verilog_code += f"    end else begin\n"
            verilog_code += f"      {reg.signal} <= {reg.next};\n"
            verilog_code += f"    end\n"
        elif reg.en is not None:
            verilog_code += f"    if ({reg.en}) begin\n"
            verilog_code += f"      {reg.signal} <= {reg.next};\n"
            verilog_code += f"    end\n"
        else:
            verilog_code += f"    {reg.signal} <= {reg.next};\n"
    verilog_code += "  end\n"

    return verilog_code


def parse_arguments():
    if len(sys.argv) < 3:
        vs_print(ERROR, "Not enough arguments.")
        exit(1)

    comment = sys.argv[2].replace("/*", "").replace("*/", "").strip()
    lines = [line.strip() for line in comment.split("\n") if line.strip()]
    clock, global_rst, lines = parse_global_header(lines)

    register_list = []
    for description in lines:
        # Split the string by commas outside of any type of braces
        reg_properties = re.split(r",(?![^{}[\]()]*[}\])])", description)
        register_list.append(register(reg_properties))

    return register_list, clock, global_rst


# Check if this script is called directly
if __name__ == "__main__":
    reg_list, clock, global_rst = parse_arguments()
    vs_content = reg_description(reg_list, clock, global_rst)
    write_vs(vs_content, vs_name)
