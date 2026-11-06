"""brant-site:每日直播总结 + 心路历程文章 → 单文件网页(只用 Python 标准库)。

用法:
  python build.py                  同步 ../brant-lens/export/daily.json 到 content/daily.json,
                                   读 content/essays/*.md,生成 dist/index.html
  python build.py --data 路径.json  从别处同步每日总结数据(也可设环境变量 BRANT_DAILY_JSON)
  python build.py --sample         用 sample/daily.sample.json(虚构示例),不带文章
  python build.py --out 路径.html   指定输出位置

content/ 进 git(本仓库公开,网页由 GitHub Actions 发布到 Pages);dist/ 是生成结果,不进 git。
找不到 brant-lens 的导出时,直接用 content/daily.json 里上次同步的版本。数据格式见 README。
"""
import argparse
import html
import json
import os
import re
import shutil
import sys
from pathlib import Path

from enrich import enrich  # 每日总结各节拆结构 + 个股档案

ROOT = Path(__file__).resolve().parent
TPL = ROOT / 'templates' / 'daily.html'
CONTENT = ROOT / 'content'
DAILY = CONTENT / 'daily.json'
ESSAYS = CONTENT / 'essays'
SAMPLE = ROOT / 'sample' / 'daily.sample.json'
UPSTREAM = Path(os.environ.get('BRANT_DAILY_JSON') or ROOT.parent / 'brant-lens' / 'export' / 'daily.json')
NEED = ('days', 'presets', 'rules')
SCHEMA = 1

FM = re.compile(r'^---\n(.*?)\n---\n', re.S)
LI = re.compile(r'^(\s*)[-*]\s+(.*)$')
NUM = re.compile(r'^[一二三四五六七八九十]+、\s*')


CHART = re.compile(r'^\{\{chart\s+([\w-]+)\}\}$')


def block(line):
    """一行 → 一个块:- 列表;> 「原话」[[出处]] 是引文块,> 其他是提示框;{{chart 名字}} 是图表(数据在同名 .json)。"""
    m = LI.match(line.rstrip())
    if m:
        return {'t': 'li', 'lvl': len(m[1].expandtabs(2)) // 2, 'md': m[2].strip()}
    s = line.strip()
    if s.startswith('>'):
        body = s[1:].strip()
        return {'t': 'quote' if body.startswith('「') else 'aside', 'md': body}
    m = CHART.match(s)
    if m:
        return {'t': 'chart', 'chart': m[1], 'md': ''}
    return {'t': 'p', 'md': s}


def short(title):
    """节标题 → 导航短名:去掉「一、」,取冒号前那段。"""
    return re.split(r'[::,,]', NUM.sub('', title))[0].strip()[:9]


def essay(p):
    """content/essays/<slug>.md:开头 --- 包住的 title/period/written/summary,正文 ## 节、### 小节、- 列表、段落、> 引文/提示、{{chart}}。"""
    t = p.read_text(encoding='utf-8').replace('\r\n', '\n')
    meta, m = {}, FM.match(t)
    if m:
        for line in m[1].splitlines():
            k, _, v = line.partition(':')
            meta[k.strip()] = v.strip()
        t = t[m.end():]
    secs, cur, sub = [], None, None
    for line in t.splitlines():
        if not line.strip():
            continue
        if line.startswith('## '):
            title = line[3:].strip()
            kind = 'brief' if ('速览' in title or '一句话' in title) else 'timeline' if '时间线' in title else 'essay'
            cur = {'n': len(secs) + 1, 'title': title, 'kind': kind, 'short': short(title), 'blocks': [], 'subs': []}
            secs.append(cur)
            sub = None
        elif line.startswith('### ') and cur:
            sub = {'title': line[4:].strip(), 'blocks': []}
            cur['subs'].append(sub)
        elif cur:
            (sub['blocks'] if sub else cur['blocks']).append(block(line))
    side = p.with_suffix('.json')  # 同名 .json:图表数据 {"charts": {名字: {...}}}
    charts = json.loads(side.read_text(encoding='utf-8')).get('charts', {}) if side.exists() else {}
    body = re.sub(r'\[\[[^\]]*\]\]|\{\{[^}]*\}\}|\*\*|^#+ |^\s*[-*>] ', '', t, flags=re.M)
    chars = len(re.sub(r'\s', '', body))
    return {'slug': p.stem, 'title': meta.get('title') or p.stem, 'period': meta.get('period', ''),
            'written': meta.get('written', ''), 'summary': meta.get('summary', ''),
            'chars': chars, 'mins': max(1, round(chars / 450)), 'quotes': len(re.findall(r'「[^「」]+」', t)),
            'srcs': len(re.findall(r'\[\[[^\]]+\]\]', t)), 'charts': charts, 'sections': secs}


def sync(src):
    """brant-lens 的导出比 content/daily.json 新(内容不同)就拷过来。"""
    if not src.exists():
        return False
    if DAILY.exists() and DAILY.read_bytes() == src.read_bytes():
        return False
    CONTENT.mkdir(exist_ok=True)
    shutil.copyfile(src, DAILY)
    return True


def main():
    sys.stdout.reconfigure(encoding='utf-8')  # Windows 控制台默认 GBK
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data', type=Path, help='从这里同步每日总结数据(brant-lens 导出的 daily.json)')
    ap.add_argument('--sample', action='store_true', help='用虚构示例数据,不带文章')
    ap.add_argument('--out', type=Path, default=ROOT / 'dist' / 'index.html')
    a = ap.parse_args()

    if a.sample:
        src, essays = SAMPLE, []
    else:
        up = a.data or UPSTREAM
        if sync(up):
            print(f'同步了每日总结:{up} → {DAILY.relative_to(ROOT)}')
        elif not up.exists():
            print(f'没找到 {up},用上次同步的 {DAILY.relative_to(ROOT)}')
        src = DAILY
        essays = sorted((essay(p) for p in ESSAYS.glob('*.md')), key=lambda e: (e['period'], e['slug']))
    if not src.exists():
        sys.exit(f'找不到数据 {src}\n先在 brant-lens 跑 export_daily.py,或用 --data 指定、--sample 看示例')
    data = json.loads(src.read_text(encoding='utf-8'))
    miss = [k for k in NEED if k not in data]
    if miss:
        sys.exit(f'{src} 缺字段 {miss},不是 brant-lens 导出的 daily.json')
    if data.get('schema', SCHEMA) != SCHEMA:
        print(f'⚠ 数据 schema={data.get("schema")},本模板按 schema={SCHEMA} 写的,显示可能不全', file=sys.stderr)
    data['essays'] = essays
    enrich(data)

    tpl = TPL.read_text(encoding='utf-8')
    if '/*__DATA__*/' not in tpl:
        sys.exit('模板里没有 /*__DATA__*/ 占位')
    # JSON 里所有 < 写成 <:仍是合法 JSON,且不会提前结束 <script>
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    page = tpl.replace('__TITLE__', html.escape(data.get('title') or '直播总结')).replace('/*__DATA__*/', js)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(page, encoding='utf-8')
    n_open = sum(p.get('status') == '待触发' for p in data['presets'])
    print(f"每日总结 {len(data['days'])} 场 · 心路历程 {len(essays)} 篇 · 预设 {len(data['presets'])} 条(待触发 {n_open})"
          f"\n  网页 {a.out}({len(page.encode()) // 1024} KB,双击打开)")


if __name__ == '__main__':
    main()
