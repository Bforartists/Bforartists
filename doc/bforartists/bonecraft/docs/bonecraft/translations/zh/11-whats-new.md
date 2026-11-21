# 新功能 {#whats-new}

[← 目录](index.md)

最新版本列在最前。

## 9.2.19 — 面板控件（本地候选版） {#9219--panel-controls-local-candidate}

本地候选版尚未发布，独立发布版仍为 9.2.18。

- Collections 和 Visibility Bookmarks 在面板绘制之外初始化设置。
- 分组面板使用各自的控件，并检查当前选择和模式。
- Hair Physics 在当前宿主中读取选中的姿态骨骼。
- Bone Inspector 显示静置骨骼滚转角，并通过标题栏按钮复制名称。
- Eye Tracking 显示角度值，同时保留已保存的设置。

英文手册为工具和设置增加了对应图片。早期图片仍保留原版本标签。

## 9.2.18 — 已保存的机械机构形态 {#9218--saved-mechanism-forms}

早期保存的形态在当前 Bforartists 构建中仍可读取和使用。打开或应用形态不会重新保存它。**Save Form** 使用当前格式捕获当前值；现有控制柄、滑块和面板位置保持不变。

此版本修复较新宿主中的兼容性诊断。仅凭该诊断，并不能证明早期宿主无法使用已保存的形态。参见[形态](07-mechanisms.md#forms)和[发布说明](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.18/RELEASE-NOTES.md)。

这是独立 Toolkit 发布版，不代表已被官方 Bforartists 接纳。历史截图和教程测试的适用范围仍保留在各章中。

## 9.2.17 — 导出命名与模式恢复 {#9217--export-naming-and-mode-restoration}

**Unity / VRChat** 和 **Unreal Engine 5** 现在提供 **Bone Names**：**Keep Original Names**、**Unity-Preset** 和 **Unreal-Preset**。预览显示已识别的骨骼及拟用名称。命名影响导出副本，包括顶点组、动画通道和 Unity 辅助文件引用；工作骨架保留原名。

两个主要引擎导出按钮现在接受对象、姿态和编辑模式。导出或清理后，会恢复原模式和选择。烘焙活动动作的 FBX 不再需要单独的 NLA 片段。

命名也涵盖已识别的可选人形骨骼、手指和脚趾。名称冲突或映射不明确会阻止重命名。这些配置保留层级、朝向和静置姿态，不会构建 Manny/Quinn 骨架。

重命名后的 **Export (Profile)** 输出支持 **Active Action** 和 **No Animation**；**All Actions** 必须使用 **Keep Original Names**。参见[游戏引擎导出](08-vrchat.md#game-engine-export)和 [9.2.17 说明](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.17/RELEASE-NOTES.md)。

## 9.2.15 — 经检查的材质图集流程 {#9215--reviewed-material-atlas-workflow}

面板现在分为三个阶段：目标选择、材质和纹理选择、烘焙与检查。**Smart Combine Materials** 是初始自动快捷操作。分析后，**Refresh Analysis** 重建列表；**Bake Checked Sources** 烘焙检查后选定的来源。

两个来源列表均有 **Select All** 和 **Deselect All**，仅更改活动组及来源列表内的 Include 复选框。缺失的纹理保持未勾选；批量选择不会启用已禁用的组。**Object → Atlas Source Selection** 提供相同操作。

**Source Details** 初始折叠，**Copy Debug Report** 位于 **Advanced Options** 下。备份、Accept 和 Revert 仍保持可见。这些界面更改保留现有烘焙流程及数据保留限制。

## 9.2.14 — 仅颜色网格 {#9214--color-only-meshes}

没有预先制作 UV 的仅颜色网格，会在最终组装时获得烘焙的图集 UV 层。

## 9.2.13 — 材质计数 {#9213--material-counts}

材质估算和结果会计算每个输出网格上的图集槽位；Revert 会重置这些结果。

## 9.2.12 — 导出 UV0 {#9212--export-uv0}

关闭 **Keep Source UV Maps** 时，重建后的图集网格将 `atlas_uv` 作为 UV0 导出。保留来源 UV 映射可能使图集位于 UV1。

## 9.2.11 — 来源变化检查 {#9211--changed-source-checks}

创建图集备份前，预检会拒绝已分析但缺失或发生变化的材质来源。

1. 刷新分析。

2. 再次检查来源选择。

## 9.2.10 — 排除的材质 {#9210--excluded-materials}

图集组装保留已排除的材质和共享材质引用。

## 9.2.9 — 渲染隐藏的来源 {#929--render-hidden-sources}

合并器通过临时副本烘焙在渲染中隐藏的来源。Revert 恢复原可见性。

## 9.2.8 — 已连接的着色器输入 {#928--connected-shader-inputs}

合并器在烘焙时保留已连接的 Principled 色调、映射和 Alpha 节点图。MToon 保留其回退路径。**Metallic** 和 **Pack ORM Channels** 仍会被预检阻止。

## 9.2.7 — 透明度分类 {#927--transparency-classification}

材质分类支持现代 DITHERED 不透明度，以及连接或常量 Alpha。单凭渲染设置，不再将不透明材质强行划入透明组。

## 9.2.6 — MMD 与 PMX 安装 {#926--mmd-and-pmx-installation}

安装器识别现代 MMD Extensions 和旧式插件。安装扩展时保留其依赖项，并报告不可用的本地存储库。即使没有旧式插件元数据，也能识别已启用的扩展。PMX 导入被取消时会保留取消结果，不再报告成功。

[带日期的修复记录](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-fixes-2026-10-23.md)涵盖 9.2.6–9.2.15 及其生成测试模型的检查。[9.2.15 界面审查](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-ui-review-9.2.15.md)记录操作器检查和视觉测试的限制。这些历史记录不表示在 9.2.18 中重新执行了整本手册。

## 9.2.5 — Starter Rigs 目录选项卡 {#925--starter-rigs-catalog-tab}

Starter Rigs 现在使用原生底部资产架中的一个目录选项卡，取代视口左上角的控件。要让它显示在其他目录旁，请在资产架的目录菜单中启用一次 **Starter Rigs**。原生资产导入和 **Add → Armature → Starter Rig Catalog** 仍可使用。

## 9.2.4 — Task Board 与原生工具 {#924--task-board-and-native-tools}

**Open Health Check** 现在运行绑定验证并打开结果。使用前，选择骨架或其绑定网格。**Quick Wins** 最多显示三项建议；**Remaining Tasks** 不重复列出这些卡片。**Refresh Task Board** 重新检查。

Place Rig Markers 和 Build Mechanism 仍可作为视口工具使用。其注册不再破坏对象和姿态模式中的原生 Grab/Move 或工具循环切换。

## 9.2.3 — VRChat 导出位置 {#923--vrchat-export-location}

移除 Avatar Tools 中重复的 Export to VRChat 面板。导出仍位于 CATS → Import / Export → Unity / VRChat。

## 9.2.2 — 当前界面 {#922--current-interface}

每个选项卡包含一组工作区工具。Setup Rigging、Skin、Review、Avatar Tools 和 Facial 是选项卡内可展开的分区。以下路径使用英文界面标签；实际译名取决于 Language 偏好设置。

- Bone Merge → BoneCraft → Setup Rigging
- Delta Mush / Proximity Wrap → BoneCraft → Skin
- Viseme Library / Lip Sync → CATS → Avatar Tools
- VRChat Viseme Mapping / Face Tracking → CATS → VRChat Tools → Facial

## 9.2.0（2026 年十月） {#920-october-2026}

- <strong>完整起始骨架目录：</strong>全部九个捆绑骨架/元骨架自带缩略图，分别为 Basic Humanoid、Simple Human、Full Human、Basic Quadruped、Cat、Horse、Wolf、Bird 和 Shark。目录选择器按 Humans、Quadrupeds 和 Other Animals 分组。
- <strong>按需使用 Rigify：</strong>Basic Humanoid 可独立工作。Rigify 未启用时，Rigify 起始骨架仍保持可见；选择后会提供 **Enable Rigify & Add Rig** 或 Cancel。取消、激活失败或预设不可用时，均不会添加绑定。
- <strong>可选资产架，历史 9.2.0 位置：</strong>视口标题栏的 **Starter Rigs** 开关返回普通资产架，选择保存在偏好设置中。9.2.5 版本以原生目录选项卡替代此开关。**Add → Armature → Starter Rig Catalog** 仍以弹出窗口打开选择器。
- <strong>点击或拖放：</strong>点击起始骨架或将其拖入视口均可添加。网格拟合初始启用，权重和控制生成初始关闭，可在 Adjust Last Operation 中调整。原生点击、拖放、取消和撤销/重做检查使用 Bforartists 5.2.0。

## 9.1.2（2026 年十月） {#912-october-2026}

- <strong>Scene Properties 开关：</strong>Preferences > Tabs 新增 Scene Properties 行。Show 按钮控制 Properties > Scene 选项卡中的所有 BoneCraft 分区，包括 Rig Builder、Mechanisms、CATS、Avatar Tools、VRChat Tools 和 Import / Export。开关默认启用，启用时呈蓝色；不会禁用插件或更改视口选项卡及 Armature 选项卡。参见[各功能的位置](01-start.md#where-things-are)。

## 9.1.1（2026 年十月） {#911-october-2026}

- <strong>更清楚的图标：</strong>每个图标在整个界面中只有一种含义。约 60 个按钮换用了更符合功能的 Bforartists 图标，包括 Apply All Transforms、Decimate、Normalize Names、Translate、Merge、Separate、Blend Pose 和 Lip Sync。每个按钮在所有面板中使用相同图标。
- <strong>更简洁的面板：</strong>标题和固定文字不再带主题图标；报告状态的提示使用信息、警告或勾选图标。
- <strong>可读的图标网格：</strong>Pose 和 Weights 工具架选项卡的每个按钮都有专用图标，窄工具架仍能清晰识别。

## 9.1.0（2026 年十月） {#910-october-2026}

- <strong>遵循 Bforartists 自有工具的位置：</strong>BoneCraft 在 Add → Armature 及 Pose、Weights、Object 菜单中添加入口，也在 Bforartists 的 Pose 和 Weights 工具架选项卡添加按钮面板。
- <strong>先执行，后微调：</strong>Quick Rig、Fit Dropped Rig 和权重工具使用上次值立即运行。Ribbon、Spline IK、Delta Mush 和 CATS 骨骼工具同样如此，随后通过 Adjust Last Operation 调整选项，减少确认弹窗。
- <strong>操作在前，选项折叠：</strong>若干面板将按钮放在可选设置折叠区上方。必填输入及 Fix Model 清理开关仍在操作按钮上方。设置使用复选框，而非按钮；面板标题不带图标。
- <strong>手势工具：</strong>Place Rig Markers 和 Build Mechanism 位于视口工具栏。点击网格时，前者放置 Auto-Rig Wizard 的下一个标记；点击部件时，后者开始创建关节或连接。
- <strong>虚拟形象分区，历史 9.1.0 位置：</strong>Avatar Tools 曾包含人形映射、头发、口形和导出。独立的 VRChat Tools 分区集中性能、服装和命名工具。导出现位于 **Import / Export → Game Engine Export → Unity / VRChat**。
- <strong>工具提示：</strong>每个操作器和选项均有说明。
- <strong>保持可见并说明条件：</strong>没有绑定时，分区仍保持可见，解释需要选择什么。Auto-Rig Wizard 位于 Rig Builder 首项，工具架初始宽度足以阅读。
- <strong>修复：</strong>Generate Spline IK 恢复工作；Add Influence 使用所选骨骼；口形预览使用其所属集合。

## 9.0.0（2026 年十月） {#900-october-2026}

- <strong>Mechanisms：</strong>BoneCraft 选项卡和 Properties 的 Scene 选项卡新增此分区，用于为道具和机械绑定。类型包括 Hinge、Slide、Telescope、Piston、Gear Link、Follow 和 Sequence，通过引导步骤构建，并用 Test 检查运动。BoneCraft 不会自动覆盖手工修改；**Keep mine** 保留修改，**Restore** 重建机构。参见[机械机构](07-mechanisms.md)。
- **示例文件：**`examples/crescent-rose/` 包含使用 Mechanisms 绑定的 Crescent Rose（镰刀、步枪和紧凑形态），手册[第 12 章](12-crescent-rose.md)逐步介绍其制作方法。
- <strong>选项卡位置：</strong>各视口选项卡可放在左侧工具架或右侧栏（Preferences → Tabs → Left / Right）。BoneCraft 和 Rig Builder 初始位于左侧，CATS 位于右侧。
- <strong>Rig Builder：</strong>始终显示在 Properties 的 Scene 选项卡，同时有独立视口选项卡。紧凑布局适合窄工具架。BoneCraft Rigs 资产库包含 Basic Humanoid；Fit Dropped Rig 拟合从资产架拖入的绑定。
- <strong>CATS 选项卡：</strong>Import / Export 移入 CATS 选项卡。CATS、VRChat 和 Import / Export 也始终显示在 Scene 选项卡。
- <strong>Show Helpers：</strong>一个偏好设置用于显示或隐藏 BoneCraft 教学说明；Compact Mode 控制同一设置。
- <strong>Rig Validator：</strong>带连字符的骨骼名可通过检查。驱动器仅对需要 Python 的表达式发出警告。检查也涵盖 Mechanisms 绑定；Task Board 的验证器任务恢复报告。
- <strong>名称：</strong>插件名称为 BoneCraft。

## 8.9.x（2026 年九–十月） {#89x-septemberoctober-2026}

- <strong>8.9.6：</strong>整块裙装跟随裙骨，不再穿入髋部。张嘴时嘴角修正支持黏唇。
- <strong>8.9.5：</strong>IK/FK 肘部切换保留姿态，不再跳变；肩部检测对称，眼部标记不再吸附跳动，Control Picker 显示选择。其他更改包括更圆润的嘴角、裙装与大腿相交修正、重定向时更放松的锁骨以及 T 姿态导出。
- <strong>8.9.4：</strong>用修正形态键替代 Preserve Volume，改善膝部圆润度；还增加深度弯曲接触形态键和肩缝混合。
- <strong>8.9.3：</strong>两段式裙骨跟随腿部，腿部也会推动这些骨骼。
- <strong>8.9.2：</strong>形态键生成无眼睑折叠的眨眼，嘴部开口呈椭圆形。
- <strong>8.9.1：</strong>密集网格蒙皮加速（678,000 个顶点：从 232 s 降至 57 s）。骨骼热权重改用更轻的代理网格，不再静默失败。
- <strong>8.9.0：</strong>新增关节修正形态键，以及眼睛瞄准、眨眼和嘴唇跟随的面部控制；服装随关节弯曲。
- 8.9 版本还增加自动骨骼权重重算及更清楚的图集选择。

## 8.7–8.8（2026 年九月） {#8788-september-2026}

- <strong>8.8.0：</strong>重定向面板可在 Blender 5 宿主中工作。手指标记按手部形状放置。其他更改包括 IK 向皮肤拉伸、Preserve Volume 选项及 Delta Mush 绑定修复。
- <strong>8.7.0：</strong>新增集成控制绑定、沿肢体追踪的关节检测、方向匹配的重定向和扭转骨骼。

## 8.5–8.6（2026 年七月） {#8586-july-2026}

- <strong>8.6.1–8.6.3：</strong>Material Atlas 增加烘焙后贴片诊断，并改进混合材质分区。按实际纹理 Alpha 检查 MToon 透明度，并在制作图集时保留透明度。
- <strong>8.5.5–8.5.10：</strong>VRM / MToon 材质遵守 Alpha 模式，Alpha 可在 Blender 5 宿主中工作。其他更改避免过强自发光，增加品红色诊断和安全图集命名。
- <strong>8.5.4：</strong>人形映射正确加载，并新增 Naming Prep 指引。
- <strong>8.5.2–8.5.3：</strong>新增 VRoid 下载文件（.zip）导入及 VRoid 项目交接卡。
- <strong>8.5.1：</strong>FBX 导出保留混合形状。

## 更早版本 {#earlier-versions}

<strong>8.5.0：</strong>烘焙后，Smart Combine 默认将 `atlas_uv` 用作导出 UV0。除非在 Advanced 设置中启用 **Keep Source UV Maps**，否则会从生成的图集网格中移除制作图集之前的来源 UV 映射。开放的 Blender 构建现在共享 CATS / Material Combiner / 源自 UVToolkit 的控件；生产绑定、控制、重定向/导出和 B4Artists 专用发布系统仍仅供 B4Artists 使用。

8.5.0 还更新了导出和验证。VRChat、VRM、MMD 和 Unreal 导出现可在 BoneCraft 面板设置文件夹和文件名，不再只依赖 Blender 文件浏览器默认值。VRChat/Unity 和 Unreal FBX 默认启用 **Embed Textures**，便于导入材质。除非启用 **Helper Meshes**，否则 VRChat 导出会将辅助网格/控制器形状网格排除在 FBX 之外。VRM 面板增加 **Lint Now** 和 **Fix Humanoid Map**；后者在导出前修复过时的人形别名映射，不重命名骨骼。

<strong>8.4.5：</strong>烘焙时，Smart Combine 使来源纹理采样保留的制作图集前 UV。隐藏原对象前，会验证生成的图集网格，并将图集所有面重置到最终图集材质槽，避免长袍/服装区域变灰或错乱。

<strong>8.4.4：</strong>Material Atlas Combiner 增加烘焙前检查控件以对齐质量，包括着色器/材质诊断、纹理角色标签、重复/共享来源标记、各材质尺寸覆盖和打包预设。可选输出烘焙包括 Normal/Emission/Roughness；在 Metallic/ORM 通道打包路径验证前，预检会阻止使用。

<strong>8.4.3：</strong>Material Atlas Combiner 在现有流程中增加可选 UV 打包方法，包括 Smart Pack、Grid Pack、Seeded Variation、Oriented Pack、Fit 0-1 Bounds、Advanced Variation 和 Rotation Step。调试报告和烘焙记录包含 UV 方法详情。

<strong>8.4.2：</strong>烘焙时，Material Atlas Combiner 针对生成的图集 UV；复制的来源纹理节点则明确读取制作图集前 UV，修复来源纹理与烘焙图集采样不同 UV 映射而导致的长袍/服装图集错误。8.4.1 的可选材质和纹理行仍可使用。

<strong>7.1.3（偏好设置标签清理）：</strong>两个插件偏好开关改为与侧栏选项卡一致的名称。“VRChat Avatar Tools”改为 **CATS**；“Task Board & Sidebar”改为 **Rig Builder**。仅更改 Edit > Preferences > Add-ons > BoneCraft 中的开关标签，没有移除工具。

<strong>7.1.1：</strong>BoneCraft 新增完整 CATS 套件，用于 VRChat 虚拟形象清理、优化和配置。CATS 有独立侧栏选项卡，其流程指引操作顺序。

下一章：[教程：使用 Mechanisms 制作 Crescent Rose](12-crescent-rose.md)
