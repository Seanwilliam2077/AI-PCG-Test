"""boots: patch spec/parts/boots.json in place with key=value pairs.

    python out/boots_ab.py splay=0.0 cuffOutset=0.03
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "spec", "parts", "boots.json")
s = open(p, encoding="utf-8").read()
for arg in sys.argv[1:]:
    k, v = arg.split("=")
    pat = re.compile(r'("%s"\s*:\s*)(-?[0-9.eE+-]+)' % re.escape(k))
    if not pat.search(s):
        raise SystemExit("key not found: " + k)
    s = pat.sub(lambda m: m.group(1) + v, s, count=1)
    print("  %-16s -> %s" % (k, v))
json.loads(s)
open(p, "w", encoding="utf-8").write(s)
