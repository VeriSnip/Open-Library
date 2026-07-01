`timescale 1ns / 1ps

// ============================================================================
// Testbench for AXIL_mem (AXI-Lite subordinate memory).
// The focus of this testbench is the AXI-Lite interface: handshakes, ID
// pass-through, write strobes, ordering and valid/ready back-pressure.
// A small software reference model keeps track of the expected memory
// contents so read data can be checked against previous writes.
// ============================================================================

module AXIL_mem_tb ();

  // Local parameters
  localparam integer AXIL_ADDR_WIDTH = 32;
  localparam integer AXIL_DATA_WIDTH = 32;
  localparam integer AXIL_ID_W_WIDTH = 2;
  localparam integer AXIL_ID_R_WIDTH = 2;
  // Memory depth is 2**ADDR_WIDTH words. Kept small so the simulator does not
  // have to allocate a huge array.
  localparam integer ADDR_WIDTH = 12;
  localparam integer DATA_WIDTH = 32;
  localparam integer STRB_WIDTH = AXIL_DATA_WIDTH / 8;
  // Number of addressable words (memory index is addr[ADDR_WIDTH-1:2]).
  localparam integer WORDS = 1 << (ADDR_WIDTH - 2);

  // Clock and reset
  reg clk = 1'b0;
  reg arst = 1'b1;

  // Clock generation: 10 ns period (100 MHz)
  always #5 clk = ~clk;

  // --------------------------------------------------------------------------
  // DUT connections
  // --------------------------------------------------------------------------
  // Write address channel
  reg                           AXIL_awvalid_i;
  wire                          AXIL_awready_o;
  reg     [AXIL_ID_W_WIDTH-1:0] AXIL_awid_i;
  reg     [AXIL_ADDR_WIDTH-1:0] AXIL_awaddr_i;
  // Write data channel
  reg                           AXIL_wvalid_i;
  wire                          AXIL_wready_o;
  reg     [AXIL_DATA_WIDTH-1:0] AXIL_wdata_i;
  reg     [     STRB_WIDTH-1:0] AXIL_wstrb_i;
  // Write response channel
  wire                          AXIL_bvalid_o;
  reg                           AXIL_bready_i;
  wire    [AXIL_ID_W_WIDTH-1:0] AXIL_bid_o;
  // Read address channel
  reg                           AXIL_arvalid_i;
  wire                          AXIL_arready_o;
  reg     [AXIL_ID_R_WIDTH-1:0] AXIL_arid_i;
  reg     [AXIL_ADDR_WIDTH-1:0] AXIL_araddr_i;
  // Read data channel
  wire                          AXIL_rvalid_o;
  reg                           AXIL_rready_i;
  wire    [AXIL_ID_R_WIDTH-1:0] AXIL_rid_o;
  wire    [AXIL_DATA_WIDTH-1:0] AXIL_rdata_o;

  // --------------------------------------------------------------------------
  // Scoreboard
  // --------------------------------------------------------------------------
  integer                       errors = 0;
  integer                       checks = 0;
  reg     [     DATA_WIDTH-1:0] ref_mem        [0:WORDS-1];

  AXIL_mem #(
      .AXIL_ADDR_WIDTH(AXIL_ADDR_WIDTH),
      .AXIL_DATA_WIDTH(AXIL_DATA_WIDTH),
      .AXIL_ID_W_WIDTH(AXIL_ID_W_WIDTH),
      .AXIL_ID_R_WIDTH(AXIL_ID_R_WIDTH),
      .ADDR_WIDTH(ADDR_WIDTH),
      .DATA_WIDTH(DATA_WIDTH)
  ) DUT (
      .AXIL_awvalid_i(AXIL_awvalid_i),
      .AXIL_awready_o(AXIL_awready_o),
      .AXIL_awid_i   (AXIL_awid_i),
      .AXIL_awaddr_i (AXIL_awaddr_i),
      .AXIL_wvalid_i (AXIL_wvalid_i),
      .AXIL_wready_o (AXIL_wready_o),
      .AXIL_wdata_i  (AXIL_wdata_i),
      .AXIL_wstrb_i  (AXIL_wstrb_i),
      .AXIL_bvalid_o (AXIL_bvalid_o),
      .AXIL_bready_i (AXIL_bready_i),
      .AXIL_bid_o    (AXIL_bid_o),
      .AXIL_arvalid_i(AXIL_arvalid_i),
      .AXIL_arready_o(AXIL_arready_o),
      .AXIL_arid_i   (AXIL_arid_i),
      .AXIL_araddr_i (AXIL_araddr_i),
      .AXIL_rvalid_o (AXIL_rvalid_o),
      .AXIL_rready_i (AXIL_rready_i),
      .AXIL_rid_o    (AXIL_rid_o),
      .AXIL_rdata_o  (AXIL_rdata_o),
      // Generic IOs
      .clk_i         (clk),
      .arst_i        (arst)
  );

  // --------------------------------------------------------------------------
  // Helpers
  // --------------------------------------------------------------------------
  function integer word_index(input [AXIL_ADDR_WIDTH-1:0] addr);
    word_index = (addr >> $clog2(STRB_WIDTH)) & (WORDS - 1);
  endfunction

  task expect_eq(input [255:0] name, input [63:0] got, input [63:0] exp);
    begin
      checks = checks + 1;
      if (got !== exp) begin
        errors = errors + 1;
        $display("[%0t] FAIL %0s: expected 0x%0h, got 0x%0h", $time, name, exp, got);
      end
    end
  endtask

  // --------------------------------------------------------------------------
  // Reset
  // --------------------------------------------------------------------------
  task do_reset;
    begin
      arst           = 1'b1;
      AXIL_awvalid_i = 1'b0;
      AXIL_awid_i    = {AXIL_ID_W_WIDTH{1'b0}};
      AXIL_awaddr_i  = {AXIL_ADDR_WIDTH{1'b0}};
      AXIL_wvalid_i  = 1'b0;
      AXIL_wdata_i   = {AXIL_DATA_WIDTH{1'b0}};
      AXIL_wstrb_i   = {STRB_WIDTH{1'b0}};
      AXIL_bready_i  = 1'b1;
      AXIL_arvalid_i = 1'b0;
      AXIL_arid_i    = {AXIL_ID_R_WIDTH{1'b0}};
      AXIL_araddr_i  = {AXIL_ADDR_WIDTH{1'b0}};
      AXIL_rready_i  = 1'b1;
      repeat (4) @(posedge clk);
      @(negedge clk);
      arst = 1'b0;
      // Allow the synchronous reset to clear and the ready flags to assert.
      repeat (2) @(posedge clk);
      @(negedge clk);
    end
  endtask

  // --------------------------------------------------------------------------
  // AXI-Lite write transaction (bready is assumed to be held high).
  // Drives AW and W together, waits for both to be accepted, then checks BID.
  // --------------------------------------------------------------------------
  task axil_write(input [AXIL_ADDR_WIDTH-1:0] addr, input [AXIL_ID_W_WIDTH-1:0] id,
                  input [AXIL_DATA_WIDTH-1:0] data, input [STRB_WIDTH-1:0] strb);
    integer widx;
    integer b;
    begin
      @(negedge clk);
      AXIL_awvalid_i = 1'b1;
      AXIL_awaddr_i  = addr;
      AXIL_awid_i    = id;
      AXIL_wvalid_i  = 1'b1;
      AXIL_wdata_i   = data;
      AXIL_wstrb_i   = strb;

      // Wait until both address and data are accepted.
      @(negedge clk);
      while (!(AXIL_awvalid_i && AXIL_awready_o && AXIL_wvalid_i && AXIL_wready_o)) @(negedge clk);
      AXIL_awvalid_i = 1'b0;
      AXIL_wvalid_i  = 1'b0;

      // Wait for the write response and check the returned ID.
      while (!AXIL_bvalid_o) @(negedge clk);
      expect_eq("write BID", AXIL_bid_o, id);

      // Update the reference model (byte enables honoured).
      widx = word_index(addr);
      for (b = 0; b < STRB_WIDTH; b = b + 1) if (strb[b]) ref_mem[widx][8*b+:8] = data[8*b+:8];

      // Let the response be consumed (bready held high) so the bus is idle.
      @(negedge clk);
      while (AXIL_bvalid_o) @(negedge clk);
    end
  endtask

  // --------------------------------------------------------------------------
  // AXI-Lite read transaction (rready is assumed to be held high).
  // Checks the returned data against the reference model and the returned ID.
  // --------------------------------------------------------------------------
  task axil_read(input [AXIL_ADDR_WIDTH-1:0] addr, input [AXIL_ID_R_WIDTH-1:0] id);
    reg [DATA_WIDTH-1:0] exp;
    begin
      @(negedge clk);
      AXIL_arvalid_i = 1'b1;
      AXIL_araddr_i  = addr;
      AXIL_arid_i    = id;

      @(negedge clk);
      while (!(AXIL_arvalid_i && AXIL_arready_o)) @(negedge clk);
      AXIL_arvalid_i = 1'b0;

      while (!AXIL_rvalid_o) @(negedge clk);
      exp = ref_mem[word_index(addr)];
      expect_eq("read RDATA", AXIL_rdata_o, exp);
      expect_eq("read RID", AXIL_rid_o, id);

      // Let the data beat be consumed (rready held high) so the bus is idle.
      @(negedge clk);
      while (AXIL_rvalid_o) @(negedge clk);
    end
  endtask

  // --------------------------------------------------------------------------
  // Main stimulus
  // --------------------------------------------------------------------------
  integer i;
  reg [AXIL_ADDR_WIDTH-1:0] a;

  initial begin
    $display("==================================================");
    $display(" AXIL_mem testbench");
    $display("==================================================");

    do_reset;

    // ---- Test 0: idle interface state after reset -------------------------
    $display("\n--- Test 0: reset / idle state ---");
    expect_eq("awready idle", AXIL_awready_o, 1'b1);
    expect_eq("wready idle", AXIL_wready_o, 1'b1);
    expect_eq("arready idle", AXIL_arready_o, 1'b1);
    expect_eq("bvalid idle", AXIL_bvalid_o, 1'b0);
    expect_eq("rvalid idle", AXIL_rvalid_o, 1'b0);

    // ---- Test 1: single write followed by read-back -----------------------
    $display("\n--- Test 1: single write + read-back ---");
    axil_write(32'h0000_0000, 2'd1, 32'hDEAD_BEEF, 4'hF);
    axil_read(32'h0000_0000, 2'd1);

    // ---- Test 2: several words, then read them all back -------------------
    $display("\n--- Test 2: multiple words ---");
    for (i = 0; i < 8; i = i + 1) begin
      a = 32'h0000_0100 + (i << 2);
      axil_write(a, i[AXIL_ID_W_WIDTH-1:0], 32'h1000_0000 + (i * 32'h0101_0101), 4'hF);
    end
    for (i = 0; i < 8; i = i + 1) begin
      a = 32'h0000_0100 + (i << 2);
      axil_read(a, i[AXIL_ID_R_WIDTH-1:0]);
    end

    // ---- Test 3: byte write strobes ---------------------------------------
    $display("\n--- Test 3: byte write strobes ---");
    axil_write(32'h0000_0200, 2'd0, 32'hFFFF_FFFF, 4'hF);  // pre-fill word
    axil_write(32'h0000_0200, 2'd2, 32'h1122_3344, 4'b0101);  // update bytes 0 and 2
    axil_read(32'h0000_0200, 2'd2);  // expect 0xFF22FF44
    axil_write(32'h0000_0200, 2'd3, 32'hAABB_CCDD, 4'b1010);  // update bytes 1 and 3
    axil_read(32'h0000_0200, 2'd3);  // expect 0xAA22CC44

    // ---- Test 4: ID pass-through ------------------------------------------
    $display("\n--- Test 4: ID pass-through ---");
    for (i = 0; i < (1 << AXIL_ID_W_WIDTH); i = i + 1) begin
      axil_write(32'h0000_0300, i[AXIL_ID_W_WIDTH-1:0], 32'hC0DE_0000 + i, 4'hF);
      axil_read(32'h0000_0300, i[AXIL_ID_R_WIDTH-1:0]);
    end

    // ---- Test 5: back-to-back streaming -----------------------------------
    $display("\n--- Test 5: back-to-back transactions ---");
    for (i = 0; i < 16; i = i + 1) begin
      a = 32'h0000_0400 + (i << 2);
      axil_write(a, 2'd1, 32'h5A5A_0000 + i, 4'hF);
    end
    for (i = 0; i < 16; i = i + 1) begin
      a = 32'h0000_0400 + (i << 2);
      axil_read(a, 2'd2);
    end

    // ---- Test 6: write response back-pressure (bready held low) -----------
    $display("\n--- Test 6: write-response back-pressure ---");
    AXIL_bready_i = 1'b0;
    @(negedge clk);
    AXIL_awvalid_i = 1'b1;
    AXIL_awaddr_i  = 32'h0000_0500;
    AXIL_awid_i    = 2'd2;
    AXIL_wvalid_i  = 1'b1;
    AXIL_wdata_i   = 32'h600D_F00D;
    AXIL_wstrb_i   = 4'hF;
    @(negedge clk);
    while (!(AXIL_awvalid_i && AXIL_awready_o && AXIL_wvalid_i && AXIL_wready_o)) @(negedge clk);
    AXIL_awvalid_i = 1'b0;
    AXIL_wvalid_i  = 1'b0;
    while (!AXIL_bvalid_o) @(negedge clk);
    // Response must stay asserted and stable while bready is low.
    for (i = 0; i < 4; i = i + 1) begin
      @(negedge clk);
      expect_eq("bvalid held", AXIL_bvalid_o, 1'b1);
      expect_eq("bid held", AXIL_bid_o, 2'd2);
    end
    AXIL_bready_i = 1'b1;  // accept the response
    @(negedge clk);
    while (AXIL_bvalid_o) @(negedge clk);
    ref_mem[word_index(32'h0000_0500)] = 32'h600D_F00D;
    axil_read(32'h0000_0500, 2'd2);

    // ---- Test 7: read data back-pressure (rready held low) ----------------
    $display("\n--- Test 7: read-data back-pressure ---");
    AXIL_rready_i = 1'b0;
    @(negedge clk);
    AXIL_arvalid_i = 1'b1;
    AXIL_araddr_i  = 32'h0000_0500;
    AXIL_arid_i    = 2'd3;
    @(negedge clk);
    while (!(AXIL_arvalid_i && AXIL_arready_o)) @(negedge clk);
    AXIL_arvalid_i = 1'b0;
    while (!AXIL_rvalid_o) @(negedge clk);
    // Read data must stay asserted and stable while rready is low.
    for (i = 0; i < 4; i = i + 1) begin
      @(negedge clk);
      expect_eq("rvalid held", AXIL_rvalid_o, 1'b1);
      expect_eq("rdata held", AXIL_rdata_o, 32'h600D_F00D);
      expect_eq("rid held", AXIL_rid_o, 2'd3);
    end
    AXIL_rready_i = 1'b1;  // accept the data
    @(negedge clk);
    while (AXIL_rvalid_o) @(negedge clk);

    // ---- Summary ----------------------------------------------------------
    repeat (2) @(posedge clk);
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
    $dumpfile("AXIL_mem_tb.vcd");
    $dumpvars(0, AXIL_mem_tb);
  end

endmodule
