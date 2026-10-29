"""Render measured VCD transitions; no illustrative/synthesized signal values."""
from pathlib import Path
import csv,json,bisect
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent
events={}; names={}; t=0
for line in (root/'medium_first3.vcd').read_text().splitlines():
    s=line.strip()
    if s.startswith('$var'):
        p=s.split();names[p[3]]=p[4];events[p[4]]=[]
    elif s.startswith('#'):t=int(s[1:])
    elif s and s[0] in '01xXzZ' and s[1:] in names:
        events[names[s[1:]]].append((t,s[0].lower()))
    elif s.startswith('b'):
        val,code=s[1:].split()
        if code in names:events[names[code]].append((t,val.lower()))
def val_at(name,time):
    a=events[name];i=bisect.bisect_right([p[0] for p in a],time)-1
    return a[i][1] if i>=0 else 'x'
def number(v):return None if any(c in v for c in 'xz') else int(v,2)
start=next(t for t,v in events['i'] if number(v)==2)
end=next(t for t,v in events['i'] if number(v)==3)
selected={n:[(t,number(v)) for t,v in a if start<=t<=end] for n,a in events.items()}
(root/'medium_events.json').write_text(json.dumps({'index_zero_based':2,'image_start_ps':start,'next_image_ps':end,'transitions':selected},indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
signals=['clk','data_in','margin','mode','ch_en','conv2_en','fc_light_en','fc_full_en','valid_out_6','decision']
fig,axes=plt.subplots(1,2,figsize=(15,7),gridspec_kw={'width_ratios':[2,1]},layout='constrained')
for ax,(lo,hi,title) in zip(axes,[(28400,30320,'Medium backend and output'),(30230,30300,'Output pulse detail (10 ns clock)')]):
    lo*=1000;hi*=1000
    for j,n in enumerate(signals):
        y=len(signals)-j
        ev=[(lo,val_at(n,lo))]+[(t,v) for t,v in events[n] if lo<t<hi]+[(hi,val_at(n,hi))]
        if n in ['clk','conv2_en','fc_light_en','fc_full_en','valid_out_6']:
            ax.step([t/1e6 for t,v in ev],[y+0.55*(number(v) or 0) for t,v in ev],where='post',color='#087f8c',lw=1)
        else:
            for (t,v),(tn,_) in zip(ev,ev[1:]):
                ax.plot([t/1e6,tn/1e6],[y+0.1,y+0.1],color='#2457a7',lw=1)
                ax.plot([t/1e6,tn/1e6],[y+0.5,y+0.5],color='#2457a7',lw=1)
                ax.plot([t/1e6,t/1e6],[y+0.1,y+0.5],color='#2457a7',lw=.6)
                if (tn-t)/(hi-lo)>.045:
                    value=number(v);label=('X' if value is None else f'0x{value:02X}' if n in ['ch_en','data_in'] else str(value))
                    ax.text((t+tn)/2e6,y+.29,label,ha='center',va='center',fontsize=9)
        ax.axhline(y-.15,color='#dddddd',lw=.4)
    ax.set_yticks([len(signals)-j+.25 for j in range(len(signals))],signals)
    ax.set_xlim(lo/1e6,hi/1e6);ax.set_ylim(.6,len(signals)+.8)
    ax.set_xlabel('Simulation time (us)');ax.set_title(title);ax.grid(axis='x',alpha=.18)
fig.suptitle('WM image #3 (index 2): margin 16, Medium, ch_en=0x0F, decision=0\nMeasured Vivado 2024.1 VCD; functional simulation clock = 10 ns (not physical Fmax)',fontsize=13)
fig.savefig(root/'medium_wave_measured.png',dpi=220)
fig.savefig(root/'medium_wave_measured.pdf')
print(json.dumps({n:selected[n] for n in ['mode','margin','ch_en','conv2_en','fc_light_en','fc_full_en','valid_out_6','decision']},indent=2))
