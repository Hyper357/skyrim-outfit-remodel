# 验证记录

日期：2026-10-11。此记录验证技能包和检查工具；不是全身所有装备的游戏验收证书。真实资源留在本机，公开仓库只有汇总，没有几何快照或第三方资产。

## 工具基线

| 工具 | 本轮实际使用 |
|---|---|
| Blender | 5.2.0 LTS，background，disable-autoexec，不保存输入 blend |
| BodySlide | 5.9.1.0，独立工具副本，独立 ProjectPath/GameDataPath，两个全新输出目录 |
| NIF reader | 外部 PyNifly Python + NiflyDLL，只读；DLL SHA256 `b66a0eaada3b3c1dc38a5bee8643e3cb2c0502c901074de1886a8445f1475f67` |
| Python | 标准库脚本；本地 Windows 运行，CI 使用 Python 3.10 的 Windows/Linux 矩阵 |

本地 PyNifly reader DLL 的精确发行号未独立确认，因此以哈希识别，不把当前 GitHub release 号当本地 DLL 版本。

## 可复现的合成验证

```text
python -m unittest discover -s tests -v
```

29 项测试覆盖：非法/退化/重复几何、UV 数值、未加权/负值/非有限/未知骨/五项影响、静态 shape、保护区域越界、拓扑/UV/坐标系变化、空快照拒绝、损坏/越界/未知格式 OSD/TRIP、可选空/非空 UV morph block、OSP target 别名、输出路径越界、哈希清单增删改、自身排除、构建零退出但缺输出、超时和现存目录保护，以及 UTF-8/相对文档链接/入口元数据。

本地结果：全部通过。另用 skill-creator `quick_validate.py` 检查入口，通过；Windows 非 UTF-8 默认 Python 需 `python -X utf8`。GitHub Actions 自动执行同一合成测试集，其运行状态以仓库 Actions 为准。

## 真实鞋靴只读与构建验证

使用已有已确认造型的 J3 鞋靴案例；本轮没有改其形体或部署原模组。

| 验证 | 结果与范围 |
|---|---|
| Blender 原始 basis 快照 | 两个 mesh 数值审计通过；原 blend 前后 SHA256 相同 |
| 可编辑网格统计 | 25,578 空间顶点、26,062 多边形，其中 24,970 四边形；等效 51,032 三角形 |
| ShapeData NIF 与原低/高体重 NIF | 三个文件只读审计通过，输入哈希未变；2 shapes，28,725 导出顶点、51,032 三角形 |
| 数量差异 | 导出拆点后的顶点多于 Blender 空间顶点；不能用源点数直接校验运行时 TRI |
| 导出权重数值 | 鞋身最多 4 项，跟/底 shape 最多 1 项；无本检查器发现的未加权/非有限/越界问题 |
| OSP / OSD | 34 sliders、68 local datasets；source shape 和逐点索引检查通过 |
| 已有及新构建 TRIP | position block：鞋身 34 morphs、跟/底 1 morph；UV block 为空；最终输出索引范围通过 |
| 实际 BodySlide 构建 | 两次全新隔离构建均退出 0，分别产生非空 `_0.nif`、`_1.nif` 和 `.tri`；记录命令、日志及输出哈希 |
| 本轮基准构建 NIF | 低/高输出只读数值审计通过，2 shapes/数量与基线一致 |
| 单滑块语义实验 | 仅 CalfSize 在 small/big 各 +10；两端鞋身均有 6,381 点改变；实测位移与 source OSD delta × 0.1 的最大分量误差约 `1.0e-5`（NIF shape-local 单位，阈值 `1e-4`）；跟/底 0 点改变；faces/UV/骨名/权重保持 |
| 交付 manifest | 技能目录 25 个文件，make/verify 通过；复制安装后应再次核对 |

单滑块实验只证明该测试形态和当前导出链的对应，不能推出其余所有滑块/组合或未知拓扑映射都正确。上述形状统计对应两只靴子合计，不是单只。

## 本轮查出的具体问题

初版 TRIP reader 把标准尾部 UV shape-count 当作未知扩展，真实文件测试因此失败。对照 BodySlide v5.9.1 的 TriFile.cpp，补齐可选 UV block、截断/越界拒绝及空/非空 UV 测试后通过。未知尾部仍拒绝，不靠忽略字节处理。

对照 SliderSet.cpp 修正 target 别名与实际源 shape 的映射，补别名测试。空形态快照不能声称已查索引；构建退出 0 但缺本轮输出也必须失败。

首次云端运行中 Linux 通过，Windows Python 3.10 的清单自身排除测试失败。输入 exclude 路径与扫描路径的规范化不一致；统一 resolve 并增加等价路径回归断言后重新运行。最终云端状态见仓库 Actions，不能用本地通过覆盖云端失败。

## 尚未覆盖

本轮未重新进行 UV 棋盘格/烘焙视觉、全部 slider 组合、骨架 bind/skin transform/逐面分区覆盖的独立验证、关节动画、游戏穿戴/物品预览或 SMP 测试。Blender basis probe 不代表当前 shape key 混合后的表面。没有独立 subagent 行为验收；其他部位的 recipes 是流程走查，不是已完成的资产实例。

保留 `pending` 的目的是让接手 agent 知道下一步所需证据。未来每件装备应填写自己的 job/HANDOFF，不能继承本案例的 pass 状态。
