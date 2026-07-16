`timescale 1ns / 1ps

module SyncRSTTest_tb;

    logic clk_i;
    logic arst_low_i;
    logic arst_high_i;
    logic sync_low_from_low_o;
    logic sync_high_from_low_o;
    logic sync_low_from_high_o;
    logic sync_high_from_high_o;
    logic sync_default_clk_o;
    logic sync_default_types_o;

    SyncRSTTest dut (
        .clk_i(clk_i),
        .arst_low_i(arst_low_i),
        .arst_high_i(arst_high_i),
        .sync_low_from_low_o(sync_low_from_low_o),
        .sync_high_from_low_o(sync_high_from_low_o),
        .sync_low_from_high_o(sync_low_from_high_o),
        .sync_high_from_high_o(sync_high_from_high_o),
        .sync_default_clk_o(sync_default_clk_o),
        .sync_default_types_o(sync_default_types_o)
    );

    // Clock generation
    initial begin
        clk_i = 0;
        forever #5 clk_i = ~clk_i;
    end

    initial begin
        // Initialize
        arst_low_i = 1;
        arst_high_i = 0;

        // Wait a few cycles
        repeat (4) @(negedge clk_i);

        // Assert resets asynchronously
        #2;
        arst_low_i = 0;
        arst_high_i = 1;

        // Check if synchronous resets are asserted immediately
        #1;
        if (sync_low_from_low_o !== 0) $error("sync_low_from_low_o should be 0");
        if (sync_high_from_low_o !== 1) $error("sync_high_from_low_o should be 1");
        if (sync_low_from_high_o !== 0) $error("sync_low_from_high_o should be 0");
        if (sync_high_from_high_o !== 1) $error("sync_high_from_high_o should be 1");
        if (sync_default_clk_o !== 0) $error("sync_default_clk_o should be 0");
        if (sync_default_types_o !== 0) $error("sync_default_types_o should be 0");

        // Wait a few cycles while reset is held
        repeat (4) @(negedge clk_i);

        // De-assert resets asynchronously
        #2;
        arst_low_i = 1;
        arst_high_i = 0;

        // The synchronous resets should still be asserted right after de-assertion
        #1;
        if (sync_low_from_low_o !== 0) $error("sync_low_from_low_o should be 0");
        if (sync_high_from_low_o !== 1) $error("sync_high_from_low_o should be 1");
        if (sync_low_from_high_o !== 0) $error("sync_low_from_high_o should be 0");
        if (sync_high_from_high_o !== 1) $error("sync_high_from_high_o should be 1");
        if (sync_default_clk_o !== 0) $error("sync_default_clk_o should be 0");
        if (sync_default_types_o !== 0) $error("sync_default_types_o should be 0");

        // Wait for synchronization (2 cycles)
        repeat (4) @(negedge clk_i);

        // Now they should be de-asserted
        if (sync_low_from_low_o !== 1) $error("sync_low_from_low_o should be 1");
        if (sync_high_from_low_o !== 0) $error("sync_high_from_low_o should be 0");
        if (sync_low_from_high_o !== 1) $error("sync_low_from_high_o should be 1");
        if (sync_high_from_high_o !== 0) $error("sync_high_from_high_o should be 0");
        if (sync_default_clk_o !== 1) $error("sync_default_clk_o should be 1");
        if (sync_default_types_o !== 1) $error("sync_default_types_o should be 1");

        $display("All tests passed!");
        $finish;
    end

    // Dump waves
    initial begin
        $dumpfile("SyncRSTTest.vcd");
        $dumpvars(0, SyncRSTTest_tb);
    end

endmodule
