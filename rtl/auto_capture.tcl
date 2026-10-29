# auto_capture.tcl — GTKWave 자동 캡처: 신호 배치 -> 구간 줌 -> PNG 저장 4장
# 실행: gtkwave -S auto_capture.tcl tb_adapath.vcd
set sigs [list \
  tb_adapath.start \
  tb_adapath.dut.front_done \
  tb_adapath.dut.mode_v \
  tb_adapath.dut.mode\[1:0\] \
  tb_adapath.dut.u_fsm.state\[2:0\] \
  tb_adapath.dut.u_fsm.conv2_en \
  tb_adapath.dut.u_fsm.ch_en\[7:0\] \
  tb_adapath.dut.fm_ov \
  tb_adapath.dut.u_fsm.fc_light_en \
  tb_adapath.dut.u_fsm.fc_full_en \
  tb_adapath.dut.result_sel\[1:0\] \
  tb_adapath.dut.margin\[11:0\] \
  tb_adapath.dut.u_fsm.done \
  tb_adapath.valid_out \
  tb_adapath.dut.decision\[3:0\] ]
gtkwave::addSignalsFromList $sigs
gtkwave::/Edit/Set_Trace_Max_Hier 0
gtkwave::/Edit/Select_All
gtkwave::/Edit/Data_Format/Hex
gtkwave::/Edit/UnSelect_All

set outdir "C:/Users/yhe44/AppData/Local/Temp/claude/C--Users-yhe44-OneDrive----IDEC-----------/6d138761-2b93-4e6f-9ffd-1767ee64f5a6/scratchpad/gtkcap"
foreach {name t0 t1} {
    gtkwave_easy     8295000  8575000
    gtkwave_hard     33795000 35785000
    gtkwave_medium   64425000 66415000
    gtkwave_overview 0        87155000
} {
    gtkwave::setZoomRangeTimes $t0 $t1
    update
    after 500
    gtkwave::/File/Grab_To_File "$outdir/$name.png"
}
gtkwave::/File/Quit
