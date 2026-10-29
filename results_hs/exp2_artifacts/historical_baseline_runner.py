from pathlib import Path
import subprocess, hashlib, json, time, concurrent.futures

ROOT = Path(__file__).resolve().parent
HANDOFF = ROOT / 'PPA_Codex_Handoff'
RTL = HANDOFF / 'project/rtl'
OUT = ROOT.parent / 'outputs/baseline_verification'
OUT.mkdir(parents=True, exist_ok=True)
BIN = ROOT / 'iverilog/bin'
manifest = json.loads((HANDOFF / 'manifest.json').read_text(encoding='utf-8'))
for name, info in manifest['files'].items():
    assert hashlib.sha256((HANDOFF / name).read_bytes()).hexdigest() == info['sha256'], name
core = 'mac_tree.v conv1_engine.v conv2_engine.v maxpool_relu_n.v fmap_buffer.v early_classifier.v fc_engine.v top2_finder.v score_margin_calc.v difficulty_decoder.v mode_control_fsm.v adapath_top.v ref/conv1_buf.v ref/conv2_buf.v'.split()
cmd = [str(BIN / 'iverilog.exe'), '-g2012', '-I.', '-DMODEL_A', '-DDATA="../out/rtl_data_mnist_A/"', '-o', 'codex_baseline_ada.vvp', *core, 'tb_threshold_sweep.v']
r = subprocess.run(cmd, cwd=RTL, capture_output=True)
(OUT / 'compile.log').write_bytes(r.stdout+r.stderr)
r.check_returncode()
expected = {'1': ['970','851.84','960','0','40'], '0.3': ['930','909.98','620','0','380']}
def run(level):
    start = time.monotonic()
    args = [str(BIN / 'vvp.exe'), 'codex_baseline_ada.vvp', '+TL=63', '+TH=63', f'+IMG=noisy/input_1000_contrast_{level}.txt']
    with (OUT / f'contrast_{level}.log').open('wb') as log:
        result = subprocess.run(args, cwd=RTL, stdout=log, stderr=subprocess.STDOUT)
    raw = (OUT / f'contrast_{level}.log').read_text(encoding='utf-8', errors='replace')
    lines = [x for x in raw.splitlines() if x.startswith('SWEEP,')]
    actual = lines[0].split(',')[3:] if len(lines)==1 else None
    record = dict(level=level, expected=expected[level], actual=actual, elapsed_seconds=time.monotonic()-start, returncode=result.returncode, passed=result.returncode==0 and actual==expected[level] and 'ERROR' not in raw)
    (OUT / f'contrast_{level}.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record), flush=True)
    return record
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(run, expected))
(OUT / 'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
if not all(x['passed'] for x in results):
    raise SystemExit('STOP: baseline mismatch. RTL was not changed; full experiment not started.')
print('Both baseline checks passed.', flush=True)
