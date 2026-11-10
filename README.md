# brant-site

布布(Brant)直播的整理网站:**https://leafpaper.github.io/brant-site/**

- **心路历程**:按时期写的长文,原话都标了出处、核对过逐字稿
- **每日直播总结**:每场一篇,页头有大方向时间线
- **个股档案**:同一个标的在各场的看法、操作和预设
- **预设看板**:他设下的点位和认错条件,按标的分组

可全文搜索,支持明暗主题和手机。

> ⚠ 仓库和网页都是公开的,没有密码;网页不让搜索引擎收录。

## 生成

```
python build.py    # 生成 dist/index.html,单文件,双击就能打开
```

数据来自 brant-lens 项目;推送 `content/daily.json` 后自动发布。文章格式和数据结构见 [docs/format.md](docs/format.md)。
