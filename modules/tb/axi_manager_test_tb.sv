`timescale 1ns / 1ps

`ifndef DEBUG
`define DEBUG 0
`endif

// ============================================================================
// Self-checking testbench for the AXI-Full manager wrapper.
//
// Drives the generated user ports (usr_cmd_*, usr_rd_*, usr_wr_*), talks to
// axi_ram over AXI4-Full, and checks read data against a byte-accurate golden
// image updated on every accepted write beat.
// ============================================================================
module axi_manager_test_tb;

  // --------------------------------------------------------------------------
  // Parameters
  // --------------------------------------------------------------------------
  localparam integer AXI_M_ID_W_WIDTH = 1;
  localparam integer AXI_M_ADDR_WIDTH = 32;
  localparam integer AXI_M_DATA_WIDTH = 32;
  localparam integer AXI_M_BRESP_WIDTH = 2;
  localparam integer AXI_M_ID_R_WIDTH = 1;
  localparam integer RAM_ADDR_WIDTH = 16;  // 64 KiB byte space
  localparam integer STRB_WIDTH = AXI_M_DATA_WIDTH / 8;
  localparam integer AXI_SIZE_FULL = $clog2(STRB_WIDTH);
  localparam integer DEBUG = `DEBUG;
  localparam integer TIMEOUT = 10000;
  localparam integer MAX_BEATS = 256;

  localparam logic [1:0] BURST_FIXED = 2'b00;
  localparam logic [1:0] BURST_INCR = 2'b01;

  // --------------------------------------------------------------------------
  // Clock / reset
  // --------------------------------------------------------------------------
  logic clk = 0;
  logic arst = 1;
  always #5 clk = ~clk;

  // --------------------------------------------------------------------------
  // Scoreboard
  // --------------------------------------------------------------------------
  integer errors = 0;
  integer checks = 0;
  integer aw_hs = 0;
  integer ar_hs = 0;

  logic [7:0] golden[0:(1<<RAM_ADDR_WIDTH)-1];

  logic [AXI_M_DATA_WIDTH-1:0] wr_payload[0:MAX_BEATS-1];
  logic [STRB_WIDTH-1:0] wr_strb[0:MAX_BEATS-1];

  logic [AXI_M_ADDR_WIDTH-1:0] cur_wr_addr, cur_rd_addr;
  logic [7:0] cur_wr_len, cur_rd_len;
  logic [2:0] cur_wr_size, cur_rd_size;
  logic [1:0] cur_wr_burst, cur_rd_burst;

  // --------------------------------------------------------------------------
  // AXI-Full manager <-> RAM
  // --------------------------------------------------------------------------
  logic [0:0] axi_awid;
  logic [AXI_M_ADDR_WIDTH-1:0] axi_awaddr;
  logic [7:0] axi_awlen;
  logic [2:0] axi_awsize;
  logic [1:0] axi_awburst;
  logic axi_awlock;
  logic [3:0] axi_awcache;
  logic [2:0] axi_awprot;
  logic [3:0] axi_awqos;
  logic axi_awvalid;
  logic axi_awready;

  logic [AXI_M_DATA_WIDTH-1:0] axi_wdata;
  logic [STRB_WIDTH-1:0] axi_wstrb;
  logic axi_wlast;
  logic axi_wvalid;
  logic axi_wready;

  logic [0:0] axi_bid;
  logic [AXI_M_BRESP_WIDTH-1:0] axi_bresp;
  logic axi_bvalid;
  logic axi_bready;

  logic [0:0] axi_arid;
  logic [AXI_M_ADDR_WIDTH-1:0] axi_araddr;
  logic [7:0] axi_arlen;
  logic [2:0] axi_arsize;
  logic [1:0] axi_arburst;
  logic axi_arlock;
  logic [3:0] axi_arcache;
  logic [2:0] axi_arprot;
  logic [3:0] axi_arqos;
  logic axi_arvalid;
  logic axi_arready;

  logic [0:0] axi_rid;
  logic [AXI_M_DATA_WIDTH-1:0] axi_rdata;
  logic [1:0] axi_rresp;
  logic axi_rlast;
  logic axi_rvalid;
  logic axi_rready;

  // --------------------------------------------------------------------------
  // User ports
  // --------------------------------------------------------------------------
  logic usr_cmd_rd_valid;
  logic usr_cmd_rd_ready;
  logic [AXI_M_ADDR_WIDTH-1:0] usr_cmd_rd_addr;
  logic [7:0] usr_cmd_rd_len;
  logic [2:0] usr_cmd_rd_size;
  logic [1:0] usr_cmd_rd_burst;
  logic [0:0] usr_cmd_rd_id;

  logic usr_rd_data_valid;
  logic usr_rd_data_ready;
  logic [AXI_M_DATA_WIDTH-1:0] usr_rd_data;
  logic [1:0] usr_rd_resp;
  logic [0:0] usr_rd_id;
  logic usr_rd_last;

  logic usr_cmd_wr_valid;
  logic usr_cmd_wr_ready;
  logic [AXI_M_ADDR_WIDTH-1:0] usr_cmd_wr_addr;
  logic [7:0] usr_cmd_wr_len;
  logic [2:0] usr_cmd_wr_size;
  logic [1:0] usr_cmd_wr_burst;
  logic [0:0] usr_cmd_wr_id;

  logic usr_wr_data_valid;
  logic usr_wr_data_ready;
  logic [AXI_M_DATA_WIDTH-1:0] usr_wr_data;
  logic [STRB_WIDTH-1:0] usr_wr_strb;

  logic usr_wr_resp_valid;
  logic usr_wr_resp_ready;
  logic [0:0] usr_wr_resp_id;
  logic [AXI_M_BRESP_WIDTH-1:0] usr_wr_resp;

  // --------------------------------------------------------------------------
  // DUT
  // --------------------------------------------------------------------------
  axi_manager_test #(
      .AXI_M_ID_W_WIDTH (AXI_M_ID_W_WIDTH),
      .AXI_M_ADDR_WIDTH (AXI_M_ADDR_WIDTH),
      .AXI_M_DATA_WIDTH (AXI_M_DATA_WIDTH),
      .AXI_M_BRESP_WIDTH(AXI_M_BRESP_WIDTH),
      .AXI_M_ID_R_WIDTH (AXI_M_ID_R_WIDTH)
  ) dut (
      .clk_i  (clk),
      .arstn_i(~arst),

      .AXI_M_awVALID_o(axi_awvalid),
      .AXI_M_awREADY_i(axi_awready),
      .AXI_M_awID_o   (axi_awid),
      .AXI_M_awADDR_o (axi_awaddr),
      .AXI_M_awLEN_o  (axi_awlen),
      .AXI_M_awSIZE_o (axi_awsize),
      .AXI_M_awBURST_o(axi_awburst),
      .AXI_M_awLOCK_o (axi_awlock),
      .AXI_M_awCACHE_o(axi_awcache),
      .AXI_M_awPROT_o (axi_awprot),
      .AXI_M_awQOS_o  (axi_awqos),

      .AXI_M_wVALID_o(axi_wvalid),
      .AXI_M_wREADY_i(axi_wready),
      .AXI_M_wDATA_o (axi_wdata),
      .AXI_M_wSTRB_o (axi_wstrb),
      .AXI_M_wLAST_o (axi_wlast),

      .AXI_M_bVALID_i(axi_bvalid),
      .AXI_M_bREADY_o(axi_bready),
      .AXI_M_bID_i   (axi_bid),
      .AXI_M_bRESP_i (axi_bresp),

      .AXI_M_arVALID_o(axi_arvalid),
      .AXI_M_arREADY_i(axi_arready),
      .AXI_M_arID_o   (axi_arid),
      .AXI_M_arADDR_o (axi_araddr),
      .AXI_M_arLEN_o  (axi_arlen),
      .AXI_M_arSIZE_o (axi_arsize),
      .AXI_M_arBURST_o(axi_arburst),
      .AXI_M_arLOCK_o (axi_arlock),
      .AXI_M_arCACHE_o(axi_arcache),
      .AXI_M_arPROT_o (axi_arprot),
      .AXI_M_arQOS_o  (axi_arqos),

      .AXI_M_rVALID_i(axi_rvalid),
      .AXI_M_rREADY_o(axi_rready),
      .AXI_M_rID_i   (axi_rid),
      .AXI_M_rDATA_i (axi_rdata),
      .AXI_M_rRESP_i (axi_rresp),
      .AXI_M_rLAST_i (axi_rlast),

      .AXI_M_usr_cmd_rd_valid_i(usr_cmd_rd_valid),
      .AXI_M_usr_cmd_rd_ready_o(usr_cmd_rd_ready),
      .AXI_M_usr_cmd_rd_addr_i (usr_cmd_rd_addr),
      .AXI_M_usr_cmd_rd_len_i  (usr_cmd_rd_len),
      .AXI_M_usr_cmd_rd_size_i (usr_cmd_rd_size),
      .AXI_M_usr_cmd_rd_burst_i(usr_cmd_rd_burst),
      .AXI_M_usr_cmd_rd_id_i   (usr_cmd_rd_id),

      .AXI_M_usr_rd_data_valid_o(usr_rd_data_valid),
      .AXI_M_usr_rd_data_ready_i(usr_rd_data_ready),
      .AXI_M_usr_rd_data_o      (usr_rd_data),
      .AXI_M_usr_rd_resp_o      (usr_rd_resp),
      .AXI_M_usr_rd_id_o        (usr_rd_id),
      .AXI_M_usr_rd_last_o      (usr_rd_last),

      .AXI_M_usr_cmd_wr_valid_i(usr_cmd_wr_valid),
      .AXI_M_usr_cmd_wr_ready_o(usr_cmd_wr_ready),
      .AXI_M_usr_cmd_wr_addr_i (usr_cmd_wr_addr),
      .AXI_M_usr_cmd_wr_len_i  (usr_cmd_wr_len),
      .AXI_M_usr_cmd_wr_size_i (usr_cmd_wr_size),
      .AXI_M_usr_cmd_wr_burst_i(usr_cmd_wr_burst),
      .AXI_M_usr_cmd_wr_id_i   (usr_cmd_wr_id),

      .AXI_M_usr_wr_data_valid_i(usr_wr_data_valid),
      .AXI_M_usr_wr_data_ready_o(usr_wr_data_ready),
      .AXI_M_usr_wr_data_i      (usr_wr_data),
      .AXI_M_usr_wr_strb_i      (usr_wr_strb),

      .AXI_M_usr_wr_resp_valid_o(usr_wr_resp_valid),
      .AXI_M_usr_wr_resp_ready_i(usr_wr_resp_ready),
      .AXI_M_usr_wr_resp_id_o   (usr_wr_resp_id),
      .AXI_M_usr_wr_resp_o      (usr_wr_resp)
  );

  // --------------------------------------------------------------------------
  // AXI RAM model (address buses sliced to the reduced depth)
  // --------------------------------------------------------------------------
  axi_ram #(
      .DATA_WIDTH(AXI_M_DATA_WIDTH),
      .ADDR_WIDTH(RAM_ADDR_WIDTH),
      .ID_WIDTH  (1)
  ) axi_ram_inst (
      .clk(clk),
      .rst(arst),

      .s_axi_awid(axi_awid),
      .s_axi_awaddr(axi_awaddr[RAM_ADDR_WIDTH-1:0]),
      .s_axi_awlen(axi_awlen),
      .s_axi_awsize(axi_awsize),
      .s_axi_awburst(axi_awburst),
      .s_axi_awlock(axi_awlock),
      .s_axi_awcache(axi_awcache),
      .s_axi_awprot(axi_awprot),
      .s_axi_awvalid(axi_awvalid),
      .s_axi_awready(axi_awready),

      .s_axi_wdata (axi_wdata),
      .s_axi_wstrb (axi_wstrb),
      .s_axi_wlast (axi_wlast),
      .s_axi_wvalid(axi_wvalid),
      .s_axi_wready(axi_wready),

      .s_axi_bid(axi_bid),
      .s_axi_bresp(axi_bresp),
      .s_axi_bvalid(axi_bvalid),
      .s_axi_bready(axi_bready),

      .s_axi_arid(axi_arid),
      .s_axi_araddr(axi_araddr[RAM_ADDR_WIDTH-1:0]),
      .s_axi_arlen(axi_arlen),
      .s_axi_arsize(axi_arsize),
      .s_axi_arburst(axi_arburst),
      .s_axi_arlock(axi_arlock),
      .s_axi_arcache(axi_arcache),
      .s_axi_arprot(axi_arprot),
      .s_axi_arvalid(axi_arvalid),
      .s_axi_arready(axi_arready),

      .s_axi_rid(axi_rid),
      .s_axi_rdata(axi_rdata),
      .s_axi_rresp(axi_rresp),
      .s_axi_rlast(axi_rlast),
      .s_axi_rvalid(axi_rvalid),
      .s_axi_rready(axi_rready)
  );

  always @(posedge clk) begin
    if (axi_awvalid && axi_awready) aw_hs = aw_hs + 1;
    if (axi_arvalid && axi_arready) ar_hs = ar_hs + 1;
  end

  // --------------------------------------------------------------------------
  // Helpers
  // --------------------------------------------------------------------------
  task automatic check(input string msg, input logic cond);
    begin
      checks = checks + 1;
      if (!cond) begin
        errors = errors + 1;
        $display("  FAIL: %0s", msg);
      end else if (DEBUG) $display("  PASS: %0s", msg);
    end
  endtask

  function automatic [AXI_M_ADDR_WIDTH-1:0] beat_addr(
      input [AXI_M_ADDR_WIDTH-1:0] base, input [2:0] size, input [1:0] burst, input integer idx);
    begin
      if (burst == BURST_FIXED) beat_addr = base;
      else beat_addr = base + (idx << size);
    end
  endfunction

  task automatic golden_write(input [AXI_M_ADDR_WIDTH-1:0] baddr, input [AXI_M_DATA_WIDTH-1:0] data,
                              input [STRB_WIDTH-1:0] strb);
    integer i;
    logic [AXI_M_ADDR_WIDTH-1:0] waddr;
    begin
      waddr = baddr & ~(STRB_WIDTH - 1);
      for (i = 0; i < STRB_WIDTH; i = i + 1) if (strb[i]) golden[waddr+i] = data[i*8+:8];
    end
  endtask

  task automatic golden_read_word(input [AXI_M_ADDR_WIDTH-1:0] baddr,
                                  output [AXI_M_DATA_WIDTH-1:0] data);
    integer i;
    logic [AXI_M_ADDR_WIDTH-1:0] waddr;
    begin
      waddr = baddr & ~(STRB_WIDTH - 1);
      data  = '0;
      for (i = 0; i < STRB_WIDTH; i = i + 1) data[i*8+:8] = golden[waddr+i];
    end
  endtask

  // --------------------------------------------------------------------------
  // Reset
  // --------------------------------------------------------------------------
  task automatic do_reset;
    integer gi;
    begin
      arst              = 1'b1;
      usr_cmd_rd_valid  = 1'b0;
      usr_cmd_rd_addr   = '0;
      usr_cmd_rd_len    = '0;
      usr_cmd_rd_size   = AXI_SIZE_FULL[2:0];
      usr_cmd_rd_burst  = BURST_INCR;
      usr_cmd_rd_id     = '0;
      usr_rd_data_ready = 1'b0;
      usr_cmd_wr_valid  = 1'b0;
      usr_cmd_wr_addr   = '0;
      usr_cmd_wr_len    = '0;
      usr_cmd_wr_size   = AXI_SIZE_FULL[2:0];
      usr_cmd_wr_burst  = BURST_INCR;
      usr_cmd_wr_id     = '0;
      usr_wr_data_valid = 1'b0;
      usr_wr_data       = '0;
      usr_wr_strb       = '0;
      usr_wr_resp_ready = 1'b1;
      for (gi = 0; gi < (1 << RAM_ADDR_WIDTH); gi = gi + 1) golden[gi] = 8'h00;
      repeat (8) @(posedge clk);
      @(negedge clk);
      arst = 1'b0;
      repeat (4) @(posedge clk);
    end
  endtask

  // --------------------------------------------------------------------------
  // User-port drivers
  // --------------------------------------------------------------------------
  task automatic issue_wr_cmd(input [AXI_M_ADDR_WIDTH-1:0] addr, input [7:0] len, input [2:0] size,
                              input [1:0] burst, input [0:0] id);
    integer tmo;
    begin
      cur_wr_addr      = addr;
      cur_wr_len       = len;
      cur_wr_size      = size;
      cur_wr_burst     = burst;
      usr_cmd_wr_addr  = addr;
      usr_cmd_wr_len   = len;
      usr_cmd_wr_size  = size;
      usr_cmd_wr_burst = burst;
      usr_cmd_wr_id    = id;
      usr_cmd_wr_valid = 1'b1;
      tmo              = 0;
      @(posedge clk);
      while (!(usr_cmd_wr_valid && usr_cmd_wr_ready)) begin
        @(posedge clk);
        tmo = tmo + 1;
        if (tmo > TIMEOUT) begin
          $display("  TIMEOUT waiting for usr_cmd_wr_ready");
          errors = errors + 1;
          usr_cmd_wr_valid = 1'b0;
          disable issue_wr_cmd;
        end
      end
      usr_cmd_wr_valid = 1'b0;
    end
  endtask

  task automatic issue_rd_cmd(input [AXI_M_ADDR_WIDTH-1:0] addr, input [7:0] len, input [2:0] size,
                              input [1:0] burst, input [0:0] id);
    integer tmo;
    begin
      cur_rd_addr      = addr;
      cur_rd_len       = len;
      cur_rd_size      = size;
      cur_rd_burst     = burst;
      usr_cmd_rd_addr  = addr;
      usr_cmd_rd_len   = len;
      usr_cmd_rd_size  = size;
      usr_cmd_rd_burst = burst;
      usr_cmd_rd_id    = id;
      usr_cmd_rd_valid = 1'b1;
      tmo              = 0;
      @(posedge clk);
      while (!(usr_cmd_rd_valid && usr_cmd_rd_ready)) begin
        @(posedge clk);
        tmo = tmo + 1;
        if (tmo > TIMEOUT) begin
          $display("  TIMEOUT waiting for usr_cmd_rd_ready");
          errors = errors + 1;
          usr_cmd_rd_valid = 1'b0;
          disable issue_rd_cmd;
        end
      end
      usr_cmd_rd_valid = 1'b0;
    end
  endtask

  task automatic push_wr_beats(input integer nbeats, input integer stall);
    integer i, tmo;
    logic [AXI_M_ADDR_WIDTH-1:0] baddr;
    begin
      i   = 0;
      tmo = 0;
      while (i < nbeats) begin
        usr_wr_data = wr_payload[i];
        usr_wr_strb = wr_strb[i];
        usr_wr_data_valid = (stall && (i != 0) && ($urandom_range(0, 3) == 0)) ? 1'b0 : 1'b1;
        @(posedge clk);
        tmo = tmo + 1;
        if (tmo > TIMEOUT) begin
          $display("  TIMEOUT waiting for usr_wr_data_ready (beat %0d)", i);
          errors = errors + 1;
          usr_wr_data_valid = 1'b0;
          disable push_wr_beats;
        end
        if (usr_wr_data_valid && usr_wr_data_ready) begin
          baddr = beat_addr(cur_wr_addr, cur_wr_size, cur_wr_burst, i);
          golden_write(baddr, wr_payload[i], wr_strb[i]);
          i   = i + 1;
          tmo = 0;
        end
      end
      usr_wr_data_valid = 1'b0;
    end
  endtask

  task automatic wait_wr_resp(input [0:0] exp_id);
    integer tmo;
    begin
      usr_wr_resp_ready = 1'b1;
      tmo               = 0;
      @(posedge clk);
      while (!usr_wr_resp_valid) begin
        @(posedge clk);
        tmo = tmo + 1;
        if (tmo > TIMEOUT) begin
          $display("  TIMEOUT waiting for usr_wr_resp_valid");
          errors = errors + 1;
          disable wait_wr_resp;
        end
      end
      check("write BRESP == OKAY", usr_wr_resp == 2'b00);
      check("write B ID matches", usr_wr_resp_id == exp_id);
    end
  endtask

  task automatic pull_rd_beats(input integer nbeats, input integer stall, input [0:0] exp_id);
    integer i, tmo;
    logic [AXI_M_DATA_WIDTH-1:0] exp;
    logic [AXI_M_ADDR_WIDTH-1:0] baddr;
    string msg;
    begin
      i   = 0;
      tmo = 0;
      while (i < nbeats) begin
        usr_rd_data_ready = (stall && ($urandom_range(0, 3) == 0)) ? 1'b0 : 1'b1;
        @(posedge clk);
        tmo = tmo + 1;
        if (tmo > TIMEOUT) begin
          $display("  TIMEOUT waiting for AXI R beat %0d", i);
          errors = errors + 1;
          usr_rd_data_ready = 1'b0;
          disable pull_rd_beats;
        end
        // rREADY is registered from usr_rd_data_ready, so consume on the AXI
        // R handshake (one beat) rather than the delayed user ready.
        if (axi_rvalid && axi_rready) begin
          baddr = beat_addr(cur_rd_addr, cur_rd_size, cur_rd_burst, i);
          golden_read_word(baddr, exp);
          $sformat(msg, "rd data beat %0d: got 0x%08h exp 0x%08h", i, usr_rd_data, exp);
          check(msg, usr_rd_data === exp);
          check("rd RRESP == OKAY", usr_rd_resp == 2'b00);
          check("rd ID matches", usr_rd_id == exp_id);
          if (i == nbeats - 1) check("usr_rd_last on final beat", usr_rd_last === 1'b1);
          else check("usr_rd_last clear before final beat", usr_rd_last === 1'b0);
          i   = i + 1;
          tmo = 0;
        end
      end
      usr_rd_data_ready = 1'b0;
    end
  endtask

  task automatic fill_incr_payload(input integer nbeats, input [AXI_M_DATA_WIDTH-1:0] base,
                                   input [STRB_WIDTH-1:0] strb);
    integer i;
    begin
      for (i = 0; i < nbeats; i = i + 1) begin
        wr_payload[i] = base + i;
        wr_strb[i]    = strb;
      end
    end
  endtask

  task automatic write_then_readback(input string tname, input [AXI_M_ADDR_WIDTH-1:0] addr,
                                     input [7:0] len, input [2:0] size, input [1:0] burst,
                                     input [0:0] id, input integer stall_wr, input integer stall_rd,
                                     input integer exp_aw, input integer exp_ar);
    integer nbeats, aw0, ar0, err0;
    begin
      nbeats = len + 1;
      err0   = errors;
      $display("Test %0s : start  addr=0x%08h len=%0d size=%0d burst=%0d stall_wr=%0d stall_rd=%0d",
               tname, addr, len, size, burst, stall_wr, stall_rd);
      aw0 = aw_hs;
      ar0 = ar_hs;

      issue_wr_cmd(addr, len, size, burst, id);
      push_wr_beats(nbeats, stall_wr);
      wait_wr_resp(id);
      if (exp_aw >= 0) check("AW segment count", (aw_hs - aw0) == exp_aw);

      issue_rd_cmd(addr, len, size, burst, id);
      pull_rd_beats(nbeats, stall_rd, id);
      if (exp_ar >= 0) check("AR segment count", (ar_hs - ar0) == exp_ar);

      if (errors == err0) $display("Test %0s : PASS", tname);
      else
        $display(
            "Test %0s : FAIL (%0d new error%0s)",
            tname,
            errors - err0,
            ((errors - err0) == 1) ? "" : "s"
        );
    end
  endtask

  // --------------------------------------------------------------------------
  // Main stimulus
  // --------------------------------------------------------------------------
  initial begin
    $display("==================================================");
    $display(" AXI manager wrapper testbench");
    $display("==================================================");
    do_reset;

    // 1. Single-beat aligned INCR
    fill_incr_payload(1, 32'hDEADBEEF, {STRB_WIDTH{1'b1}});
    write_then_readback("01_single", 32'h0000_0000, 8'd0, AXI_SIZE_FULL[2:0], BURST_INCR, 1'b0, 0,
                        0, 1, 1);

    // 2. Short INCR burst
    fill_incr_payload(16, 32'hA000_0000, {STRB_WIDTH{1'b1}});
    write_then_readback("02_incr_burst", 32'h0000_0100, 8'd15, AXI_SIZE_FULL[2:0], BURST_INCR, 1'b0,
                        0, 0, 1, 1);

    // 3. 4KB split: 8 beats starting 2 beats before the page boundary
    fill_incr_payload(8, 32'hB000_0000, {STRB_WIDTH{1'b1}});
    write_then_readback("03_4k_split", 32'h0000_0FF8, 8'd7, AXI_SIZE_FULL[2:0], BURST_INCR, 1'b0, 0,
                        0, 2, 2);

    // 4. Backpressure on the same 16-beat burst shape
    fill_incr_payload(16, 32'hC000_0000, {STRB_WIDTH{1'b1}});
    write_then_readback("04_backpressure", 32'h0000_0200, 8'd15, AXI_SIZE_FULL[2:0], BURST_INCR,
                        1'b0, 1, 1, 1, 1);

    // 5. Sparse WSTRB on an aligned word
    wr_payload[0] = 32'hAABBCCDD;
    wr_strb[0]    = 4'b0101;
    write_then_readback("05_sparse_wstrb", 32'h0000_0040, 8'd0, AXI_SIZE_FULL[2:0], BURST_INCR,
                        1'b0, 0, 0, 1, 1);

    // 6. Byte beat at an odd address (SIZE=0, matching strobe)
    wr_payload[0] = 32'h0000EE00;
    wr_strb[0]    = 4'b0010;
    write_then_readback("06_byte_odd", 32'h0000_0051, 8'd0, 3'd0, BURST_INCR, 1'b0, 0, 0, 1, 1);

    // 7. FIXED burst: last beat overwrites the same word
    wr_payload[0] = 32'h1111_1111;
    wr_payload[1] = 32'h2222_2222;
    wr_payload[2] = 32'h3333_3333;
    wr_payload[3] = 32'h4444_4444;
    wr_strb[0] = {STRB_WIDTH{1'b1}};
    wr_strb[1] = {STRB_WIDTH{1'b1}};
    wr_strb[2] = {STRB_WIDTH{1'b1}};
    wr_strb[3] = {STRB_WIDTH{1'b1}};
    write_then_readback("07_fixed", 32'h0000_0080, 8'd3, AXI_SIZE_FULL[2:0], BURST_FIXED, 1'b0, 0,
                        0, 1, 1);

    repeat (4) @(posedge clk);
    $display("==================================================");
    $display(" Checks run : %0d", checks);
    $display(" Errors     : %0d", errors);
    if (errors == 0) $display(" RESULT     : PASS");
    else $display(" RESULT     : FAIL");
    $display("==================================================");
    $finish;
  end

  initial begin
    repeat (1000000) @(posedge clk);
    $display("[%0t] TIMEOUT: simulation did not finish in time", $time);
    $finish;
  end

  initial begin
    $dumpfile("axi_manager_test_tb.vcd");
    $dumpvars(0, axi_manager_test_tb);
  end

endmodule
