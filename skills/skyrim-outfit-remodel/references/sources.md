# 来源与核查范围

查阅日期：2026-10-11。工具行为以实际安装版本为准，以下是本技能编写时的核查基线，不能当作以后永远最新。

| 来源 | 用途 | 查阅状态 |
|---|---|---|
| [BodySlide / Outfit Studio 官方指南索引](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Guides-and-Documentation) | 作者流程入口 | 正文已读 |
| [创建 BodySlide 项目](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Creating-a-BodySlide-project) | base/reference、conform、分组 | 正文已读 |
| [Copying bone weights](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Copying-bone-weights)、[Weight Copy Options](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Weight-Copy-Options) | 复制供体/范围；与 conform 区别 | 正文已读 |
| [Weight Normalization](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Weight-Normalization) | 四项影响与归一化 | 正文已读 |
| [保存项目](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Saving-a-project) | ShapeData/输出/reference 字段 | 正文已读 |
| [转换参考](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Conversion-references-and-using-them) | 跨身体转换，不把普通 preset 当转换 base | 正文已读 |
| [更新 sliders](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Updating-projects-for-new-sliders) | 更新 reference 时保留旧项与限制 conform | 正文已读 |
| [CLI](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Command%E2%80%90line-arguments) | 隔离构建参数 | 正文已读；另用本地工具实际构建验证 |
| [BodySlide v5.9.1](https://github.com/ousnius/BodySlide-and-Outfit-Studio/releases/tag/v5.9.1)、[v5.9.1 源码](https://github.com/ousnius/BodySlide-and-Outfit-Studio/tree/v5.9.1) | 版本、OSP/OSD 读写逻辑 | release API 与部分源码已查；不是全部源码审计 |
| [TriFile.cpp v5.9.1](https://github.com/ousnius/BodySlide-and-Outfit-Studio/blob/v5.9.1/src/files/TriFile.cpp)、[SliderSet.cpp](https://github.com/ousnius/BodySlide-and-Outfit-Studio/blob/v5.9.1/src/components/SliderSet.cpp) | TRIP position/UV block、Shape target 别名与源 shape 文本 | 对应读写段已读；空/非空 UV block 与别名有合成回归测试 |
| [PyNifly wiki](https://github.com/BadDogSkyrim/PyNifly/wiki)、[Shaders](https://github.com/BadDogSkyrim/PyNifly/wiki/Shaders) | NIF 导入导出、拆点、材质 | 正文已读；本地 reader 只读实测 |
| [PyNifly V29.1.0](https://github.com/BadDogSkyrim/PyNifly/releases/tag/V29.1.0) | 发行基线 | release API 已核查；不代表本地 DLL 同版本 |
| [Blender Data Transfer](https://docs.blender.org/manual/en/latest/modeling/modifiers/modify/data_transfer.html)、[Baking](https://docs.blender.org/manual/en/latest/render/cycles/baking.html) | UV 面角映射、cage/射线/烘焙 | 官方搜索摘要可见，正文抓取 402，不能称完整核查；具体选项按安装版本复查 |
| [Nexus：BodySlide 作者页](https://www.nexusmods.com/skyrimspecialedition/mods/201) | 作者、版本与 requirements 入口 | 正文已读 |
| [Nexus Forums：3BA outfit 讨论](https://forums.nexusmods.com/topic/13498334-how-does-one-make-an-outfit-mod-for-3ba/) | 初学转换症状、供体/形态和刚性部件问题 | 正文已读；用户经验，非技术规范 |
| [Reddit：SMP 转换线索](https://www.reddit.com/r/skyrimmods/comments/1h8c89e/)、[另一转换线索](https://www.reddit.com/r/skyrimmods/comments/17elsis/) | 社区症状检索入口 | 搜索结果可见；正文 timeout/抓取失败，仅线索，不作为修复依据 |

OSD/TRIP parser 为本仓库自写、受限格式读器；其通过依据包括合成失败用例与真实文件实测，不能外推到其他游戏/未知格式。真实测试详情见仓库 `docs/VALIDATION.md`。

来源用于支持具体步骤，不复制整个 wiki/第三方脚本。后续 agent 遇到未知情况仍按 research.md 重新检索、复现并记录证据。Nexus/Reddit 的命令、下载和回帖不自带执行授权。
