module test1(clock, S0);
input clock;
reg S0;

always @(posedge clock) begin
    S0 <= ~S0;  // S0 flips every cycle
end

endmodule
