# Agent / AI 工具编排

本技能不把 agent 限定为只读文档或手工 GUI。执行 remodel 前先发现当前机器已经可用的 AI、MCP、Blender、NIF 与 BodySlide 工具，再按任务选择最短、可验证的执行链。工具存在不等于必须调用；只在它能直接提高当前阶段质量、速度或可复现性时使用。

## 1. 先发现实际工具

工具根目录按以下优先级确定：

1. 用户明确指定的工作区；例如 `E:\SkyrimAI`。
2. 环境变量 `SKYRIM_AI_ROOT` 指向的目录。
3. 当前工程及其父目录中可识别的工具工作区。

常见布局可以包含：

```text
<AI_ROOT>/
  ComfyUI/       # 图像生成、参考图、局部重绘等
  MCP/           # Blender 或其他 MCP server / adapter
  skills/        # 其他可复用 agent skill
  workflows/     # 已验证工作流
  outputs/       # 生成结果
  logs/          # 执行日志
```

目录名只是线索。agent 必须读取实际配置、`--help`、MCP resource/tool 列表或工作流文件确认能力，不因目录存在就宣称工具可用。不要扫描、复制或提交凭据文件；API key 只由对应工具在运行时读取。

## 2. 按能力路由

| 当前任务 | 优先工具 | 主要证据 |
|---|---|---|
| 参考图补全、统一多视图、局部设计探索 | 已验证的 ComfyUI / 图像生成 workflow | workflow、副本/标识、模型或 checkpoint、seed（如适用）、输出图 |
| 参考图与当前模型的形体比较 | 具视觉能力的 agent + 同角度 Blender render | 对照图、差异说明、可量化尺寸/轮廓 |
| 实际几何编辑、局部雕改、法线/UV 操作 | Blender MCP；批量且确定的操作优先 Blender Python | 修改后的 `.blend`、操作记录、同角度前后 render |
| NIF 读写与结构核查 | PyNifly / NiflyDLL + 本技能审计工具 | 输入/输出哈希、NIF 审计报告 |
| 权重、BodySlide、OSD/TRI、构建 | Outfit Studio / BodySlide + 本技能审计/构建工具 | OSP/OSD/TRI、实际构建输出、审计报告 |
| TruePBR / 材质部署 | `$skyrim-truepbr-workflow` 及其规定工具 | 通道、配置、构建和游戏证据 |
| 未知版本、格式或工具行为 | 官方 GitHub / 作者文档，必要时最小实验 | 来源、版本、复现实验 |

音频、语音等与服装 remodel 无关的 AI 工具即使位于同一工作区，也不进入本技能执行链。

## 3. Agy 的默认执行循环

1. **Probe**：列出当前任务真正可调用的工具、版本、入口与限制，写入 job/HANDOFF。
2. **Baseline**：保护源资产并建立当前形体、拓扑、权重、BodySlide 和视觉基线。
3. **Reference**：仅在参考不足时调用图像 AI；优先复用 `workflows/` 中已验证工作流，统一姿态、镜头和比例。
4. **Edit**：几何工作由 Blender MCP / Blender Python 实际修改，不把图像生成结果当作模型修改本身。
5. **Render & Review**：自动输出与参考一致的正、侧、背或任务要求视图，让视觉模型/agent 对比轮廓、体积和局部结构。
6. **Numeric QA**：进入后续 Gate 前运行对应 mesh/NIF/BodySlide 检查，视觉通过不能替代数据通过。
7. **Iterate**：根据明确差异继续局部修改；每轮保留可回滚节点。参考矛盾时先确定主参考，不让生成模型在多个随机方案之间漂移。
8. **Freeze**：形体确认后冻结拓扑/索引策略，再进入 UV、权重、morph、材质与游戏交付。

对于可重复的确定性操作，优先脚本或 MCP tool call；对于视觉判断和设计补全，使用图像/视觉模型。不要用鼠标自动化替代已有稳定 API、CLI 或 MCP 接口。

## 4. AI 参考的证据等级

参考优先级默认是：

```text
用户明确指定的真实参考 / 已确认设计
  > 原始或已验证的游戏资产
  > 已确认目标身体、骨架与穿戴姿态
  > AI 生成的补充参考
```

AI 图可以帮助确定比例、轮廓、结构和材质方向，但不能证明真实拓扑、骨骼位置、权重、UV、BodySlide delta 或 NIF 结构。生成多视图时固定主体设计、镜头规则和可复现参数；视图互相冲突时回到用户指定的主轮廓。

## 5. ComfyUI 使用规则

- 优先复用 `<AI_ROOT>/workflows` 内已经验证的 workflow，而不是临时重新搭一套。
- 生成任务要保存 workflow 标识/副本、核心模型或 checkpoint、关键参数和输出；能固定 seed 时固定 seed。
- 原始工作流和模型默认只读；本次试验产生的新 workflow 放入本次 job/evidence，再决定是否升级为共享 workflow。
- ComfyUI 输出属于参考或视觉证据，不直接宣称模型已通过 Gate B/C/D/E。

## 6. Blender MCP 使用规则

- 先确认 MCP server 与 Blender addon 实际连接，再执行场景修改。
- 可逆局部编辑可以直接由 Agy 自主执行；每个重要阶段保存新版本或明确回滚点。
- 大范围重拓扑前确认当前路线是“保索引”还是“重拓扑”，不要让 MCP 在不知情时破坏 OSD/TRI 对应。
- MCP 操作完成后必须重新读取/渲染结果；tool call 成功只说明命令执行，不说明形体正确。
- 重复批处理优先生成/运行 Blender Python，并把脚本或命令记录到 evidence，避免大量不可复现的逐点 UI 操作。

## 7. 记录与交接

每件装备的 HANDOFF 至少记录本次实际调用的工具，而不是只写“AI 已处理”：

```text
AI/tool workspace: <root or unavailable>
Reference generation: <tool/workflow/model/seed or not used>
Geometry execution: <Blender MCP / Blender Python / manual>
NIF I/O: <PyNifly/NiflyDLL version or hash>
BodySlide/OS: <version and project>
Evidence: <renders/reports/workflow/log paths>
Pending tools/tests: <items>
```

本地绝对路径可留在私有 HANDOFF/evidence；公开仓库只提交去标识化的流程、测试和汇总。API key、token、个人路径清单、第三方模型与生成缓存不进入公开仓库。
