from pathlib import Path
import argparse, subprocess, zipfile, tempfile, os, json, hashlib, concurrent.futures, re, csv
p=argparse.ArgumentParser();p.add_argument('--iverilog',required=True);p.add_argument('--vvp',required=True);p.add_argument('--scratch',required=True);a=p.parse_args()
ev=Path(__file__).resolve().parent;repo=ev.parents[1];scratch=Path(a.scratch).resolve();scratch.mkdir(parents=True,exist_ok=True)
archive=repo/'vivado/submit/PPA_AdaPath_NPU_A.zip'
with zipfile.ZipFile(archive) as z:z.extractall(scratch)
project=scratch/'PPA_AdaPath_NPU_A';data=project/'data';src=project/'src'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected=[archive,project/'sim/top_tb.v']+sorted(src.glob('*'))+sorted(data.glob('*'))
before={str(p.relative_to(repo)) if p.is_relative_to(repo) else str(p.relative_to(scratch)):sha(p) for p in protected if p.is_file()}
cmd=[str(Path(a.iverilog).resolve()),'-g2012','-I',str(src),'-s','top_tb_1000_corrected','-s','corrected_observer','-o',str(scratch/'corrected.vvp'),str(ev/'top_tb_1000_corrected.v'),str(ev/'corrected_observer.v')]+[str(p) for p in sorted(src.glob('*.v'))]
cmd=[cmd[0]]+[os.path.relpath(x,data) if Path(x).is_absolute() else x for x in cmd[1:]]
c=subprocess.run(cmd,cwd=data,capture_output=True,text=True);(ev/'compile.log').write_text(c.stdout+c.stderr,encoding='utf-8');c.check_returncode()
def run(case):
 seq=case=='sequential';run_cmd=[str(Path(a.vvp).resolve()),str(scratch/'corrected.vvp'),f'+SEQUENTIAL={int(seq)}','+SEED=2026']
 with (ev/f'{case}.log').open('w',encoding='utf-8') as f:subprocess.run(run_cmd,cwd=data,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=900)
 text=(ev/f'{case}.log').read_text();summary=dict((k,int(v)) for k,v in re.findall(r'(\w+)=(\d+)',re.search(r'^SUMMARY .*$',text,re.M)[0]));obs=dict((k,int(v)) for k,v in re.findall(r'(\w+)=(\d+)',re.search(r'^OBSERVER .*$',text,re.M)[0]))
 assert obs=={'outputs':1000,'x_outputs':0,'invalid_reads':0,'unknown_reads':0,'reads':784000},obs
 rows=[line.split(',')[1:] for line in text.splitlines() if line.startswith('RESULT,')];assert len(rows)==1000
 with (ev/f'{case}.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(['output','image_index','label','decision','mode','interface_cycles']);w.writerows(rows)
 return {'case':case,'summary':summary,'observer':obs,'command':run_cmd}
with concurrent.futures.ThreadPoolExecutor(2) as pool:results=list(pool.map(run,['sequential','random_seed2026']))
after={str(p.relative_to(repo)) if p.is_relative_to(repo) else str(p.relative_to(scratch)):sha(p) for p in protected if p.is_file()};assert before==after
seq=list(csv.DictReader((ev/'sequential.csv').open()));rnd=list(csv.DictReader((ev/'random_seed2026.csv').open()));assert [int(x['image_index']) for x in seq]==list(range(1000))
assert all((x['decision'],x['mode'])==(seq[int(x['image_index'])]['decision'],seq[int(x['image_index'])]['mode']) for x in rnd)
res={'compiler':subprocess.run([a.iverilog,'-V'],capture_output=True,text=True).stdout.splitlines()[0],'compile_command':cmd,'protected_hashes_unchanged':True,'protected_sha256':before,'runs':results,'random_vs_sequential_same_index_matches':1000,'cycle_definition':'Number of rising edges from first deasserted-reset edge through the edge observing valid_out, inclusive; original 10 ps functional clock, not physical timing.'}
(ev/'validation.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(results,indent=2))
