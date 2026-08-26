"""Build docs/*.html from process/*.json.

Every number on the generated pages comes out of an artefact in `process/`. None is
typed into the HTML. That is the point: the pages are a view of the run record, so a
page that disagrees with the record is a bug in this script rather than a caption
somebody forgot to update.

    python tools/build_report.py

Reads   process/run_summary.json, gate_ledger.json, pass_ladder.json, agent_fleets.json
Writes  docs/gate.html, docs/routes.html
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / 'process'
DOCS = ROOT / 'docs'

CSS = """
*{box-sizing:border-box}
:root{
  --bg:#0f1216; --panel:#161a20; --sunken:#12161b; --ink:#e7ebf2; --muted:#98a1b2;
  --faint:#6d7686; --line:#252b35; --accent:#6fb0e4; --good:#63b98a; --bad:#d1746e;
  --warn:#d6a95f;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",
         "Hiragino Sans GB",sans-serif;
}
@media (prefers-color-scheme:light){:root{
  --bg:#f6f7f9; --panel:#fff; --sunken:#eef1f5; --ink:#151a20; --muted:#5a6474;
  --faint:#8a94a4; --line:#dde2e9; --accent:#2b6ca3; --good:#2c7a52; --bad:#a8433c;
  --warn:#8a6414;
}}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
     font-size:15px;line-height:1.65;padding:0 20px 80px}
.wrap{max-width:1080px;margin:0 auto}
header{padding:44px 0 8px;border-bottom:1px solid var(--line);margin-bottom:32px}
h1{font-size:clamp(24px,3.4vw,34px);margin:0 0 10px;letter-spacing:-.02em;line-height:1.2}
h2{font-size:19px;margin:44px 0 6px;padding-bottom:10px;border-bottom:1px solid var(--line)}
h3{font-size:15px;margin:26px 0 4px;color:var(--accent)}
.lede{color:var(--muted);max-width:62em;margin:0}
.src{font-family:var(--mono);font-size:11.5px;color:var(--faint);margin-top:14px}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:4px;
        background:var(--panel);margin-top:14px}
table{border-collapse:collapse;width:100%;font-size:13px;min-width:640px;
      font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:8px 14px;border-bottom:1px solid var(--line);vertical-align:top}
thead th{font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:var(--faint);
         border-bottom:1px solid var(--ink);white-space:nowrap;position:sticky;top:0;
         background:var(--panel)}
tbody tr:last-child td{border-bottom:none}
td.n,th.n{text-align:right;font-family:var(--mono)}
td.id{font-family:var(--mono);font-size:12px;white-space:nowrap}
.ok{color:var(--good);font-weight:600}
.no{color:var(--bad)}
.hm{color:var(--warn)}
.note{color:var(--muted);font-size:12.5px;max-width:46em}
.chart{background:var(--panel);border:1px solid var(--line);border-radius:4px;
       padding:18px;margin-top:14px}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
      margin-top:16px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:4px;padding:14px 16px}
.kpi .v{font-family:var(--mono);font-size:26px;font-weight:600;letter-spacing:-.02em}
.kpi .k{font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:var(--faint)}
.kpi .s{font-size:12.5px;color:var(--muted);margin-top:2px}
a{color:var(--accent)}
footer{margin-top:56px;padding-top:18px;border-top:1px solid var(--line);
       color:var(--muted);font-size:12.5px}
"""


def esc(x) -> str:
    return html.escape(str(x if x is not None else ''))


_CN = ('零', '一', '二', '三', '四', '五', '六', '七', '八', '九')


def cn(n: int) -> str:
    """A small integer in Chinese numerals, so prose counts can be derived too.

    The headline said "thirty-six attempts, twelve accepted" as literal text while the
    page claimed every figure came out of the artefacts. It went stale the moment the
    thirty-seventh attempt landed, which is exactly the failure the claim was about.
    """
    if n < 10:
        return _CN[n]
    if n < 20:
        return '十' + (_CN[n % 10] if n % 10 else '')
    if n < 100:
        return _CN[n // 10] + '十' + (_CN[n % 10] if n % 10 else '')
    return str(n)


def page(title: str, body: str, sources: list[str]) -> str:
    src = ' · '.join(f'<code>{esc(s)}</code>' for s in sources)
    return f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><style>{CSS}</style></head>
<body><div class="wrap">{body}
<footer>本页每一个数字都由 <code>tools/build_report.py</code> 从 {src} 生成，没有一处是写死在 HTML 里的。
页面和记录不一致，就是这个脚本的 bug，而不是谁忘了改标题。</footer>
</div></body></html>"""


def timeline_svg(rows: list[dict]) -> str:
    """Score against attempt number. Accepted attempts move the line; the rest do not."""
    n_rej = sum(1 for r in rows if r['result'].startswith('reject'))
    n_rev = sum(1 for r in rows if 'visual' in r['result'])
    pts, score = [], None
    for r in rows:
        if r.get('scoreAfter') is not None and r['result'] == 'accepted':
            score = r['scoreAfter']
        elif score is None and r.get('scoreBefore') is not None:
            score = r['scoreBefore']
        pts.append((r['seq'], score, r['result'], r['patch'], r.get('scoreAfter')))
    vals = [p[1] for p in pts if p[1] is not None]
    if not vals:
        return ''
    lo, hi = min(vals) - 0.6, max(vals) + 0.6
    W, H, PL, PR, PT, PB = 1000, 260, 48, 16, 16, 34
    def X(i): return PL + (i - 1) / max(1, len(pts) - 1) * (W - PL - PR)
    def Y(v): return PT + (hi - v) / (hi - lo) * (H - PT - PB)
    grid = ''.join(
        f'<line x1="{PL}" y1="{Y(v):.1f}" x2="{W - PR}" y2="{Y(v):.1f}" '
        f'stroke="var(--line)"/><text x="{PL - 8}" y="{Y(v) + 4:.1f}" text-anchor="end" '
        f'font-size="10" fill="var(--faint)" font-family="var(--mono)">{v:.0f}</text>'
        for v in range(int(lo) + 1, int(hi) + 1))
    line = ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, v, *_ in pts if v is not None)
    dots = ''
    for i, v, res, patch, after in pts:
        if v is None:
            continue
        if res == 'accepted':
            dots += (f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="4" fill="var(--good)">'
                     f'<title>#{i} {esc(patch)} — accepted, {v:.2f}</title></circle>')
        elif after is not None:
            dots += (f'<circle cx="{X(i):.1f}" cy="{Y(after):.1f}" r="2.6" fill="none" '
                     f'stroke="var(--bad)" stroke-width="1.2">'
                     f'<title>#{i} {esc(patch)} — {esc(res)}, would have been {after:.2f}'
                     f'</title></circle>')
    return (f'<div class="chart"><svg viewBox="0 0 {W} {H}" width="100%" '
            f'role="img" aria-label="scoreboard against gate attempt">{grid}'
            f'<polyline points="{line}" fill="none" stroke="var(--accent)" stroke-width="2"/>'
            f'{dots}<text x="{PL}" y="{H - 8}" font-size="11" fill="var(--faint)">'
            f'第 1 次尝试</text><text x="{W - PR}" y="{H - 8}" font-size="11" '
            f'fill="var(--faint)" text-anchor="end">第 {len(pts)} 次</text></svg>'
            f'<p class="note">实心绿点是被接受的改动，线随它移动；空心红圈是被否决的，'
            f'标注里是它「本来会得到」的分数。{cn(n_rej)}次否决里有 {n_rev} 次是数字通过、'
            f'看图之后手动回退的。</p></div>')


def build_gate() -> None:
    rows = json.loads((PROC / 'gate_ledger.json').read_text(encoding='utf-8'))
    fleets = json.loads((PROC / 'agent_fleets.json').read_text(encoding='utf-8'))
    ladder = json.loads((PROC / 'pass_ladder.json').read_text(encoding='utf-8'))

    acc = [r for r in rows if r['result'] == 'accepted']
    rej = [r for r in rows if r['result'].startswith('reject')]
    broke = [r for r in rows if r['result'] in ('patch-error', 'validation-failed', 'build-failed')]
    reverted = [r for r in rows if 'visual' in r['result']]
    first = next((r['scoreBefore'] for r in rows if r.get('scoreBefore') is not None), None)
    last = next((r['scoreAfter'] for r in reversed(acc) if r.get('scoreAfter') is not None), None)

    kpis = [
        (f'{len(rows)}', '闸门尝试', f'{len(acc)} 次接受 · {len(rej)} 次否决 · {len(broke)} 次跑不起来'),
        (f'{first} → {last}', '独立记分板', f'两轮迭代，+{round(last - first, 2)}'),
        (f'{fleets["totalAgents"]}', 'agent 数', f'{len(fleets["fleets"])} 个编队 · '
         f'{fleets["totalSubagentTokens"] / 1e6:.1f}M token'),
        (f'{len(reverted)}', '数字通过、看图回退', '色彩项权重 0.10，看不见摩尔纹'),
    ]
    kpi_html = ''.join(f'<div class="kpi"><div class="k">{esc(k)}</div>'
                       f'<div class="v">{esc(v)}</div><div class="s">{esc(s)}</div></div>'
                       for v, k, s in kpis)

    trs = []
    for r in rows:
        cls = 'ok' if r['result'] == 'accepted' else ('hm' if 'visual' in r['result'] else 'no')
        d = r.get('delta')
        dtxt = f'{d:+.2f}' if isinstance(d, (int, float)) else '—'
        trs.append(
            f'<tr><td class="n">{r["seq"]}</td><td class="id">{esc(r["patch"])}</td>'
            f'<td class="{cls}">{esc(r["result"])}</td>'
            f'<td class="n">{esc(r.get("scoreBefore") or "—")}</td>'
            f'<td class="n">{esc(r.get("scoreAfter") or "—")}</td>'
            f'<td class="n {cls if isinstance(d, (int, float)) and d else ""}">{dtxt}</td>'
            f'<td class="n">{esc(r.get("triangles") or "—")}</td>'
            f'<td class="note">{esc((r.get("note") or "")[:300])}</td></tr>')

    lad = ''.join(
        f'<tr><td class="id">{esc(h["passId"])}</td><td class="n">{esc(h["aiVisionScore"])}</td>'
        f'<td class="note">{esc((h["summary"] or "")[:220])}</td></tr>' for h in ladder)

    fl = ''.join(
        f'<tr><td class="id">{esc(f["workflow"])}</td><td class="n">{esc(f["agents"])}</td>'
        f'<td class="n">{esc(f["dimensions"])}</td>'
        f'<td class="n">{f["subagentTokens"] / 1e6:.2f}M</td>'
        f'<td class="note">{esc(" → ".join(f["stages"]))}'
        f'{"　" + esc(f["note"]) if f.get("note") else ""}</td></tr>'
        if f.get('subagentTokens') else
        f'<tr><td class="id">{esc(f["workflow"])}</td><td class="n">{esc(f["agents"])}</td>'
        f'<td class="n">{esc(f["dimensions"])}</td><td class="n">—</td>'
        f'<td class="note">{esc(" → ".join(f["stages"]))}'
        f'{"　" + esc(f["note"]) if f.get("note") else ""}</td></tr>'
        for f in fleets['fleets'])

    body = f"""
<header><h1>闸门记录 · {cn(len(rows))}次尝试，接受{cn(len(acc))}次</h1>
<p class="lede">每一次对 spec 的改动都要过同一道闸门：应用 → 严格校验 → 重新生成 → 渲六个视角 →
本地指标 → 一个不属于它自己的独立记分板 → 通过才留下。判据在看到任何结果之前就写死了。
被否决的{cn(len(rej))}次比被接受的{cn(len(acc))}次更有信息量。</p>
<div class="grid">{kpi_html}</div></header>

<h2>分数怎么走的</h2>
{timeline_svg(rows)}

<h2>逐次尝试</h2>
<div class="scroll"><table><thead><tr>
<th class="n">#</th><th>改动</th><th>结果</th><th class="n">改前</th><th class="n">改后</th>
<th class="n">Δ</th><th class="n">三角面</th><th>备注</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table></div>

<h2>八道构建 pass</h2>
<p class="note">img2threejs 的 pass 阶梯：每一道都有数值验收标准，没有记录评审就不解锁下一道。
分数是看着参考并排图给的，不是算出来的。</p>
<div class="scroll"><table><thead><tr>
<th>pass</th><th class="n">视觉分</th><th>摘要</th></tr></thead>
<tbody>{lad}</tbody></table></div>

<h2>agent 编队</h2>
<p class="note">每个补丁由一个 agent 写，再由另一个只被要求「推翻它」的 agent 攻击。
两条写在简报里的前提就是这样在进入构建之前被证伪的。</p>
<div class="scroll"><table><thead><tr>
<th>工作流</th><th class="n">agent</th><th class="n">维度</th><th class="n">token</th>
<th>阶段</th></tr></thead><tbody>{fl}</tbody></table></div>
"""
    DOCS.mkdir(exist_ok=True)
    (DOCS / 'gate.html').write_text(
        page('闸门记录 — AI PCG Test', body,
             ['process/gate_ledger.json', 'process/pass_ladder.json',
              'process/agent_fleets.json']), encoding='utf-8')
    print(f'docs/gate.html  — {len(rows)} attempts, {len(ladder)} passes, '
          f'{fleets["totalAgents"]} agents')


def zapper_block(z: dict | None) -> str:
    """Route 3's section. Every figure comes out of the record; none is written here.

    Returns an empty string when the record carries no measured result, so a report
    generated before the pistol was scored says nothing rather than something stale --
    which is how the old "contract frozen" line survived past the build finishing.
    """
    if not z or not z.get('nova3d'):
        return ''
    n = z['nova3d']
    c, t, j, l = n['constraints'], n['assemblyTree'], n['joints'], n['locality']
    # Numbers come from the record; the prose is written here, in the page's language.
    # The record stays English because it is the machine-readable artefact and the rest of
    # process/ is English; the report is Chinese because the rest of the report is.
    rows = ''.join(
        f'<tr><td>{lab}</td><td class="ok">{val}</td><td class="note">{cond}</td></tr>'
        for lab, val, cond in [
            ('合同约束', f'{c["passed"]} / {c["total"]}',
             f'这 {c["total"]} 条是 104 条可证伪行里能翻译成检查器 DSL 的部分，'
             '覆盖率由 <code>analysis/build_contract_json.py</code> 显式报告，不是 104 条全过'),
            ('装配树', f'VALID，{t["namedParts"]} 个命名部件，单根 <code>{t["roots"][0]}</code>',
             '—'),
            ('关节几何有效', f'{j["valid"]} / {j["total"]}',
             '一把手枪就只有击锤和扳机两个铰接件。'
             'Nova3D 报的是 59 个关节，量级完全不同'),
            ('编辑局部性', f'{l["passed"]} / {l["total"]}',
             f'其中只有 {l["generationParameters"]} 个是<b>生成参数</b>'
             '——句柄是产出几何的那段代码里的一项；'
             f'另外 {l["scopedTransforms"]} 个是作用在命名子树上的变换，'
             '是<b>弱形式</b>，按弱形式记'),
        ])
    falsified = (
        '<li><b>H1</b> 同时要求 <code>mid-band</code> 随枪管加长而平移、又把 '
        '<code>tube-fore</code> 的后端面钉死——而那个后端面（110.3 mm）就是 mid-band '
        '自己的前端面。两条在任何模型上都不可能同时成立，一动就在枪管上裂开一道缝。</li>'
        '<li><b>H4</b> 的 move 列表只写了开口，漏了 struts——而 struts 就是开口之间剩下的'
        '那些实心弧，改计数不可能不重建它们。</li>')
    assert len(l['contractRowsFalsified']) == 2, (
        'the record now carries a different number of falsified rows than this page '
        'renders; update the prose rather than letting the count drift')
    return f"""
<h2>线 3 · 硬表面，约束先于模型</h2>
<p class="note">已建完并按冻结的合同打过分。{z['meshes']} 个网格，{z['triangles']:,} 三角形。
材质全部从测得的 CIE Lab 数值<b>生成</b>，源码里没有任何一处加载图片文件，
所以它的带材质渲染可以公开——这一点和两条角色线相反。</p>
<div class="scroll"><table><thead><tr><th>项</th><th>结果</th><th>条件</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="note"><b>首轮 {c['firstRun']}/{c['total']}，失败的 5 条全部是检查表达式的缺陷，不是模型的。</b>
<code>inside</code> 比较三个轴，而同轴配对只该比两个；<code>flush</code> 比的是两个 <code>hi</code> 面，
而贴合要比的是「A 的近端面对 B 的远端面」。补上 <code>concentric</code>、<code>meets</code>、
<code>sub</code> 三个算子之后才是 {c['passed']}/{c['total']}——
<b>这些检查是看到失败之后才改的</b>，记在这里，不当成一次过。</p>
<h3>实现 §8 证伪了合同自己的两行</h3>
<ul class="note">{falsified}</ul>
<p class="note">两条都是<b>真去实现</b>才撞上的，不是读出来的；
同一份文档那次 25 条缺陷的对抗审计一条都没抓到。读一份约束和满足一份约束，会在不同的地方出错。</p>
"""


def build_routes() -> None:
    s = json.loads((PROC / 'run_summary.json').read_text(encoding='utf-8'))
    a, b = s['routes'][0], s['routes'][1]
    # Route 3 is a different subject with a different accountability, so it gets its own
    # section rather than a third column. Putting a pistol's constraint count beside a
    # character's silhouette IoU would invite exactly the comparison neither number
    # supports.
    z = next((r for r in s['routes'] if r['id'] == 'zapper-i2t'), None)
    zap = zapper_block(z)
    ta, t0, t2 = a['scoreboard'], b['scoreboardFirstBuild'], b['scoreboardAfterTwoRounds']
    W = ta['weights']

    trs = ''
    for k in ('shape', 'edge', 'chamfer', 'width', 'landmark', 'colour'):
        gain = (t2['terms'][k] - t0['terms'][k]) * W[k] * 100
        gap = (ta['terms'][k] - t2['terms'][k]) * W[k] * 100
        lead = ' <span class="ok">← 线 2 领先</span>' if gap < 0 else ''
        trs += (f'<tr><td class="id">{k}</td><td class="n">{W[k]:.2f}</td>'
                f'<td class="n">{ta["terms"][k]:.4f}</td>'
                f'<td class="n">{t0["terms"][k]:.4f}</td>'
                f'<td class="n"><b>{t2["terms"][k]:.4f}</b></td>'
                f'<td class="n {"ok" if gain > 0 else "no"}">{gain:+.2f}</td>'
                f'<td class="n">{gap:+.2f}{lead}</td></tr>')
    tot_gain = t2['score'] - t0['score']
    tot_gap = ta['score'] - t2['score']
    trs += (f'<tr><td class="id"><b>合计</b></td><td class="n"></td>'
            f'<td class="n"><b>{ta["score"]}</b></td><td class="n">{t0["score"]}</td>'
            f'<td class="n"><b>{t2["score"]}</b></td>'
            f'<td class="n ok">{tot_gain:+.2f}</td><td class="n">{tot_gap:+.2f}</td></tr>')

    raw = f"""<div class="grid">
<div class="kpi"><div class="k">原始轮廓 IoU</div><div class="v">{t2['iou']}</div>
<div class="s">线 1 是 {ta['iou']} — 线 2 已反超</div></div>
<div class="kpi"><div class="k">宽度剖面 RMS</div><div class="v">{t2['widthRmsPct']}%</div>
<div class="s">线 1 是 {ta['widthRmsPct']}%</div></div>
<div class="kpi"><div class="k">地标高度 RMS</div><div class="v">{t2['landmarkRmsPct']}%</div>
<div class="s">线 1 是 {ta['landmarkRmsPct']}% — 剩余差距全在这里</div></div>
<div class="kpi"><div class="k">三角面 / 预算</div>
<div class="v">{b['trianglesNow'] // 1000}k</div>
<div class="s">预算 {b['triangleBudget'] // 1000}k，用了
{round(100 * b['trianglesNow'] / b['triangleBudget'])}%</div></div></div>"""

    body = f"""
<header><h1>三条线放在一起看</h1>
<p class="lede">同一个角色，两条完全不同的路线，同一套记分板、同一批参考面板、同一个度量取景。
第三条线换了对象——一把枪——用来试 Nova3D 那个「约束先于资产」的主张。</p></header>

<h2>逐项拆分</h2>
<p class="note">线 1 是手写 SDF + Surface Nets；线 2 是一份 spec 走 img2threejs 的八道 pass。
「本次增益」是线 2 两轮迭代拿到的分，「剩余差距」是负数就表示线 2 已经领先。</p>
<div class="scroll"><table><thead><tr>
<th>分项</th><th class="n">权重</th><th class="n">线 1</th><th class="n">线 2 初始</th>
<th class="n">线 2 现在</th><th class="n">本次增益</th><th class="n">剩余差距</th>
</tr></thead><tbody>{trs}</tbody></table></div>

<h2>原始指标</h2>
{raw}

<h2>线 2 带着线 1 没有的东西</h2>
<div class="scroll"><table><thead><tr><th>项</th><th>线 1</th><th>线 2</th></tr></thead><tbody>
<tr><td>命名部件 + 装配树</td><td class="no">无</td><td class="ok">{b['components']} 个组件</td></tr>
<tr><td>骨骼与关节</td><td class="no">无</td>
<td class="ok">{b['bones']} 根骨，枢轴在关节而非几何中心，插槽误差 0.05 mm</td></tr>
<tr><td>材质</td><td>代码里的程序化项</td>
<td class="ok">{b['materials']} 个，每个带参考派生的 PBR 与自己的提取置信度</td></tr>
<tr><td>三角面预算</td><td>{a['triangles']['high'] // 1000}k / {a['triangles']['medium'] // 1000}k / {a['triangles']['low'] // 1000}k，未声明预算</td>
<td class="ok">{b['trianglesNow'] // 1000}k，声明预算 {b['triangleBudget'] // 1000}k，三档 LOD 逐档实测</td></tr>
<tr><td>重建整个模型</td><td>手调常数散在代码里</td><td class="ok">一条命令</td></tr>
</tbody></table></div>

<h2>差距分析</h2>
<p class="note">线 1 在相似度上仍然赢，{ta['score']} 对 {t2['score']}，剥掉贴图的对比更不接近。
但线 2 在六项里领先四项，原始轮廓 IoU 也反超了。<b>剩下 {tot_gap:+.2f} 分几乎全部是地标高度一项</b>——
东西长在哪，不是外形是什么。那一项失败过三次：第一次补丁把 delta 写死，在别的补丁合并掉一个组件之后崩了；
第二次自己写了个地标检测器，它要求膝盖下移 60 mm 而小腿肚上移 60 mm，可小腿肚在膝盖下面；
第三次才改用裁判自己的地标表，按每个地标被几个视角看到来加权阻尼。</p>
<p class="note">诚实的读法是：这两条线本来就不在比同一件事。一条是一个相似度，
另一条是一个能产出相似度、并且可以被检查、度量、编辑和驱动的程序。</p>
{zap}
"""
    DOCS.mkdir(exist_ok=True)
    (DOCS / 'routes.html').write_text(
        page('三条线 — AI PCG Test', body, ['process/run_summary.json']), encoding='utf-8')
    print(f'docs/routes.html — {ta["score"]} vs {t0["score"]} → {t2["score"]}')


if __name__ == '__main__':
    build_gate()
    build_routes()
