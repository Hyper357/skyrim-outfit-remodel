# Agent / AI 工具编排

本技能不把 agent 限定为只读文档或手工 GUI。执行 remodel 前先发现当前机器已经可用的 AI、MCP、Blender、NIF、BodySlide 与 Skyrim 专项 agent 工具，再按任务选择最短、可验证的执行链。工具存在不等于必须调用；只在它能直接提高当前阶段质量、速度或可复现性时使用。

## 1. 先发现实际工具

工具根目录按以下优先级确定：

1. 用户明确指定的工作区；例如 `E:\SkyrimAI`。
2. 环境变量 `SKYRIM_AI_ROOT` 指向的目录。
3. 当前工程及其父目录中可识别的工具工作区。

常见布局可以包含：

```text
<AI_ROOT>/
  ComfyUI/                        # 图像生成、参考图、局部重绘等
  MCP/                            # Blender 或其他 MCP server / adapter
  skills/                         # 其他可复用 agent skill
  workflows/                      # 已验证工作流
  outputs/                        # 生成结果
  logs/                           # 执行日志
  skyrimvr-claude-toolkit-*/      # Skyrim AI Assistant Toolkit；版本号目录名只作线索
```

目录名只是线索。agent 必须读取实际配置、`--help`、MCP resource/tool 列表、工作流文件或工具自带说明确认能力，不因目录存在就宣称工具可用。不要扫描、复制或提交凭据文件；API key 只由对应工具在运行时读取。

如果发现 `skyrimvr-claude-toolkit-*`，将它识别为 **Skyrim AI Assistant Toolkit**，不是普通素材目录。先读取其 `README.md`、`AGENTS.md`、版本/发行信息和本地配置；例如用户当前工作区可能出现 `skyrimvr-claude-toolkit-3.9.1`。目录名中的版本不能替代工具自己的版本与配置探测。

## 2. 按能力路由

| 当前任务 | 优先工具 | 主要证据 |
|---|---|---|
| 参考图补全、统一多视图、局部设计探索 | 已验证的 ComfyUI / 图像生成 workflow | workflow、副本/标识、模型或 checkpoint、seed（如适用）、输出图 |
| 参考图与当前模型的形体比较 | 具视觉能力的 agent + 同角度 Blender render | 对照图、差异说明、可量化尺寸/轮廓 |
| 实际几何编辑、局部雕改、法线/UV 操作 | Blender MCP；批量且确定的操作优先 Blender Python | 修改后的 `.blend`、操作记录、同角度前后 render |
| NIF 读写与结构核查 | PyNifly / NiflyDLL + 本技能审计工具；已配置时可调用 Skyrim AI Assistant Toolkit 的 NIF 工具 | 输入/输出哈希、NIF 审计报告、独立解析结果 |
| NIF 几何手术、动画控制器、独立渲染证明 | Skyrim AI Assistant Toolkit + PyNifly / NifSkope / headless Blender（按实际可用组件） | 输入/输出哈希、解析 gate、render PNG、操作日志 |
| 权重、BodySlide、OSD/TRI、构建 | Outfit Studio / BodySlide + 本技能审计/构建工具 | OSP/OSD/TRI、实际构建输出、审计报告 |
| ESP/TXST/记录 winner、插件结构或覆盖链 | Skyrim AI Assistant Toolkit 的 xEdit/xeditlib/Spriggit/skyrim-winner 路线（仅已配置时） | 记录链、winner、插件 diff 或序列化 diff |
| Papyrus/CrashLogger/SKSE 相关运行时诊断 | Skyrim AI Assistant Toolkit 的 triage / load-status 工具（若当前问题需要） | 归类报告、日志总量与命中项、版本信息 |
| TruePBR / 材质部署 | `$skyrim-truepbr-workflow` 及其规定工具；插件/TXST 复核可借助 toolkit | 通道、配置、构建和游戏证据 |
| 未知版本、格式或工具行为 | 官方 GitHub / 作者文档，必要时最小实验 | 来源、版本、复现实验 |

音频、语音等与服装 remodel 无关的 AI 工具即使位于同一工作区，也不自动进入本技能执行链；只有当前装备任务确实涉及音频/插件联动时才按专项需求调用。

## 3. Skyrim AI Assistant Toolkit 的定位

该工具包是 **Skyrim 专项辅助与验证层**，不是 BodySlide remodel 本身的替代品。它公开说明的能力包括 NIF/PyNifly 处理、headless Blender 渲染验证、NifSkope/PyNifly 双 gate、ESP/xEdit/Spriggit、BSA、日志诊断等；具体能力以本机版本和已安装的 optional tools 为准。

Agy 发现该工具后：

1. 记录工具根目录和版本；版本化目录如 `skyrimvr-claude-toolkit-3.9.1` 可作为候选，但仍读取实际说明/元数据确认。
2. 判断是“仅解压存在”还是“已完成 setup/config”。如果只解压未配置，标记 `present/unconfigured`，不要假称 hooks、xeditlib、PyNifly、NifSkope 或 Blender 已可用。
3. 若其 hooks 已配置，按工具自己的 canary / toolchain check 验证；未运行验证时写 `unknown`，不写 `pass`。
4. 仅调用与当前 remodel 有关的组件。优先价值通常是：NIF 独立检查、NIF 几何处理、headless render proof、插件 winner/记录分析、崩溃/脚本日志诊断。
5. Skyrim VR 经验不能直接当 SE/AE 结论；执行前按当前游戏版本读取 toolkit 的版本专项指导。
6. 该 toolkit 的成功结果也必须回到本技能 Gate：例如 render 正常不等于权重/BodySlide 正确，NIF 可解析不等于动画姿态或游戏穿戴通过。

对于常规服装 remodel，推荐关系是：

```text
Agy
 ├─ ComfyUI / visual model        -> 参考和视觉比较
 ├─ Blender MCP / Blender Python  -> 实际几何编辑
 ├─ Skyrim AI Assistant Toolkit   -> Skyrim 专项 NIF/ESP/render/runtime 辅助
 ├─ PyNifly / NiflyDLL            -> NIF I/O / 审计
 ├─ Outfit Studio / BodySlide     -> 权重、slider、OSD/TRI、构建
 └─ skyrim-outfit-remodel         -> 总流程、Gate、证据与交付
```

## 4. Agy 的默认执行循环

1. **Probe**：列出当前任务真正可调用的工具、版本、入口与限制，写入 job/HANDOFF；同时探测 Skyrim AI Assistant Toolkit 是否存在、是否配置及哪些组件可用。
2. **Baseline**：保护源资产并建立当前形体、拓扑、权重、BodySlide 和视觉基线。
3. **Reference**：仅在参考不足时调用图像 AI；优先复用 `workflows/` 中已验证工作流，统一姿态、镜头和比例。
4. **Edit**：几何工作由 Blender MCP / Blender Python 实际修改；需要 NIF 专项手术时可路由到 toolkit 的对应确定性工具，不把图像生成结果当作模型修改本身。
5. **Render & Review**：自动输出与参考一致的正、侧、背或任务要求视图；若 toolkit 的 headless render 链已配置，可作为额外 render proof / 独立 gate。
6. **Numeric QA**：进入后续 Gate 前运行对应 mesh/NIF/BodySlide 检查；视觉通过不能替代数据通过。
7. **Iterate**：根据明确差异继续局部修改；每轮保留可回滚节点。参考矛盾时先确定主参考，不让生成模型在多个随机方案之间漂移。
8. **Freeze**：形体确认后冻结拓扑/索引策略，再进入 UV、权重、morph、材质与游戏交付。

对于可重复的确定性操作，优先脚本或 MCP tool call；对于视觉判断和设计补全，使用图像/视觉模型。不要用鼠标自动化替代已有稳定 API、CLI 或 MCP 接口。

## 5. AI 参考的证据等级

参考优先级默认是：

```text
用户明确指定的真实参考 / 已确认设计
  > 原始或已验证的游戏资产
  > 已确认目标身体、骨架与穿戴姿态
  > AI 生成的补充参考
```

AI 图可以帮助确定比例、轮廓、结构和材质方向，但不能证明真实拓扑、骨骼位置、权重、UV、BodySlide delta 或 NIF 结构。生成多视图时固定主体设计、镜头规则和可复现参数；视图互相冲突时回到用户指定的主轮廓。

## 6. ComfyUI 使用规则

- 优先复用 `<AI_ROOT>/workflows` 内已经验证的 workflow，而不是临时重新搭一套。
- 生成任务要保存 workflow 标识/副本、核心模型或 checkpoint、关键参数和输出；能固定 seed 时固定 seed。
- 原始工作流和模型默认只读；本次试验产生的新 workflow 放入本次 job/evidence，再决定是否升级为共享 workflow。
- ComfyUI 输出属于参考或视觉证据，不直接宣称模型已通过 Gate B/C/D/E。

## 7. Blender MCP 使用规则

- 先确认 MCP server 与 Blender addon 实际连接，再执行场景修改。
- 可逆局部编辑可以直接由 Agy 自主执行；每个重要阶段保存新版本或明确回滚点。
- 大范围重拓扑前确认当前路线是“保索引”还是“重拓扑”，不要让 MCP 在不知情时破坏 OSD/TRI 对应。
- MCP 操作完成后必须重新读取/渲染结果；tool call 成功只说明命令执行，不说明形体正确。
- 重复批处理优先生成/运行 Blender Python，并把脚本或命令记录到 evidence，避免大量不可复现的逐点 UI 操作。

## 8. 记录与交接

每件装备的 HANDOFF 至少记录本次实际调用的工具，而不是只写“AI 已处理”：

```text
AI/tool workspace: <root or unavailable>
Skyrim AI Assistant Toolkit: <path/version/configured|unconfigured/not used>
Toolkit components used: <NIF/render/xEdit/Spriggit/triage/other or not used>
Reference generation: <tool/workflow/model/seed or not used>
Geometry execution: <Blender MCP / Blender Python / toolkit NIF tool / manual>
NIF I/O: <PyNifly/NiflyDLL version or hash>
BodySlide/OS: <version and project>
Evidence: <renders/reports/workflow/log paths>
Pending tools/tests: <items>
```

本地绝对路径可留在私有 HANDOFF/evidence；公开仓库只提交去标识化的流程、测试和汇总。API key、token、个人路径清单、第三方模型与生成缓存不进入公开仓库。
