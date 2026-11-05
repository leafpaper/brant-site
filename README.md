# brant-site

布布(Brant)的直播整理网站,两块内容:

- **心路历程**:按时期或主题写的长文——他当时怎么做、怎么想,后来怎么回头看。每句原话都标了出处,并且逐句回逐字稿核对过。文章在 `content/essays/`。
- **每日直播总结**:每场一篇(速览、操作、心法、个股、时间线……),加上按标的分组的预设看板。数据由 brant-lens 导出,同步到 `content/daily.json`。

两块都能全文搜索,有明暗主题,手机上也能看。

> ⚠ **本仓库必须保持私有**:内容是付费直播的原话,还有他的账户金额和盈亏。不要改成公开,也不要部署到不加登录的地址(GitHub Pages 即使仓库私有,网站也是公开的)。

## 用法

只用 Python 标准库(3.9+)。

```
python build.py            # 同步 ../brant-lens/export/daily.json → content/daily.json,读文章,生成 dist/index.html
python build.py --sample   # 用 sample/daily.sample.json(虚构示例)看版式,不带文章
```

生成的 `dist/index.html` 是单文件、离线可用,双击用浏览器打开。找不到 brant-lens 时直接用 `content/daily.json` 里上次同步的版本,所以换台电脑 clone 下来也能生成。

每日流程(在 brant-lens 里):`build_why_data.py` → `export_daily.py` → `python ../brant-site/build.py`,然后在这里提交 `content/daily.json`。

## 目录

| 路径 | 内容 |
|---|---|
| `content/essays/*.md` | 心路历程文章(格式见下) |
| `content/daily.json` | 每日总结数据(从 brant-lens 同步,别手改) |
| `build.py` | 同步数据、读文章、生成网页 |
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
## 时间线                     (标题含「时间线」:每行写 - **时间**:事情)
```

- 原话用「」,后面紧跟出处:`[[20250509_7ZMWXJgEf9Q#26]]`(场次#卡号)或 `[[20240924_mtaD4yBJRZI 00:27:41]]`(场次 + 直播进度)。
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
Block = {t: "li", lvl, md} | {t: "p", md}
```

`build.py` 生成时再加上 `essays: [{slug, title, period, written, summary, chars, sections}]`,结构同上。
