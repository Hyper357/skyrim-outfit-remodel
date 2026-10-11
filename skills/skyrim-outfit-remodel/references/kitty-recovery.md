# Kitty 路线：Blender 重塑 + Outfit Studio 原生 Zap + BodySlide 隔离构建

本路线来自 `AE_Latex_Kitty` 的真实修复。适用于：已有 3BA/BodySlide 工程，需要继续用 Blender 做造型，但又必须保留/重建 slider、Zap、低高体重、TRI 和 MO2 部署闭环的紧身衣、长袜、连体衣等。

这是一条**工程路线**，不是把某个 Kitty 的具体顶点、预设或材质直接套到其他装备。案例记录见仓库 Issue #1；其他装备仍需按自己的 topology、slider、body group 和游戏资源验证。

## 核心分工

- **Blender**：负责造型、局部曲率、轮廓、褶皱、UV/表面等美术修改。
- **Outfit Studio**：负责 BodySlide 语义层：reference、Copy Bone Weights、Conform、Zap、shape/slider 映射、OSP/OSD。
- **BodySlide**：负责真实 preset 构建、`_0/_1.nif`、TRI 和构建结果验证。
- **MO2**：负责确认实际 winner，防止旧 `_0/_1/TRI` 覆盖新工程。

不要用 Blender 的几何“伪删除”替代 BodySlide 的 Zap。尤其不要把数千/数万待删除顶点缩放、合并或压到手腕、脚踝等同一点附近。这类处理可能让模型视觉上像“删掉了”，但仍保留大量顶点/三角面，并可能在 Outfit Studio 构建 weld/adjacency 等数据结构时造成严重性能问题或卡死。

## 路线 A：保拓扑 Blender 重塑

优先用于已有成熟 OSP/OSD、只需要继续优化形体的项目。

1. 盘点实际 source NIF、OSP、OSD、SliderGroups、preset、运行时 `_0/_1/TRI` 和 MO2 winner；保存哈希基线。
2. 从 source 导入 Blender，只移动现有顶点；默认保持顶点数、面连接和 vertex order。不要执行 Remesh、Decimate、Merge by Distance、Dissolve、Delete Faces 等会改变索引的操作，除非任务明确进入路线 B。
3. 导回后用 compare/audit 检查 topology/索引不变量；同顶点数不等于顺序没变，必要时做小位移往返实验。
4. 在 Outfit Studio 载入真实项目，检查旧 slider 是否仍落在正确区域。造型变化较大时，旧 delta 即便索引合法也要做极值/组合视觉检查。
5. 需要隐藏身体/手脚/内层几何时，在 Outfit Studio 创建或维护原生 Zap；让 BodySlide Build 时真正删除输出几何。
6. 如 Zap 属于日常默认行为，核对 `small` / `big` 默认值；如果项目要求始终启用，可将对应端点设为启用状态。不要把“测试时手动勾选过”当作默认配置已经正确。
7. 用隔离 BodySlide 环境真实构建目标 preset 与零位/基线，确认本轮新 `_0/_1/TRI` 确实产生；不要只看退出码或旧文件存在。
8. 比较目标 preset 与零位构建，确认 slider 真实改变了输出，而不是 source 与 runtime 同哈希。
9. 部署后检查 MO2 实际 winner，特别是旧 BodySlide Output 中的 TRI、旧 shape 名和旧 `_0/_1.nif`；源模组目录正确不代表游戏实际读取正确。
10. 预览、GUI Build、姿态、游戏内穿戴分别记录；缺哪项就保持 pending。

## 路线 B：拓扑变化 / 新网格

一旦 Blender 中确实需要删除、合并、重拓扑或重新布线，就不要继续把旧 OSD/TRI 当成可复用索引数据。

1. 把新网格视为新的 BodySlide 基形。
2. 在 Outfit Studio 使用目标身体的带 slider reference/project。
3. 重新复制/修正骨骼权重，重新 Conform 目标 slider；恢复自定义 slider、Zap、clamp、hidden、default 等属性。
4. 对新 topology 重新生成 OSD/运行时 TRI；旧 OSD/TRI 只可作为语义/视觉参考，不能直接按旧索引沿用。
5. 重新检查 OSP 的 shape 名、target/data 映射、ShapeData source、OutputFile、GenWeights 和 group。
6. 继续执行隔离 Build → `_0/_1/TRI` → MO2 winner → runtime 验收。

## 原生 Zap 的使用原则

Zap 用于“构建输出时真正删除不需要的几何”。典型对象包括：被衣服完全遮挡的身体表面、全包手套下不需要的手部、全包鞋袜下不需要的脚部，或项目明确设计为可切换删除的附件。

Agent 应区分：

- **造型调整**：移动/塑形，保留几何。
- **可切换删除**：原生 Zap。
- **永久新 topology**：路线 B，重建形态映射。

不能把“把顶点藏到别处”“缩成一点”“压进身体里”当作 Zap 等价物。

## BodySlide group / preset 同步

新建或改名 Outfit 时，同时检查它与目标身体 group 的交集。自定义装备组可以保留，但若这是 3BA 项目，还应确认项目属于可与目标 preset 匹配的 `3BA`/相应 master group。预设下拉有文字不代表当前 outfit 已成功匹配并应用目标 preset。

## 最小验收 Gate

- **G1 Blender**：确认是否保 topology；若否，转路线 B。
- **G2 Outfit Studio**：shape/reference/weights/slider 对应正确；Zap 为原生删除逻辑。
- **G3 BodySlide source**：OSP/OSD/分组/default Zap 落盘，重新打开项目仍一致。
- **G4 Isolated Build**：全新目录真实生成 `_0/_1` 和需要的 TRI；目标 preset 与零位输出有可解释差异。
- **G5 Output audit**：两端 topology/shape 角色、TRI 索引和新输出时间/哈希正确。
- **G6 MO2 winner**：实际获胜的 `_0/_1/TRI` 与本轮隔离构建一致，无旧高优先级输出覆盖。
- **G7 Runtime**：姿态、穿插、材质、物理和游戏内穿戴按实际完成程度记录。

## Kitty 案例给出的失败模式

`AE_Latex_Kitty` 的本地修复记录揭示了几类可复用的工程风险：

- 以“压缩顶点到手腕/脚踝”模拟删除，会留下异常密集同位点几何；不应作为标准路线。
- OSP 已有 Zap 但默认值关闭，手动测试启用不能代表日常 Build 会启用。
- `_0/_1.nif` 与 ShapeData source 完全同哈希时，应怀疑 preset 根本没有真实构建到运行时输出。
- MO2 高优先级 BodySlide Output 中的旧 TRI 可以继续覆盖新工程；只查原模组目录会漏掉 winner。
- Shape 改名后必须同步 OSP/OSD/TRI/运行时资源，不能只改 NIF 显示名。

这些结论支持把 Kitty 路线作为紧身全包类装备的重要路径，但不证明每个项目都应使用完全相同的 Zap 区域或 preset。

## 参考

- 本仓库 Issue #1：`Kitty BodySlide 修复复盘：Zap 默认关闭、未构建的运行时网格与旧 TRI 覆盖`
- `bodyslide.md`：BodySlide 数据角色、Conform、分组、隔离构建与索引冻结
- `modeling.md`：保索引与重拓扑路线
- `materials-deployment.md`：MO2 winner 与运行时部署
