#!/usr/bin/env python

# FIFO.py script creates a First In First Out (FIFO) buffer
# To call this script in a Verilog file it should follow one of the following patterns:
#   `include "FIFO_{name}.vs" // {Width}x{Depth}, Write Data, Write Enable, Read Data, Read Enable, Empty, Full
# and
#   `include "FIFO_{list_name}.vs" /*
#             FIFO name, {Width}x{Depth}, Write Data, Write Enable, Read Data, Read Enable, Empty, Full
#             FIFO name, {Width}x{Depth}, Write Data, Write Enable, Read Data, Read Enable, Empty, Full
#             ...
#             */
# Note: If we pass "None" to the Empty or Full signals then these signals will not be generated. If we pass an empty string then we will use the default signals.
# Default signals are: {FIFO_name}_w, {FIFO_name}_w_en, {FIFO_name}_r, {FIFO_name}_r_en, {FIFO_name}_empty, {FIFO_name}_full

import sys, re

from VeriSnip.vs_colours import *

# Check if this script is called directly
if __name__ == "__main__":
    print(sys.argv)
