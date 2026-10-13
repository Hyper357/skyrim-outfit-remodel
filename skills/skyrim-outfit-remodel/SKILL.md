---
name: skyrim-outfit-remodel
description: Remodel Skyrim SE/AE wearable equipment from references while preserving the intended wearing pose, then prepare UVs, skin weights, BodySlide projects, NIF assets, and verified deployment. Use for boots, gloves, fitted clothing, collars, head coverings, and armor; route cloth physics to its specialist procedure when present.
---

# Skyrim 全身装备重塑

从用户指定毛坯和参考图出发，保留目标穿戴姿态，交付可编辑、可重建、可验证的装备。按任务选阶段；局部修复不必重做全部数据。检查脚本不会自动雕刻模型。

## 开始

读项目 AGENTS.md 与最新交接，确认游戏/体型/骨架/工具版本和实际底稿。用 [intake.md](references/intake.md) 建立修改范围与基线。把 [job.template.json](assets/job.template.json) 和 [HANDOFF.template.md](assets/HANDOFF.template.md) 复制到本次工作目录并填写；null 表示未确认，不能当成功。

## 执行与验收

| 阶段 | 必读 | 继续的证据 |
|---|---|---|
| A 原始资源、参考 | [intake.md](references/intake.md)、[research.md](references/research.md) | 底稿、姿态、参考优先级、资源 winner、范围可追溯 |
| B 形体、拓扑 | [modeling.md](references/modeling.md) | 同角度多视图、连接和边流、保护区域检查 |
| C UV、表面 | [uv-normals.md](references/uv-normals.md) | 棋盘格、接缝、烘焙和导出表面证据 |
| D 绑定、动态贴合 | [weights.md](references/weights.md) | 导出权重、关节姿态、骨架/绑定变换有效 |
| E BodySlide、形态 | [bodyslide.md](references/bodyslide.md)；紧身全包类或 Blender 往返项目另读 [kitty-recovery.md](references/kitty-recovery.md)；预设消失/只剩旧项/无法应用时读 [preset-groups.md](references/preset-groups.md) | 源工程、体重与滑块组合、实际构建对应 |
| F 材质、部署 | [materials-deployment.md](references/materials-deployment.md)、[validation.md](references/validation.md) | 资源闭合、winner、重建和游戏测试分别记录 |

涉及 SMP 骨链、裙摆或披风另读 [physics.md](references/physics.md)。出现色块、爆点、CTD 先按 [troubleshooting.md](references/troubleshooting.md) 定位，不跨层盲修。

针对贴身、参考图染色和往返修改，只加载对应分支：

- 紧身/半透明外壳、身体内层与动态间隙：[fitted-clothing.md](references/fitted-clothing.md)。
- 艺术参考分区、真实部件识别与 UV 蒙版：[reference-colouring.md](references/reference-colouring.md)。
- Blender 保索引往返、权重/形态同步与连续接边：[indexed-roundtrip.md](references/indexed-roundtrip.md)。
- TruePBR：安装并调用本仓库配套 [skyrim-truepbr-workflow](../skyrim-truepbr-workflow/SKILL.md)；完整通道、Manager/PGPatcher、部署与验收由它负责。
- 已验证范围和案例常数：[bioenclosure-case.md](references/bioenclosure-case.md)。

## 关键约束

- 零滑块、低体重、OSP 默认和个人 preset 分别验收；需要零位复用时，检查基础贴合是否依赖隐藏非零默认项。出现合并项目后过粗但 preset 正常时读 [base-shape.md](references/base-shape.md)，不直接烘焙整个个人 preset。

- 原穿戴姿态是设计锚点；骨架 bind/rest pose 与动画姿态分开。不要整体缩放或清除变换掩盖绑定错误。
- 拓扑或顶点顺序变更会使旧索引失效。重建 UV/权重/形态映射，不直接套用旧 OSD/TRI。
- 保留四边形编辑工程和独立游戏输出。三角化、UV/法线拆点、分区与形态用同一稳定导出流程；检查真实输出数量和映射。
- 保护已确认区域。索引一致可用 compare_mesh.py；重拓扑后用映射、轮廓与表面偏差证据，不能假称逐点保护通过。
- 改 BodySlide 装备要更新源工程并实际构建；只改 meshes NIF 会被重建覆盖。
- 需要删除被服装遮挡的身体、手脚或内层几何时，优先使用 Outfit Studio 原生 Zap，让 BodySlide Build 真正删除输出几何；不要把大量顶点压到单点或藏入身体来模拟删除。Blender 负责造型，BodySlide 语义层回 Outfit Studio 收口；详见 [kitty-recovery.md](references/kitty-recovery.md)。
- 新建、改名或复制 BodySlide Outfit 时，检查 `Outfit Groups ∩ Target Preset Groups ≠ ∅`。自定义装备组可保留，但 3BA 等项目还要加入对应兼容组；UI 残留上次 preset 名称不算已成功应用。详见 [preset-groups.md](references/preset-groups.md)。
- 保留装备身份、插槽、颜色和既有物理机制，除非用户要求修改。检查用参考身体按实际需求决定是否导出，避免重复身体。
- 未知菜单/格式/版本行为先调研和最小实验。research.md 规定来源优先级、记录和停止条件。
- 技能不额外授权发布模组、改加载顺序或删历史工程；沿用本次用户授权。缺工具时完成可做的阶段并准确记录缺项。

## 工具与交付

在技能目录运行 `python scripts/<name>.py --help`（Blender 工具需在 Blender 中运行）。审计工具只读输入；indexed bridge 可保存新建的编辑 blend，但不覆盖输入；构建报告和预期输出写入全新目录，BodySlide 本身使用隔离工具副本。用户指定自行构建时交接源和待验项目。

- blender_probe.py / audit_mesh.py：网格、UV、权重快照和数值检查。
- compare_mesh.py：索引一致时检查局部保护与不变量。
- audit_nif.py：外部 PyNifly 只读导出 NIF。
- audit_bodyslide.py：OSP 引用及可选 OSD/TRIP 索引检查。
- build_bodyslide.py：隔离实际构建、输出与日志核验。
- manifest.py：明确目录的文件哈希清单。
- indexed_blender_bridge.py：带点身份、权重和可选位置 morph 的 Blender/JSON 编辑通道，不写 NIF/OSD。
- surface_transfer.py：显式对应的基形、骨名权重和形态插值，以及接边 delta 修正，不自动找供体。

命令及能力边界见 [tools.md](references/tools.md)。交付当前可编辑工程、完整重建输入、游戏资源、依赖与测试交接。造型、静态、重建、姿态、游戏状态分别报告，未做保持 pending；见 [validation.md](references/validation.md)。

[case-study.md](references/case-study.md) 是案例与适用边界；[sources.md](references/sources.md) 是已查来源。案例的坐标、预设、材质常数和工具异常不能直接推广。

需要从鞋靴迁移到其他部位时，参见 [recipes.md](references/recipes.md) 的手套、领口与硬甲/物理分支走查。
