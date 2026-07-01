  always @(posedge clk_i) begin
    if (arst_i) sync_reset <= 1'b1;
    else sync_reset <= 1'b0;
  end
