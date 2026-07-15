`timescale 1ns / 1ps

// ============================================================================
// Testbench for Reg (Register).
// ============================================================================

module Reg_tb ();

  localparam integer DataWidth = 8;

  // Clock and reset
  reg                     clk = 1'b0;
  reg                     arst = 1'b1;

  // Inline register controls
  reg                     data_e;
  reg                     data_r;
  reg     [DataWidth-1:0] data_n;
  wire    [DataWidth-1:0] data_q;

  // List register controls
  reg                     count_en;
  reg                     count_r;
  reg     [          7:0] count_n;
  wire    [          7:0] count_q;
  reg                     valid_r;
  reg                     valid_n;
  wire                    valid_q;
  wire                    free_q;

  integer                 checks = 0;
  integer                 errors = 0;

  always #5 clk = ~clk;

  Reg #(
      .DATA_W (DataWidth),
      .RST_VAL(8'h00)
  ) DUT (
      .clk_i   (clk),
      .cke_i   (1'b1),
      .arst_i  (arst),
      .data_e  (data_e),
      .data_r  (data_r),
      .data_n  (data_n),
      .data_q  (data_q),
      .count_en(count_en),
      .count_r (count_r),
      .count_n (count_n),
      .count_q (count_q),
      .valid_r (valid_r),
      .valid_n (valid_n),
      .valid_q (valid_q),
      .free_q  (free_q)
  );

  // --------------------------------------------------------------------------
  // Helpers
  // --------------------------------------------------------------------------
  task automatic expect_eq(input [255:0] name, input [63:0] got, input [63:0] exp);
    begin
      checks = checks + 1;
      if (got !== exp) begin
        errors = errors + 1;
        $display("[%0t] FAIL %0s: expected 0x%0h, got 0x%0h", $time, name, exp, got);
      end else begin
        $display("[%0t] PASS %0s: 0x%0h", $time, name, got);
      end
    end
  endtask

  // --------------------------------------------------------------------------
  // Reset
  // --------------------------------------------------------------------------
  task automatic do_reset;
    begin
      arst    = 1'b1;
      data_e  = 1'b0;
      data_r  = 1'b0;
      data_n   = {DataWidth{1'b0}};
      count_en = 1'b0;
      count_r  = 1'b0;
      count_n  = 8'h00;
      valid_r  = 1'b0;
      valid_n  = 1'b0;
      repeat (2) @(negedge clk);
      @(negedge clk);
      arst = 1'b0;
      repeat (2) @(negedge clk);
      @(negedge clk);
    end
  endtask

  // --------------------------------------------------------------------------
  // Main stimulus
  // --------------------------------------------------------------------------
  initial begin
    $display("==================================================");
    $display(" Reg testbench");
    $display("==================================================");

    do_reset;

    // ---- Test 1: data_q after reset ---------------------------------------
    @(negedge clk);
    expect_eq("data_q after reset", data_q, 8'h00);

    // ---- Test 2: data_e=0 holds value ---------------------------------------
    @(negedge clk);
    data_n = 8'hFF;
    @(negedge clk);
    expect_eq("data_q hold when disabled", data_q, 8'h00);

    // ---- Test 3: data_e=1 updates value -----------------------------------
    @(negedge clk);
    data_e = 1'b1;
    data_n = 8'hA5;
    @(negedge clk);
    expect_eq("data_q update when enabled", data_q, 8'hA5);

    // ---- Test 4: data_r resets while enabled ------------------------------
    @(negedge clk);
    data_r = 1'b1;
    @(negedge clk);
    data_r = 1'b0;
    expect_eq("data_q sync reset", data_q, 8'h00);

    // ---- Test 5: count_q enable gating ------------------------------------
    @(negedge clk);
    data_e   = 1'b0;
    count_n  = 8'h03;
    count_en = 1'b0;
    @(negedge clk);
    expect_eq("count_q hold when disabled", count_q, 8'h00);

    @(negedge clk);
    count_en = 1'b1;
    @(negedge clk);
    expect_eq("count_q update when enabled", count_q, 8'h03);

    // ---- Test 6: count_r resets -------------------------------------------
    @(negedge clk);
    count_r = 1'b1;
    @(negedge clk);
    count_r = 1'b0;
    expect_eq("count_q sync reset", count_q, 8'h00);

    // ---- Test 7: valid_q updates without enable ---------------------------
    @(negedge clk);
    valid_n = 1'b1;
    @(negedge clk);
    expect_eq("valid_q update without enable", valid_q, 1'b1);

    // ---- Test 8: free_q toggles -------------------------------------------
    begin : free_toggle_check
      reg prev_free_q;
      integer i;
      @(negedge clk);
      prev_free_q = free_q;
      for (i = 0; i < 4; i = i + 1) begin
        @(negedge clk);
        if (free_q === prev_free_q) begin
          errors = errors + 1;
          checks = checks + 1;
          $display("[%0t] FAIL free_q toggle: value did not change at cycle %0d", $time, i);
        end else begin
          checks = checks + 1;
          $display("[%0t] PASS free_q toggle: %0b -> %0b", $time, prev_free_q, free_q);
        end
        prev_free_q = free_q;
      end
    end

    // ---- Summary ----------------------------------------------------------
    repeat (2) @(negedge clk);
    $display("\n==================================================");
    $display(" Checks run : %0d", checks);
    $display(" Errors     : %0d", errors);
    if (errors == 0) $display(" RESULT     : PASS");
    else $display(" RESULT     : FAIL");
    $display("==================================================");
    $finish;
  end

  // Watchdog to avoid a hung simulation.
  initial begin
    #50000;
    $display("[%0t] TIMEOUT: simulation did not finish in time", $time);
    $finish;
  end

  // Dump waves
  initial begin
    $dumpfile("Reg_tb.vcd");
    $dumpvars(0, Reg_tb);
  end

endmodule
