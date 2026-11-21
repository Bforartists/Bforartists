# 入门 {#getting-started}

[← 目录](index.md)

## BoneCraft 是什么？ {#what-is-bonecraft}

BoneCraft 是 Bforartists 的插件，用于为角色和道具绑定骨骼，并为 VRChat、VRoid / VRM 和 MMD 准备 3D 虚拟形象。其面板可以自动创建绑定、绘制权重、处理骨骼命名、口型同步、眼球追踪和导出。

**BoneCraft 做不到的事：**

- 不能为虚拟形象的身体外形建模或雕刻
- 不能从零创建纹理或材质
- 不能直接上传到 VRChat（仍需 VRChat Creator Companion / SDK）

---

## BoneCraft 与 BoneForge {#bonecraft-and-boneforge}

BoneCraft 仅在 Blender 分支 Bforartists 中运行。BoneForge 是面向标准 Blender 的另一个插件，工具较少。两者只安装其一。在标准 Blender 中，BoneCraft 只显示提示和获取 Bforartists 的按钮，不加载工具。

BoneForge 9.0.0 及以后版本面向标准 Blender；BoneCraft 是独立的 Bforartists 插件。两者均有 Auto-Rig Wizard、Quick Rig、Mannequin 和共享的 CATS/Material Atlas 工具。BoneCraft 另有 Mechanisms、Control Picker，以及生产用控制绑定、关节检测和配置文件导出工具。相似的布局不会让 BoneForge 获得这些工具。

## 随附构建快速入门 {#supplied-build-quick-start}

原先提供的 Bforartists 构建内置 BoneCraft 9.2.18；新的本地预览版内置 9.2.19 候选版。两者均通过出厂设置启用 BoneCraft，无需安装 ZIP 或手动启用。

1. 打开提供的 Bforartists 构建。
2. 按 **T** 显示左侧工具架。
3. 选择 **BoneCraft** 或 **Rig Builder**。
4. 按 **N** 显示右侧栏。
5. 选择 **CATS**，访问虚拟形象工具和 **Import / Export**。

本手册中的界面路径和设置均适用。可选工具包和依赖项仍须满足各自要求；Rigify 起始绑定及 VRM/MMD 桥接工具仍需所列依赖项。

本说明针对本地贡献预览版。官方 Bforartists 5.2.3 软件包不包含此套件。审查历史见[贡献提案](https://github.com/Bforartists/Bforartists/pull/7067)。

## 安装 BoneCraft {#installing-bonecraft}

本节适用于独立 Toolkit ZIP。使用随附构建的用户可直接从上面的现有选项卡开始。

链接指向已发布的 9.2.18 ZIP。9.2.19 候选版修复尚未发布，需使用本地预览版。

**所需条件：**

- Bforartists（BoneCraft 已在 Bforartists 5.2 上测试）
- 独立的 [BoneCraft-BFA-9.2.18.zip](https://github.com/Axleonex/B4Artists_Toolkit/releases/download/bonecraft-v9.2.18/BoneCraft-BFA-9.2.18.zip) 文件

**步骤：**

更新已有安装时：

1. 保存工作。

2. 禁用旧的独立 BoneCraft 插件。

3. 删除旧的独立 BoneCraft 插件。

4. 重启 Bforartists，再安装新的 ZIP。

首次安装从这里开始：

1. 打开 Bforartists。
2. 打开 **Edit** → **Preferences** → **Add-ons**。
3. 选择 **Install from Disk…**。

4. 选择 BoneCraft 的 `.zip` 文件。

5. 勾选 BoneCraft 旁边的复选框。
6. 确认链接所指已发布 ZIP 在偏好设置中显示的版本为 **9.2.18**。

7. 展开 BoneCraft 条目，查看 **Language**、**Tabs**、**Shelf Width**、**Show Helpers** 和 **Tools**。

以上步骤安装的是独立 Toolkit ZIP。如果提供的构建已内置 BoneCraft，请使用随附构建快速入门。避免同时启用独立副本和内置副本。

<strong>应看到的界面：</strong>左侧工具架（按 **T**）中的 BoneCraft 和 Rig Builder 选项卡，以及右侧栏（按 **N**）中的 CATS 选项卡。

## 各功能的位置 {#where-things-are}

每个选项卡包含一组工作区工具。Setup Rigging、Skin、Review、Avatar Tools 和 Facial 是选项卡内可展开的分区。下列路径使用英文界面标签；实际译名取决于 Language 偏好设置。

| 选项卡 | 默认位置 | 分区 |
| --- | --- | --- |
| Rig Builder | 左侧工具架（T） | Auto-Rig Wizard, Quick Rig - premade armatures, Mannequin |
| BoneCraft | 左侧工具架（T） | Overview, Setup Rigging, Skin, Mechanisms, Review |
| CATS | 右侧栏（N） | CATS, Avatar Tools, VRChat Tools, Import / Export |

英文原稿图片描述（图片已省略）：左侧工具架选中 BoneCraft，右侧栏选中 CATS。按 T 或 N 可显示相应区域。

*本地预览，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。左侧工具架选中 BoneCraft，右侧栏选中 CATS。按 T 或 N 可显示相应区域。*

| 工具 | 打开路径 |
| --- | --- |
| Bone Merge | BoneCraft → Setup Rigging → Bone Merge |
| Delta Mush / Proximity Wrap | BoneCraft → Skin → Delta Mush / Proximity Wrap |
| Viseme Library / Lip Sync | CATS → Avatar Tools → Viseme Library → Lip Sync |
| VRChat Viseme Mapping / Face Tracking | CATS → VRChat Tools → Facial |
| Humanoid / Hair | CATS → Avatar Tools → Set Up Humanoid Bones / Add Hair Physics |
| VRChat export | CATS → Import / Export → Game Engine Export → Unity / VRChat |
| Unreal 导出与 Bone Names | CATS → Import / Export → Game Engine Export → Unreal Engine 5 |
| 经验证的配置文件导出 | CATS → Import / Export → Game Export → Export (Profile) |
| Material Atlas | CATS → CATS → Material Atlas → Analyze Materials / Refresh Analysis → Bake Checked Sources |
| VRM / MMD / I/O Hub | CATS → Import / Export → VRM / VRoid, MMD / PMX, Game Engine Export |
| 性能 / 服装 / 命名 | CATS → VRChat Tools → Check Performance / Attach Clothing / VRChat Naming Extras |

使用绑定和口型库控件时，选择骨架。使用 Delta Mush 和 Proximity Wrap 时，在对象模式选择网格。Lip Sync 需要处于姿态模式的骨架。展开分区三角形即可显示按钮；Options 折叠区包含可选设置。若工具立即运行，应在执行其他操作前通过 Adjust Last Operation 调整。

三种面部工作流程各有用途：CATS 口型生成创建嘴部形态键；Viseme Library / Lip Sync 保存姿态并为动画插入关键帧；Facial 将已有形态键映射到 VRChat，或配置面部追踪。

UV 打包控件位于 **CATS → CATS → Material Atlas → Advanced Options → UV Packing**。早期说明将此折叠区称为 Override Inherited Settings。BoneCraft 提供共享的图集 UV 辅助工具，并非完整的独立 UVToolkit 插件。

**Starter Rigs：**

1. 在底部资产架的目录菜单中启用 **Starter Rigs**。

2. 必要时选择 **All** 库。

9.2.5 版本移除了左上角旧的 Starter Rigs 控件。**Add → Armature → Starter Rig Catalog** 提供拟合和生成功能，并检查依赖项。

**移动选项卡：**

1. 打开 **Edit** → **Preferences** → **Add-ons** → BoneCraft → **Tabs**。

2. 为选项卡选择 **Left** 或 **Right**。

每个选项卡也有显示开关，更改立即生效。隐藏选项卡后，其 Left 和 Right 按钮会变灰，但仍可使用。

<strong>属性编辑器：</strong>Preferences → Tabs 下的 **Scene Properties** 默认启用，用于在属性编辑器的 Scene 选项卡显示 Rig Builder、Mechanisms、CATS、Avatar Tools、VRChat Tools 和 Import / Export。

选择 **Show** 可隐藏或显示这些分区。蓝色表示分区可见。此开关不改变视口选项卡或 Armature 数据选项卡。

选择骨架时，BoneCraft 的骨架工具也会出现在 Armature 数据选项卡中。这些工具不受可见性开关控制；Rig Builder、Mechanisms 和 CATS 分区则使用 Scene 选项卡。

若要从所有位置移除某个工具，请在 **Tools** 中禁用其工具包，或禁用整个插件。

<strong>Shelf Width：</strong>Widen Narrow Shelves 默认启用。当包含 BoneCraft 选项卡的工具架宽度低于 Left 或 Right 的最小值时，会自动加宽一次。在 1× 界面缩放下，默认左侧为 240 像素，右侧为 260 像素。之后若手动拖窄工具架，将保留您选择的宽度。要手动控制宽度，请关闭此开关；宽度字段随即停用。

英文原稿图片描述（图片已省略）：Tabs 将 BoneCraft 和 Rig Builder 放在左侧，CATS 放在右侧。下方为 Shelf Width 和 Show Helpers。

*本地预览，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。Tabs 将 BoneCraft 和 Rig Builder 放在左侧，CATS 放在右侧。下方为 Shelf Width 和 Show Helpers。*

<strong>菜单与内置工具架选项卡：</strong>也可通过 3D 视口标题栏菜单访问工具：

| 位置 | 工具 |
| --- | --- |
| Add → Armature | Quick Rig、Auto-Rig Wizard、Mannequin for Active Rig |
| Pose → BoneCraft（姿态模式） | 姿态工具、选择器、骨骼集合、绑定设置和检查 |
| Weights → BoneCraft（权重绘制模式） | 权重填充、镜像和归一化 |
| Object → Mechanisms（对象模式） | 添加部件、关节和连接；测试运动 |
| Tool Shelf → Pose 或 Weights → BoneCraft | 常用姿态或权重操作按钮 |

工具架较宽时，Pose 和 Weights 按钮显示文字；较窄时，显示图标网格。将鼠标悬停在图标上可阅读提示。这些位置使用的工具与 BoneCraft 选项卡相同，仅提供已启用工具包中的工具。

<strong>视口工具：</strong>点击网格时，Place Rig Markers 放置 Auto-Rig Wizard 的下一个标记；点击部件时，Build Mechanism 开始引导创建关节或连接。设置和控制方法见 [Rig Builder](06-rig-builder.md#auto-rig-wizard) 和 [Mechanisms](07-mechanisms.md#joints-and-links-one-example-each)。

<strong>先运行，后调整：</strong>Quick Rig、Fit Dropped Rig、Weight Mirror、Weight Transfer、Flood to Custom、Ribbon、Spline IK 和 Delta Mush 会立即运行。

1. 选择工具。

2. 立即在视口的 Adjust Last Operation 面板中调整选项。

3. 完成调整后，再执行其他操作。

其他面板在操作按钮下方的折叠区中提供可选设置；展开后即可使用。若面板需要其他选择，它仍可保持可见，并说明应选择什么。

<strong>Show Helpers：</strong>BoneCraft 使用简短的“用途 / 使用时机”和“How this works”说明解释分区。要隐藏说明，请在插件偏好设置中关闭 **Show Helpers**。Avatar Tools 中的 **Compact Mode** 控制同一个开关。

<strong>Language：</strong>插件偏好设置中的 **Language** 将 BoneCraft 自身面板切换为 English、日本語、한국어、中文、Français、Português 或 Español。

英文原稿图片描述（图片已省略）：本地预览显示 BoneCraft 9.2.19，Language 为 English。

*本地预览，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。本地预览显示 BoneCraft 9.2.19，Language 为 English。*

**先检查清理选项：**

1. 检查 Fix Model 的选项。

2. 选择虚拟形象所需的操作。

3. 更改前保存文件检查点。

4. 操作后检查结果。

Pipeline Status 和 Operation Ledger 记录进度，详见 [CATS 流程](04-cats-pipeline.md)。

<strong>快捷面板：</strong>在 3D 视口按 **Ctrl+Shift+R**，可在鼠标下方弹出 BoneCraft 绑定面板。

---

## 我该从哪里开始？ {#where-should-i-start}

按任务选择指南：

> **为新的 FBX、OBJ 或 Blender 模型绑定骨骼，用于 VRChat。**
> → 参阅[指南 1：将第一个虚拟形象带入 VRChat](02-guides-a.md#guide-1-get-your-first-avatar-into-vrchat)

> **准备从 VRoid Studio 导出的 VRM 虚拟形象。**
> → 参阅[指南 2：将 VRoid 虚拟形象带入 VRChat](02-guides-a.md#guide-2-bring-a-vroid-avatar-into-vrchat)

> **为 VRChat 准备 MMD 模型（PMX 文件）。**
> → 参阅[指南 3：将 MMD 虚拟形象带入 VRChat](02-guides-a.md#guide-3-bring-an-mmd-avatar-into-vrchat)

> **修正导致已绑定虚拟形象无法上传的骨骼名称。**
> → 参阅[指南 4：修复虚拟形象的骨骼名称](02-guides-a.md#guide-4-fix-your-avatars-bone-names)

> **为 VRChat 准备已绑定虚拟形象的口型同步、眼球追踪和网格。**
> → 参阅[指南 13：通过 CATS 准备 VRChat 虚拟形象](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats)

> **查找某个具体问题的解决方法。**
> → 前往[快速修复索引](10-reference.md#quick-fix-index)

下一章：[指南 1–7](02-guides-a.md)
