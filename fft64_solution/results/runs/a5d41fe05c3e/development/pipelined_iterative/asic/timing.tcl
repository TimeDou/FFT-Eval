read_liberty /mnt/DATA1/sj/ALS/DP2.0/DSBench/FFT-Bench/fft64_benchmark/tech/ASAP7_RVT_TT_nldm_NO_FAHA.lib
read_liberty /mnt/DATA1/sj/ALS/DP2.0/DSBench/FFT-Bench/fft64_benchmark/tech/ASAP7_SEQ_RVT_TT_nldm_220123.lib
read_verilog /mnt/DATA1/sj/ALS/DP2.0/DSBench/FFT-Bench/fft64_solution/results/runs/47657957d1b4/development/pipelined_iterative/asic/timing_netlist.v
link_design fft64_top
source /mnt/DATA1/sj/ALS/DP2.0/DSBench/FFT-Bench/fft64_solution/results/runs/47657957d1b4/development/pipelined_iterative/asic/constraints.sdc
check_setup -verbose
report_checks -path_delay max -format full_clock_expanded -digits 4
report_worst_slack -digits 4
exit
