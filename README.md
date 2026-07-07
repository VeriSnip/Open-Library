# Open-Library

This repository contains a collection of reusable hardware modules. It is designed to be seamlessly integrated with the **VeriSnip** tool and the **Util-Tool** repository to streamline hardware development, testing, and building processes.

## Integration with VeriSnip and Util-Tool

The `Open-Library` provides the foundational Verilog/SystemVerilog source files. By combining this library with the `Util-Tool` repository (which provides the Nix environment and build scripts) and the VeriSnip tool, you can easily manage, compile, and synthesize these hardware modules.

The Nix shell environment provided by `Util-Tool` ensures that all necessary dependencies and tools (like VeriSnip) are available, allowing for reproducible builds.

## Example: Building `AXIL_mem`

You can build modules directly using the `vs_build` command provided by VeriSnip within the Nix shell. 

For example, to clean and build the `AXIL_mem` module, run the following command from the root of your project:

```bash
nix-shell --run "vs_build --clean AXIL_mem"
```

This command will:
1. Enter the Nix shell environment configured by `Util-Tool`.
2. Execute `vs_build` to clean any previous build artifacts for `AXIL_mem`.
3. Build the `AXIL_mem` module using the sources provided in this library.

## Acknowledgements

We would like to give special credit to **Alex Forencich** for the `axi_ram.v` module used in this library. The original source code can be found at:
[https://github.com/alexforencich/verilog-axi/blob/master/rtl/axi_ram.v](https://github.com/alexforencich/verilog-axi/blob/master/rtl/axi_ram.v)
