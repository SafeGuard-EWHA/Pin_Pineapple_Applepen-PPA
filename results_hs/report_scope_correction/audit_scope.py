"""Audit existing evidence only; no simulation and no changes to original results."""
from pathlib import Path
import csv
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit():
    archive = ROOT / 'vivado/submit/PPA_AdaPath_NPU_A.zip'
    with zipfile.ZipFile(archive) as z:
        names = [n for n in z.namelist() if n.endswith('/data/input_1000.txt')]
        assert len(names) == 1
        raw = z.read(names[0])
    tokens = raw.decode('ascii').split()
    assert len(tokens) == 1000 * 784
    pixels = bytes(int(t, 16) for t in tokens)
    image_hashes = [sha(pixels[i*784:(i+1)*784]) for i in range(1000)]
    ref_path = ROOT / 'results_hs/corrected_tb/sequential.csv'
    with ref_path.open(encoding='utf-8', newline='') as f:
        ref = {int(r['image_index']): r for r in csv.DictReader(f)}
    summary_path = ROOT / 'evidence/vivado_netlist/summary.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    rows, runs, hashes = [], [], {}
    for run in summary['runs']:
        name = 'net_seed_default.log' if run['key'] == 'default' else 'net_' + run['key'] + '.log'
        log_path = ROOT / 'evidence/vivado_netlist/logs' / name
        log_bytes = log_path.read_bytes()
        hashes[str(log_path.relative_to(ROOT))] = sha(log_bytes)
        text = log_bytes.decode('utf-8', errors='replace')
        obs = [tuple(map(int, m)) for m in re.findall(r'OBS n=(\d+) idx=(\d+) dec=(\d+) t=(\d+)', text)]
        # The current evidence contains only partial runs, entirely within n=1..1000.
        assert [o[0] for o in obs] == list(range(1, len(obs)+1))
        assert len(obs) <= 1000
        prev_valid_ps = 10175  # Initial, unscored output; OBS prints one 10 ps clock later.
        matched_d = matched_c = correct = 0
        for n, idx, decision, obs_ps in obs:
            assert 0 <= idx < 1000, 'Out-of-range inputs require a separate xfill-matched reference'
            valid_ps = obs_ps - 10
            elapsed_ps = valid_ps - prev_valid_ps
            assert elapsed_ps % 10 == 0
            cycles = elapsed_ps // 10 - 1
            prev_valid_ps = valid_ps
            rd = int(ref[idx]['decision'])
            rc = int(ref[idx]['interface_cycles'])
            label = int(ref[idx]['label'])
            matched_d += decision == rd
            matched_c += cycles == rc
            correct += decision == label
            rows.append({'run': run['key'], 'output': n, 'image_index': idx,
                         'pixel_sha256': image_hashes[idx], 'decision': decision,
                         'rtl_decision': rd, 'interface_cycles': cycles,
                         'rtl_interface_cycles': rc, 'label': label})
        assert (len(obs), matched_d, matched_c, correct) == (
            run['outputs'], run['decision_match'], run['cycle_match'], run['correct'])
        runs.append({'run': run['key'], 'outputs': len(obs), 'decision_match': matched_d,
                     'cycle_match': matched_c, 'correct': correct,
                     'full_1000_completed': len(obs) == 1000 and run['final_accuracy_line'] is not None})
    indices = sorted({r['image_index'] for r in rows})
    distinct_pixels = len({r['pixel_sha256'] for r in rows})
    result = {
        'audit_type': 'Existing-log and input-byte audit; no new simulation',
        'base_commit': '6cf837b4d21ee530348caa53578b77d9a8b786d3',
        'input_archive': str(archive.relative_to(ROOT)), 'input_member': names[0],
        'input_member_sha256': sha(raw), 'input_pixels_sha256': sha(pixels),
        'input_images': 1000, 'input_unique_pixel_contents': len(set(image_hashes)),
        'total_outputs': len(rows), 'distinct_indices': len(indices),
        'distinct_pixel_contents': distinct_pixels,
        'decision_match': sum(r['decision_match'] for r in runs),
        'cycle_match': sum(r['cycle_match'] for r in runs),
        'correct': sum(r['correct'] for r in runs),
        'all_outputs_within_input_range': True, 'runs': runs,
        'sample_interpretation': 'Repeated contents and output transactions are not independent image samples',
        'xfill_condition': 'Any X or Z in TB data_in causes the entire DUT input byte to be forced to 0; TB source unchanged',
        'cycle_method': '10 ps clock; OBS time minus 10 ps is valid time; subtract one reset cycle between valid times; initial unscored valid time 10175 ps',
        'sha256': {**hashes, str(ref_path.relative_to(ROOT)): sha(ref_path.read_bytes()),
                   str(summary_path.relative_to(ROOT)): sha(summary_path.read_bytes())},
    }
    assert len(indices) == summary['distinct_indices']
    assert len(rows) == summary['total_outputs']
    (HERE / 'scope_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    with (HERE / 'observations.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({k: result[k] for k in ['total_outputs', 'distinct_indices', 'distinct_pixel_contents', 'decision_match', 'cycle_match', 'correct']}, ensure_ascii=False))


if __name__ == '__main__':
    audit()
