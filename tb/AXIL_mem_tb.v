`timescale 1ns / 1ps

module AXI_Test_tb ();

  // DUT Inputs
  reg clk = 0;

  // Clock generation
  always #5 clk = ~clk;

  initial begin
    $finish;
  end

  // Dump waves
  initial begin
    $dumpfile("bitSerialNNAcel_tb.vcd");
    $dumpvars(0, bitSerialNNAcel_tb);
  end

endmodule
