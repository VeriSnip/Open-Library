`timescale 1ns / 1ps

/*
  Example DUT used to exercise Open-Library/scripts/FSM.py.
*/
module TestFSM (
    input  logic       clk_i,
    input  logic       arst_i,
    input  logic       condition_1_i,
    input  logic       condition_2_i,
    input  logic       condition_3_i,
    input  logic       condition_4_i,
    input  logic       condition_5_i,
    output logic [3:0] output_signal_o
);

  // ============================================================================
  // Signal Declarations
  // ============================================================================
  `include "FSM_TestFSM_signals.vs"  // VS_NO_GENERATE

  logic sync_reset;
  logic [3:0] output_signal, output_signal_n;

  assign output_signal_o = output_signal;

  // ============================================================================
  // Main logic
  // ============================================================================
  `include "synchronize_reset_TestFSM_1.vs"  // arst_i (active-low), sync_reset (active-high)

  `include "FSM_TestFSM.vs"  /* asynchronous reset = arst_i (active-low), clock = clk_i
    Idle   -> GrantA: condition_1_i
           -> GrantB: condition_2_i & condition_3_i
    GrantA -> GrantB: condition_4_i | condition_5_i
           -> Idle
    GrantB -> GrantA: condition_1_i | condition_2_i
           -> Idle
    */

  // Moore defaults (1/2/3) with Mealy overrides (4..9) on the same arcs as the FSM.
  always_comb begin
    output_signal_n = output_signal;
    case (TestFSM_state)
      TestFSM_Idle: begin
        output_signal_n = 4'd1;
        if (TestFSM_Idle_GrantA) begin
          output_signal_n = 4'd4;
        end else if (TestFSM_Idle_GrantB) begin
          output_signal_n = 4'd5;
        end
      end
      TestFSM_GrantA: begin
        output_signal_n = 4'd2;
        if (TestFSM_GrantA_GrantB) begin
          output_signal_n = 4'd6;
        end else begin
          output_signal_n = 4'd7;
        end
      end
      TestFSM_GrantB: begin
        output_signal_n = 4'd3;
        if (TestFSM_GrantB_GrantA) begin
          output_signal_n = 4'd8;
        end else begin
          output_signal_n = 4'd9;
        end
      end
      default: output_signal_n = 4'd0;
    endcase
  end

  `include "reg_output_signal.vs"  // 4, 0, sync_reset, , _n

endmodule
