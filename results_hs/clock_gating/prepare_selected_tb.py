"""Create a new power TB supporting explicit image indices; preserve original."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('stage', type=Path)
a = p.parse_args()
tb = (a.stage / 'tb_gl_A.v').read_text()
tb = tb.replace('integer i, k, o, c, cyc, acc;', 'integer i, k, o, c, cyc, acc, selected_index;')
needle = '            base = (start_img + i) * 784;'
if tb.count(needle) != 1:
    raise SystemExit('Unexpected upstream TB layout')
tb = tb.replace(needle, '''            if (!$value$plusargs($sformatf("I%0d=%%d",i), selected_index))
                selected_index = start_img + i;
            base = selected_index * 784;''')
# Only reporting/label expressions remain; pixel base was replaced above.
tb = tb.replace('((start_img + i) % 10)', '(selected_index % 10)')
tb = tb.replace('start_img + i, decision, (start_img + i) % 10', 'selected_index, decision, selected_index % 10')
(a.stage / 'tb_gl_selected.v').write_text(tb)
print('Created', a.stage / 'tb_gl_selected.v')
