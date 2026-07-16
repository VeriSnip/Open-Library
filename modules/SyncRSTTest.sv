`timescale 1ns / 1ps

/*
  Test module for the synchronous reset from asynchronous reset VeriSnip script.
*/
module SyncRSTTest (
    input  logic clk_i,
    input  logic arst_low_i,
    input  logic arst_high_i,
    output logic sync_low_from_low_o,
    output logic sync_high_from_low_o,
    output logic sync_low_from_high_o,
    output logic sync_high_from_high_o,
    output logic sync_default_clk_o,
    output logic sync_default_types_o
);

  // 1. arst (active-low), sync (active-low)
  `include "synchronize_reset_SyncRSTTest_0.vs" // arst_low_i (active-low), sync_low_from_low_o (active-low), clock = clk_i

  // 2. arst (active-low), sync (active-high)
  `include "synchronize_reset_SyncRSTTest_1.vs" // arst_low_i (active-low), sync_high_from_low_o (active-high), clock = clk_i

  // 3. arst (active-high), sync (active-low)
  `include "synchronize_reset_SyncRSTTest_2.vs" // arst_high_i (active-high), sync_low_from_high_o (active-low), clock = clk_i

  // 4. arst (active-high), sync (active-high)
  `include "synchronize_reset_SyncRSTTest_3.vs" // arst_high_i (active-high), sync_high_from_high_o (active-high), clock = clk_i

  // 5. default clock test
  `include "synchronize_reset_SyncRSTTest_4.vs" // arst_low_i (active-low), sync_default_clk_o (active-low)

  // 6. default types test
  `include "synchronize_reset_SyncRSTTest_5.vs" // arst_low_i, sync_default_types_o

endmodule
