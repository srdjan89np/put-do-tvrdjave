"""Pravi Android App Bundle (.aab) iz APKEditor projekta, bez Android SDK-a.

Manifest i tabela resursa se pišu u proto formatu (aapt.pb) pomoću klasa iz bundletool-a,
a bundletool od modula pravi .aab.
Upotreba: python3 make_aab.py <apkeditor_proj> <decoded_json_dir> <out.aab>
"""
import json, os, shutil, subprocess, sys, zipfile
import xml.etree.ElementTree as ET

PROJ, DEC, OUT = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
BT = os.path.join(HERE, 'bundletool.jar')
ANDROID = 'http://schemas.android.com/apk/res/android'
W = os.path.join(HERE, 'work'); shutil.rmtree(W, ignore_errors=True); os.makedirs(W)

def u32(v): return v & 0xffffffff

# ---------- tabela resursa ----------
arsc = json.load(open(os.path.join(DEC, 'resources', 'resources.arsc.json')))
pkg = arsc['packages'][0]
pid = pkg['package_id']
names = {}  # id -> 'type/name'
for spec in pkg['specs']:
    for t in spec['types']:
        for e in t['entries']:
            names[(pid << 24) | (t['id'] << 16) | e['id']] = f"{t['name']}/{e['entry_name']}"
DENS = {'ldpi': 120, 'mdpi': 160, 'hdpi': 240, 'xhdpi': 320, 'xxhdpi': 480, 'xxxhdpi': 640}

def item(v):
    vt, d = v['value_type'], v['data']
    if vt == 'REFERENCE':
        r = {'id': u32(d)}
        if u32(d) in names: r['name'] = names[u32(d)]
        return {'ref': r}
    if vt == 'STRING':
        if isinstance(d, str) and d.startswith('res/'):
            return {'file': {'path': d, 'type': 'PNG' if d.endswith('.png') else 'UNKNOWN'}}
        return {'str': {'value': d}}
    if vt == 'COLOR_ARGB8': return {'prim': {'colorArgb8Value': u32(d)}}
    if vt == 'DEC': return {'prim': {'intDecimalValue': d}}
    if vt == 'HEX': return {'prim': {'intHexadecimalValue': u32(d)}}
    if vt == 'BOOLEAN': return {'prim': {'booleanValue': bool(d)}}
    raise SystemExit('nepoznat tip ' + vt)

types = []
for spec in pkg['specs']:
    entries = {}
    tname = None
    for t in spec['types']:
        tname = t['name']
        cfg = {}
        if t.get('config', {}).get('density'): cfg['density'] = DENS[t['config']['density']]
        for e in t['entries']:
            ent = entries.setdefault(e['id'], {'entryId': {'id': e['id']}, 'name': e['entry_name'],
                                               'visibility': {'level': 'PUBLIC'}, 'configValue': []})
            if e.get('is_complex'):
                st = {'parent': {'id': u32(e['parent_id'])}, 'entry': []}
                for v in e['values']:
                    st['entry'].append({'key': {'id': u32(v['name'])}, 'item': item(v)})
                val = {'compoundValue': {'style': st}}
            else:
                val = {'item': item(e['value'])}
            ent['configValue'].append({'config': cfg, 'value': val})
    types.append({'typeId': {'id': spec['spec']['id']}, 'name': tname, 'entry': list(entries.values())})
table = {'package': [{'packageId': {'id': pid}, 'packageName': pkg.get('package_name') or json.load(open(os.path.join(PROJ, 'resources', 'package_1', 'package.json')))['name'], 'type': types}]}
json.dump(table, open(os.path.join(W, 'table.json'), 'w'), ensure_ascii=False)

# ---------- manifest ----------
mj = json.load(open(os.path.join(DEC, 'AndroidManifest.xml.json')))
src = ET.parse(os.path.join(PROJ, 'AndroidManifest.xml')).getroot()

def conv(dnode, snode, top=False):
    el = {'name': dnode['name'], 'attribute': [], 'child': []}
    if top: el['namespaceDeclaration'] = [{'prefix': 'android', 'uri': ANDROID}]
    for a in dnode.get('attributes', []):
        uri = a.get('uri', '')
        txt = snode.get(('{%s}' % uri if uri else '') + a['name'])
        assert txt is not None, (dnode['name'], a['name'])
        at = {'name': a['name'], 'value': txt}
        if uri: at['namespaceUri'] = uri
        if a['id']: at['resourceId'] = a['id']
        vt = a['value_type']
        if vt == 'REFERENCE':
            at['compiledItem'] = item(a)
        elif vt in ('DEC', 'HEX', 'BOOLEAN'):
            at['compiledItem'] = item(a)
        # STRING: samo tekstualna vrednost, kao aapt2
        el['attribute'].append(at)
    schildren = list(snode)
    dchildren = [n for n in dnode.get('nodes', []) if n.get('node_type') == 'element']
    assert len(schildren) == len(dchildren), dnode['name']
    for dc, sc in zip(dchildren, schildren):
        el['child'].append(conv(dc, sc))
    return {'element': el}

root = [n for n in mj['nodes'] if n.get('node_type') == 'element'][0]
json.dump(conv(root, src, True), open(os.path.join(W, 'manifest.json'), 'w'), ensure_ascii=False)

cp = os.pathsep.join([BT, os.path.join(HERE, 'j')])
for kind, js, out in (('table', 'table.json', 'resources.pb'), ('xml', 'manifest.json', 'AndroidManifest.xml')):
    subprocess.run(['java', '-cp', cp, 'Json2Pb', kind, os.path.join(W, js), os.path.join(W, out)], check=True)

# ---------- modul ----------
mod = os.path.join(W, 'base.zip')
with zipfile.ZipFile(mod, 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(W, 'AndroidManifest.xml'), 'manifest/AndroidManifest.xml')
    z.write(os.path.join(W, 'resources.pb'), 'resources.pb')
    z.write(os.path.join(PROJ, 'root', 'classes.dex'), 'dex/classes.dex')
    resdir = os.path.join(PROJ, 'resources', 'package_1', 'res')
    for d in sorted(os.listdir(resdir)):
        if d.startswith('values'): continue
        for f in sorted(os.listdir(os.path.join(resdir, d))):
            z.write(os.path.join(resdir, d, f), f'res/{d}/{f}')
    adir = os.path.join(PROJ, 'root', 'assets')
    for base, _, files in os.walk(adir):
        for f in sorted(files):
            p = os.path.join(base, f)
            z.write(p, 'assets/' + os.path.relpath(p, adir))
if os.path.exists(OUT): os.remove(OUT)
subprocess.run(['java', '-jar', BT, 'build-bundle', f'--modules={mod}', f'--output={OUT}'], check=True)
print('AAB:', OUT, os.path.getsize(OUT))
