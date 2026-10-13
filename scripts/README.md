# Scripts
Generator scripts for VeriSnip. Each script is called through a `` `include "<script>_<name>.vs" `` line in a Verilog file and writes the matching `.vs` snippet. The full syntax and defaults are in the comment at the top of each script.

Two conventions are shared by the register scripts (`reg.py`, `unpacked_reg.py`, `MMIO.py`) and `FSM.py`:
- A list is written inside `/* ... */`. An optional first line right after `/*` sets the clock and reset (`reset = <rst>, clock = <clk>`).
- Resets in the register scripts are synchronous and active-high only.

| Script | Generates |
|---|---|
| [AXI.py](AXI.py) | AXI5 parameters, IOs, signals and logic (`AXI_{ios,signals,logic}[_name].vs`) |
| [counter.py](counter.py) | Up or down counter |
| [FSM.py](FSM.py) | Finite state machine |
| [instantiate.py](instantiate.py) | Module instantiation |
| [Mem.py](Mem.py) | RAM, ROM and true dual-port memories |
| [MMIO.py](MMIO.py) | Memory mapped registers |
| [reg.py](reg.py) | Registers |
| [synchronize_reset.py](synchronize_reset.py) | Reset synchronizer |
| [unpacked_reg.py](unpacked_reg.py) | Registers for unpacked arrays |

## AXI.py
Creates the parameters, IOs, signals and logic of AXI5 buses. The `AXI-Lite` Subordinate and `AXI-Full` Manager interfaces are implemented; the other combinations print a warning. Several buses can share one interface name.

> `include "AXI_[ios,signals,logic][_{interface_name}].vs" // AXI-[Lite,Full,Stream] [Manager,Subordinate] [{bus_name}]

Dependencies: `reg.py`, `FSM.py`.

## counter.py
Creates a counter as a register plus a `{name}_next` assign.

> `include "counter_{name}.vs" // Width, Enable, Reset, Reset_value, Direction

Dependencies: `reg.py`.

## FSM.py
Creates a finite state machine from a list of transitions, with Gray or one-hot encoding and an error flag for illegal states. Signals are written to `FSM_{name}_signals.vs`.

> `include "FSM_{name}.vs" /* [asynchronous] reset = <rst>, clock = <clk>, encoding = <gray|one-hot>  
    State -> Next_state: Condition  
          -> Next_state  
    */

## instantiate.py
Instantiates a module found in the project, with optional port prefix, suffix and per-port connections.

> `include "instantiate_{module}_{instance_name}.vs" // prefix="p" suffix="s" {port}="signal"

## Mem.py
Creates a memory of type RAM, distributed RAM, BRAM, TDP BRAM, URAM or ROM, with an optional init file.

> `include "Mem_{name}.vs" // Type, Depth, Width, Init_file

## MMIO.py
Creates memory mapped registers with address decoding, read and write selects and read and write data muxes. The registers themselves are generated through `reg.py`, which receives the global clock and reset.

> `include "MMIO_{module}.vs" /* [reset = <rst>,] [clock = <clk>]  
    Name, Size, Reset_value, Reg_reset, Reg_enable, Address, Access_type, Next_value  
    */

Dependencies: `reg.py`.

## reg.py
Creates a list of registers. A register with both a global and a custom reset gets a `{Name}_int_rst` wire, the OR of the two. Inline registers (`// ...`) are not supported.

> `include "reg_{list_name}.vs" /* [reset = <rst>,] [clock = <clk>]  
    Name, Size, Reset_value, Reg_reset, Reg_enable, Reg_next  
    */

## synchronize_reset.py
Creates a reset synchronizer: asynchronous assert, synchronous de-assert. Both resets can be active-low or active-high.

> `include "synchronize_reset_{prefix}.vs" // arst_i (active-low), sync_reset (active-high), clock = clk_i

## unpacked_reg.py
Creates registers for unpacked arrays whose size depends on parameters. All arrays are updated with for loops inside a single always block instead of one block per element. Fields and header follow `reg.py`, plus the array dimensions.

> `include "unpacked_reg_{list_name}.vs" /* [reset = <rst>,] [clock = <clk>]  
    Name, Size, [DIM0][DIM1], Reset_value, Reg_reset, Reg_enable, Reg_next  
    */

Dependencies: `reg.py`.
