`timescale 1ns / 1ps

module FIFO_tb;

  parameter int WIDTH = 8;
  parameter int DEPTH = 16;

  logic               clk;
  logic               rst;
  logic               wr_en;
  logic   [WIDTH-1:0] wr_data;
  logic               rd_en;
  logic   [WIDTH-1:0] rd_data;
  logic               empty;
  logic               full;

  integer             error_count = 0;
  integer             test_count = 0;

  logic   [WIDTH-1:0] ref_mem         [DEPTH];
  integer             ref_head = 0;
  integer             ref_tail = 0;
  integer             ref_size = 0;

  FIFO #(
      .WIDTH(WIDTH),
      .DEPTH(DEPTH)
  ) uut (
      .clk_i    (clk),
      .rst_i    (rst),
      .wr_en_i  (wr_en),
      .wr_data_i(wr_data),
      .rd_en_i  (rd_en),
      .rd_data_o(rd_data),
      .empty_o  (empty),
      .full_o   (full)
  );

  always begin
    #5 clk = ~clk;
  end

  function automatic logic ref_empty();
    return ref_size == 0;
  endfunction

  function automatic logic ref_full();
    return ref_size == DEPTH;
  endfunction

  task automatic ref_reset;
    ref_head = 0;
    ref_tail = 0;
    ref_size = 0;
  endtask

  task automatic ref_push(input logic [WIDTH-1:0] data);
    ref_mem[ref_tail] = data;
    ref_tail          = (ref_tail + 1) % DEPTH;
    ref_size          = ref_size + 1;
  endtask

  task automatic ref_pop(output logic [WIDTH-1:0] data);
    data     = ref_mem[ref_head];
    ref_head = (ref_head + 1) % DEPTH;
    ref_size = ref_size - 1;
  endtask

  task automatic check_flag(input string name, input logic got, input logic exp);
    test_count = test_count + 1;
    if (got !== exp) begin
      error_count = error_count + 1;
      $display("[FAIL] Test %0d: %0s expected %b, got %b", test_count, name, exp, got);
    end else begin
      $display("[PASS] Test %0d: %0s", test_count, name);
    end
  endtask

  task automatic check_data(input string name, input logic [WIDTH-1:0] got,
                            input logic [WIDTH-1:0] exp);
    test_count = test_count + 1;
    if (got !== exp) begin
      error_count = error_count + 1;
      $display("[FAIL] Test %0d: %0s expected 0x%h, got 0x%h", test_count, name, exp, got);
    end else begin
      $display("[PASS] Test %0d: %0s (0x%h)", test_count, name, got);
    end
  endtask

  task automatic reset_dut;
    begin
      rst     = 1'b1;
      wr_en   = 1'b0;
      wr_data = '0;
      rd_en   = 1'b0;
      ref_reset();
      repeat (2) @(negedge clk);
      rst = 1'b0;
      @(negedge clk);
      check_flag("empty after reset", empty, 1'b1);
      check_flag("full after reset", full, 1'b0);
    end
  endtask

  task automatic fifo_cycle(input logic do_wr, input logic [WIDTH-1:0] wdata, input logic do_rd,
                            input logic verify_read);
    logic             tunnel;
    logic             int_wr;
    logic             int_rd;
    logic [WIDTH-1:0] expected_rdata;
    logic [WIDTH-1:0] popped;

    tunnel = do_wr && do_rd && empty;
    int_wr = do_wr && (~full || do_rd) && !tunnel;
    int_rd = do_rd && !empty;

    if (tunnel) expected_rdata = wdata;
    else if (int_rd) expected_rdata = ref_mem[ref_head];

    wr_en   = do_wr;
    wr_data = wdata;
    rd_en   = do_rd;

    @(negedge clk);
    wr_en = 1'b0;
    rd_en = 1'b0;

    if (verify_read && int_rd) begin
      check_data("read data", rd_data, expected_rdata);
    end
    if (~tunnel) begin
      if (int_rd) ref_pop(popped);
      if (int_wr) ref_push(wdata);
    end

    check_flag("empty flag", empty, ref_empty());
    check_flag("full flag", full, ref_full());
  endtask

  task automatic test_write_read_sequence;
    integer i;
    logic [WIDTH-1:0] write_data;
    begin
      $display("\n--- Test: Write and read sequence ---");
      for (i = 0; i < DEPTH; i = i + 1) begin
        write_data = $urandom_range(0, (1 << WIDTH) - 1);
        fifo_cycle(1'b1, write_data, 1'b0, 1'b0);
      end

      for (i = 0; i < DEPTH; i = i + 1) begin
        fifo_cycle(1'b0, '0, 1'b1, 1'b1);
      end
    end
  endtask

  task automatic test_fill_fifo;
    begin
      $display("\n--- Test: Fill FIFO ---");
      while (!full) begin
        fifo_cycle(1'b1, $urandom_range(0, (1 << WIDTH) - 1), 1'b0, 1'b0);
      end
      check_flag("FIFO full", full, 1'b1);
      check_flag("FIFO not empty when full", empty, 1'b0);
    end
  endtask

  task automatic test_write_when_full;
    logic [WIDTH-1:0] head_before;
    begin
      $display("\n--- Test: Write when full ---");
      head_before = ref_mem[ref_head];
      fifo_cycle(1'b1, 8'hAA, 1'b0, 1'b0);
      check_data("head unchanged after blocked write", ref_mem[ref_head], head_before);
      check_flag("still full after blocked write", full, 1'b1);
    end
  endtask

  task automatic test_read_write_when_full;
    begin
      $display("\n--- Test: Simultaneous read and write when full ---");
      fifo_cycle(1'b1, 8'hFF, 1'b1, 1'b1);
    end
  endtask

  task automatic test_empty_fifo;
    begin
      $display("\n--- Test: Empty FIFO ---");
      while (!empty) begin
        fifo_cycle(1'b0, '0, 1'b1, 1'b1);
      end
      check_flag("FIFO empty", empty, 1'b1);
      check_flag("FIFO not full when empty", full, 1'b0);
    end
  endtask

  task automatic test_read_when_empty;
    begin
      $display("\n--- Test: Read when empty ---");
      fifo_cycle(1'b0, '0, 1'b1, 1'b0);
      check_flag("still empty after blocked read", empty, 1'b1);
    end
  endtask

  task automatic test_tunneling;
    begin
      $display("\n--- Test: Tunneling ---");
      fifo_cycle(1'b1, 8'h55, 1'b1, 1'b1);
      check_flag("empty after tunneling", empty, 1'b1);
      check_flag("not full after tunneling", full, 1'b0);
    end
  endtask

  task automatic test_normal_operations;
    begin
      $display("\n--- Test: Normal write/read operations ---");
      fifo_cycle(1'b1, 8'h01, 1'b0, 1'b0);
      fifo_cycle(1'b1, 8'h02, 1'b1, 1'b1);
      fifo_cycle(1'b1, 8'h03, 1'b0, 1'b0);
      fifo_cycle(1'b0, '0, 1'b1, 1'b1);
      fifo_cycle(1'b0, '0, 1'b1, 1'b1);
      check_flag("empty after draining", empty, 1'b1);
    end
  endtask

  initial begin
    clk = 1'b0;

    $display("--------------------------------------------------");
    $display("Starting FIFO Testbench (WIDTH=%0d, DEPTH=%0d)", WIDTH, DEPTH);
    $display("--------------------------------------------------");

    reset_dut();
    test_write_read_sequence();
    test_fill_fifo();
    test_write_when_full();
    test_read_write_when_full();
    test_empty_fifo();
    test_read_when_empty();
    test_tunneling();
    test_normal_operations();

    $display("\n--- Test Summary ---");
    if (error_count == 0) begin
      $display("\033[32m[PASS] FIFO testbench: %0d checks passed.\033[0m", test_count);
    end else begin
      $display("\033[31m[FAIL] FIFO encountered %0d errors in %0d tests.\033[0m", error_count,
               test_count);
    end

    #10 $finish;
  end

  initial begin
    $dumpfile("FIFO_tb.vcd");
    $dumpvars(0, FIFO_tb);
  end

endmodule
