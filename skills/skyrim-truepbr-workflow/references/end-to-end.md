# 完整 TruePBR 流程与交付

按当前阶段读取 [材质通道](materials.md)、[Manager 版本兼容](manager-compatibility.md)；本页把它们串成可交接的顺序。不是对任意工具版本通用的一键转换器。

1. **确认输入与渲染环境。** 记录游戏/Community Shaders/Open Shaders/TruePBR、Manager、PGPatcher 和 texconv 的实际版本或哈希；检查活动 MO2 profile、原 mod、overwrite/生成器输出的 winner。区分已有 Classic/PBR、ShapeData 源和运行时 NIF。验证 feature 实际加载，设置项里的 Disable at Boot=false 只是“不禁用”。
2. **冻结已认可形体。** 保存 NIF/OSP/OSD/TRI 与插件基线。贴合、权重、滑块属于模型工作；PBR 转换本身不应顺带换身体/改 alpha/砍高领。多个套装需要唯一模型/BodySlide/TRI 路径与独立 ARMO/ARMA，不能靠同一个输出路径任选其一。
3. **建材料清单和私有匹配路径。** 按真实 shape/UV/组件定义 albedo、normal、RMAOS、CNR 及可选通道。共享旧 diffuse 但用途不同的部件先消除匹配歧义；不发布覆盖全 mod 的粗放 alias。原理和艺术分区见配套 [参考上色](../../skyrim-outfit-remodel/references/reference-colouring.md)。
4. **制作物理贴图。** albedo RGB 为 sRGB；normal/RMAOS/CNR 为线性。RMAOS=roughness/metallic/AO/specular，CNR alpha=coat roughness。保留自然褶皱，AO 无烘焙证据时用中性或明确标注 heuristic。树脂观感与真实透明分开；半透明需要真实、同形变的内层身体和目标 shader 的排序验证。
5. **编码并做像素回读。** 按通道选择 BC7/其他格式及完整 mip；需要 CNR alpha 不能用丢掉 alpha 的格式。普通 sRGB PNG→BC7 sRGB 的已验证 texconv profile 用 `-srgb -f BC7_UNORM_SRGB -m 0`，数据贴图保持线性。用 `audit_colour_roundtrip.py` 比较源 PNG 与解码 DDS；再查 header、尺寸和 mip。文件能打开不证明没有二次 gamma。
6. **创建 `.tpbr`。** 这是可脚本生成的 JSON 项目，但不嵌入源贴图。记录实际本地路径、匹配名、feature、参数和压缩 profile。`audit_manager_export.py PROJECT.tpbr --report NEW-project.json` 检查 prepared-BC7 输入；未来版本先看项目 loader，别臆造 HTTP/CLI 导出 API。
7. **明确执行路线。** 原生路线：Manager 查看代表材质，导出到新 staging，保留 raw native JSON/DDS。脚本路线：使用已验证工具生成 DDS、配置和 NIF，保留可编辑 `.tpbr`，明确它不是 Manager GUI export。两者都需要实际产物检查；项目/配置有效不代表 NIF 已转换。
8. **校验配置并生成 NIF。** 对目标版本 schema 检查部署 JSON，核对匹配一一对应及 clearcoat 组合。已知 Manager 0.7 漏 multilayer 的案例保留 raw，并只修项目明确请求且未冲突的字段。执行有界 PGPatcher 转换，或使用已核验的受限 NIF authoring route。后二者分开报告，不把直接预制 NIF 说成全加载顺序 patcher 已运行。
9. **读取实际 NIF。** 查 shader/type/flags/参数以及全部原始 texture slots：特别是 slot 5 RMAOS 和 slot 6 CNR，Classic wrapper 的条件可见槽会漏报。材质单改时非材质块应保持；有授权的几何修改则单独允许和核验。同步 ShapeData、第三/第一人称、地面模型；如装备身份/路径变更则同步插件、名称与说明。
10. **部署与交接。** 备份受影响 winner，按用户选择整合原 mod 或交付其他结构；不要默认增加一堆附加 mod。部署目录只保留一个不冲突的有效 PBR 配置，检查所有资源闭合与最终 winner，防止旧 BodySlide/PGPatcher 输出覆盖。用户自行构建时交接精确项目/组名与同 preset 要求。验收按文件、材质预览、实际构建、动作/物理、游戏分别记录。

## 最小交付包

可编辑 `.tpbr` 与源纹理/生成说明、最终 DDS、raw 与部署 JSON、输入/输出 schema 与工具标识、NIF/BodySlide 重建输入、按需 ESP/第一人称/GND、文件清单与回滚、已做与待做检查。第三方资产权限不因使用技能而改变。

原生 prepared-BC7 导出审计示例：

```text
python scripts/audit_manager_export.py PROJECT.tpbr --export-root EXPORT_DIR --raw-json RAW.json --patched-json NEW-DEPLOY.json --schema pbr.schema.json --report NEW-export-audit.json
```

所有输出使用新路径。这个 helper 不执行 Manager、PGPatcher、NIF 修改或部署；精确依赖和 profile 限制见入口。Blender/Manager 预览是材质参考，最终透明排序、反射、动画和物理需要实际 Skyrim 测试。
