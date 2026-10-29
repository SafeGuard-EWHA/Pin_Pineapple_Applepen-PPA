from pathlib import Path
import zipfile,shutil,json,hashlib,argparse
p=argparse.ArgumentParser()
p.add_argument('--workdir',required=True)
a=p.parse_args()
repo=Path(__file__).resolve().parents[2];out=repo/'results_hs/clock_gating'
src=out/'rtl';stage=Path(a.workdir).resolve();stage.mkdir(parents=True,exist_ok=False)
text=(repo/'rtl/adapath_top.v').read_text(encoding='utf-8')
text=text.replace('module adapath_top #(', 'module adapath_top_cg #(',1)
anchor='    // ================= Region 3'
gate='''    // Experimental coarse backend gate. Reset/start clocks remain enabled.
    // S_DONE stays clocked to retire backend pulses before stopping the clock.
    wire clk_backend;
    wire backend_gate_enable = !rst_n | start | conv2_en | fsm_done;
    icg_latch u_backend_icg(.clk(clk), .enable(backend_gate_enable),
        .test_enable(1'b0), .gclk(clk_backend));

'''
text=text.replace(anchor,gate+anchor,1)
for inst in ['u_conv2','u_pool2','u_fcf','u_fcl']:
    pos=text.index(' '+inst+' (');end=text.index(');',pos)
    block=text[pos:end];assert '.clk(clk)' in block
    text=text[:pos]+block.replace('.clk(clk)','.clk(clk_backend)',1)+text[end:]
(src/'adapath_top_cg.v').write_text(text,encoding='utf-8')
metadata={'base_core_sha256':hashlib.sha256((repo/'rtl/adapath_top.v').read_bytes()).hexdigest(),'gated_instances':['u_conv2','u_pool2','u_fcf','G_LIGHT.u_fcl'],'clock_gate':'low-transparent latch + AND; technology mapping not yet verified'}
(out/'source_manifest.json').write_text(json.dumps(metadata,indent=2))
for model in ['A','WM']:
    with zipfile.ZipFile(repo/f'vivado/submit/PPA_AdaPath_NPU_{model}.zip') as z:z.extractall(stage)
    project=stage/f'PPA_AdaPath_NPU_{model}'; psrc=project/'src'
    chip=(psrc/'chip_adapath.v').read_text(encoding='utf-8').replace('module chip (','module chip_cg (',1).replace('adapath_top #(','adapath_top_cg #(',1)
    (psrc/'chip_cg.v').write_text(chip,encoding='utf-8')
    for name in ['icg_latch.v','adapath_top_cg.v']:shutil.copy2(src/name,psrc/name)
    top='top_tb_1000' if model=='A' else 'tb_wm';dut=f'{top}.chip1' if model=='A' else f'{top}.dut'
    tbtext=(project/'sim'/('top_tb.v' if model=='A' else 'tb_wm.v')).read_text(encoding='utf-8')
    # Shadow interface uses constant weights internally, just like the submission wrapper.
    ports=['.clk('+top+'.clk)','.rst_n('+top+'.rst_n)','.data_in('+top+'.data_in)','.decision(cg_decision)','.valid_out_6(cg_valid)']
    for name,width in [('w_11',200),('w_12',200),('w_13',200),('b_1',24),('b_2',24)]+[(f'w_{a}{b}',200) for a in [21,22,23] for b in [1,2,3]]+[('w_fc',3840),('b_fc',80)]:ports.append(f'.{name}({width}\'d0)')
    audit='''`timescale 1ps/1ps
module clockgate_audit;
wire [3:0] cg_decision; wire cg_valid;
chip_cg cg('''+',\n'.join(ports)+''');
integer checked=0, valid_mismatches=0, output_mismatches=0;
integer easy=0,med=0,hard=0, parent_edges=0,gated_edges=0,glitches=0;
always @(posedge cg.u_core.clk_backend) begin
 gated_edges=gated_edges+1;
 if (TOP.clk !== 1'b1) glitches=glitches+1;
end
always @(posedge TOP.clk) begin
 parent_edges=parent_edges+1;
 #1;
 if(TOP.rst_n === 1'b1) begin
   if(cg_valid !== TOP.valid_out_6) begin
     valid_mismatches=valid_mismatches+1;
     if(valid_mismatches<10) $display("VALID_MISMATCH time=%0t ref=%b gated=%b",$time,TOP.valid_out_6,cg_valid);
   end
   if(TOP.valid_out_6 === 1'b1) begin
     checked=checked+1;
     if(cg_decision !== TOP.decision || cg.u_core.mode_out !== REF.u_core.mode_out || cg.u_core.margin_out !== REF.u_core.margin_out) begin
       output_mismatches=output_mismatches+1;
       if(output_mismatches<10) $display("OUTPUT_MISMATCH time=%0t ref=%d gated=%d",$time,TOP.decision,cg_decision);
     end
     case(REF.u_core.mode_out) 0:easy=easy+1;1:med=med+1;2:hard=hard+1;endcase
   end
 end
end
endmodule
'''
    audit=audit.replace('TOP',top).replace('REF',dut)
    (out/f'lockstep_{model}.v').write_text(audit)
    (stage/f'lockstep_{model}.v').write_text(audit)
    sim=project/f'PPA_AdaPath_NPU_{model}.sim/sim_1/behav/xsim'
    script=f'''open_project {project.as_posix()}/PPA_AdaPath_NPU_{model}.xpr
set_property xsim.elaborate.xelab.more_options {{xil_defaultlib.clockgate_audit}} [get_filesets sim_1]
set_property xsim.simulate.runtime 0ns [get_filesets sim_1]
launch_simulation -mode behavioral -step compile
cd {sim.as_posix()}
puts [exec C:/Xilinx/Vivado/2024.1/bin/unwrapped/win64.o/xvlog.exe --work xil_defaultlib -i {psrc.as_posix()} {psrc.as_posix()}/icg_latch.v {psrc.as_posix()}/adapath_top_cg.v {psrc.as_posix()}/chip_cg.v {stage.as_posix()}/lockstep_{model}.v]
launch_simulation -mode behavioral -step elaborate
launch_simulation -mode behavioral -step simulate
run all
'''
    for name in ['checked','valid_mismatches','output_mismatches','easy','med','hard','parent_edges','gated_edges','glitches']:
        script+=f'puts "CLOCKGATE {name}=[get_value -radix unsigned /clockgate_audit/{name}]"\n'
    script+='close_sim\nclose_project\nexit\n'
    (out/f'run_lockstep_{model}.tcl').write_text(script)
    (stage/f'run_{model}.tcl').write_text(script)
print(stage)
