# 快速修复与术语表 {#quick-fixes-and-glossary}

[← 目录](index.md)

## 快速修复索引 {#quick-fix-index}

通过本索引查找问题对应的指引。

| 问题 | 参考位置 |
|---|---|
| 上传失败——无法识别骨骼 | [指南 4](02-guides-a.md#guide-4-fix-your-avatars-bone-names) + [VRChat Naming Extras](08-vrchat.md#vrchat-naming-extras) |
| 虚拟形象保持 T 姿态 / 不跟踪运动 | [指南 5](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system) + [Set Up Humanoid Bones](08-vrchat.md#set-up-humanoid-bones) |
| 网格变形异常 / 皮肤拉伸 | [Weight Transfer](05-rig-tools.md#weight-transfer) + [Weight Mirror](05-rig-tools.md#weight-mirror)，或通过[自动骨骼权重重算](05-rig-tools.md#automatic-bone-weight-recalculation)重新计算 |
| 身体两侧权重不同 | [Weight Mirror](05-rig-tools.md#weight-mirror) |
| 头发穿入头部 | [指南 6，步骤 5](02-guides-a.md#step-5--add-colliders-recommended)——添加碰撞体 |
| 头发物理没有运动 | [指南 6](02-guides-a.md#guide-6-add-hair-physics)——检查链检测和 PhysBone 预设 |
| 服装穿入身体 | [指南 7](02-guides-a.md#guide-7-attach-clothing-that-moves-with-your-body)：<ol><li>检查摆好姿态的网格。</li><li>若有穿插，调整贴合或权重。</li></ol> **Detect Collisions** 仅检查骨骼名称。 |
| 口型同步不工作 | [指南 8](03-guides-b.md#guide-8-set-up-lip-sync) + [VRChat Viseme Mapping](08-vrchat.md#vrchat-viseme-mapping) |
| 虚拟形象性能为 Very Poor | [指南 9](03-guides-b.md#guide-9-improve-your-avatars-performance) + [Check Performance](08-vrchat.md#check-performance) |
| VRM 导入失败 | [指南 2，步骤 1](02-guides-a.md#step-1--install-the-vrm-add-on)——安装 VRM 插件 |
| MMD 导入失败 | [指南 3，步骤 1](02-guides-a.md#step-1--install-mmd_tools)——安装 mmd_tools |
| 已安装 MMD，但桥接未激活 | 通过 **Open Add-on Preferences** 启用 mmd_tools，并检查[指南 3](02-guides-a.md#step-1--install-mmd_tools)中的安装消息。 |
| 刷新后图集来源选择改变 | **Refresh Analysis** 会重建选择。<ol><li>检查来源。</li><li>选择 Bake Checked Sources。</li></ol>参见[材质图集合并器](09-cats.md#material-atlas-combiner)。 |
| Select All 仍有纹理未勾选 | 缺失的纹理保持排除。批量选择仅更改活动组内对应的列表——参见[来源选择](09-cats.md#analyze-and-choose-sources)。 |
| 图集报告来源发生变化 | <ol><li>刷新分析。</li><li>再次检查来源。</li></ol>创建备份前，预检会拒绝过时的分析来源。 |
| 图集没有 Revert 选项 | **Preserve Backup Duplicate** 已关闭，或 Accept 已删除备份。请使用已保存的文件检查点。 |
| Metallic 或 ORM 图集烘焙被阻止 | 保持 **Metallic** 和 **Pack ORM Channels** 关闭。9.2.18 仍阻止这些通道。 |
| 引擎中的图集纹理错乱 | 检查 UV0。**Keep Source UV Maps** 可能使 `atlas_uv` 留在 UV1——参见 [UV 设置](09-cats.md#advanced-options)。 |
| 在姿态或编辑模式导出失败 | 使用当前主要 Unity 或 Unreal 按钮；它会恢复模式和选择。**Export (Profile)** 应在对象模式使用。 |
| 导出命名报告冲突 | 修正目标名称或人形映射——参见[导出骨骼命名](08-vrchat.md#export-bone-naming)。 |
| 命名预设阻止 All Actions | 选择 **Active Action**、**No Animation** 或 **Keep Original Names**——参见[经验证的配置文件导出](08-vrchat.md#validated-profile-export)。 |
| 早期机械机构形态需要当前版本 | 9.2.18 可读取和应用早期形态，无需重新保存——参见[形态](07-mechanisms.md#forms)。 |
| 绑定验证器显示错误 | [Rig Validator](05-rig-tools.md#rig-validator)：<ol><li>运行验证。</li><li>按消息处理。</li></ol> |
| 骨骼消失 / 看不到骨骼 | [Bone Collections](05-rig-tools.md#bone-collections) → **Show All Collections** |
| 找不到 BoneCraft 面板 | BoneCraft 和 Rig Builder 使用左侧工具架（**T**），CATS 使用右侧栏（**N**）。参见[各功能的位置](01-start.md#where-things-are)。 |
| 想要完整的 Mechanisms 实例 | [教程：Crescent Rose](12-crescent-rose.md)——8 步准备和 30 步机械机构操作，保留书面指令及英文原稿图片描述；完成文件位于 `examples/crescent-rose/`。 |
| 选项卡位于错误的一侧 | Preferences → Add-ons → BoneCraft → Tabs → Left 或 Right |
| Properties → Scene 缺少 BoneCraft 分区 | Preferences → Add-ons → BoneCraft → Tabs → Scene Properties → Show。蓝色表示已启用；同时检查 Tools 中的工具包。 |
| 想在 Properties → Scene 隐藏 BoneCraft | 在 Preferences → Tabs 关闭 Scene Properties → Show。视口选项卡和 Armature 数据选项卡不变。 |
| 尚未来得及选选项，工具就已运行 | 在 9.1 中，立即通过视口的 Adjust Last Operation 面板调整选项，之后再执行其他操作。 |
| Place Rig Markers 不放置标记 | <ol><li>启动 Auto-Rig Wizard。</li><li>前进至标记步骤。</li><li>切换到对象模式。</li><li>点击向导选中的网格。</li></ol>参见 [Rig Builder](06-rig-builder.md#auto-rig-wizard)。 |
| Build Mechanism 不知道应使用哪些部件 | <ol><li>先使用 Add Parts from Selection。</li><li>选择机械机构绑定或其部件之一。</li><li>在工具标题栏选择类型。</li><li>点击第一个部件。</li></ol>参见[机械机构](07-mechanisms.md#joints-and-links-one-example-each)。 |
| 导出被阻止：骨骼明明存在，却报告缺少人形骨骼 | 必需骨骼若不存在，必须先补齐；若已存在：<ol><li>运行 Auto-Map All。</li><li>在 VRM / VRoid 的检查工具下运行 Fix Humanoid Map。</li></ol>参见[指南 5](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system)。 |
| 导出的 FBX 出现巨大辅助形状或管状物 | 不需要控制器或自定义形状网格时，保持 **Helper Meshes** 关闭。 |
| Unity 或 Unreal 导入的材质为灰色 | <ol><li>启用 Embed Textures 后导出。</li><li>使用 Unity 的材质导入/提取选项，或 Unreal 的 FBX 材质导入。</li></ol> |
| 权重全部位于错误骨骼 | 重新运行向导的 Generate Rig，使用 [Weight Transfer](05-rig-tools.md#weight-transfer)，或 CATS 选项卡中的 **Smart Automatic Weights**。 |
| 两套绑定需要合为一套 | [指南 11：合并两套绑定](03-guides-b.md#guide-11-merge-two-rigs-together) |
| 修正形态没有启用 | 检查[修正形态键](05-rig-tools.md#corrective-shape-keys)中的骨骼轴和角度。 |
| 动画用于另一套绑定时不正常 | [Retarget](05-rig-tools.md#retarget)——检查骨骼映射。 |
| CATS 工具警告“Run Fix Model first” | <ol><li>检查清理选项。</li><li>判断虚拟形象是否需要。</li></ol>警告不会锁定工具。参见 [CATS 流程](04-cats-pipeline.md)。 |
| 说话时嘴部撕裂或分开 | 检查来源嘴部形态键、网格拓扑和修改器——参见 [CATS：Visemes](09-cats.md#visemes)。 |
| VRChat 中眼睛始终向下看 | <ol><li>检查左右骨骼分配、朝向及约束。</li><li>检查导出的虚拟形象。</li></ol>参见 [CATS：Eye Tracking](09-cats.md#eye-tracking)。 |
| 触发形态键时网格爆开 | <ol><li>单独测试该键。</li><li>检查拓扑、来源形态键值和修改器。</li></ol>BoneCraft 捕获形态键混合，不捕获骨骼变形。参见 [CATS：姿态与形态键](09-cats.md#pose--shape-keys)。 |
| 虚拟形象进入 VRChat 后尺寸错误 | 检查网格变换、骨架变换和导出/导入缩放设置。如需恢复，使用 Undo 或已保存的检查点。参见[应用全部变换](09-cats.md#apply-all-transforms)。 |
| 骨骼名称为日文 / 中文 / 韩文 | [CATS：翻译骨骼名称](09-cats.md#translate-bone-names) |
| 没有口型同步，也没有嘴部形态键 | [CATS：Visemes](09-cats.md#visemes)：先创建基础口形。CATS 根据 A、O、CH 三项来源分配生成 15 个口形。 |
| 机械机构显示“changed by hand” | [机械机构](07-mechanisms.md)——使用 **Keep mine** 或 **Restore**。 |

## 术语表 {#glossary}

<strong>Adjust Last Operation（调整上一步操作）：</strong>用于更改最后一次操作选项的视口面板。许多 BoneCraft 9.1 工具先运行，再在这里显示选项；执行其他操作前完成调整。

<strong>Armature（骨架）：</strong>Bforartists 对骨骼系统的称呼，即一组可以摆姿态和制作动画的骨骼。

<strong>Blend shape（混合形状）：</strong>参见 Shape key。

<strong>Bone（骨骼）：</strong>骨架中的一个节段。骨骼按父级 → 子级构成层级，子骨骼跟随父骨骼。

<strong>Bone collection（骨骼集合）：</strong>具名骨骼组，可一次显示或隐藏整个集合。

<strong>Bone Names（骨骼名称）：</strong>导出命名选项。Keep Original Names 保留名称；Unity-Preset 和 Unreal-Preset 在导出副本上重命名已识别的骨骼。

<strong>Bake Checked Sources：</strong>按已检查的组和来源选择烘焙图集，不自动重建分析。

<strong>CATS：</strong>用于 VRChat 模型准备的工具，带有清理、口形、眼球追踪和变换的引导流程，位于 CATS 选项卡。

<strong>CATS pipeline（CATS 流程）：</strong>六阶段顺序为 Fix Model → Material Atlas → Visemes → Eye Tracking → Pose to Shape → Apply Transforms。若所依赖的前一阶段未完成，工具会发出警告。

<strong>Corrective shape key（修正形态键）：</strong>骨骼到达某个角度时启用的形态键，用于修正在极端姿态下的网格。

<strong>Deform bone（变形骨骼）：</strong>用于移动网格的骨骼。有些骨骼仅用于控制，不使网格变形。

<strong>Eye tracking（眼球追踪）：</strong>设置眼部骨骼（`LeftEye`、`RightEye`）及 VRChat 转动眼球所用旋转约束的 CATS 工具。

<strong>FBT（Full Body Tracking，全身追踪）：</strong>VRChat 功能，配合 Vive Trackers 等额外硬件追踪全身，包括髋部和双脚。Fix FBT 为此功能调整根骨骼。

<strong>FBX：</strong>在软件间传递 3D 模型、骨架和动画的文件格式，也是 VRChat 的标准格式。

<strong>Fix Model：</strong>可选择的 CATS 清理操作，处理重复顶点、松散几何体、法线和其他数据。

1. 检查选项。

2. 仅运行虚拟形象需要的操作。

<strong>FK（Forward Kinematics，正向运动学）：</strong>依次旋转骨骼链上的每根骨骼来摆姿态，例如肩部、肘部、手腕，适合整体身体姿态。

<strong>IK（Inverse Kinematics，反向运动学）：</strong>通过放置链条末端（如手或脚）来摆姿态，中间骨骼随之跟随，适合精确放置手脚。

<strong>Humanoid（人形）：</strong>VRChat 将骨骼映射到标准身体槽位的虚拟形象系统，让每个虚拟形象使用相同的运动控制。

<strong>Mechanism（机械机构）：</strong>使用普通骨骼和约束构建的道具或机器绑定，可以是关节（Hinge、Slide、Telescope）或连接（Piston、Gear Link、Follow）。参见[机械机构](07-mechanisms.md)。

<strong>Mesh（网格）：</strong>构成虚拟形象可见身体的 3D 表面。

<strong>MMD（MikuMikuDance）：</strong>在日本及动漫社群流行的免费 3D 动画软件，使用 `.pmx` 模型文件和 `.vmd` 动画文件。

<strong>Morph target（变形目标）：</strong>参见 Shape key。

<strong>Operation Ledger（操作记录）：</strong>CATS 记录您运行的每次操作及其时间和结果的列表。

<strong>PhysBone：</strong>让骨骼摆动、弹跳和碰撞的 VRChat 组件，用于头发、尾巴和悬挂配饰。

<strong>Pipeline Status（流程状态）：</strong>CATS 六阶段列表，完成的阶段旁显示勾选标记。

<strong>PMX：</strong>MikuMikuDance 的主要 3D 模型格式。

<strong>Pose Mode（姿态模式）：</strong>用于为骨骼摆姿态和制作动画的模式。

1. 选择骨架。

2. 按 Ctrl+Tab。

也可在视口左上角的模式下拉菜单选择 Pose Mode。

<strong>Rig / rigging（绑定）：</strong>在 3D 模型内部构建骨架，并将网格连接到骨架，使其能够摆姿态和制作动画。

<strong>Shape key（形态键）：</strong>保存网格某种变形位置的版本。形态键可以按不同强度混合，用于面部表情、口型同步和身体形变。

<strong>SDK（Software Development Kit，软件开发工具包）：</strong>此处指 VRChat Creator Companion 及其用于在 Unity 上传虚拟形象的工具。

<strong>Spline IK（样条 IK）：</strong>沿曲线运动的骨骼链，用于尾巴、触手、长发和脊柱。

<strong>T-pose（T 姿态）：</strong>直立、双臂向两侧伸出的参考姿态。

<strong>Tool Shelf（工具架）：</strong>3D 视口左侧面板（**T**），BoneCraft 和 Rig Builder 默认使用此面板。

<strong>Vertex（顶点）：</strong>3D 空间中的单个点。网格由大量通过边和面连接的顶点组成。

<strong>Vertex group（顶点组）：</strong>具名顶点集合，定义某根骨骼移动哪些顶点。

<strong>Viseme（口形）：</strong>与某个语音对应的嘴部形状。VRChat 使用 15 个口形进行口型同步。

<strong>Weight / weight painting（权重 / 权重绘制）：</strong>0.0 至 1.0 的数值，表示每根骨骼移动每个顶点的强度。权重绘制是可视化调整这些数值的方法。

<strong>Wizard（向导）：</strong>Rig Builder 的 Auto-Rig Wizard，通过在网格上放置标记来构建绑定。

<strong>Zero-weight bone（零权重骨骼）：</strong>不移动任何顶点的骨骼，不改变虚拟形象外观却降低性能。Fix Model 和性能优化器会移除这类骨骼。

下一章：[新功能](11-whats-new.md)
