read_liberty /root/ppa-tools/ORFS/flow/platforms/asap7/lib/NLDM/asap7sc7p5t_SEQ_RVT_TT_nldm_220123.lib
read_lef /root/ppa-tools/ORFS/flow/platforms/asap7/lef/asap7_tech_1x_201209.lef
read_lef /root/ppa-tools/ORFS/flow/platforms/asap7/lef/asap7sc7p5t_28_R_1x_220121a.lef
read_verilog probe.v
link_design probe
create_clock -name clk -period 10000 [get_ports clk]
create_generated_clock -name gc -source [get_ports clk] -divide_by 1 [get_pins gate/GCLK]
report_checks -path_delay max
report_clock_properties
read_vcd -scope tb/dut probe.vcd
report_activity_annotation
report_power -digits 9
report_power -instances [get_cells ff] -digits 9
exit
