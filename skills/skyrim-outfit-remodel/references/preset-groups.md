# BodySlide Preset Group 匹配路线

本路线来自 `AE_VRC_Dwarven_BioEnclosure_suit_A` 的真实故障：Outfit 本身、NIF、OSD 与 slider 都可以正常，但 BodySlide 的预设列表异常，只显示残留的上次预设名称或无法切换到其他 3BA preset。根因不是几何，而是 **Outfit group 与 Preset group 没有有效交集**。

适用于：新建、改名、复制或重组 BodySlide 项目后，项目能显示，但目标 preset 消失、只剩一项、无法真实应用，或 UI 仍显示旧预设名但滑块/预览不随之变化。

## 核心规则

BodySlide 项目至少应满足：

```text
Outfit Groups ∩ Target Preset Groups ≠ ∅
```

例如目标是 3BA：

```text
Outfit Groups:  AE_VRC_Dwarven_BioEnclosure + 3BA
Preset Groups:  3BA + 3BBB + CBBE
Intersection:   3BA
```

自定义装备组可以继续保留，用于 Batch Build、分类或项目管理；但不能只保留自定义组而遗漏目标身体体系的兼容组。

## 典型故障

错误状态：

```xml
<Group name="AE_VRC_Dwarven_BioEnclosure">
    <Member name="AE_VRC_Dwarven_BioEnclosure_suit_A"/>
</Group>
```

如果目标 preset 只声明 `3BA`、`3BBB`、`CBBE` 等组，那么自定义组与 preset 组交集为空。BodySlide 会把这些 preset 过滤掉。

UI 中残留 `SelectedPreset=Creamy Curves` 或下拉框仍显示某个名字，不能证明该 preset 已对当前 Outfit 成功加载。验收必须实际展开预设列表、切换目标 preset，并确认 slider 值和预览发生对应变化。

## 最小修复

保留原自定义组，并为目标 Outfit 增加目标身体体系的 master/compatibility group。例如：

```xml
<Group name="3BA">
    <Member name="AE_VRC_Dwarven_BioEnclosure_suit_A"/>
</Group>
```

修复 group 元数据时，不应顺手重写 NIF、OSD、OSP 几何、材质或权重；如果这些文件没有独立证据表明有问题，就保持不变。

## Agent 执行顺序

1. 找到 MO2/VFS 实际生效的 OSP、SliderGroups XML 与目标 preset XML，先排除同相对路径的高优先级覆盖。
2. 精确确认 Outfit 名称；Group 的 `<Member name>` 必须与 BodySlide 项目显示/匹配名称一致。
3. 收集该 Outfit 的全部 groups 与目标 preset 的全部 groups。
4. 计算交集；为空时优先修复 group 元数据，不进入 NIF/OSD/权重排查。
5. 对 3BA 项目，保留自定义装备组，同时补充 `3BA` 或当前目标体型要求的兼容组；不要凭模组文件夹名称给所有项目随意添加体型标签。
6. 正常关闭 BodySlide，从实际 MO2 入口重新启动，避免只观察缓存状态。
7. 展开 preset 列表，实际选择目标 preset；确认 slider 数值和预览随 preset 改变。
8. 只有在 preset 能真实应用后，才继续 Build、低高体重与游戏验收。

## 最小验收 Gate

- **G1 Winner**：OSP、SliderGroups、preset XML 都来自实际生效 provider，无旧文件覆盖。
- **G2 Name**：Group Member 精确指向目标 Outfit。
- **G3 Compatibility**：`Outfit Groups ∩ Target Preset Groups` 非空。
- **G4 GUI**：重启 BodySlide 后预设列表恢复；不是只显示旧 `SelectedPreset` 文本。
- **G5 Apply**：实际切换目标 preset 后 slider 值与预览发生对应变化。
- **G6 Build**：需要时再执行真实 Build；Group 修复本身不等于几何/游戏验收通过。

## 与其他故障的边界

- **项目完全不显示**：先查 OSP、SliderSets、DataFolder、MO2 winner，不先归因 group。
- **Preset 可选但 slider 不动**：查 reference、shape/data 映射、OSD，而不是继续加 group。
- **Build 卡死/无响应**：查几何、Zap、weld/adjacency、输出链；参见 `kitty-recovery.md`。
- **游戏仍是旧模型**：查 `_0/_1/TRI` 与 MO2 winner；Group 只控制 BodySlide 侧的项目/preset 兼容性。

## 案例

仓库 Issue #2：`矮人 BioEnclosure 预设无法选择：自定义装备组缺少 3BA 关联`。

该案例的最小修复只是在目标 SliderGroups XML 中新增 `3BA` membership；原自定义组继续保留，OSP、源 NIF/OSD、preset 本体不需要为此重写。
