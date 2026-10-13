# 带权重与 BodySlide 的 Blender 往返、连续接边

## 先定义“无损”

| 路线 | 可以证明的内容 | 不能声称 |
|---|---|---|
| 同索引局部改形 | 点身份、faces、UV、未修改权重/OSD 和其他 NIF 块保持；只改允许字段 | 旧 delta 对新轮廓一定合理、所有动作不穿插 |
| 重拓扑/拆点/真正焊接 | 显式对应、重新转移的权重和 morph 可检查 | 原逐点数据和原文件逐字节无损 |
| 两个 shape 连续接边 | 同一边界曲线、材质、delta、skin 与光照法线协调，保留原索引 | 已焊接成单一拓扑网格 |

不要只比较顶点数。重排、焊接后再拆点，点数也可能相同。OSD/TRI 的索引依赖最终游戏顶点，UV 缝和硬边拆点也必须包含在映射中。

## 保索引编辑通道

1. 从实际 ShapeData NIF 和 OSP/OSD 读取基线，保存哈希、shape 名、点身份、面顺序/朝向、loop UV、权重、骨名、分区、材质和 extra data。原 NIF 留作容器，不通过未知 exporter 完整重存。
2. 少量试点：移动一个已知索引，往返后核对落点、faces、UV 与已知 slider。使用 PyNifly/Outfit Studio 的直接导入导出路线时，记录确切插件版本/坐标转换/骨名选项，不能把一次成功推广为所有 NIF。
3. 可以使用下列 JSON bridge：它从 `audit_nif.py --snapshot` 的三角化导出点直接生成 Blender 对象、骨名 vertex groups 及 `_original_vertex_id` POINT 属性。NIF UV 缝对应的重复点保持独立；这些对象是 NIF shape-local 编辑代理，不是已装好完整骨架的动画工程。
4. 编辑 Basis 时保留拓扑和 UV。雕刻位移、手动移动、平滑可走此路线；Remesh、Decimate、Merge by Distance、删面和细分改变索引语义，应切换重建路线。不要 apply transforms 掩盖空间不匹配。
5. 导出读取原 Basis，而非当前 pose/shape-key 混合或 modifier 的 evaluated surface。可按保留的 point ID 恢复点序；缺失/重复 ID、faces/UV 变化、对象变换或启用的 modifier 都拒绝。脚本只写新 JSON，不写原 NIF/OSD。

```text
blender --background --factory-startup --disable-autoexec --python indexed_blender_bridge.py -- import source-snapshot.json --blend NEW-edit.blend
blender --background --factory-startup NEW-edit.blend --disable-autoexec --python indexed_blender_bridge.py -- export source-snapshot.json --out NEW-edited.json
```

脚本路径在 `scripts/`。`import` 唯一会保存的 blend 是指定的新文件；输入快照/原工程不改。原骨架、bind/skin transforms、材质和分区应保留在原 NIF 中，不能从代理对象的 identity transform 反推新的绑定矩阵。`--allow-weight-edits` 才允许修改权重，导出仍检查骨名、非负、最多 4 项及量化容差。默认拒绝权重漂移。

## 滑块通过哪一层传递

原 OSD 保留在外部最稳妥。`audit_bodyslide.py` 中的 `osd_entries` 可读本技能支持的 OSD v1；先解析 OSP 的 Data target/shape alias，再按具体 shape 组装稠密 delta，缺值补零。不要把 UV morph、Zap 或 clamp 数据直接当位置 shape key。

可给快照每个 mesh 增加：

```json
{"morphs":{"ExampleSlider":[[0,0,0],[0,0,0.1],[0,0,0]]}}
```

此时 bridge 将其导入相对 Basis 的 shape keys，并按原 ID 导出 delta。它不解释 OSP 默认值、反向/隐藏/Zap/夹限、reference 与构建行为，也不创建 OSD 文件。这些语义必须留在项目层。只支持相对 Basis 的 keys，改 key 名或删除 key 会拒绝。

**仅修改基形时的陷阱**：若改变 Basis，却让所有其他 key 的绝对坐标保持原样，导出的 delta 会多出负的基形位移。若原意是保留旧 delta，应给每个 key 加同一基形位移，或直接保留外部 OSD；若原意是重塑 slider 的最终表面，则计算新的 `key_position - new_basis`。两种意图不要混用。

## 回写 NIF / BS 的边界

本仓库的 bridge 和 surface_transfer 是身份检查及数据交换工具，**不是通用 NIF exporter**。回写须由已核验版本的工具或受限布局 writer 完成：

- 检查游戏/NIF/BS stream 版本、shape 类型、vertex descriptor、skin partition 数量与 bone palette；只支持过的布局才能写，不用案例字节偏移猜别的文件。
- 使用原 NIF 容器，按索引写允许变化的位置。改形后重算几何法线和切线，更新包围信息；分区中有重复 vertex buffer 或 skin 数据时同步维护。
- 改权重时，骨名映射到该 shape 的实际骨列表和 partition palette，同步受影响的所有权重副本及 NiSkinData，保留 bind transforms；导出半精度量化会有微小数值误差，报告实测残差。
- 形成明确 block/field allowlist，对其余块逐字节比较；用独立读取回查 shape 数、faces/UV、骨名/绑定/分区。完整 `NifFile.save()` 若会重构无关数据，则不能作为“保留无关块”的路线。
- 将修改写回 ShapeData；受影响的 OSD、OSP、FP 源同步。使用隔离 BodySlide 构建 `_0/_1` 和按需 TRI，再审计最终索引/BODYTRI，最后部署 MO2 实际 winner。
- 用户明确自行点构建时，交付完整源工程和构建清单，记录 build pending；不要替用户执行，也不要把暂存基形当已应用 preset。

## 连接两段已带权重/滑块的衣服

先限定部件、左右侧和层。检测开口边界时，可以在**分析副本**按位置聚类 UV 重复点；不要直接焊掉生产网格。

1. 选择稳定的一侧为主曲线；比较方向和周期相位，建立另一侧到主曲线顶点/边的显式对应。近邻距离只是候选，还要检查边界顺序和法线。
2. 若两边的分段不同，简单等弧长采样通常只近似同一曲线，另一侧的直线弦可能跨过主曲线折点。要精确共享折线，需要保留所有必要折点。案例恰好是 50/51 点，可以保留 50 个折点再加一个边中点；并非任意两条环都能不改拓扑解决。无法容纳必要折点时进入重建路线。
3. 主边界 A 不动，B 的边界落到同一曲线上，附近顶点以有限衰减平移：`B'_i = B_i + f_i*(A_mapped_boundary - B_nearest_boundary)`。边界 f=1，远处 f=0；过渡宽度按网格密度与造型选，不照抄案例数字。
4. 每个相关位置 slider 做同样的边界约束：

```text
deltaB'_i(s) = deltaB_i(s)
              + f_i * (deltaA_mapped_boundary(s) - deltaB_nearest_boundary(s))
```

这样边界基形和 delta 都一致，线性 slider 组合下边界仍对齐。`surface_transfer.synchronize_delta` 提供这一步的纯数值 helper。缺 B 数据时创建正确 dataset 与 OSP Data 引用，更新主/FP 工程；别静默跳过。

5. 附近 skin 用同一衰减混合主边界按骨名插值的权重，top4 并归一化；边界以相同参数化的权重为目标。两个 shape 若 bind transforms 不同，仅权重相同仍不能保证动作接合。
6. 协调边界法线、重算各自 UV 下的切线，统一材质分区和贴图采样。连续世界法线不意味着两片不同 UV 可以复制相同的切线法线 RGB；需要检查实际光照接缝。

有中间插值点时，top4 裁剪、NIF 半精度权重、不同骨骼/物理或非线性变形都可能产生残差。逐个 slider 静态通过不代替动画/物理验收。实际案例和误差见 [bioenclosure-case.md](bioenclosure-case.md)。
