# 贴身衣物：同一表面对应驱动基形、滑块和权重

用于乳胶衣、长袜、手套及半透明外层。先读 intake/weights/bodyslide 对应阶段；不要把个人 preset 烘焙两次。

## 选路线

**局部修原衣**：已有轮廓、UV、权重和 OSD 健康时，保留索引，按部位限定供体，建立一次身体三角面最近点及重心坐标映射。可用 Blender BVH/Shrinkwrap 找候选，但要排除左右腿、腋窝、胸下、内外层的误投射；限制距离、面向和解剖区域。别在每个 slider 状态重新找最近点，否则点会跳到另一片皮肤。

**从身体重建外壳**：原衣与目标体型差异大、半透明时浮空严重，可按原衣覆盖范围选取目标身体的表面，沿平滑法线外移，保留身体的 UV 缝。长边需要细分时共享边中点，避免相邻面产生 T 形接缝。新拓扑使用新映射与形态数据，不复用旧衣 OSD 索引。这是本次半透明版最终采用的路线；早期将旧衣包裹到身体的实验不是最终底稿。

## 建立唯一对应

对衣服点 i，保存身体 donor 索引 a/b/c、重心系数 u/v/w、局部间隙向量 o；直接复制身体点可用系数 (1,0,0)，边中点可用 (.5,.5,0)。在统一坐标系中：

```text
g_i = u*b_a + v*b_b + w*b_c + o_i
delta_g_i(s) = u*delta_b_a(s) + v*delta_b_b(s) + w*delta_b_c(s)
skin_g_i = normalize(top4(u*skin_b_a + v*skin_b_b + w*skin_b_c))
```

骨权重按**骨名**对齐，而非不同 shape 的骨列表编号。0 值缺失 slider 可以按零 delta 处理，但先确认它确实不存在，并非 OSP target 别名或数据集解析失败。法线可按对应插值后归一化；导出时重算正确的切线架。

固定间隙加上相同身体 delta 是可检查的近似：大变形后的法线方向、曲率和 top4 裁剪仍可能产生误差。对夸张 slider 可以按该 slider 的目标身体重新生成期望外壳，再计算相对基形 delta；对应关系仍保持固定。动作使用实际骨架和绑定矩阵，不能靠相同静态坐标保证动态一致。

`scripts/surface_transfer.py` 执行已明确映射的上述计算，标准库 JSON 输入，**不自动找对应、不写 NIF/OSD**：

```json
{"donor_vertices":[[0,0,0],[2,0,0],[0,2,0]],
 "donor_weights":[{"Thigh":1},{"Thigh":1},{"Pelvis":1}],
 "donor_morphs":{"Size":[[0,0,0],[0,0,1],[0,0,2]]},
 "map":[{"indices":[0,1,2],"weights":[0.5,0.25,0.25],"offset":[0,0,0.1]}]}
```

```text
python scripts/surface_transfer.py correspondence.json --out NEW-transfer.json
```

映射与 offset 的构造由建模阶段决定，不能拿示例的 0.1 当所有衣物的厚度。输入 morph 为 donor 顺序的稠密三向量；输出 morph 也是 delta，**不再加一次衣料厚度**。helper 对已量化供体权重允许总和偏差 .002，输出 top4 后归一化；这是数据检查阈值，不是通用变形误差阈值。

## 间隙与半透明内层

- 使用正向微间隙，不把原身体整体缩小来掩盖穿模。半透明区域必须有真实内层身体，外壳、内层采用同一 target body、preset、骨架及 slider 定义。
- 沿法线均匀膨胀会在紧密凹褶中翻面。比较新旧三角面朝向、面积，局部减小厚度；失败时停在 staged 文件，不能无限减薄直到数值碰巧通过。
- 材质边界拆 shape 时，保存 unsplit→split 映射。复制的边界点同时复制 UV、权重和每一个 morph；两侧位置、delta 和法线需要协调。
- 高领是独立设计区域。颈部适合的身体参考、骨骼过渡和覆盖范围需另做；不能被躯干选面规则顺手截掉。
- glossy amber 的“树脂感”与真实半透明分别处理。alpha blend、深度写入、shape 排序和不透明包边随目标 shader 验证，别把本案例 alpha flags 当通用值。

## 验收

检查 `_0/_1` 与中间体重、主要 slider 单项和组合、表面距离、翻面/退化、导出后 skin 量化误差；然后做相关关节动作和物理。半透明层要检查深度排序、双层皮肤、肤色与颈缝。有限单骨 LBS 数值实验只是诊断，不代表游戏动画、CBPC/SMP 已验收。

案例证据见 [bioenclosure-case.md](bioenclosure-case.md)。保索引往返与接边见 [indexed-roundtrip.md](indexed-roundtrip.md)。
