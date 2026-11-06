# brant-site

## 👉 打开网页:https://leafpaper.github.io/brant-site/

布布(Brant)的直播整理网站:

- **心路历程**:按时期或主题写的长文——他当时怎么做、怎么想,后来怎么回头看。每句原话都标了出处,并且逐句回逐字稿核对过。文章在 `content/essays/`。
- **每日直播总结**:每场一篇,每节按自己的结构排版——心法是目录 + 卡片(原话、要点、对应理念的名称),个股和对人是「名称 | 内容」对齐列表,变化是「之前 → 今天」,预设直接列出新设和了结,老毛病写出编号的名称;页头有**大方向时间线**(长期 / 大方向 / 这几天 × 每一场,发散色)。数据由 brant-lens 导出,同步到 `content/daily.json`。
- **个股与板块档案**:把每场对同一个标的的看法、操作、变化和预设串在一起(中文名、代码、杠杆和反向 ETF 归到一处)。
- **预设看板**:按标的分组。

全部都能全文搜索,有明暗主题,手机上也能看。

> ⚠ **本仓库和网页都是公开的,没有密码**(2026-11-06 用户决定,之后再加密码):拿到链接的人都能看,内容含付费直播的原话和他的账户盈亏。网页带 noindex 和 robots.txt,不让搜索引擎收录。以后加密码时,要把 `content/` 挪出这个仓库并清掉历史(公开仓库的历史谁都能翻)。

## 用法

只用 Python 标准库(3.9+)。

```
python build.py            # 同步 ../brant-lens/export/daily.json → content/daily.json,读文章,生成 dist/index.html
python build.py --sample   # 用 sample/daily.sample.json(虚构示例)看版式,不带文章
```

生成的 `dist/index.html` 是单文件、离线可用,双击用浏览器打开。找不到 brant-lens 时直接用 `content/daily.json` 里上次同步的版本,所以换台电脑 clone 下来也能生成。

每日流程(在 brant-lens 里):`build_why_data.py` → `export_daily.py` → `python ../brant-site/build.py`,然后在这里提交并推送 `content/daily.json`。推送后 GitHub Actions(`.github/workflows/pages.yml`)自动重新生成网页并发布,一两分钟后网址上就是新的。

## 目录

| 路径 | 内容 |
|---|---|
| `content/essays/*.md` | 心路历程文章(格式见下) |
| `content/daily.json` | 每日总结数据(从 brant-lens 同步,别手改) |
| `build.py` | 同步数据、读文章、生成网页 |
| `enrich.py` | 把每日总结各节拆成结构(名称/内容、之前/今天、像/不像)并汇总个股档案;**别名表 `ALIAS`**:新标的认不出、或中文名和代码没合到一起时在这里加 |
| `templates/daily.html` | 网页模板(样式和脚本都在里面) |
| `sample/daily.sample.json` | 虚构示例数据,测试版式用 |
| `dist/` | 生成结果,不进 git |

## 文章格式

```
---
title: 标题
period: 2020–2022            (侧栏和排序用)
written: 2026-11-06
summary: 一两句摘要(列表页显示)
---

## 速览                       (标题含「速览」或「一句话」:画成摘要卡,每行写 **标签**:内容)
## 一、2020 年:……             (普通节;导航短名取「一、」之后、冒号之前)
### 小节
- 列表,可缩进
段落
> 「一句最重要的原话」[[场次#卡号]]     (引文块:整行是 > 加一句原话加出处,大字显示)
> **容易读错**:……                    (提示框:> 后面不是原话的,画成灰底说明框,标签取 **…**)
{{chart qqq}}                        (图表:数据放在同名的 .json 里,见下)
## 时间线                     (标题含「时间线」:每行写 - **时间**:事情,画成竖排时间轴)
```

- 原话用「」,后面紧跟出处:`[[20250509_7ZMWXJgEf9Q#26]]`(场次#卡号)或 `[[20240924_mtaD4yBJRZI 00:27:41]]`(场次 + 直播进度)。网页上出处显示成小角标 1 2 3,点开看是哪天哪场。
- 标点照常写半角也行:网页显示时,中文旁边的 `, : ; ? ! ( )` 会自动换成全角。
- 图表数据 `content/essays/<同名>.json`:`{"charts": {"qqq": {title, sym, note, series: [[日期, 收盘价]…], phases: [{from, to, n, name}], marks: [{d, st: 多|空|事, q: 原话, src: 出处, what: 一句说明, lab: 图上短标签(可省)}]}}}`。`phases[].n` 写 ①②…,和正文 `### ① …` 小节标题开头对上,点图上编号就能跳过去。`marks[].q` 也必须是原话:改了标注,把它们写成一行行 `- 「原话」[[出处]]` 存成临时 md,交给 brant-lens 的 `check_essay.py` 核一遍。价格是长桥日线收盘价(未复权)。
- 写完要逐句核对原话(brant-lens 里的核对脚本:原话必须出现在所标场次的逐字稿里,出处必须存在)。
- 加了「」却不是原话的,改成原话或去掉引号。

## 每日总结数据约定(schema 1)

brant-lens 的 `export_daily.py` 负责解析总结 md;总结格式改了改那边,这里的结构尽量不变。要加字段可以,改已有字段要升 `schema`。

```
{
  schema: 1, title, generated: "YYYY-MM-DD HH:MM", note: "页头免责说明",
  days: [{ stem, date, wd, title, meta, start: {et, off} | null, fmt: "v1"|"v2", headline, chars,
           sections: [{ n, title, kind, short, blocks: [Block], subs: [{title, blocks}] }] }],
  presets: [{ preset_id, date, stem, card_id, t, ticker, kind, condition, action, quote, status, note, first,
              history: [{date, status, note, quote, card_id}] }],
  rules: { 编号: { n: 名称, s: 陈述, st: 有效期 } }
}
Block = {t: "li", lvl, md} | {t: "p", md}            (文章里另有 quote / aside / chart)
```

`build.py` 生成时再加上 `essays: [{slug, title, period, written, summary, chars, mins, quotes, srcs, charts, sections}]`,结构同上。
