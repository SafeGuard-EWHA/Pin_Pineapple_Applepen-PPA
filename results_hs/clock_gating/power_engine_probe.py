"""Small measured check that OpenSTA responds to gated-clock VCD activity."""
import argparse
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--orfs', type=Path, required=True)
p.add_argument('--stage', type=Path, required=True)
p.add_argument('--attempt', type=int, default=1)
a = p.parse_args()
out = a.stage / ('power_engine_probe' if a.attempt == 1 else 'power_engine_probe_' + str(a.attempt))
out.mkdir(exist_ok=False)
(out / 'probe.v').write_text('''module probe(input clk,en,d,output q);
wire gc;
ICGx1_ASAP7_75t_R gate(.CLK(clk),.ENA(en),.SE(1'b0),.GCLK(gc));
DFFHQNx1_ASAP7_75t_R ff(.CLK(gc),.D(d),.QN(q));
endmodule
''')
(out / 'tb.v').write_text('''`timescale 1ns/1ps
module tb;
reg clk=0,en=1,d=0;
wire q;
integer disabled;
probe dut(clk,en,d,q);
always #5 clk=~clk;
always @(negedge clk) d=~d;
initial begin
if (!$value$plusargs("DISABLED=%d",disabled)) disabled=0;
$dumpfile("probe.vcd"); $dumpvars(0,tb);
#21; if(disabled) en=0;
#979; $finish;
end
endmodule
''')
seq = a.orfs / 'flow/platforms/asap7/lib/NLDM/asap7sc7p5t_SEQ_RVT_TT_nldm_220123.lib'
(out / 'power.tcl').write_text(f'''read_liberty {seq}
read_lef {a.orfs}/flow/platforms/asap7/lef/asap7_tech_1x_201209.lef
read_lef {a.orfs}/flow/platforms/asap7/lef/asap7sc7p5t_28_R_1x_220121a.lef
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
''')
cmd = ['iverilog', '-g2012', '-s', 'tb', '-o', 'probe.vvp', 'probe.v', 'tb.v']
cmd += [str(f.resolve()) for f in sorted((a.stage/'std_cell_fn').glob('*.v'))]
subprocess.run(cmd, cwd=out, check=True)
for disabled in (0, 1):
    with (out / f'sim_{disabled}.log').open('w') as log:
        subprocess.run(['vvp', 'probe.vvp', f'+DISABLED={disabled}'], cwd=out,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    with (out / f'power_{disabled}.log').open('w') as log:
        subprocess.run(['openroad', '-exit', 'power.tcl'], cwd=out,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    (out / 'probe.vcd').rename(out / f'probe_{disabled}.vcd')
print('Probe logs saved:', out)
