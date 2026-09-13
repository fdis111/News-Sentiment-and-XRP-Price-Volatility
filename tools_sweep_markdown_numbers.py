import json, re, sys
nb = json.load(open('notebook.ipynb')); cells = nb['cells']
WINDOW = int(sys.argv[1]) if len(sys.argv) > 1 else 8

def celltext(c):
    p = [''.join(c['source'])] if c['cell_type'] == 'code' else []
    for o in c.get('outputs', []):
        if 'text' in o: p.append(''.join(o['text']))
        elif 'data' in o and 'text/plain' in o['data']:
            p.append(''.join(o['data']['text/plain']))
    return '\n'.join(p)

TEXTS = [celltext(c) for c in cells]
DEC = re.compile(r'(?<![\d.])(\d+\.\d+)(?![\d])')
PCT = re.compile(r'(\d+(?:\.\d+)?)\s?%')

def near(i, tok):
    lo, hi = max(0, i-1-WINDOW), min(len(cells), i+WINDOW)
    hay = '\n'.join(TEXTS[lo:hi])
    if tok in hay: return True
    try: v = float(tok)
    except ValueError: return False
    return any(c in hay for c in (f'{v:.4f}', f'{v:.3f}', f'{v:.2f}',
                                  f'{v/100:.4f}', f'{v/100:.3f}', f'{v/100:.1%}'))

flagged = {}
for i, c in enumerate(cells, 1):
    if c['cell_type'] != 'markdown' or i == 204: continue
    s = ''.join(c['source'])
    s = re.sub(r'§\d+(\.\d+)*', '', s)
    s = re.sub(r'\((19|20)\d{2}\)', '', s)
    s = re.sub(r'\$\$.*?\$\$', '', s, flags=re.S)
    toks = set(DEC.findall(s)) | set(PCT.findall(s))
    miss = sorted({t for t in toks if not near(i, t)}, key=float)
    if miss: flagged[i] = miss

total = sum(len(v) for v in flagged.values())
print(f"window=±{WINDOW} cells | {len(flagged)} markdown cells, {total} unverified numbers\n")
for i, m in sorted(flagged.items()):
    print(f"[{i}] {', '.join(m)}")
