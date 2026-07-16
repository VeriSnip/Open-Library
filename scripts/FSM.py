#!/usr/bin/env python

# FSM.py script creates a finite state machine.
# To call this script in a Verilog file it should follow:
#   `include "FSM_{FSM_name}.vs" /* [asynchronous] reset = <rst>, clock = <clk>
#     Current_state -> Next_state: Condition
#                   -> Next_state              // unconditional (else) transition
#     ...
#     */
# Signals are written to FSM_{FSM_name}_signals.vs (include with VS_NO_GENERATE).
# Defaults: asynchronous reset = arst_i, clock = clk_i. Encoding is Gray.
# Condition wires are named {FSM_name}_{From}_{To} and driven by continuous assigns.

import re
import sys
from typing import Any

from VeriSnip.vs_colours import *

vs_name_suffix = sys.argv[1].removesuffix(".vs")
vs_logic_name = f"FSM_{vs_name_suffix}.vs"
vs_signals_name = f"FSM_{vs_name_suffix}_signals.vs"


class Transition:
    def __init__(self, src, dst, condition=None):
        self.src = src
        self.dst = dst
        self.condition = condition.strip() if condition and condition.strip() else None

    @property
    def cond_signal(self):
        if self.condition is None:
            return None
        return f"{vs_name_suffix}_{self.src}_{self.dst}"


class FSM:
    def __init__(
        self, name, states, transitions, reset, clock, async_reset, active_low
    ):
        self.name = name
        self.states = states
        self.transitions = transitions
        self.reset = reset
        self.clock = clock
        self.async_reset = async_reset
        self.active_low = active_low
        self.width = max(1, (len(states) - 1).bit_length())
        self.enum_t = f"{name.lower()}_state_t"
        self.state = f"{name}_state"
        self.state_n = f"{name}_state_n"
        self.reset_state = f"{name}_{states[0]}"

    def transitions_from(self, state):
        return [t for t in self.transitions if t.src == state]

    def conditional_transitions(self):
        return [t for t in self.transitions if t.condition is not None]

    def check_health(self):
        # 1. Unreachable states
        reachable = {self.states[0]}
        queue = [self.states[0]]
        while queue:
            curr = queue.pop(0)
            for t in self.transitions_from(curr):
                if t.dst not in reachable:
                    reachable.add(t.dst)
                    queue.append(t.dst)

        unreachable = set[Any](self.states) - reachable
        if unreachable:
            vs_print(
                ERROR,
                f"FSM {self.name} has unreachable state(s): {', '.join(unreachable)}.",
            )
            exit(1)

        for state in self.states:
            arcs = self.transitions_from(state)

            # 2. Multiple unconditional transitions
            unconditional = [t for t in arcs if t.condition is None]
            if len(unconditional) > 1:
                vs_print(
                    ERROR, f"State {state} has multiple unconditional transitions."
                )
                exit(1)

            # 3. Dead-end state warning
            outgoing = [t for t in arcs if t.dst != state]
            if not outgoing:
                vs_print(
                    WARNING, f"State {state} is a dead-end (can enter but never exit, unless the FSM is reset)."
                )


def gray_code(n):
    return n ^ (n >> 1)


def format_gray(index, width):
    return f"{width}'b{gray_code(index):0{width}b}"


def write_vs(string, file_name):
    with open(file_name, "w") as file:
        file.write(string)


def parse_header(line):
    """Parse 'asynchronous reset = ..., clock = ...' (or defaults)."""
    async_reset = True
    active_low = False
    reset = "arst_i"
    clock = "clk_i"

    if not line or "->" in line:
        return reset, clock, async_reset, active_low, False

    lower = line.lower()
    if "reset" not in lower and "clock" not in lower and "clk" not in lower:
        return reset, clock, async_reset, active_low, False

    # Split on commas that separate key=value pairs (not inside parentheses).
    parts = re.split(r",(?![^(]*\))", line)
    for part in parts:
        part = part.strip()
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        if "reset" in key:
            async_reset = "asynchronous" in key

            # Check for active-low or active-high
            if "(active-low)" in value.lower():
                active_low = True
                value = re.sub(r"(?i)\(active-low\)", "", value).strip()
            elif "(active-high)" in value.lower():
                active_low = False
                value = re.sub(r"(?i)\(active-high\)", "", value).strip()

            reset = value
        elif key in ("clock", "clk"):
            clock = value

    return reset, clock, async_reset, active_low, True


def parse_transition_line(line, current_state):
    """Parse 'State -> Next, cond' or '-> Next[, cond]'."""
    match = re.match(
        r"^(?:(\w+)\s*)?->\s*(\w+)\s*(?:[,:]\s*(.*))?$",
        line.strip(),
    )
    if not match:
        return None, current_state

    src = match.group(1)
    dst = match.group(2)
    condition = match.group(3)

    if src:
        current_state = src
    elif current_state is None:
        vs_print(ERROR, f"Transition '{line}' has no source state.")
        exit(1)

    return Transition(current_state, dst, condition), current_state


def parse_arguments():
    if len(sys.argv) < 3:
        vs_print(ERROR, "Not enough arguments for FSM generator.")
        exit(1)

    comment = sys.argv[2].replace("/*", "").replace("*/", "").strip()
    lines = [ln.strip() for ln in comment.split("\n") if ln.strip()]

    reset, clock, async_reset, active_low = "arst_i", "clk_i", True, False
    start = 0
    if lines:
        reset, clock, async_reset, active_low, is_header = parse_header(lines[0])
        if is_header:
            start = 1

    states = []
    transitions = []
    current_state = None

    for line in lines[start:]:
        transition, current_state = parse_transition_line(line, current_state)
        if transition is None:
            vs_print(ERROR, f"Malformed FSM transition: '{line}'")
            exit(1)
        for state in (transition.src, transition.dst):
            if state not in states:
                states.append(state)
        transitions.append(transition)

    if not states:
        vs_print(ERROR, f"No states found for FSM {vs_name_suffix}.")
        exit(1)

    return FSM(
        vs_name_suffix, states, transitions, reset, clock, async_reset, active_low
    )


def generate_signals(fsm):
    code = f"  // Automatically generated signals for {fsm.name} FSM\n"
    code += f"  typedef enum logic [{fsm.width - 1}:0] {{\n"
    enum_lines = []
    for i, state in enumerate[Any](fsm.states):
        enum_lines.append(f"    {fsm.name}_{state} = {format_gray(i, fsm.width)}")
    code += ",\n".join(enum_lines) + "\n"
    code += f"  }} {fsm.enum_t};\n"
    code += f"  {fsm.enum_t} {fsm.state}, {fsm.state_n};\n"

    conds = fsm.conditional_transitions()
    if conds:
        names = ", ".join(t.cond_signal for t in conds)
        code += f"  logic {names};\n"

    write_vs(code, vs_signals_name)


def generate_logic(fsm):
    code = f"  // Automatically generated logic for {fsm.name} FSM\n"

    for t in fsm.conditional_transitions():
        code += f"  assign {t.cond_signal} = {t.condition};\n"

    if fsm.conditional_transitions():
        code += "\n"

    code += "  always_comb begin\n"
    code += f"    {fsm.state_n} = {fsm.state};\n"
    code += f"    case ({fsm.state})\n"

    for state in fsm.states:
        arcs = fsm.transitions_from(state)
        code += f"      {fsm.name}_{state}: begin\n"
        if not arcs:
            code += "      end\n"
            continue

        conditional = [t for t in arcs if t.condition is not None]
        unconditional = [t for t in arcs if t.condition is None]

        for i, t in enumerate[Any](conditional):
            keyword = "if" if i == 0 else "end else if"
            code += f"        {keyword} ({t.cond_signal}) begin\n"
            code += f"          {fsm.state_n} = {fsm.name}_{t.dst};\n"

        if unconditional:
            t = unconditional[0]
            if conditional:
                code += "        end else begin\n"
                code += f"          {fsm.state_n} = {fsm.name}_{t.dst};\n"
                code += "        end\n"
            else:
                code += f"        {fsm.state_n} = {fsm.name}_{t.dst};\n"
        elif conditional:
            code += "        end\n"

        code += "      end\n"

    code += f"      default: {fsm.state_n} = {fsm.reset_state};\n"
    code += "    endcase\n"
    code += "  end\n\n"

    if fsm.async_reset:
        if fsm.active_low:
            code += f"  always_ff @(posedge {fsm.clock} or negedge {fsm.reset}) begin\n"
        else:
            code += f"  always_ff @(posedge {fsm.clock} or posedge {fsm.reset}) begin\n"
    else:
        code += f"  always_ff @(posedge {fsm.clock}) begin\n"

    reset_cond = f"!{fsm.reset}" if fsm.active_low else f"{fsm.reset}"
    code += f"    if ({reset_cond}) begin\n"
    code += f"      {fsm.state} <= {fsm.reset_state};\n"
    code += "    end else begin\n"
    code += f"      {fsm.state} <= {fsm.state_n};\n"
    code += "    end\n"
    code += "  end\n"

    write_vs(code, vs_logic_name)


if __name__ == "__main__":
    fsm = parse_arguments()
    fsm.check_health()
    generate_signals(fsm)
    generate_logic(fsm)
    rst_kind = "asynchronous" if fsm.async_reset else "synchronous"
    vs_print(
        OK,
        f"Generated FSM {fsm.name} ({len(fsm.states)} states, {rst_kind} reset={fsm.reset}, clock={fsm.clock}).",
    )
