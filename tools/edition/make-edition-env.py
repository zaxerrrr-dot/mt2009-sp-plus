#!/usr/bin/env python3
"""make-edition-env.py <.env.example> <edition .env> <out> -- MT2009_CLASSIC_EDITION_V1:
the .env.example of an edition's package: every key the edition file names
takes its value, the rest (and every comment) stays as the PLUS file has it."""
import re
import sys

src, ed, out = sys.argv[1:4]
values = {}
for line in open(ed, encoding='utf-8'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        values[k] = v
text = open(src, encoding='utf-8', newline='').read()
seen = set()
def sub(m):
    seen.add(m.group(1))
    return m.group(1) + '=' + values[m.group(1)]
text = re.sub(r'(?m)^(' + '|'.join(map(re.escape, values)) + r')=[^\r\n]*', sub, text)
missing = [k for k in values if k not in seen]
if missing:
    nl = '\r\n' if '\r\n' in text else '\n'
    text += nl + nl.join(k + '=' + values[k] for k in missing) + nl
open(out, 'w', encoding='utf-8', newline='').write(text)
print('%s: %d value(s) set, %d added' % (out, len(seen), len(missing)))
