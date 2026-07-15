`timescale 1ns / 1ps

module FIFO_tb;

  // Parameters for the FIFO instance
  parameter int WIDTH = 8;
  parameter int DEPTH = 16;  // Test with DEPTH = 1 and DEPTH = 16 to verify both branches

  // Testbench signals
  reg              clk;
  reg              rst;
  reg              wr_en;
  reg  [WIDTH-1:0] wr_data;
  reg              rd_en;
  wire [WIDTH-1:0] rd_data;
  wire             empty;
  wire             full;

  // Instantiate the FIFO module
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

  // Clock generation
  always begin
    #5 clk = ~clk;  // Clock period of 10ns (100 MHz)
  end

  // Test sequence
  initial begin
    // Initialize signals
    clk     = 1'b0;
    rst     = 1'b1;
    wr_en   = 1'b0;
    wr_data = '0;
    rd_en   = 1'b0;

    $display("--------------------------------------------------");
    $display("Starting FIFO Testbench (WIDTH=%0d, DEPTH=%0d)", WIDTH, DEPTH);
    $display("--------------------------------------------------");

    // Apply reset
    #10 rst = 1'b0;
    $display("Reset released.");

    // --- Test 1: Write some data ---
    $display("\n--- Test 1: Writing data ---");
    repeat (DEPTH / 2) begin : write_half_fifo
      @(posedge clk) #1;
      wr_en   = 1'b1;
      wr_data = $urandom_range(0, (1 << WIDTH) - 1);  // Random data
      $display("Time: %0t | Writing data: 0x%h, wr_en: %b, empty: %b, full: %b", $time, wr_data,
               wr_en, empty, full);
    end
    @(posedge clk) #1;
    wr_en = 1'b0;  // Stop writing
    $display("Time: %0t | Stopped writing. empty: %b, full: %b", $time, empty, full);

    // --- Test 2: Read some data ---
    $display("\n--- Test 2: Reading data ---");
    repeat (DEPTH / 4) begin : read_quarter_fifo
      @(posedge clk) #1;
      rd_en = 1'b1;
      $display("Time: %0t | Reading data: 0x%h, rd_en: %b, empty: %b, full: %b", $time, rd_data,
               rd_en, empty, full);
    end
    @(posedge clk) #1;
    rd_en = 1'b0;  // Stop reading
    $display("Time: %0t | Stopped reading. empty: %b, full: %b", $time, empty, full);

    // --- Test 3: Fill the FIFO ---
    $display("\n--- Test 3: Filling the FIFO ---");
    while (!full) begin
      @(posedge clk) #1;
      wr_en   = 1'b1;
      wr_data = $urandom_range(0, (1 << WIDTH) - 1);
      $display("Time: %0t | Writing data: 0x%h, empty: %b, full: %b", $time, wr_data, empty, full);
    end
    @(posedge clk) #1;
    wr_en = 1'b0;
    $display("Time: %0t | FIFO is full. empty: %b, full: %b", $time, empty, full);

    // --- Test 4: Attempt to write when full ---
    $display("\n--- Test 4: Attempting to write when full (should not write) ---");
    @(posedge clk) #1;
    wr_en   = 1'b1;
    wr_data = 'hAA;  // Distinct data
    $display("Time: %0t | Attempting to write 0x%h. empty: %b, full: %b", $time, wr_data, empty,
             full);
    @(posedge clk) #1;
    wr_en = 1'b0;
    $display("Time: %0t | Write attempt finished. empty: %b, full: %b", $time, empty, full);

    // --- Test 5: Read and write when full ---
    $display("\n--- Test 5: Attempting to read and write when full (should read/write) ---");
    @(posedge clk) #1;
    wr_en   = 1'b1;
    rd_en   = 1'b1;
    wr_data = 'hFF;  // Distinct data
    $display("Time: %0t | Reading data: 0x%h, wrote data: 0x%h, empty: %b, full: %b", $time,
             rd_data, wr_data, empty, full);
    @(posedge clk) #1;
    wr_en = 1'b0;
    rd_en = 1'b0;
    $display("Time: %0t | Read/Write attempt finished. empty: %b, full: %b", $time, empty, full);

    // --- Test 6: Empty the FIFO ---
    $display("\n--- Test 6: Emptying the FIFO ---");
    while (!empty) begin
      @(posedge clk) #1;
      rd_en = 1'b1;
      $display("Time: %0t | Reading data: 0x%h, empty: %b, full: %b", $time, rd_data, empty, full);
    end
    @(posedge clk) #1;
    rd_en = 1'b0;
    $display("Time: %0t | FIFO is empty. empty: %b, full: %b", $time, empty, full);

    // --- Test 7: Tunneling (write and read simultaneously when empty) ---
    $display("\n--- Test 7: Testing Tunneling (simultaneous write/read when empty) ---");
    @(posedge clk) #1;
    wr_en   = 1'b1;
    rd_en   = 1'b1;
    wr_data = 'h55;  // Distinct data for tunneling
    #1
    $display(
        "Time: %0t | Tunneling: Writing 0x%h, Reading 0x%h. empty: %b, full: %b",
        $time,
        wr_data,
        rd_data,
        empty,
        full
    );
    @(posedge clk) #1;
    wr_en = 1'b0;
    rd_en = 1'b0;
    $display("Time: %0t | Tunneling finished. empty: %b, full: %b", $time, empty, full);

    // --- Test 8: Write and Read (normal operation) ---
    $display("\n--- Test 8: Normal write and read operations ---");
    @(posedge clk) #1;
    wr_en   = 1'b1;
    wr_data = 'h01;
    $display("Time: %0t | W: 0x%h, empty: %b, full: %b", $time, wr_data, empty, full);
    @(posedge clk) #1;
    wr_en   = 1'b1;
    wr_data = 'h02;
    rd_en   = 1'b1;
    $display("Time: %0t | W: 0x%h, R: 0x%h, empty: %b, full: %b", $time, wr_data, rd_data, empty,
             full);
    @(posedge clk) #1;
    wr_en   = 1'b1;
    wr_data = 'h03;
    $display("Time: %0t | W: 0x%h, R: 0x%h, empty: %b, full: %b", $time, wr_data, rd_data, empty,
             full);
    @(posedge clk) #1;
    rd_en = 1'b1;
    $display("Time: %0t | R: 0x%h, empty: %b, full: %b", $time, rd_data, empty, full);
    @(posedge clk) #1;
    wr_en = 1'b0;
    rd_en = 1'b0;
    $display("Time: %0t | empty: %b, full: %b", $time, empty, full);

    // Final checks
    @(posedge clk) #1;
    $display("\n--- Test Complete ---");
    $display("Final empty: %b, full: %b", empty, full);

    #50 $finish;  // End simulation
  end

  // VCD dump for waveform viewing
  initial begin
    $dumpfile("FIFO_tb.vcd");
    $dumpvars(0, FIFO_tb);
  end

endmodule
