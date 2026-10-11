# 权重、绑定与动作

## 供体与转移

使用匹配游戏、性别/种族、体型和姿态的实际骨架；身体/手/脚/头/物理件可能需要不同供体。保留骨名、bind transform、蒙皮结构和分区。权重归一化不能修复错误的 bind pose。先对齐供体和装备的 rest/bind 状态，不用 apply pose as rest、全清变换或随意改骨名掩盖偏移；PyNifly 方向/重命名选项前后一致。[PyNifly](https://github.com/BadDogSkyrim/PyNifly/wiki)

1. 原权重健康且索引不变则保留，姿态测试后只修局部。
2. 新拓扑按部位转移 deform groups；Outfit Studio 选目标 shape，使用 `Shape → Copy Selected Weights` 或 `Copy Bone Weights`，记录供体/骨骼/区域/选项。[作者步骤](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Copying-bone-weights)
3. 手指、左右腿、内外层和刚性板分开处理。先小范围检查，再适量放宽；未覆盖点找正确供体，不无限扩大半径。[复制选项](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Weight-Copy-Options)
4. 保护自定义/SMP 骨链和运动层，人体权重不能整件覆盖；见 physics.md。

## 局部判断

| 部位 | 判断 |
|---|---|
| 领口 | 下缘随胸肩，向上渐变到实际颈骨；是否加少量 Head 由高度和动作决定。不整圈硬绑胸或头 |
| 手套 | 每根指节独立供体，指蹼/拇指单查，手腕向前臂渐变 |
| 鞋靴 | 筒随小腿/膝、鞋面随足；跟座/细跟合理刚性，避免远端脚趾拉伸 |
| 硬甲 | 刚板与软接合分开；集中权重保持刚性，动作决定边缘过渡 |
| 紧身服 | 与内层身体协调变形；外层留活动空间，不把静态零间隙当正确贴合 |

## 数值和结构验收

这里支持的 Skyrim SE/AE 常规 skinned NIF 每点有效骨骼影响最多 4，非负/有限、总和接近 1，无未加权点，引用骨骼存在。OS 保存会裁为最强四项再归一化，必须在导出后复查。[归一化](https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Weight-Normalization)

清无效微权重、保护必要骨骼、限制影响数、归一化，再查折痕。不要删除用于分区的非 deform groups。非 skinned 静态件不强制加权；审计必须正确标记。

检查输出骨名/骨列表索引/权重/绑定变换/分区面覆盖/插槽。能解析文件不等于蒙皮正确；两个同用 Nifly 的界面也不是独立解析器。

## 姿态测试

身体和外层用同骨架/姿态。先单关节再组合，记录角度或动画：领口左右转头、低/仰头、肩动；手套握拳/展开/拇指/腕；上衣抬臂/前伸/屈肘/扭转；下装髋膝/蹲伏/足踝。按用途补坐姿。

在低/中/高体重和主要 slider 极值下重复相关动作。静态间隙不证明动态无穿插；不露皮也可能是误删身体，应同时查遮挡策略与插槽。
