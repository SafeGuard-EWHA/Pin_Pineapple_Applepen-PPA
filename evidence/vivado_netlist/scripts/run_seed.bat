@echo off
set PATH=C:\Xilinx\Vivado\2023.1\bin;%PATH%
call xsim.bat netfill -sv_seed 2 -tclbatch trace.tcl -log net.log > xsim.out 2>&1
echo DONE > done.flag
