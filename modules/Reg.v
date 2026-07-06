/* Register module
    Updates data on the posedge of the clk_i or the arst_i signal.
*/
`include "timescale.vs"

module Reg #(
    parameter integer DATA_W = 8,
    parameter logic [DATA_W-1:0] RST_VAL = {DATA_W{1'b0}}
) (
    `include "io_clk_en_rst.vs"
    // Inline register (reg_data_q)
    input  wire              data_e,
    input  wire              data_r,
    input  wire [DATA_W-1:0] data_n,
    output reg  [DATA_W-1:0] data_q,
    // List registers (reg_reg_list)
    input  wire              count_en,
    input  wire              count_r,
    input  wire [       7:0] count_n,
    output reg  [       7:0] count_q,
    input  wire              valid_r,
    input  wire              valid_n,
    output reg               valid_q,
    output reg               free_q
);

  reg  sync_reset;

  // cke_i is part of the standard IO bundle; register updates are not gated here.
  wire _unused_cke;
  assign _unused_cke = cke_i;

  `include "synchronous_reset_from_async.vs"

  wire data_rst = data_r | sync_reset;
  wire count_rst = count_r | sync_reset;
  wire valid_rst = valid_r | sync_reset;
  wire free_n;

  assign free_n = ~free_q;

  `include "reg_data_q.vs"  // DATA_W, RST_VAL, data_rst, _e, _n

  `include "reg_reg_list.vs"  /*
    count_q, 8, 0, count_rst, count_en, count_n
    valid_q, 1, 0, valid_rst, , valid_n
    free_q, 1, 0, sync_reset, , free_n
    */

endmodule
