"""给每日总结数据补结构(build.py 调用;只用标准库)。

- 个股 / 对人 / 操作 / 账户 这几节的每一行:拆成「名称 + 内容」(b['ents']),名称认得出就带上标的键(key)
- 变化:拆成 之前 → 今天(b['chg'])
- 老毛病:拆成 像 / 不像 + 编号(b['mis'])
- 个股档案:把所有带 key 的条目和预设按标的汇总(data['tickers'])
解析不了的行原样保留,网页按普通文字显示。别名表 ALIAS:新标的认不出时在这里加。
"""
import re

# 标的键 → (显示名, 别名)。别名不分大小写;认不出、但长得像代码(2–5 个大写字母)的也单独成一个标的。
ALIAS = {
    '大盘': ('大盘 · 纳指/标普', ['大盘', '纳指', '标普', '纳指/标普', '指数', 'NQ', 'MNQ', 'QQQ', 'SPY', 'SQQQ', 'TQQQ',
                             'NDX', 'SPX', '大盘策略', '大盘定性', 'UNKNOWN']),
    '半导体': ('半导体 · SOXX/SOXL/SOXS', ['半导体', '晶片', 'SOXX', 'SOXL', 'SOXS', 'SMH']),
    '存储': ('存储', ['存储']),
    '波动率': ('波动率 · UVXY/VIX', ['UVXY', 'VIX', 'VIXY', 'UVXY/VIX']),
    '黄金': ('黄金 · GLD', ['黄金', 'GLD', 'GLD/黄金']),
    '比特币': ('比特币 · BTC', ['比特币', 'BTC', 'IBIT']),
    '软件': ('软件 · IGV', ['软件', '软件股', 'IGV', 'SaaS']),
    '小盘股': ('小盘股 · IWM', ['小盘股', '小盘', '罗素', 'IWM', 'TZA', 'TNA']),
    '原油': ('原油', ['原油', '油', 'USO']),
    '美债': ('美债 · TLT', ['美债', 'TLT', '国债']),
    '美元': ('美元', ['美元', 'DXY']),
    '新能源': ('新能源', ['新能源']),
    'Mega7': ('Mega7', ['Mega7', 'Mega 7', 'MAGS']),
    'NVDA': ('英伟达 NVDA', ['英伟达', 'NVDA']),
    'TSLA': ('特斯拉 TSLA', ['特斯拉', 'TSLA', 'TSLL']),
    'AAPL': ('苹果 AAPL', ['苹果', 'AAPL']),
    'MSFT': ('微软 MSFT', ['微软', 'MSFT']),
    'AMZN': ('亚马逊 AMZN', ['亚马逊', 'AMZN']),
    'GOOGL': ('谷歌 GOOGL', ['谷歌', 'GOOGL', 'GOOG']),
    'META': ('Meta META', ['Meta', 'Facebook']),
    'INTC': ('英特尔 INTC', ['英特尔', 'INTC']),
    'TSM': ('台积电 TSM', ['台积电', 'TSM']),
    'MU': ('美光 MU', ['美光', 'MU']),
    'SNDK': ('闪迪 SNDK', ['闪迪', 'SNDK']),
    'STX': ('希捷 STX', ['希捷', 'STX']),
    'MRVL': ('Marvell MRVL', ['Marvell', 'MRVL']),
    'AVGO': ('博通 AVGO', ['博通', 'AVGO']),
    'LRCX': ('泛林 LRCX', ['泛林', 'LRCX']),
    'BA': ('波音 BA', ['波音', '播音']),
    'ADBE': ('Adobe ADBE', ['Adobe', '阿多比']),
    'CRM': ('Salesforce CRM', ['Salesforce']),
    'SPOT': ('Spotify SPOT', ['Spotify']),
    'HOOD': ('Robinhood HOOD', ['Robinhood']),
    'COIN': ('Coinbase COIN', ['Coinbase']),
    'CRCL': ('Circle CRCL', ['Circle']),
    'CRWV': ('CoreWeave CRWV', ['CoreWeave']),
    'SHOP': ('Shopify SHOP', ['Shopify']),
    'UBER': ('Uber', ['Uber']),
    'BRK.B': ('伯克希尔 BRK.B', ['伯克希尔', 'BRKB']),
    'SpaceX': ('SpaceX', ['SpaceX']),
    '中芯国际': ('中芯国际', ['中芯国际']),
    'BABA': ('阿里 BABA', ['阿里', '阿里巴巴']),
    '腾讯': ('腾讯', ['腾讯']),
}
STOP = {'AI', 'ETF', 'FOMC', 'CPI', 'PPI', 'QE', 'QT', 'IPO', 'LEAPS', 'EMA', 'ATR', 'VIP', 'CEO', 'GDP', 'PCE', 'CME',
        'IRA', 'IB', 'TD', 'OK', 'DJ', 'PC', 'APP', 'UNKNOWN2'}
TICKER = re.compile(r'[A-Z]{2,5}(?:\.[A-Z])?')
LOOK = {}
for k, (_, al) in ALIAS.items():
    for a in [k] + al:
        LOOK[a.casefold()] = k
RID = re.compile(r'(?<![A-Za-z0-9])([A-Z]{1,2}\d{1,3})(?!\d)')
STANCE = {'看多': '看多', '看涨': '看多', '偏多': '偏多', '观望': '观望', '中性': '观望', '没表态': '没表态',
          '偏空': '偏空', '看空': '看空', '看跌': '看空', '不碰': '不碰'}
STANCE_RX = re.compile(r'^(看多|看涨|偏多|观望|中性|没表态|偏空|看空|看跌|不碰)\s*[;;,,。]\s*')
BOLD = re.compile(r'\*\*([^*]{1,40})\*\*')
HEAD = re.compile(r'^\*\*([^*]+)\*\*[::]\s*(.*)$', re.S)


def lookup(name):
    name = name.strip()
    k = LOOK.get(name.casefold())
    if k:
        return k
    return name if TICKER.fullmatch(name) and name not in STOP else None


def keys_of(name):
    """「Adobe(改口)」「闪迪(SNDK)」「SOXS 买入」「半导体 / SOXS」「CRWV→NBIS(改口)」→ (标的键们, 括号标签, 动作)。"""
    raw, tag, extra, action = name.strip(), '', [], ''
    m = re.match(r'^(.*?)\s*[((]([^()()]*)[))]\s*$', raw)
    if m:
        raw, tag = m[1].strip(), m[2].strip()
        if TICKER.fullmatch(tag):
            extra.append(tag)
            tag = ''
    keys = []
    for p in [x for x in re.split(r'\s*(?:/|、|,|,|\svs\s|→|和)\s*', raw) if x.strip()] + extra:
        k = lookup(p)
        if not k and ' ' in p.strip():
            first, rest = p.strip().split(' ', 1)
            k = lookup(first)
            if k:
                action = action or rest.strip()
        if k and k not in keys:
            keys.append(k)
    return keys, tag, action


def segments(md):
    """一行里的「**名称**:内容。**名称2**「原话」……」拆成 [(名称, 内容)];不是以 **名称** 开头的行返回 None。"""
    starts = [m for m in BOLD.finditer(md) if m.start() == 0 or re.search(r'[。;;]\s*$', md[:m.start()])]
    if not starts or starts[0].start() != 0:
        return None
    out = []
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(md)
        text = re.sub(r'^[::]\s*', '', md[m.end():end].strip())
        out.append((m[1].strip(), re.sub(r'[;;]\s*$', '', text)))  # 按「;」切开后,段尾的分号去掉
    return out


def split_arrow(s):
    """在第一个不在「」里的 → 处切开。"""
    depth = 0
    for i, ch in enumerate(s):
        if ch == '「':
            depth += 1
        elif ch == '」':
            depth = max(0, depth - 1)
        elif ch == '→' and depth == 0:
            return s[:i].strip(), s[i + 1:].strip()
    return None


def enrich(data):
    days = data['days']
    mentions = {}

    def add(key, rec):
        mentions.setdefault(key, []).append(rec)

    for d in days:
        for s in d['sections']:
            kind = s['kind']
            groups = [(None, s['blocks'])] + [(u['title'], u['blocks']) for u in s['subs']]
            for gtitle, blocks in groups:
                grp = gtitle or ''
                for b in blocks:
                    md = b['md']
                    if kind == 'trades' and b['t'] == 'p' and re.fullmatch(r'\*\*[^*]+\*\*[::]?', md):
                        grp = md.strip('*::')  # 「他自己做的」「给听众(不算他的操作)」这类小标题
                        continue
                    if kind in ('assets', 'people', 'trades', 'account') and b['t'] == 'li':
                        segs = segments(md)
                        if segs:
                            ents = []
                            for name, text in segs:
                                keys, tag, action = keys_of(name) if kind != 'people' else ([], '', '')
                                ent = {'name': name, 'keys': keys, 'md': text}
                                st = STANCE_RX.match(text) if kind == 'assets' else None
                                if st:  # 新写法:立场放最前面(看多;理由…),网页按它上色
                                    ent['stance'], ent['md'] = STANCE[st[1]], text[st.end():]
                                ents.append(ent)
                                for k in keys:
                                    add(k, {'date': d['date'], 'sn': s['n'], 'kind': kind, 'grp': grp,
                                            'name': name, 'md': text, 'id': None})
                            b['ents'] = ents
                        elif kind == 'trades':  # 旧格式:「ADBE 继续持有…」「NQ 空单(大账户)…」,从行首认标的,只进档案
                            m = re.match(r'^(?:明确不买[::])?\s*([A-Za-z][A-Za-z.]{1,6}|[一-鿿]{2,4})', md)
                            k = lookup(m[1]) if m else None
                            if k:
                                add(k, {'date': d['date'], 'sn': s['n'], 'kind': kind, 'grp': grp, 'name': '', 'md': md, 'id': None})
                    elif kind == 'changes' and b['t'] == 'li':
                        m = HEAD.match(md)
                        if m:
                            topic, rest = m[1].strip(), m[2]
                            keys, tag, _ = keys_of(topic)
                            t = re.match(r'^(.*?)\s*[((]([^()()]*)[))]\s*$', topic)
                            name = t[1] if t else topic
                            tag = t[2] if t else ''
                            ba = split_arrow(rest)
                            chg = {'topic': name, 'tag': tag, 'keys': keys}
                            if ba:
                                before, after = ba
                                w = re.match(r'^(\d{2}-\d{2})\s*', before)
                                chg.update(when=w[1] if w else '', before=before[w.end():] if w else before, after=after)
                            else:
                                chg['same'] = rest
                            b['chg'] = chg
                            for k in keys:
                                add(k, {'date': d['date'], 'sn': s['n'], 'kind': 'changes', 'grp': tag,
                                        'name': topic, 'md': rest, 'id': None})
                    elif kind == 'mistakes' and b['t'] == 'li':
                        m = HEAD.match(md) or re.match(r'^((?:像|不像)\s*[A-Z]\d{1,3}(?:[((][^()()]*[))])?)[::]\s*(.*)$', md, re.S)
                        if m:
                            label, text = m[1].strip(), m[2]
                            mk = '不像' if label.startswith(('不像', '没犯', '没有')) else '像' if label.startswith('像') else ''
                            ids = RID.findall(label) or (RID.findall(text) if mk == '不像' else [])
                            b['mis'] = {'kind': mk, 'label': label, 'ids': ids, 'md': text}

    # 预设也按标的归(组合标的拆开;UNKNOWN 归大盘)
    pre = {}
    for p in data.get('presets', []):
        for tok in (p.get('ticker') or 'UNKNOWN').split('/'):
            k = lookup(tok)
            if k:
                pre.setdefault(k, [])
                if p['preset_id'] not in pre[k]:
                    pre[k].append(p['preset_id'])
    tickers = []
    for k in set(mentions) | set(pre):
        items = mentions.get(k, [])
        dates = sorted({i['date'] for i in items} | {p['first'] for p in data['presets'] if p['preset_id'] in pre.get(k, [])})
        tickers.append({'key': k, 'name': ALIAS.get(k, (k,))[0], 'items': items, 'presets': pre.get(k, []),
                        'dates': dates, 'last': dates[-1] if dates else ''})
    tickers.sort(key=lambda t: t['key'])
    tickers.sort(key=lambda t: t['last'], reverse=True)  # 同样场次数时,最近提到的在前
    tickers.sort(key=lambda t: -len(t['dates']))         # 出现场次多的在前
    data['tickers'] = tickers
    return data
