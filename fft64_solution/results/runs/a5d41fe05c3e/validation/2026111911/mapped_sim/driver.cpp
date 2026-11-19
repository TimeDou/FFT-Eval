#include "Vfft64_top.h"
#include "verilated.h"
#include <fstream>
#include <cstdint>
int main(int argc,char**argv){std::ifstream in(argv[1]);std::ofstream out(argv[2]);Vfft64_top d;long long rs,iv,fs,r,i;long long c=0;
 while(in>>rs>>iv>>fs>>r>>i){d.clk=0;d.rst=rs;d.in_valid=iv;d.frame_start=fs;d.in_re=(uint32_t)r;d.in_im=(uint32_t)i;d.eval();d.clk=1;d.eval();
 int64_t rr=(int64_t)(((uint64_t)d.out_re^8388608ULL)-8388608ULL),ii=(int64_t)(((uint64_t)d.out_im^8388608ULL)-8388608ULL);
 out<<c<<" "<<(int)d.out_valid<<" "<<(int)d.out_start<<" "<<rr<<" "<<ii<<"\n";d.clk=0;d.eval();++c;}d.final();}
