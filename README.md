# brant-site

每日直播总结的网页。数据由私有项目 brant-lens 导出(`export/daily.json`),这里只负责把它变成好读的网页:按场次读、心法卡片、个股卡片、时间线、预设看板(按标的分组)、全文搜索、明暗主题、手机可读。

> ⚠ 本仓库只放代码和**虚构的示例数据**。真实数据是付费直播的原话,不进这里的 git,也不要部署到不加登录的公开地址(GitHub Pages 即使仓库私有,网站也是公开的)。

## 用法

只用 Python 标准库(3.9+)。

```
python build.py                 # 读 ../brant-lens/export/daily.json → dist/daily.html
python build.py --sample        # 用 sample/daily.sample.json(虚构示例)看效果
python build.py --data 路径.json # 指定数据;也可设环境变量 BRANT_DAILY_JSON
```

生成的 `dist/daily.html` 是单文件、离线可用,双击用浏览器打开。

每日流程(在 brant-lens 里):`build_why_data.py` → `export_daily.py`(导出 json)→ `python ../brant-site/build.py`(生成网页)。

## 目录

| 路径 | 内容 |
|---|---|
| `build.py` | 读 daily.json,嵌进模板,写 `dist/daily.html` |
| `templates/daily.html` | 网页模板(样式 + 脚本都在里面),数据替换 `/*__DATA__*/`,标题替换 `__TITLE__` |
| `sample/daily.sample.json` | 虚构示例数据,结构与真实导出一致,可以公开 |
| `dist/` | 生成结果,不进 git |

## 数据约定(schema 1)

brant-lens 的 `export_daily.py` 负责解析总结 md;总结格式改了改那边,这里的结构尽量不变。要加字段可以,改已有字段要升 `schema`。

```
{
  schema: 1, title: "网页标题", generated: "YYYY-MM-DD HH:MM", note: "页头免责说明",
  days: [{
    stem, date: "YYYY-MM-DD", wd: "周一", title, meta,
    start: {et: 开播美东分钟数, off: 北京比美东快几小时} | null,   // 进度时间换钟点用
    fmt: "v1" | "v2", headline, chars,
    sections: [{ n, title, kind, short, blocks: [Block], subs: [{title, blocks: [Block]}] }]
  }],
  presets: [{ preset_id, date, stem, card_id, t, ticker, kind, condition, action, quote,
              status: 待触发|已触发-照做|已触发-没做|改口|作废|过期, note, first,
              history: [{date, status, note, quote, card_id}] }],
  rules: { 编号: { n: 名称, s: 陈述, st: 有效期 } }     // 只含总结和预设里用到的编号
}
Block = {t: "li", lvl: 缩进层级, md: 行内 markdown} | {t: "p", md}
```

- `kind` 决定这一节怎么画:`brief` `direction` `trades` `lessons` `assets` `people` `account` `changes` `presets` `mistakes` `timeline` `notes`,其他按通用列表显示。
- 行内 markdown 只用到 `**粗体**`;另外认这些记号:「原话」、`(00:12:34)` 进度时间、`S20261104-01` 预设号、`E01234` 事件号、`〔标签〕`、理念编号(在 `rules` 里的才显示成可点的编号)。
- `ticker` 可以是 `AAA/BBB` 这种组合;看板按第一个代码分组,筛选按单个代码匹配;`UNKNOWN` 显示为「大盘 · 没说标的」。
