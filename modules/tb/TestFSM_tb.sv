`timescale 1ns / 1ps

// Self-checking testbench for ArbiterSM / FSM.py generation.
module TestFSM_tb ();

  logic       clk = 0;
  logic       arst = 0;
  logic       condition_1;
  logic       condition_2;
  logic       condition_3;
  logic       condition_4;
  logic       condition_5;
  logic [3:0] output_signal;

  integer errors = 0;
  integer checks = 0;

  always #5 clk = ~clk;

  TestFSM dut (
      .clk_i(clk),
      .arst_i(arst),
      .condition_1_i(condition_1),
      .condition_2_i(condition_2),
      .condition_3_i(condition_3),
      .condition_4_i(condition_4),
      .condition_5_i(condition_5),
      .output_signal_o(output_signal)
  );

  // Mirror of generated condition assigns (kept in sync with FSM_TestFSM.vs).
  logic Idle_GrantA;
  logic Idle_GrantB;
  logic GrantA_GrantB;
  logic GrantB_GrantA;
  assign Idle_GrantA  = condition_1;
  assign Idle_GrantB  = condition_2 & condition_3;
  assign GrantA_GrantB = condition_4 | condition_5;
  assign GrantB_GrantA = condition_1 | condition_2;

  task automatic check(input string label, input logic cond);
    begin
      checks = checks + 1;
      if (!cond) begin
        errors = errors + 1;
        $display("ERROR [%0t] %s (state=%0d out=%0d out_n=%0d)", $time, label,
                 dut.TestFSM_state, output_signal, dut.output_signal_n);
      end
    end
  endtask

  initial begin
    condition_1 = 1'b0;
    condition_2 = 1'b0;
    condition_3 = 1'b0;
    condition_4 = 1'b0;
    condition_5 = 1'b0;

    @(negedge clk);
    arst = 1'b1;
    repeat (3) @(negedge clk);

    // After reset: Idle, Moore output 1
    check("reset state Idle", dut.TestFSM_state === dut.TestFSM_Idle);
    check("reset output == 1", output_signal === 4'd1);

    // Idle -> GrantA (Mealy 4)
    condition_1 = 1'b1;
    #1;
    check("Idle->GrantA cond", Idle_GrantA === 1'b1);
    check("DUT cond Idle->GrantA", dut.TestFSM_Idle_GrantA === Idle_GrantA);
    check("combo Mealy out 4", dut.output_signal_n === 4'd4);
    check("combo next GrantA", dut.TestFSM_state_n === dut.TestFSM_GrantA);
    @(negedge clk);
    condition_1 = 1'b0;
    #1;
    check("entered GrantA", dut.TestFSM_state === dut.TestFSM_GrantA);
    check("registered Mealy 4", output_signal === 4'd4);

    // GrantA else -> Idle (Mealy 7)
    check("GrantA->Idle else", GrantA_GrantB === 1'b0);
    check("combo Mealy out 7", dut.output_signal_n === 4'd7);
    check("combo next Idle", dut.TestFSM_state_n === dut.TestFSM_Idle);
    @(negedge clk);
    check("back in Idle", dut.TestFSM_state === dut.TestFSM_Idle);
    check("registered Mealy 7", output_signal === 4'd7);

    @(negedge clk);
    check("Idle Moore output 1", output_signal === 4'd1);

    // Idle -> GrantB (Mealy 5)
    condition_2 = 1'b1;
    condition_3 = 1'b1;
    #1;
    check("Idle->GrantB cond", Idle_GrantB === 1'b1);
    check("DUT cond Idle->GrantB", dut.TestFSM_Idle_GrantB === Idle_GrantB);
    check("combo Mealy out 5", dut.output_signal_n === 4'd5);
    @(negedge clk);
    condition_2 = 1'b0;
    condition_3 = 1'b0;
    #1;
    check("entered GrantB", dut.TestFSM_state === dut.TestFSM_GrantB);
    check("registered Mealy 5", output_signal === 4'd5);

    // GrantB -> GrantA (Mealy 8)
    condition_1 = 1'b1;
    #1;
    check("GrantB->GrantA cond", GrantB_GrantA === 1'b1);
    check("DUT cond GrantB->GrantA", dut.TestFSM_GrantB_GrantA === GrantB_GrantA);
    check("combo Mealy out 8", dut.output_signal_n === 4'd8);
    @(negedge clk);
    check("entered GrantA from B", dut.TestFSM_state === dut.TestFSM_GrantA);
    check("registered Mealy 8", output_signal === 4'd8);

    // GrantA -> GrantB (Mealy 6)
    condition_1 = 1'b0;
    condition_4 = 1'b1;
    #1;
    check("GrantA->GrantB cond", GrantA_GrantB === 1'b1);
    check("DUT cond GrantA->GrantB", dut.TestFSM_GrantA_GrantB === GrantA_GrantB);
    check("combo Mealy out 6", dut.output_signal_n === 4'd6);
    @(negedge clk);
    check("entered GrantB from A", dut.TestFSM_state === dut.TestFSM_GrantB);
    check("registered Mealy 6", output_signal === 4'd6);

    // GrantB else -> Idle (Mealy 9)
    condition_4 = 1'b0;
    #1;
    check("GrantB->Idle else", GrantB_GrantA === 1'b0);
    check("combo Mealy out 9", dut.output_signal_n === 4'd9);
    @(negedge clk);
    check("Idle after GrantB", dut.TestFSM_state === dut.TestFSM_Idle);
    check("registered Mealy 9", output_signal === 4'd9);

    // Priority: A over B from Idle
    @(negedge clk);
    condition_1 = 1'b1;
    condition_2 = 1'b1;
    condition_3 = 1'b1;
    #1;
    check("A wins over B", dut.TestFSM_state_n === dut.TestFSM_GrantA);
    check("priority Mealy 4", dut.output_signal_n === 4'd4);
    @(negedge clk);
    check("priority entered GrantA", dut.TestFSM_state === dut.TestFSM_GrantA);

    if (errors == 0) begin
      $display("\033[32m[PASS] TestFSM / FSM.py (%0d checks)\033[0m", checks);
    end else begin
      $display("\033[31m[FAIL] TestFSM / FSM.py: %0d/%0d checks failed\033[0m", errors,
               checks);
    end
    $finish;
  end

  initial begin
    $dumpfile("TestFSM_tb.vcd");
    $dumpvars(0, TestFSM_tb);
  end

endmodule
