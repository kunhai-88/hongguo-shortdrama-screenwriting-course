# 红果短剧编剧第一课整理

这是「红果短剧创作服务平台」公众号《短剧编剧第一课》01-10 期的学习整理仓库，方便阅读、检索和打印。

> 说明：本仓库为学习整理用途。文章内容、图片和课程权益归原作者/原公众号/相关权利方所有。公开传播或商业使用前，请自行确认转载授权。

## 内容

- [课程索引](INDEX.md)
- [原文来源](SOURCES.md)
- [推荐打印版 PDF：01-10 合并，43 页](pdf/hongguo-shortdrama-course-01-10-balanced-print.pdf)
- [省纸打印版 PDF：01-10 合并，37 页](pdf/hongguo-shortdrama-course-01-10-compact-print.pdf)
- 每期 Markdown：`lessons/lesson-XX/article.md`
- 每期正文打印 Markdown：`lessons/lesson-XX/article-print.md`
- 每期单独 PDF：`lessons/lesson-XX/printable.pdf`

## 课程列表

| 课次 | 标题 | 发布时间 | 单期 PDF | 原文 |
| --- | --- | --- | --- | --- |
| 01 | [短剧编剧第一课｜01期：新人入行前必看的创作指南](lessons/lesson-01/article.md) | 2025-10-31 12:00:00 | [PDF](lessons/lesson-01/printable.pdf) | [原文](https://mp.weixin.qq.com/s/xJ9JdOZpe_XqP2w_0yHIMg) |
| 02 | [短剧编剧第一课｜02期：揭秘题材与IP选择的底层逻辑](lessons/lesson-02/article.md) | 2025-12-15 11:45:00 | [PDF](lessons/lesson-02/printable.pdf) | [原文](https://mp.weixin.qq.com/s/C8l7qTI-aAq5CHHQSjHIFg) |
| 03 | [短剧编剧第一课｜03期：如何打造吸睛的黄金开场](lessons/lesson-03/article.md) | 2025-12-19 11:30:00 | [PDF](lessons/lesson-03/printable.pdf) | [原文](https://mp.weixin.qq.com/s/DRwpTSOprevZKgdJ5ia9wg) |
| 04 | [短剧编剧第一课｜04期：揭秘主线设计的底层逻辑](lessons/lesson-04/article.md) | 2025-12-24 11:30:00 | [PDF](lessons/lesson-04/printable.pdf) | [原文](https://mp.weixin.qq.com/s/x9sXM_DOCtpqtBE4t9gzMg) |
| 05 | [短剧编剧第一课｜05期：揭秘短剧节奏的设计密码](lessons/lesson-05/article.md) | 2025-12-31 11:30:00 | [PDF](lessons/lesson-05/printable.pdf) | [原文](https://mp.weixin.qq.com/s/l_XKgSAaXseko8zJfjvtxA) |
| 06 | [短剧编剧第一课｜06期：期待、悬念、钩子设置的底层逻辑](lessons/lesson-06/article.md) | 2026-01-06 11:33:05 | [PDF](lessons/lesson-06/printable.pdf) | [原文](https://mp.weixin.qq.com/s/a9Euw2Rs6hi2nfK-6iWilg) |
| 07 | [短剧编剧第一课｜07期：详解短剧情绪点设计的实操技巧](lessons/lesson-07/article.md) | 2026-01-15 11:45:00 | [PDF](lessons/lesson-07/printable.pdf) | [原文](https://mp.weixin.qq.com/s/H3-jsAth11A5zZsAGnfYKw) |
| 08 | [短剧编剧第一课｜ 08期：如何让你的剧本“更好过稿”并顺利落地？](lessons/lesson-08/article.md) | 2026-01-22 11:45:00 | [PDF](lessons/lesson-08/printable.pdf) | [原文](https://mp.weixin.qq.com/s/IEFNcUBgQW-qLFlGK8cdmQ) |
| 09 | [短剧编剧第一课｜09期：详解台词打磨的实战方法](lessons/lesson-09/article.md) | 2026-01-27 11:47:36 | [PDF](lessons/lesson-09/printable.pdf) | [原文](https://mp.weixin.qq.com/s/d6D0hFg2Bj1GKqiElUWFQw) |
| 10 | [短剧编剧第一课｜10期：网文作者转型实战指南](lessons/lesson-10/article.md) | 2026-02-04 11:45:00 | [PDF](lessons/lesson-10/printable.pdf) | [原文](https://mp.weixin.qq.com/s/kix71hZwgt5Ua0qc06y8Ww) |


## 建议阅读顺序

1. 先读 01 期，理解短剧编剧的行业入口和思维转换。
2. 读 02-04 期，掌握题材/IP、黄金开场和主线设计。
3. 读 05-07 期，掌握节奏、悬念、钩子和情绪点。
4. 读 08-10 期，检查剧本落地性、台词打磨和网文作者转型。

## 打印建议

优先使用 `pdf/hongguo-shortdrama-course-01-10-balanced-print.pdf`。这版 43 页，兼顾可读性和省纸。`compact-print.pdf` 是更省纸的 37 页版本，字号更小。

## 文件结构

```text
.
├── INDEX.md
├── SOURCES.md
├── NOTICE.md
├── pdf/
│   ├── hongguo-shortdrama-course-01-10-balanced-print.pdf
│   └── hongguo-shortdrama-course-01-10-compact-print.pdf
├── lessons/
│   └── lesson-XX/
│       ├── article.md
│       ├── article-print.md
│       ├── metadata.json
│       ├── printable.pdf
│       └── assets/
└── scripts/
```

## 复现说明

`scripts/` 里保留了本地抽取和 PDF 生成脚本。脚本依赖 Python、ReportLab、pypdf 以及 macOS 中文字体；不同系统上生成效果可能略有差异。
