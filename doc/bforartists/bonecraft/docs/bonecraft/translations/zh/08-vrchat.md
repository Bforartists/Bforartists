# VRChat 工具 {#vrchat-tools}

[← 目录](index.md)

## VRChat 工具 {#vrchat-tools-1}

VRChat 相关工具位于右侧栏 **CATS** 选项卡的 **Avatar Tools** 分区，按 **N** 显示侧栏。Avatar Tools 包含人形骨骼、头发物理及 Viseme Library / Lip Sync；VRChat 导出位于 CATS → Import / Export → Unity / VRChat。下方独立的 **VRChat Tools** 分区集中 Check Performance、Attach Clothing、Facial 和 VRChat Naming Extras。启用 Preferences → Tabs → Scene Properties → Show 时，此分区也显示在 **Properties** 编辑器的 **Scene** 选项卡中。该开关不隐藏 CATS 视口选项卡。

---

### 设置人形骨骼 {#set-up-humanoid-bones}

将骨架骨骼映射到 VRChat 人形槽位并检查映射。

参见[指南 5：将虚拟形象映射到 VRChat 身体系统](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system)。

英文原稿图片描述（图片已省略）：Auto-Map All 前的必需人形槽位。映射后，逐项检查槽位并填补剩余空缺。

*原生面板弹出窗口，BoneCraft 9.2.18。Auto-Map All 前的必需人形槽位。映射后，逐项检查槽位并填补剩余空缺。*

---

### 添加头发物理 {#add-hair-physics}

为头发、耳朵、尾巴和配饰设置 PhysBone 链及碰撞体。

参见[指南 6：添加头发物理](02-guides-a.md#guide-6-add-hair-physics)。

英文原稿图片描述（图片已省略）：Hair Physics 骨骼链、生成操作、预设和碰撞体控件。应用物理前检查已检测的链。

*原生测试构建弹出窗口，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。Hair Physics 骨骼链、生成操作、预设和碰撞体控件。应用物理前检查已检测的链。*

---

### 添加服装 {#attach-clothing}

**位置：** CATS 选项卡 → VRChat Tools → Clothing

将服装合并到虚拟形象骨架，并传递权重。

参见[指南 7：添加随身体运动的服装](02-guides-a.md#guide-7-attach-clothing-that-moves-with-your-body)。

英文原稿图片描述（图片已省略）：Clothing 控件及 Pre-Merge 选择顺序。合并服装前，匹配骨骼并检查骨骼名称冲突。

*本地预览，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。Clothing 控件及 Pre-Merge 选择顺序。合并服装前，匹配骨骼并检查骨骼名称冲突。*

---

### VRChat 命名扩展工具 {#vrchat-naming-extras}

**位置：** CATS 选项卡 → VRChat Tools → Naming

**用途：** 检测骨架命名风格，并批量重命名骨骼。

参见[指南 4：修复虚拟形象的骨骼名称](02-guides-a.md#guide-4-fix-your-avatars-bone-names)。

**批量工具：** **Find and Replace**、**Add Prefix**、**Remove Prefix**、**Add Suffix**、**Remove Suffix** 和 **Regex Replace**

英文原稿图片描述（图片已省略）：本例中 Naming 以 16/24 的置信度检测到 Unity Humanoid。批量操作前检查名称。

*本地预览，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。本例中 Naming 以 16/24 的置信度检测到 Unity Humanoid。批量操作前检查名称。*

---

### VRChat 口形映射 {#vrchat-viseme-mapping}

**位置：** CATS → VRChat Tools → Facial。Face Tracking 也在同一分区。

**用途：** 将网格形态键映射到 VRChat 的 15 个口型同步口形。

参见[指南 8：设置口型同步](03-guides-b.md#guide-8-set-up-lip-sync)。要创建尚不存在的口形，参见 [CATS 工具：口形](09-cats.md#visemes)。

**VRChat 的 15 个口形槽位：** `sil`、`PP`、`FF`、`TH`、`DD`、`kk`、`CH`、`SS`、`nn`、`RR`、`aa`、`E`、`I`、`O`、`U`

英文原稿图片描述（图片已省略）：映射前的口形槽位和 Face Tracking。本例的口形尚未映射，表情映射数量为 0 / 55。

*本地预览，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。映射前的口形槽位和 Face Tracking。本例的口形尚未映射，表情映射数量为 0 / 55。*

---

### 检查性能 {#check-performance}

**位置：** CATS 选项卡 → VRChat Tools → Performance

**用途：** 测量虚拟形象的 VRChat 性能等级，并提供修复。

参见[指南 9：改善虚拟形象性能](03-guides-b.md#guide-9-improve-your-avatars-performance)。

**性能等级（从好到差）：** Excellent → Good → Medium → Poor → Very Poor

**工具：**

- **Calculate Performance Rank** — 当前等级，以及多边形、蒙皮网格、材质槽、骨骼、PhysBones 和接触组件的分项统计
- 优化器提供 **Remove Zero-Weight Bones**、**Merge Same-Material Meshes**、**Remove Unused Shape Keys** 和 **Remove Unused Vertex Groups**；**What-If Mode** 显示这些修复将进行的更改
- VRChat Decimation — 按比例减少多边形，同时保护形态键

使用 VRChat Decimation：

1. 选择虚拟形象网格。
2. 选择 **Preview**。
3. 选择 **Apply**。

英文原稿图片描述（图片已省略）：性能指标及 What-If 控件。选择虚拟形象网格后可使用网格清理操作。

*原生面板弹出窗口，BoneCraft 9.2.18。性能指标及 What-If 控件。选择虚拟形象网格后可使用网格清理操作。*

英文原稿图片描述（图片已省略）：Preview 或 Apply 前的减面设置。本例 Ratio 为 0.50，启用 Shape Key Safety；下方清理操作启用 What-If Mode。

*本地预览，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。Preview 或 Apply 前的减面设置。本例 Ratio 为 0.50，启用 Shape Key Safety；下方清理操作启用 What-If Mode。*

---

### 导出到 VRChat {#export-to-vrchat}

**用途：** 将完成的虚拟形象导出为供 Unity 中 VRChat SDK 使用的 FBX。除非开启 **Remove Shape Keys**，否则导出保留形态键（混合形状）。

**设置：**

- **Folder** — 导出位置
- **Avatar** — 导出文件名
- **Sidecar** — 额外写出供 BoneCraft Unity 导入器使用的 `.bfvrc` 设置文件
- **Merge Meshes** — 将导出副本的网格合为一个
- **Separate Clothing** — 将服装保留为独立网格
- **Remove Shape Keys** — 将形态键应用到导出副本的基形
- **Embed Textures** — 将纹理打包进 FBX，便于 Unity 查找
- **Helper Meshes** — 包含隐藏或辅助网格，普通虚拟形象应关闭
- **Bone Names** — **Keep Original Names**、**Unity-Preset** 或 **Unreal-Preset**，应用于导出副本

**位置：** CATS → Import / Export → Game Engine Export → Unity / VRChat。

导出前：

1. 缺少必需槽位时，在这里运行 **Auto-Map Humanoid**。
2. 检查槽位。

要在导出前检查性能，选择 **Check Performance Rank**。使用 **Bone Names** 预设前，修正映射或命名冲突；下方“导出骨骼命名”小节解释这些冲突。导出前，将链接对象转为本地。选择 **Export to VRChat (Unity)** 写出 FBX。

**Normalize Names** 重命名工作绑定；**Bone Names** 预设重命名导出副本。

Unity/VRChat 导出器写出不带动画的静置姿态。主要 Unity 和 Unreal 导出按钮支持对象、姿态和编辑模式：临时使用对象模式，完成后恢复原模式和选择。

英文原稿图片描述（图片已省略）：设置文件夹和人形映射前的 Unity / VRChat 设置。本例必需槽位映射数量为 0 / 15。

*本地预览，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。设置文件夹和人形映射前的 Unity / VRChat 设置。本例必需槽位映射数量为 0 / 15。*

---

### 清理 {#cleanup}

导出前的网格清理位于 CATS 工具中的 **Fix Model**、**Join Meshes** 和 **Apply All Transforms**。参见 [CATS 工具](09-cats.md)。

---

## VRM 桥接 {#vrm-bridge}

VRM 工具位于 **CATS** 选项卡 → **Import / Export** → **VRM / VRoid**，需要 VRM 插件。未激活的桥接提供 **Auto-Install Latest from GitHub**、**Open Add-on Preferences**、**Website** 和 **Show Manual Instructions**。

离线软件包使用原生偏好设置：旧式插件 ZIP 使用 **Add-ons → Install from Disk…**，现代扩展包使用原生 Extensions 安装菜单。

1. 通过适当的原生菜单安装软件包。
2. 启用依赖项。
3. 确认桥接报告 **Active**。

未激活的中心卡片没有 ZIP 安装按钮。

英文原稿图片描述（图片已省略）：本例两种格式桥接均未启用。安装所需桥接后，才会显示其导入和导出控件。

*本地预览，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。本例两种格式桥接均未启用。安装所需桥接后，才会显示其导入和导出控件。*

---

### VRM 与 VRoid 导入 {#vrm-and-vroid-import}

**用途：** 导入 `.vrm` 虚拟形象（来自 VRoid Studio、Virtual Cast 或其他 VRM 来源），连同材质、骨架和形态键。

- **Import VRM…** — `.vrm` 文件
- **Import VRoid (.vroid / .zip)…** — VRoid Hub 下载文件（`.zip`）。VRoid Studio 项目（`.vroid`）会显示卡片，说明应先将它导出为 VRM。

---

### VRM 导出 {#vrm-export}

**用途：** 将已绑定角色导出为 VRM 或目标应用格式。

**设置：**

- **Folder** 和 **File** — 目标位置和文件名，扩展名随目标格式变化
- **Target** — VRM 1.0、VRM 0.x、VRChat FBX、VSeeFace、Warudo 或 Resonite
- **Scope** — 活动骨架，或所有带 VRM 数据的骨架
- Skip lint — 不进行目标检查而直接导出，仅在理解报告风险时使用

点击 **Export…**。

---

### VRM 检查 {#vrm-lint}

**用途：** 导出前按所选目标检查骨架，涵盖人形映射、VRM 元数据、目标口形及目标应用的要求。

**Lint Now** 只检查，不更改数据。除非跳过检查，否则错误会阻止导出；警告表示目标应用可能导入内容，但性能可能降低。

若检查报告缺少实际已存在的人形骨骼，点击 **Fix Humanoid Map**。BoneCraft 重新检测人形槽位并保存映射，不重命名骨骼。

**同处还有：** **Convert SpringBones → PhysBones**（将 VRoid 头发物理转换为 VRChat）和 **Map VRoid Visemes**。

---

## MMD 桥接 {#mmd-bridge}

MMD 工具位于 **CATS → Import / Export → MMD / PMX**，需要安装并启用 **mmd_tools**。BoneCraft 识别旧式软件包及现代 Blender Extensions。

未激活的桥接提供 **Auto-Install Latest from GitHub**、**Open Add-on Preferences**、**Website** 和 **Show Manual Instructions**。独立桥接内容在显示时还提供 **Install from .zip on Disk...**。安装及本地扩展存储库检查见[指南 3](02-guides-a.md#step-1--install-mmd_tools)。

---

### MMD 导入 {#mmd-import}

- **Import PMX / PMD...** — MMD 模型
- **Import VMD Motion...** — MMD 动画
- **Import VPD Pose...** — MMD 姿态

确认导入成功完成。取消 PMX 导入或出现安装错误时，任务仍未完成。导入的模型在转换前可能需要检查材质及骨骼映射。

---

### MMD 导出 {#mmd-export}

**设置：** **Folder** 设置目标位置，各格式均有文件名和范围设置：

- **PMX File** 和 **PMX Scope**。
- **VMD File** 和 **VMD Scope**。
- **VPD File** 和 **VPD Scope**。

每个范围可选择活动模型或场景中的所有 MMD 模型。

**按钮：** **Export PMX...**、**Export VMD Motion...** 和 **Export VPD Pose...**

**同处还有：** **Convert Bone Names -> Unity** 和 **Convert Physics -> PhysBones**。

---

## 游戏引擎导出 {#game-engine-export}

**Game Engine Export** 是 **CATS → Import / Export** 下的内嵌区域，包含 **Unity / VRChat** 和 **Unreal Engine 5**；独立子面板 **Game Export** 提供经验证的配置文件导出。

### Unreal Engine 5 {#unreal-engine-5}

启用 **Bake Anim** 时，导出器烘焙活动动作，无需单独 NLA 片段；不会导出所有无关动作。

使用 **Bone Names** 预设前，先修正映射或命名冲突；下方“导出骨骼命名”小节解释这些冲突。导出前将链接对象转为本地。

1. 选择骨架及其网格。
2. 打开 **CATS → Import / Export → Game Engine Export → Unreal Engine 5**。
3. 设置 **Folder**。
4. 将 **File** 设为 FBX 名称。
5. 检查 **Bone Names** 及预览。
6. 需要活动动画时，启用 **Bake Anim**。
7. 点击 **Export to Unreal (FBX)**。

**Selected Only** 初始启用；应将骨架和网格一同选中。**Unit Scale** 初始启用，**Leaf Bones** 初始关闭，**Embed Textures** 初始启用。面板将 **Bake Animation** 缩写为 **Bake Anim**。

**Import from Unreal (FBX)** 打开导入文件浏览器。

英文原稿图片描述（图片已省略）：选择输出文件夹前的 Unreal Engine 5 设置。导出前检查 Bone Names、Selected Only 和 Bake Anim。

*本地预览，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。选择输出文件夹前的 Unreal Engine 5 设置。导出前检查 Bone Names、Selected Only 和 Bake Anim。*

### 导出骨骼命名 {#export-bone-naming}

两个引擎分区提供相同的 **Bone Names** 选项：

| 选项 | 导出结果 |
| --- | --- |
| Keep Original Names | 保留已有骨骼名称，默认选项。 |
| Unity-Preset | 使用识别到的 Unity Humanoid 名称，包括 `Hips`、`LeftUpperArm` 和 `LeftIndexProximal`。 |
| Unreal-Preset | 使用识别到的 Unreal 人形名称，包括 `pelvis`、`spine_01`、`upperarm_l`、`index_01_l` 和 `ball_l`。 |

选择骨架后显示预览，包括 **Recognized / renamed** 数量和最多三项拟议更改。无法识别的骨骼保留原名。

已保存的人形映射优先于名称检测。已识别的可选胸部、颈部、肩部、眼部、下颌、手指和脚趾骨骼也参与命名。独立且被识别的 `Root` 在 **Unreal-Preset** 中变为 `root`。

目标名称冲突、骨骼含义不明确或重复使用人形槽位时，会阻止重命名。导出前修正映射或命名冲突；BoneCraft 不会添加 `.001` 后缀解决这些冲突。

导出前将链接对象转为本地。预设重命名临时导出副本，工作绑定保留骨骼原名。导出的顶点组、动画通道及 Unity 辅助文件骨骼引用遵循所选名称。无论成功或失败，清理都会删除临时数据。

这些预设只改名称，保留层级、骨骼朝向和静置姿态，不补齐缺失关节，也不构建完整 Manny/Quinn 骨架。仍可能需要 Unity Avatar 映射或 Unreal 重定向。

### 经验证的配置文件导出 {#validated-profile-export}

**用途：** 使用经过验证的配置导出，包括 Unreal 人形或通用、Unity 人形、Godot 人形、通用 FBX 或 GLB。问题列表显示可用修复；修复需要您明确操作。

此配置流程使用对象模式。对象/姿态/编辑模式的恢复保证仅适用于两个主要引擎导出按钮。

使用 **Bone Names** 预设前，修正映射或命名冲突；上方“导出骨骼命名”小节解释这些冲突。导出前将链接对象转为本地。

**文件浏览器设置：** **Profile**、**Animation**、**Bone Names**、**Root Motion**、**Interpolation** 和 **T-Pose**。**Bone Names** 初始遵循 Unreal 分区的选择；导出格式配置仍是独立选项。

使用命名预设时，选择 **Active Action** 或 **No Animation**；**All Actions** 可能包含其他绑定的动作，因此必须使用 **Keep Original Names**。

默认 **T-Pose** 遵循配置：Unity 人形及 VRChat 配置使用 T 姿态。T 姿态导出包含无动画的静置姿态；需要建模时的静置姿态时，选择 **Export as modelled**。

1. 选择骨架及其网格。
2. 打开 **CATS → Import / Export → Game Export**。
3. 点击 **Check for Export**。
4. 检查问题及需要明确执行的修复。
5. 点击 **Export (Profile)**。
6. 在文件浏览器中选择设置。
7. 选择输出文件。
8. 确认导出。

英文原稿图片描述（图片已省略）：确认前的配置文件导出选项。本例使用 Generic FBX、Active Action 和 Keep Original Names。

*本地预览，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。确认前的配置文件导出选项。本例使用 Generic FBX、Active Action 和 Keep Original Names。*

**按钮：**

- **Check for Export** — 按配置检查绑定并列出问题
- **Apply Transforms (Fix)** — 检查可能提供的一项明确修复
- **Export (Profile)** — 按配置导出

**位置：** **CATS** 选项卡 → **Import / Export** → **Game Export**

其他命名详情和历史宿主验证见[独立导出命名指南](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/export-bone-naming.md)。

英文原稿图片描述（图片已省略）：Check for Export、明确修复和 Export (Profile)。本例尚无配置检查结果。

*原生面板弹出窗口，BoneCraft 9.2.18。Check for Export、明确修复和 Export (Profile)。本例尚无配置检查结果。*

---

## 任务板 {#task-board}

**用途：** 用健康评分、快速改进项及按类别分组的任务概览当前绑定。任务包括缺少人形骨骼、名称未解决、缺少口形及绑定验证警告。**Quick Wins** 最多显示三项建议任务；**Remaining Tasks** 仅包含其他任务。**Open Health Check** 运行验证并打开结果，**Refresh Task Board** 再次检查。

**位置：** **BoneCraft** 选项卡 → **Overview** → **Task Board**

英文原稿图片描述（图片已省略）：Task Board 为活动示例绑定列出健康检查发现及快捷操作。

*原生面板弹出窗口，BoneCraft 9.2.18。Task Board 为活动示例绑定列出健康检查发现及快捷操作。*

---

### 骨骼检查器 {#bone-inspector}

**用途：** 显示活动姿态骨骼的静置尺寸、父级、约束、自定义数据、驱动器和蒙皮权重。

信息只读。在姿态模式中有活动骨骼时打开此面板。要复制骨骼名称，在标题栏选择 **Copy Name**。

**位置：** **BoneCraft** 选项卡 → **Review** → **Bone Inspector**

英文原稿图片描述（图片已省略）：Bone Inspector 显示静置骨骼详情、约束、自定义数据、驱动器及蒙皮权重。标题栏包含 Copy Name。

*原生测试构建弹出窗口，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。Bone Inspector 显示静置骨骼详情、约束、自定义数据、驱动器及蒙皮权重。标题栏包含 Copy Name。*

下一章：[CATS 工具](09-cats.md)
