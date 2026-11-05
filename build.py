"""brant-site:把 brant-lens 导出的 daily.json 生成单文件网页(只用 Python 标准库)。

用法:
  python build.py                          读 ../brant-lens/export/daily.json → dist/daily.html
  python build.py --data 路径/daily.json    指定数据文件(也可设环境变量 BRANT_DAILY_JSON)
  python build.py --sample                 用 sample/daily.sample.json(虚构示例,可以公开)
  python build.py --out 路径.html           指定输出位置

dist/daily.html 数据内嵌、离线可用,双击用浏览器打开。
dist/ 不进 git:真实数据是付费直播原话,只能留在本机或加了登录的地方。数据格式见 README「数据约定」。
"""
import argparse
import html
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TPL = ROOT / 'templates' / 'daily.html'
SAMPLE = ROOT / 'sample' / 'daily.sample.json'
DEFAULT = Path(os.environ.get('BRANT_DAILY_JSON') or ROOT.parent / 'brant-lens' / 'export' / 'daily.json')
NEED = ('days', 'presets', 'rules')
SCHEMA = 1


def main():
    sys.stdout.reconfigure(encoding='utf-8')  # Windows 控制台默认 GBK
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data', type=Path, help='daily.json 路径')
    ap.add_argument('--sample', action='store_true', help='用虚构示例数据')
    ap.add_argument('--out', type=Path, default=ROOT / 'dist' / 'daily.html')
    a = ap.parse_args()

    src = SAMPLE if a.sample else (a.data or DEFAULT)
    if not src.exists():
        sys.exit(f'找不到数据 {src}\n先在 brant-lens 跑 export_daily.py,或用 --data 指定、--sample 看示例')
    data = json.loads(src.read_text(encoding='utf-8'))
    miss = [k for k in NEED if k not in data]
    if miss:
        sys.exit(f'{src} 缺字段 {miss},不是 brant-lens 导出的 daily.json')
    if data.get('schema', SCHEMA) != SCHEMA:
        print(f'⚠ 数据 schema={data.get("schema")},本模板按 schema={SCHEMA} 写的,显示可能不全', file=sys.stderr)

    tpl = TPL.read_text(encoding='utf-8')
    if '/*__DATA__*/' not in tpl:
        sys.exit('模板里没有 /*__DATA__*/ 占位')
    # JSON 里所有 < 写成 <:仍是合法 JSON,且不会提前结束 <script>
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    page = tpl.replace('__TITLE__', html.escape(data.get('title') or '直播总结')).replace('/*__DATA__*/', js)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(page, encoding='utf-8')
    n_open = sum(p.get('status') == '待触发' for p in data['presets'])
    print(f"{len(data['days'])} 场 · 预设 {len(data['presets'])} 条(待触发 {n_open})· 理念编号 {len(data['rules'])} 个"
          f"\n  数据 {src}\n  网页 {a.out}({len(page.encode()) // 1024} KB,双击打开)")


if __name__ == '__main__':
    main()
