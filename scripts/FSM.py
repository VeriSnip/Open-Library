#!/usr/bin/env python

# FSM.py script creates a finite state machine
# To call this script in a Verilog file it should follow one of the following patterns:
#   `include "FSM_{FSM_name}.vs" /*
#   Current_state -> Next_state, Condition
#   ...
#   */
# Default values are: States = None; Current_state = None; Next_state = None; Condition = None.


import sys


class FSM:
    def __init__(self, list_of_transitions, name):
        self.transitions = [t.strip() for t in list_of_transitions if t.strip()]
        self.states = []
        for transition in self.transitions:
            parts = [part.strip() for part in transition.split("->")]
            if len(parts) == 2:
                current_state, rest = parts
                next_state_condition = rest.split(",")
                next_state = next_state_condition[0].strip()
                if current_state not in self.states:
                    self.states.append(current_state)
                if next_state not in self.states:
                    self.states.append(next_state)
        self.name = name

    def generate_verilog(self):
        self.fsm_signals()
        self.fsm_logic()
        return

    def fsm_signals(self):
        verilog_code = f"// Automatically generated signals for {self.name} FSM\n"
        verilog_code += f"reg [{len(self.states)-1}:0] {self.name}_current_state, {self.name}_next_state;\n"

        with open(f"{sys.argv[4]}_generated_signals.vs", "a") as f:
            f.write(verilog_code)
        return

    def fsm_logic(self):
        n_states = len(self.states)
        register_size = (n_states - 1).bit_length()
        current_state = f"{self.states[0]}"

        verilog_code = f"// Automatically generated logic for {self.name} FSM\n"
        verilog_code += f"always @(*) begin\n"
        verilog_code += f"    case ({self.name}_current_state)\n"
        for transition in self.transitions:
            parts = [part.strip() for part in transition.split("->")]
            if len(parts) == 2:
                current_state, rest = parts
                next_state_condition = rest.split(",")
                next_state = next_state_condition[0].strip()
                condition = (
                    next_state_condition[1].strip()
                    if len(next_state_condition) > 1
                    else "1'b1"
                )
                verilog_code += f"        {current_state}: begin\n"
                verilog_code += f"            if ({condition}) begin\n"
                verilog_code += (
                    f"                {self.name}_next_state = {next_state};\n"
                )
                verilog_code += f"            end else begin\n"
                verilog_code += (
                    f"                {self.name}_next_state = {current_state};\n"
                )

                verilog_code += f"            end\n"
                verilog_code += f"        end\n"
        verilog_code += f"        default: {self.name}_next_state = {current_state};\n"
        verilog_code += f"    endcase\n"
        verilog_code += f"end\n\n"
        verilog_code += f'`include "reg_{self.name}_current_state.vs" // {register_size}, 0, 0, 0, {self.name}_next_state\n'
        with open(f"FSM_{self.name}.vs", "w") as f:
            f.write(verilog_code)


# Check if this script is called directly
if __name__ == "__main__":
    fsm_name = sys.argv[1].replace(".vs", "").strip()
    fsm_config = sys.argv[2].replace("/*", "").replace("*/", "").strip().split(",")
    fsm = FSM(fsm_config, fsm_name)
    fsm.generate_verilog()
