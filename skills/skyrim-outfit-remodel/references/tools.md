# 检查工具与命令

Python 工具使用 Python 3.10+ 标准库。`blender_probe.py` 在 Blender 自带 Python 中运行；`audit_nif.py` 需要外部 PyNifly Python 源码与匹配的 NiflyDLL。仓库不分发 Blender、BodySlide 或 DLL。先核查各工具版本，不静默安装或更新用户环境。

以下命令中的尖括号必须替换为实际值。含空格路径保留引号。报告和快照写到工作区的 evidence 目录；包含原模组几何的快照不能随公开技能发布。

## Blender 原始网格

```powershell
& '<blender.exe>' --background --disable-autoexec '<input.blend>' --python '<skill>/scripts/blender_probe.py' -- --objects '<meshA>' '<meshB>' --out '<evidence>/mesh.json' --report '<evidence>/mesh-report.json'
& '<python>' '<skill>/scripts/audit_mesh.py' '<evidence>/mesh.json' --out '<evidence>/mesh-report.json'
```

probe 不保存 blend、不应用 modifier；它采样 object-local basis，并记录对象矩阵、modifier 和 shape key 名称/点数/当前值。它**不采样当前 shape key 混合后或 modifier 后的表面**，不审计每个 shape key 坐标，也不证明当前可见形状正常。当前展示形状与游戏导出要另查。Blender 未找到指定对象会报错。probe 生成报告不把审计 fail 转成进程失败，自动流程必须读报告的 `pass`；独立 audit_mesh 返回码 0/2 对应检查通过/失败。

权重只采集实际 Armature modifier 骨列表内的组；其他组记为 `non_deform_groups`，其中可能含误拼骨名，必须人工核对，不可视为已证明无未知组。没有 Armature 时不会假设 skinned。

## 快照 schema 1

```json
{
  "schema": 1,
  "coordinate_space": "object_local_basis",
  "meshes": [{
    "name": "Equipment",
    "vertices": [[0,0,0], [1,0,0], [0,1,0]],
    "faces": [[0,1,2]],
    "uv_faces": [[[0,0], [1,0], [0,1]]],
    "normals": [[0,0,1], [0,0,1], [0,0,1]],
    "weights": [{"Bone":1}, {"Bone":1}, {"Bone":1}],
    "skinned": true,
    "bones": ["Bone"],
    "matrix_world": null
  }]
}
```

faces 为 0 起始索引；UV 每面每角一个值。normals 可省略，提供时为逐点法线，不能表示所有 split corner normals。静态 shape 设置 skinned=false，可用空 weights/bones。NIF snapshot 的坐标空间为 nif_shape_local，matrix_world=null；禁止直接跨不同坐标空间比较。

audit_mesh 检查非法点/面、重复/退化面、UV 缺失/非法、权重和可选法线数值。边界、非流形、游离点、退化 UV 产生 warnings，需结合开口/镜像等设计决定是否修复；`pass=true` 不等于所有 warnings 已处理。面积扇形算法只是筛查，不证明多边形没有自交。法线只检查有限数值/长度，非单位、零向量、方向/切线和硬边连续性另查。

## 索引保持路线的保护检查

```powershell
& '<python>' '<skill>/scripts/compare_mesh.py' '<before.json>' '<after.json>' --allow-indices '<allowed.json>' --tolerance 0.000001 --out '<compare.json>'
```

allowed.json 示例：`{"Equipment":[12,13,14]}`。只允许这些索引的坐标变化，其余坐标和全体 faces/UV/weights/bones/matrix/skinned 要保持。容差单位是快照本身的坐标单位，按工程尺度制定。没有 allow map 时所有顶点受保护。

不比较 normals/materials/shape keys/骨骼 rest transform。点序相同是调用者必须证明的前提；同点数不是证明，重拓扑不能使用该报告声称区域保护通过。空快照/非法容差拒绝接受。

## NIF 只读审计

```powershell
& '<python>' '<skill>/scripts/audit_nif.py' '<input.nif>' --pynifly-root '<PyNifly root containing pyn>' --dll '<NiflyDLL.dll>' --snapshot '<nif-snapshot.json>' --out '<nif-report.json>'
```

读取几何/UV/法线/骨权重、纹理引用、分区 ID、NiStringExtraData，并记录输入与 DLL 哈希；结束后验证输入未变。**不调用 NifFile.save**。外部 API 不兼容时给出 traceback，不能回退为成功空报告。未检查：bind/skin transform 数值、骨列表索引结构、分区逐面覆盖、外部资源 winner、材质条件结构、完整 extra-data 类型。需专用检查器/独立工具和姿态测试补齐。

## OSP / OSD / BodySlide TRIP

报告的 `constant_hidden_geometry` 列出存在非零位置差分、隐藏且两体重默认相同非零的项；出现 warning 时查裸基形与默认加载状态。它不自动判错误，也不授权烘焙，具体流程见 [base-shape.md](base-shape.md)。

```powershell
& '<python>' '<skill>/scripts/audit_bodyslide.py' '<project.osp>' --project '<exact project name>' --data-root '<Data>' --source-snapshot '<source-NIF-snapshot.json>' --tri '<built.tri>' --runtime-snapshot '<built-NIF-snapshot.json>' --out '<bs-report.json>'
```

data-root 下应有 `CalienteTools/BodySlide/ShapeData`。支持 SliderSetInfo version=1 中单个精确命名 SliderSet、local=true/1 的 OSD v1 数据集；Shape 的 target 别名按其文本对应实际 NIF shape。外部数据集、其他容器/版本、TRI 扩展要调研，不静默忽略。TRIP reader 支持 PIRT 的 position block 与可选 UV block（含空 UV block），不支持头部 FRTRI。必需用**最终运行时 NIF**快照校验 TRI；OSD 则用 ShapeData NIF。没有 source-snapshot 时仅查引用，不查 OSD 索引。

范围合法不证明对应语义；缺滑块、错误 base、delta 投到错误位置、zap/UV 拆点映射等仍需实际构建/已知 slider 对照。reader 不修改 OSP/OSD/TRI。

## 实际构建

```powershell
& '<python>' '<skill>/scripts/build_bodyslide.py' --exe '<isolated BodySlide.exe>' --project '<exact name>' --preset '<preset name or XML path>' --stage '<NEW stage>' --trimorphs --expected 'meshes/Outfit/outfit_0.nif' 'meshes/Outfit/outfit_1.nif' 'meshes/Outfit/outfit.tri'
```

先在独立工具副本核查 Config.xml 的 ProjectPath、GameDataPath、TargetGame 与 source/preset 路径，或者使用已核验的 MO2 VFS 环境。脚本不会配置输入、替换原模组或启动游戏。stage 必须不存在；包装脚本写 stage/Data、owner 标记、stdout/stderr、构建报告。BodySlide 自身可能向其工作目录写配置/日志，因此使用隔离工具副本，并先审计 OSP 输出路径。只检查进程成功和本轮非空预期输出，随后需审计实际 NIF/TRI。默认超时 180 秒，CLI 可调整；超时需诊断，不反复盲跑。进程自身报错前的输出保留供诊断。

## 交付哈希

```powershell
& '<python>' '<skill>/scripts/manifest.py' make '<explicit package root>' '<manifest.json>'
& '<python>' '<skill>/scripts/manifest.py' verify '<explicit package root>' '<manifest.json>'
```

扫描明确根目录，记录路径/字节/sha256，verify 报 changed/missing/extra。排除 manifest 本身及 .git/__pycache__/.pytest_cache/.local-validation；报告中有排除规则。拒绝符号链接/越界路径，不用于删除或自动部署。打包前仍检查文件清单和授权范围。

## 贴身映射与保索引编辑

`surface_transfer.py` 使用标准库，输入显式 donor/系数/offset/骨名权重/稠密 delta，输出新 JSON。格式、公式和限制见 [fitted-clothing.md](fitted-clothing.md)。不查最近面、不创建网格、不写 OSD/NIF、不部署。

`indexed_blender_bridge.py` 在 Blender 中执行，以 NIF 审计快照作为 shape-local 代理。import 写全新 blend，export 校验 point-ID 双射、faces/UV、变换、权重和位置 morph 后写新 JSON。导回原 NIF 与 BodySlide 的步骤、命令及形态语义见 [indexed-roundtrip.md](indexed-roundtrip.md)。它不提供通用 NIF serializer、完整骨架动画导入或自动 OSP/OSD exporter。
