# BodySlide / Outfit Studio / 形态

## 数据角色

ShapeData NIF 是基形/绑定/UV/材质源；OSP 是项目/输出/shape/slider/数据集映射；OSD 是源逐点形态；运行时 NIF/TRI 是按 preset 构建的结果。BodySlide TRIP 与头部 TRI 不互换。

零滑块不等于最小体型或低体重；裸基形、OSP 默认状态和个人 preset 要分别验证。Add Project 后过粗但 preset 正常时，先查隐藏非零默认修正，按 [base-shape.md](base-shape.md) 定位和修复。

低高体重常用 `_0/_1.nif`，OSP OutputFile 基名不带后缀，确认 GenWeights；需要游戏形态才生成 TRI。不是所有刚性配件都需 slider。[项目组成](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Creating-a-BodySlide-project)、[保存字段](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Saving-a-project)

## A 保留索引修改已有项目

1. 载入实际源 OSP，确认 DataFolder/SourceFile/shape/slider/data，隔离副本留基线。
2. 用当前工具支持的保索引方式更新基形，并实测对应。不确定用小位移标记往返实验；同点数不算证明。
3. 原 UV/权重/形态可作初始值，但新轮廓叠加旧 delta 必须重新检查。
4. 改 slider 时进入该 slider 编辑模式；改 base 时退出，避免误记 delta。
5. 保留隐藏/反向/zap/clamp/default small-big/reference/output 约定。局部修复不清空全部 slider。

## A2 Blender 往返 + 原生 Zap 路线

已有成熟 OSP/OSD、但需要 Blender 继续优化造型的紧身衣、长袜、全包服装，优先采用 [Kitty 路线](kitty-recovery.md)：

1. Blender 只负责造型；默认保持 topology 与 vertex order，不用 Remesh、Decimate、Merge by Distance、Dissolve、Delete Faces 等操作偷偷改变旧 slider 的索引语义。
2. 导回 Outfit Studio 后检查旧 slider 的落点和极值组合；索引没变也不等于旧 delta 对新轮廓仍然合理。
3. 被服装遮挡的身体、手脚或内层几何需要从最终输出删除时，使用 **Outfit Studio 原生 Zap**，让 BodySlide Build 真正删除几何。不要把大量顶点压到手腕/脚踝、藏进身体或缩成一点来模拟删除。
4. Zap 若属于项目默认设计，核对 `small` / `big` 默认值和 hidden/invert 等属性；手动测试时勾选过不代表日常 Build 会自动启用。
5. 用新隔离目录真实构建目标 preset 与零位/基线，确认本轮新 `_0/_1/TRI` 产生，并验证目标 preset 确实改变输出。
6. 部署后检查 MO2 实际 winner，尤其是旧 BodySlide Output 中残留的 `_0/_1.nif`、TRI 和旧 shape 名。

只要 Blender 改变 topology 或 vertex order，就立即转入 B 路线，把新网格视为新的 BodySlide 基形；旧 OSD/TRI 不再按旧索引直接复用。

## B 重拓扑/新项目

1. 固定新基形、shape 对应与导出规则；旧 OSD/TRI 不按旧索引复用。
2. OS 新项目选目标身体的**带滑块 reference/project**。普通 NIF 可能只有权重而无 slider。reference 用目标 base，不把已烘焙个人 preset 的身体再当零位重复变形。
3. 零位装备先适合目标 base。跨身体体系时先用匹配转换 reference，再载最终参考。转换指南中的 `Set Base Shape` 不适用于随便把普通个人 preset 烘焙成新 base。[转换参考](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Conversion-references-and-using-them)
4. 为目标 shape 复制合适权重；用当前版本 `Slider → Conform All`/所选 shape 操作生成形态。**Conform 建 slider，不等于 Copy Bone Weights。**
5. 逐个相关 slider 检查 0..100，修膨胀/穿插/硬板拉伸，保护鞋头/细跟/甲片等不应鼓起的区域；按支持范围再测试负值/超范围及组合。
6. 保留或重建隐藏/zap/配件 slider；不把全局 conform 当完成。换 reference 时对照旧 slider 清单，恢复被替换的自定义项及其属性。仅补新增/变更 slider 时，先取消全部 slider 复选框，再只勾目标项执行 conform；复查旧形态未意外重算。所用版本行为以副本实验为准。[更新项目](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Updating-projects-for-new-sliders)
7. `File → Save Project As` 核对显示名、OSP 名、ShapeData 目录、source NIF、输出路径/基名、reference 导出。仅参考身体不误导出；原装备确实含身体则按设计保留所需部分。
8. 把项目加入匹配身体的分组，以便目标 preset 可见，并按需要加入装备自己的批量构建组。同步 SliderGroups；不要把“项目能显示”误当“目标 preset 已应用”。保存后关闭副本再重新打开项目，检查 reference、slider 和输出设置确实落盘。预设列表异常时按 [preset-groups.md](preset-groups.md) 逐项检查。

## 体重和 preset

- 低/高输出有可插值对应顶点、相同 shape 角色/顶点顺序/面连接，不独立 remesh。
- 身体/内层/外层用同目标 preset；各项目 slider 定义和默认值仍需核对，名字相同不保证 delta 一致。
- 查 0/50/100 体重、主要 slider 单独极值和组合；端点正确不证明中间/动作正确。
- zap 后 topology 与 TRI 对应；删体表要匹配遮挡和插槽，不靠删光身体掩盖贴合问题。
- 自定义装备组可以保留，但项目还必须与目标 preset 的身体 group 有有效交集；3BA 项目要核对 `3BA`/对应 master group。预设下拉显示上次名称，不代表当前 outfit 已成功匹配并应用它。详细诊断和最小修复见 [preset-groups.md](preset-groups.md)。

## 实际构建与索引冻结

1. 在隔离 BodySlide 数据环境准备本次 source/project/preset，确认加载路径/版本。
2. 查当前版本帮助。核查的 5.9.1 示例：

```powershell
& '<BodySlide.exe>' --build '<精确项目名称>' --targetdir '<隔离目录>/Data' --preset '<名称或XML>' --trimorphs
```

build_bodyslide.py 要求新隔离目录、预期输出，并保存命令/日志/哈希。它不自动设置 source/preset 搜索路径，须先确认工具环境。其他版本重查参数。[CLI](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Command%E2%80%90line-arguments)

3. 查本轮新 `_0/_1/TRI`；退出 0 或旧文件存在均不足。
4. audit_nif.py 查实际导出；audit_bodyslide.py 查 OSP/OSD/可选 TRIP 索引。另做已知 slider 的输出形态对照；索引合法不证明 delta 落点正确。
5. UV/法线拆点会增加导出顶点；复制点也要映射 delta。形态依据**最终导出索引**。两端、TRI、源重建使用同一三角化/拆点/命名规则。
6. 核对 TRI shape 名、BODYTRI 路径和运行时形态系统适用/启用情况。旧 TRI 不直接沿用。
7. 从保存完整的源再构建，证明可交接；冻结后不再改索引。只改 meshes 的修复会被下次构建覆盖。
8. 对经过 Blender/OS 多次往返的项目，额外比较 source、目标 preset 构建和零位构建的哈希/顶点变化；`_0/_1.nif` 与 ShapeData source 完全同哈希时，应确认是否根本没有真实应用 preset。
9. 部署后检查 MO2 winner；源目录正确不代表运行时资源正确，高优先级 BodySlide Output 的旧 NIF/TRI 必须纳入验收。

项目不显示查 OSP/分组/数据根；预设列表异常查 outfit group 与 preset group 的交集；仍旧模型查 source/winner；slider 无效查 reference/shape/data；爆点查点序/拆点；加载/构建异常且存在大量同位点几何时，检查是否曾用压缩顶点模拟删除并改回原生 Zap；动画与形态异常分开诊断。自动审计不替代实际构建、slider 视觉和游戏测试。
