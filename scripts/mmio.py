#!/usr/bin/env python

# mmio.py script creates memory mapped registers
# To call this script in a Verilog file it should follow one of the following patterns:
#   `include "mmio_{module}.vs" /*
#   Reg_name0, Size, Reset Value, Reg_reset, Reg_enable, Reg_next, Address, Access Type, Default Value
#   Reg_name1, Size, Reset Value, Reg_reset, Reg_enable, Reg_next, Address, Access Type, Default Value
#   Reg_name2, Size, Reset Value, Reg_reset, Reg_enable, Reg_next, Address, Access Type, Default Value
#   ...
#   */
# Default values are: Size = 1 bit; Reset Value = 0; Reg_reset = None; Reg_enable = None; Reg_next = {Reg_name}_n; Access Type = "R/W"; Default Value = Reg_name.

import subprocess
import sys
from VeriSnip.vs_build import (
    find_verilog_and_scripts,
    find_filename_in_list,
)
from VeriSnip.vs_colours import *
from reg import register

vs_name_suffix = sys.argv[1].removesuffix(".vs")
vs_name = f"mmio_{vs_name_suffix}.vs"

assigns = ""
read_always = ""
write_always = ""


class memory_mapped_register:
    def __init__(self, description) -> None:
        properties = custom_split(description)
        properties = [prop.strip() for prop in properties]
        self.reg = register(
            [
                properties[0],
                properties[1],
                properties[2],
                properties[3],
                properties[4],
                properties[5],
            ]
        )
        self.set_address(properties[6])
        self.set_access_type(properties[7])
        self.set_default_value(properties[8])
        self.set_sel()

    def set_address(self, mm_reg_address):
        if "address=" in mm_reg_address:
            mm_reg_address = mm_reg_address.split("=")[1]
        self.address = mm_reg_address

    def set_access_type(self, mm_reg_access_type):
        if "access_type=" in mm_reg_access_type:
            mm_reg_access_type = mm_reg_access_type.split("=")[1]
        if mm_reg_access_type == "":
            self.access_type = "R/W"
        else:
            self.access_type = mm_reg_access_type

    def set_default_value(self, mm_reg_default_value):
        if "default=" in mm_reg_default_value:
            mm_reg_default_value = mm_reg_default_value.split("=")[1]
        if mm_reg_default_value == "":
            self.default_value = self.reg.signal
        else:
            self.default_value = mm_reg_default_value

    def set_sel(self):
        self.r_sel = f"r_{self.reg.name}_sel"
        self.w_sel = f"w_{self.reg.name}_sel"


def custom_split(description):
    result = []
    stack = []
    current_token = ""

    for char in description:
        if char == "," and not stack:
            # Split on comma when not inside nested brackets
            result.append(current_token.strip())
            current_token = ""
        else:
            current_token += char
            if char in "{[(":
                # Push opening brackets onto the stack
                stack.append(char)
            elif char in "}])":
                # Pop closing brackets from the stack
                if not stack:
                    raise ValueError("Unbalanced brackets")
                opening_bracket = stack.pop()
                if (
                    char == "}"
                    and opening_bracket != "{"
                    or char == "]"
                    and opening_bracket != "["
                    or char == ")"
                    and opening_bracket != "("
                ):
                    raise ValueError("Mismatched brackets")

    if stack:
        raise ValueError("Unbalanced brackets")

    result.append(current_token.strip())

    return result


def parse_arguments():
    reg_list = []
    if (len(sys.argv) < 2) or (sys.argv[2].strip() == ""):
        print_coloured(ERROR, "Not enough arguments")
        exit(1)
    list_of_regs = sys.argv[2].split("\n")
    for reg in list_of_regs:
        reg_list.append(memory_mapped_register(reg))
    return reg_list


def registers_description(mm_reg_list):
    reg_desc = f'  `include "reg_mmio_{vs_name_suffix}.vs" /*\n'
    for mm_reg in mm_reg_list:
        reg_desc += f"    {mm_reg.reg.signal}, {mm_reg.reg.size}, {mm_reg.reg.rst_val}, {mm_reg.reg.rst}, , {mm_reg.reg.next}\n"
    reg_desc += "  */\n"
    return reg_desc


def find_script():
    return ""


def sel_registers_desc(mm_reg_list):
    sel_reg_desc = ""
    for mm_reg in mm_reg_list:
        if "W" in mm_reg.access_type:
            sel_reg_desc += f"  assign {mm_reg.w_sel} = (w_address == {mm_reg.address}){f' & ({mm_reg.reg.en})' if mm_reg.reg.en != None else ''};\n"
        if "R" in mm_reg.access_type:
            sel_reg_desc += f"  assign {mm_reg.r_sel} = (r_address == {mm_reg.address}){f' & ({mm_reg.reg.en})' if mm_reg.reg.en != None else ''};\n"
    return sel_reg_desc


def write_registers_desc(mm_reg_list):
    w_desc = "  // Write memory mapped register always block\n"
    w_desc += "  always @(*) begin\n"
    for mm_reg in mm_reg_list:
        w_desc += f"    {mm_reg.reg.next} = {mm_reg.default_value};\n"
    w_desc += f"    if (w_enable) begin\n"
    for mm_reg in mm_reg_list:
        if "W" in mm_reg.access_type:
            w_desc += f"      if ({mm_reg.w_sel}) begin\n"
            w_desc += f"        {mm_reg.reg.next} = w_data;\n"
            w_desc += "      end\n"
    w_desc += "    end\n"
    w_desc += "  end\n"
    return w_desc


def read_registers_desc(mm_reg_list):
    r_desc = "  // Read memory mapped register always block\n"
    r_desc += "  always @(*) begin\n"
    r_desc += "    r_data = 0;\n"
    r_desc += f"    if (r_enable) begin\n"
    for mm_reg in mm_reg_list:
        if "R" in mm_reg.access_type:
            r_desc += f"      if ({mm_reg.r_sel}) begin\n"
            r_desc += (
                "        r_data = {{(DATA_WIDTH-"
                + f"{mm_reg.reg.size}"
                + "){1'b0}}, "
                + f"{mm_reg.reg.signal}"
                + "};\n"
            )
            r_desc += "      end\n"
    r_desc += "    end\n"
    r_desc += "  end\n"
    return r_desc


def generate_mmio_signals(mm_reg_list):
    signal_content = "  // Additional signals for memory mapped registers\n"
    signal_content += "  reg [DATA_WIDTH-1:0] r_data;\n"
    signal_content += "  wire [DATA_WIDTH-1:0] w_data;\n"
    signal_content += "  wire [ADDR_WIDTH-1:0] r_address;\n"
    signal_content += "  wire [ADDR_WIDTH-1:0] w_address;\n"
    signal_content += "  wire r_enable;\n"
    signal_content += "  wire w_enable;\n"
    for mm_reg in mm_reg_list:
        if "W" in mm_reg.access_type:
            signal_content += f"  wire {mm_reg.w_sel};\n"
        if "R" in mm_reg.access_type:
            signal_content += f"  wire {mm_reg.r_sel};\n"
        signal_content += f"  reg [{mm_reg.reg.size}-1:0] {mm_reg.reg.signal};\n"
        signal_content += f"  reg [{mm_reg.reg.size}-1:0] {mm_reg.reg.next};\n"
    signal_content += "\n"
    generated_signals_file = f"{sys.argv[4]}_generated_signals.vs"
    with open(generated_signals_file, "a") as file:
        file.write(signal_content)

def create_vs(reg_list):
    vs_content = f"  // Automatically generated memory mapped registers interface for {vs_name_suffix}\n"
    generate_mmio_signals(reg_list)
    vs_content += sel_registers_desc(reg_list)
    vs_content += write_registers_desc(reg_list)
    vs_content += read_registers_desc(reg_list)
    vs_content += registers_description(reg_list)
    write_vs(vs_content, vs_name)


def write_vs(string="", file_name="reg.vs"):
    with open(file_name, "w") as file:
        file.write(string)


# Check if this script is called directly
if __name__ == "__main__":
    reg_list = parse_arguments()
    create_vs(reg_list)
