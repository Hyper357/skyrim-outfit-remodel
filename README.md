# Skyrim Outfit Remodel

面向 agent 的 Skyrim SE/AE 全身装备重塑技能：从参考图和已有毛坯出发，保留穿戴姿态，完成形体、拓扑、UV、法线、权重、BodySlide 形态及可追溯交付。

适用于鞋靴、手套、紧身衣、领口、头部覆盖物与硬甲；涉及裙摆、披风和 SMP 时转入物理专用流程。包含 BioEnclosure 半透明贴合、Wing 连续接边与配套 TruePBR 工作流；案例参数不直接套到其他装备。

## 四个常用问题

| 需求 | 可直接读的流程 |
|---|---|
| 衣服怎样更贴身，半透明层怎样贴合身体 | [同一身体对应驱动基形、权重和滑块](skills/skyrim-outfit-remodel/references/fitted-clothing.md) |
| 怎样按艺术参考精准上色 | [部件 ID、三维分区到 UV 蒙版、颜色与法线复核](skills/skyrim-outfit-remodel/references/reference-colouring.md) |
| 带权重/滑块怎样进 Blender 再回 NIF/BS，怎样接边 | [保索引通道、重建路线、连续边界与 delta 同步](skills/skyrim-outfit-remodel/references/indexed-roundtrip.md) |
| 怎样完成 TruePBR | [完整 TruePBR skill](skills/skyrim-truepbr-workflow/SKILL.md) 与 [端到端交付清单](skills/skyrim-truepbr-workflow/references/end-to-end.md) |

“无损”需要指明保留了哪些数据。改变拓扑后不能直接复用旧 OSD；位置/权重/形态协调、静态验证、BodySlide 构建与游戏动作是不同验收层。真实案例的数值及尚未完成项见 [BioEnclosure / Wing](skills/skyrim-outfit-remodel/references/bioenclosure-case.md)。

## 安装和调用

将 `skills/skyrim-outfit-remodel` 复制到 Codex skills 目录；需要 PBR 时同时复制 `skills/skyrim-truepbr-workflow`。Windows 示例（目标目录不存在时）：

```powershell
git clone https://github.com/Hyper357/skyrim-outfit-remodel.git
Copy-Item -LiteralPath '.\skyrim-outfit-remodel\skills\skyrim-outfit-remodel' -Destination "$env:USERPROFILE\.codex\skills\skyrim-outfit-remodel" -Recurse
Copy-Item -LiteralPath '.\skyrim-outfit-remodel\skills\skyrim-truepbr-workflow' -Destination "$env:USERPROFILE\.codex\skills\skyrim-truepbr-workflow" -Recurse
```

已有同名技能时先比较版本，避免复制出嵌套目录。重新加载 skills 或开启新会话后使用：

```text
使用 $skyrim-outfit-remodel，以我指定的毛坯和参考图重塑这件装备。
保留穿戴姿态和已确认区域，先盘点实际资源，再完成 UV、权重、BodySlide 与交付验证。
```

从 [技能入口](skills/skyrim-outfit-remodel/SKILL.md) 按当前阶段阅读，不必把全部手册一次塞进上下文。先复制并填写 [任务契约](skills/skyrim-outfit-remodel/assets/job.template.json) 和 [交接模板](skills/skyrim-outfit-remodel/assets/HANDOFF.template.md)。

给其他 agent 的精简任务示例：

```text
使用 $skyrim-outfit-remodel；材质阶段使用 $skyrim-truepbr-workflow。
按本次 job/HANDOFF 确认实际身体、骨架、MO2 winner 与修改范围。
贴合读 fitted-clothing，接边/往返读 indexed-roundtrip，上色读 reference-colouring。
只加载当前分支的参考，保留源工程与回滚；静态、构建、动作、游戏验收分别报告。
```

## 重点内容

- 保索引修改与重拓扑两条路线；保护确认区域，并冻结最终形态索引。
- UV 面角/拆点、棋盘格、烘焙、法线与高光色块的分层诊断。
- 按部位选择权重供体，检查四项影响、归一化、绑定与关节姿态。
- 区分 Copy Bone Weights 与 Conform；同步 OSP/ShapeData/OSD、分组、低高体重和 TRI，执行真实隔离构建。
- 区分 BodySlide 预览与游戏材质，查 MO2 winner、TXST、BODYTRI 和物理依赖。
- 遇到未知问题，检索官方 GitHub、作者 Nexus 资料与社区线索，并做最小实验。

## 工具和验证

重塑技能包含七个原审计/构建工具和两个数据交换 helper，使用方式与边界见 [tools.md](skills/skyrim-outfit-remodel/references/tools.md)。Python 工具使用 3.10+ 标准库，Blender bridge 需 Blender；BodySlide、PyNifly 和 NiflyDLL 为外部依赖。配套 PBR 的颜色比较另需 Pillow、schema 检查需 jsonschema；其余依赖在对应 skill 中说明。没有这些工具仍可阅读和规划，但不能记成对应阶段已通过。

```powershell
python -m unittest discover -s tests -v
```

合成测试可在无游戏资产环境运行；真实测试与尚未覆盖的范围见 [验证记录](docs/VALIDATION.md)。检查器不会自动雕刻模型，也不能证明所有未来转换都成功。造型、数值、构建、姿态和游戏验收分别记录。

## 交接与发布范围

只包含自写流程、脚本、模板和合成测试。第三方模型、贴图、工具二进制、存档、个人配置和真实几何快照不在仓库内。原模组另行发布时需确认其权限与依赖；本技能的安装不授权修改加载顺序、删除工程或发布资产。

流程来源与访问限制见 [资料索引](skills/skyrim-outfit-remodel/references/sources.md)。本仓库自写内容采用 [MIT](LICENSE)；外部工具和资产遵循各自许可。

## English

A Chinese-first skill collection for Skyrim SE/AE outfit remodeling and TruePBR. Includes fitted surface correspondence, reference-based region colouring, indexed Blender/JSON editing, morph-aware seam alignment and material/deployment validation. Install the relevant folders from `skills/`. Scripts and synthetic tests contain no game assets. Numerical checks and successful builds never imply visual or in-game acceptance.
