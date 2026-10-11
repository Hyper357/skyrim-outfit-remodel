# Skyrim Outfit Remodel

面向 agent 的 Skyrim SE/AE 全身装备重塑技能：从参考图和已有毛坯出发，保留穿戴姿态，完成形体、拓扑、UV、法线、权重、BodySlide 形态及可追溯交付。

适用于鞋靴、手套、紧身衣、领口、头部覆盖物与硬甲；涉及裙摆、披风和 SMP 时转入物理专用流程。源自一次鞋靴重塑的经验，但不会把鞋子的坐标、材质或权重直接套到全身。

## 安装和调用

将本仓库的 `skills/skyrim-outfit-remodel` 目录复制到你的 Codex skills 目录，通常是 `~/.codex/skills/`。Windows 示例（目标目录不存在时）：

```powershell
git clone https://github.com/Hyper357/skyrim-outfit-remodel.git
Copy-Item -LiteralPath '.\skyrim-outfit-remodel\skills\skyrim-outfit-remodel' -Destination "$env:USERPROFILE\.codex\skills\skyrim-outfit-remodel" -Recurse
```

已有同名技能时先比较版本，避免复制出嵌套目录。重新加载 skills 或开启新会话后使用：

```text
使用 $skyrim-outfit-remodel，以我指定的毛坯和参考图重塑这件装备。
保留穿戴姿态和已确认区域，先盘点实际资源，再完成 UV、权重、BodySlide 与交付验证。
```

从 [技能入口](skills/skyrim-outfit-remodel/SKILL.md) 按当前阶段阅读，不必把全部手册一次塞进上下文。先复制并填写 [任务契约](skills/skyrim-outfit-remodel/assets/job.template.json) 和 [交接模板](skills/skyrim-outfit-remodel/assets/HANDOFF.template.md)。

## 重点内容

- 保索引修改与重拓扑两条路线；保护确认区域，并冻结最终形态索引。
- UV 面角/拆点、棋盘格、烘焙、法线与高光色块的分层诊断。
- 按部位选择权重供体，检查四项影响、归一化、绑定与关节姿态。
- 区分 Copy Bone Weights 与 Conform；同步 OSP/ShapeData/OSD、分组、低高体重和 TRI，执行真实隔离构建。
- 区分 BodySlide 预览与游戏材质，查 MO2 winner、TXST、BODYTRI 和物理依赖。
- 遇到未知问题，检索官方 GitHub、作者 Nexus 资料与社区线索，并做最小实验。

## 工具和验证

带七个检查工具，均有 `--help`，使用方式与能力边界见 [tools.md](skills/skyrim-outfit-remodel/references/tools.md)。Python 工具使用 3.10+ 标准库；Blender、BodySlide、PyNifly 和 NiflyDLL 为外部依赖。没有这些工具仍可阅读和规划，但不能记成对应阶段已通过。

```powershell
python -m unittest discover -s tests -v
```

合成测试可在无游戏资产环境运行；真实测试与尚未覆盖的范围见 [验证记录](docs/VALIDATION.md)。检查器不会自动雕刻模型，也不能证明所有未来转换都成功。造型、数值、构建、姿态和游戏验收分别记录。

## 交接与发布范围

只包含自写流程、脚本、模板和合成测试。第三方模型、贴图、工具二进制、存档、个人配置和真实几何快照不在仓库内。原模组另行发布时需确认其权限与依赖；本技能的安装不授权修改加载顺序、删除工程或发布资产。

流程来源与访问限制见 [资料索引](skills/skyrim-outfit-remodel/references/sources.md)。本仓库自写内容采用 [MIT](LICENSE)；外部工具和资产遵循各自许可。

## English

A Chinese-first agent skill for reference-driven Skyrim SE/AE outfit remodeling. Covers boots, gloves, fitted garments, collars, head coverings and armor, with staged UV, skinning, BodySlide, deployment and runtime checks. Copy `skills/skyrim-outfit-remodel` into your Codex skills directory. Scripts and synthetic tests contain no game assets. Numerical checks and successful builds never imply visual or in-game acceptance.
