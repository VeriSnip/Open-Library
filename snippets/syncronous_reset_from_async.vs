  always @(posedge clk_i) begin
    if (arst_i) rst <= 1'b1;
    else rst <= 1'b0;
  end
