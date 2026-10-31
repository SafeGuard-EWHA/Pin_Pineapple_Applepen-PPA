@echo off
set PATH=C:\Xilinx\Vivado\2023.1\bin;%PATH%
call xvlog.bat xfill.v > xvlog_fill.out 2>&1
call xelab.bat top_tb_1000 xfill -timescale 1ns/1ps -debug typical -s netfill > xelab.out 2>&1
call xsim.bat netfill -tclbatch trace.tcl -log net_xfill.log > xsim.out 2>&1
echo DONE > done.flag
