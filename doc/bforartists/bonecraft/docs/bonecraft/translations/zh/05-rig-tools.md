# 绑定工具 {#rig-tools}

[← 目录](index.md)

本章介绍 BoneCraft 的绑定、动画和权重工具，用于查阅功能详情或处理指南未涵盖的情况。

每项工具均说明用途、使用场景、主要控件和位置。“位置”注明所需模式：绑定控制需要姿态模式；Weight Mirror 和 Weight Transfer 需要权重绘制模式；Delta Mush 需要对象模式。工具无法运行时，有些分区仍保持可见，并提示应选择什么。

自 9.1 起，许多工具立即运行，再通过 Adjust Last Operation 面板显示选项。点击后应立即调整，再执行其他操作。常用操作在 Pose → BoneCraft 和 Weights → BoneCraft 菜单有快捷入口；Bforartists 的 Pose 和 Weights 工具架选项卡也有 BoneCraft 按钮面板。[入门](01-start.md#where-things-are)列出这些入口。

图片描述的是示例绑定及工具设置。请按各工具路径打开控件。

引擎导出见 [VRChat 工具：游戏引擎导出](08-vrchat.md#game-engine-export)。**Bone Names** 预设更改导出副本，与重命名工作绑定的工具用途不同。

---

## 绑定界面工具 {#rig-ui-tools}

这些工具在使用骨架时控制骨骼可见性、组织方式及快捷访问。

---

### 骨骼集合 {#bone-collections}

**用途：** 将骨架的骨骼集合按行显示。点击集合名选择其中骨骼，眼睛图标显示或隐藏集合。

> 骨骼集合是具名骨骼组，例如“IK Controls”“Face Bones”“Deform Bones”。隐藏集合会隐藏视口中的对应骨骼，便于专注绑定的一部分。

**主要控件：**

- 每行包含强调色、**Toggle Collection Visibility**（眼睛图标）、集合名、**Solo Collection** 和 **Rename Collection Display**。集合名用于选择骨骼；**Rename Collection Display** 为该行设置自定义显示名。仅图标按钮可通过悬停提示识别
- 列表上方的 **Show All Collections** 和 **Hide All Collections**（睁眼及闭眼图标）一次显示或隐藏全部集合
- Sections 将多个集合分组到可折叠标题下

**位置：** BoneCraft 选项卡 → Review → Collections

英文原稿图片描述（图片已省略）：骨骼集合及其可见性、选择、独显和显示名称控件。

*原生测试构建弹出窗口，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。骨骼集合及其可见性、选择、独显和显示名称控件。*

---

### 可见性书签 {#visibility-bookmarks}

**用途：** 保存哪些骨骼集合可见，便于一次切换到已保存视图。

**使用示例：** “Face Only”保存只显示面部骨骼的视图，便于表情制作；“Full Rig”保存全部骨骼视图，便于权重绘制。点击即可切换已保存视图。

**主要控件：** 每个槽位占一行。

- 书签名——点击应用保存视图
- **Save Bookmark**——将当前可见性保存到该槽位，悬停图标可查看提示
- 色块——以颜色标识书签
- **Clear Bookmark** 和 **Remove Bookmark**（关闭图标）——清空槽位或移除新增槽位
- **Add Bookmark**——添加槽位

**默认书签：** FK Arms、IK Body、Face Only、Full Rig

**位置：** BoneCraft 选项卡 → Review → Collections → Visibility Bookmarks

英文原稿图片描述（图片已省略）：Visibility Bookmarks 中有一个已保存 Full Rig 视图和三个可用槽位。

*原生测试构建弹出窗口，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。Visibility Bookmarks 中有一个已保存 Full Rig 视图和三个可用槽位。*

---

### 热键快捷面板 {#hotkey-quick-panel}

**用途：** 在鼠标所在位置弹出 BoneCraft 绑定面板（集合及书签）。

**使用方法：**

1. 在 3D 视口按 **Ctrl+Shift+R**。
2. 点击弹窗外关闭。

**位置：** 3D 视口中的 **Ctrl+Shift+R** 快捷键，没有独立面板。

快捷面板使用[上文书签控件](#visibility-bookmarks)。

---

## 动画工具 {#animation-tools}

---

### 姿态库 {#pose-library}

**用途：** 保存带缩略图的具名姿态，可一键应用到绑定。

**主要控件：**

- **Save**——将当前骨骼位置保存为具名姿态，并生成视口缩略图
- **Apply**——将骨骼吸附到保存姿态
- **Blend**——以部分强度应用姿态，与当前位置混合
- **Mirror**——应用左右翻转姿态
- **Delete**、**Rename** 和 **Category**——管理列表；**Filter** 显示一个类别
- **Export** 和 **Import**——保存或加载 `.bfpose` 文件

Blend 立即应用。点击后，在 Adjust Last Operation 设置混合强度。

**位置：** BoneCraft 选项卡 → Review → Pose Library

英文原稿图片描述（图片已省略）：保存的示例姿态提供 Apply、Mirror、Blend 和姿态库控件。

*原生面板弹出窗口，BoneCraft 9.2.18。保存的示例姿态提供 Apply、Mirror、Blend 和姿态库控件。*

---

### 控制器选择面板 {#control-picker}

**用途：** 可点击的绑定控制器示意图，点击形状选择相应骨骼，选中的控制器会高亮。

**主要控件：**

- **Generate Picker**——根据绑定构建布局
- **Edit Layout**——编辑布局；每个控件行有 **Move Picker Control**、**Resize Picker Control** 和 **Relabel Picker Control** 图标；**Snap** 将控件对齐网格，**Rebuild Layout** 重新生成布局
- **Mirror Selection**——选择镜像控制器
- **Pop-up Picker**——在浮动窗口打开选择面板，窗口还提供 **Add Selection Set**

**位置：** BoneCraft 选项卡 → Review → Control Picker

英文原稿图片描述（图片已省略）：生成的 Control Picker 显示示例控件、布局编辑、镜像选择及弹出选择面板操作。

*原生面板弹出窗口，BoneCraft 9.2.18。生成的 Control Picker 显示示例控件、布局编辑、镜像选择及弹出选择面板操作。*

---

### 控制层（IK/FK） {#control-layer-ikfk}

需要书面实操比较时，参阅[测试权重并使用 IK/FK](06-rig-builder.md#part-c-test-weights-and-use-ikfk)。

**用途：** 控制由 **Build Control Rig** 生成的绑定肢体，可无跳变地切换 IK 与 FK，并在帧范围内将 IK 动画转换为 FK，或将 FK 转换为 IK。

**主要控件：**

- **IK** 和 **FK**——切换肢体，将新控件吸附到当前位置，肘或膝不跳变
- **Bake IK** 和 **Bake FK**——在帧范围内将动画转换为 IK 或 FK
- **Pole Follow**、**Pin**、**Lock-Free** 及保留受保护锁定的 **Global Rig Scale**

**位置：** BoneCraft 选项卡 → Review → Control Layer（选择由 **Build Control Rig** 创建的绑定；见 [Rig Builder](06-rig-builder.md)）

英文原稿图片描述（图片已省略）：Control Layer 显示肢体 IK/FK 开关、烘焙操作及绑定设置。

*历史练习截图。Control Layer 显示肢体 IK/FK 开关、烘焙操作及绑定设置。*

---

### Rigify 工具 {#rigify-tools}

**用途：** 检测 Rigify 控制绑定，将 BoneCraft 集合面板、书签和属性滑块连接到 Rigify 标准控件。

> Rigify 是 Bforartists 内置的动画绑定生成系统。若绑定由 Rigify 创建，此功能将 BoneCraft 界面连接到 Rigify 的 IK/FK 控件。

**主要控件：**

- **Auto-Enhance**——为所选 Rigify 绑定配置 BoneCraft 面板
- **Re-run Enhancement**——从头重建面板
- **Enable Rigify** 位于 Quick Rig，其 Troubleshooting 折叠区包含 **Generate Control Rig (active metarig)**（见 [Rig Builder](06-rig-builder.md)）
- Rigify Properties——绑定的 IK/FK、拉伸、父级空间及头颈跟随滑块

**位置：** BoneCraft 选项卡 → Setup Rigging → Rigify Tools（及 Rigify Properties 分区）

英文原稿图片描述（图片已省略）：Rigify Tools 显示增强入口。选择生成后的 Rigify 绑定使用适用控件。

*原生面板弹出窗口，BoneCraft 9.2.18。Rigify Tools 显示增强入口。选择生成后的 Rigify 绑定使用适用控件。*

---

### 动画重定向 {#retarget}

**用途：** 在骨架间传递动画，例如将动作捕捉片段传给虚拟形象。按骨骼名称和方向匹配以保留肢体朝向；较宽松的锁骨匹配避免肩部过度旋转。

**主要控件：**

- **Import Clip** 和 **Browse Library**——加载片段或设置动画库文件夹；点击片段名选择
- **Auto-Match Bones**（片段行勾选图标）——配对来源与目标骨骼，Bone Mapping 列表显示配对
- **Preview** 和 **Stop Preview**——试用结果
- **Apply**——将片段烘焙到绑定

**位置：** BoneCraft 选项卡 → Setup Rigging → Retarget

英文原稿图片描述（图片已省略）：Retarget 从 Import Clip 和 Browse Library 开始。加载片段后显示映射及预览。

*原生面板弹出窗口，BoneCraft 9.2.18。Retarget 从 Import Clip 和 Browse Library 开始。加载片段后显示映射及预览。*

---

### 修正形态键 {#corrective-shape-keys}

**用途：** 骨骼到达指定角度时启用的形态键，修复极端姿态下的夹皱或塌陷。

**使用示例：** 角色肘部完全弯曲时塌陷，可将雕刻的肘部修正关联到手臂骨骼，弯曲时自动应用。

**主要控件：**

- New Corrective——**Shape Key**、**Driver Bone**、旋转轴、完全生效角度及渐入设置
- 修正列表——下方 **Edit** 和 **Delete** 作用于所选修正

骨架的子网格必须有基形形态键。选择骨架显示 New Corrective；其子网格提供形态键。

创建修正：

1. 选择 **Shape Key**。
2. 选择 **Driver Bone**。
3. 选择旋转轴。
4. 设置形态完全生效时的角度。
5. 设置渐入程度。
6. 选择 **Create Corrective**。

点击列表中的形态键名选择已有修正。

Edit 从当前修正值开始。点击后：

1. 在 Adjust Last Operation 更改角度。
2. 更改衰减。

**位置：** BoneCraft 选项卡 → Skin → Correctives（网格需要基形形态键）

英文原稿图片描述（图片已省略）：选择骨架显示 New Corrective，子网格提供形态键。

*原生面板弹出窗口，BoneCraft 9.2.18。选择骨架显示 New Corrective，子网格提供形态键。*

---

### 曲线工具 {#graph-tools}

**用途：** 用于关键帧和曲线的动画细化工具。

- **Interactive Breakdown**（Breakdowner）——左右拖动时，在相邻关键帧之间混合当前姿态；3D 视口快捷键为 **Ctrl+Shift+B**
- **Apply Delta**（Delta Mover）——在屏幕或世界空间按精确数值偏移所选骨骼；3D 视口快捷键为 **Ctrl+Shift+D**
- **Capture** 和 **Swap**（Buffer Curves）——保留曲线副本，并在副本和编辑结果间切换
- **Smart Bake**——将约束驱动动画烘焙为关键帧，并删除冗余键，**Tol** 控制容差
- **Euler Filter**——修复万向节锁导致的旋转翻转
- Tangent Handles——为选中键设置控制柄类型：**Auto**、**Vector**、**Aligned**、**Free** 或 **Auto Clamped**

**位置：** BoneCraft 选项卡 → Review → Graph Tools

英文原稿图片描述（图片已省略）：Interactive Breakdown 在选中姿态骨骼上开始拖动操作。

*原生面板弹出窗口，BoneCraft 9.2.18。Interactive Breakdown 在选中姿态骨骼上开始拖动操作。*

英文原稿图片描述（图片已省略）：Apply Delta 及其偏移选项。

*原生面板弹出窗口，BoneCraft 9.2.18。Apply Delta 及其偏移选项。*

英文原稿图片描述（图片已省略）：Buffer Curves、Euler Filter 和 Smart Bake。Options 折叠区关闭。

*原生面板弹出窗口，BoneCraft 9.2.18。Buffer Curves、Euler Filter 和 Smart Bake。Options 折叠区关闭。*

英文原稿图片描述（图片已省略）：Tangent Handles 提供 Auto、Vector、Aligned、Free 和 Auto Clamped。

*原生面板弹出窗口，BoneCraft 9.2.18。Tangent Handles 提供 Auto、Vector、Aligned、Free 和 Auto Clamped。*

---

## 权重工具 {#weight-tools}

这些工具控制骨骼运动时网格如何变形。权重规定每部分网格跟随哪些骨骼，以及跟随程度。

---

### 自动骨骼权重重算 {#automatic-bone-weight-recalculation}

**用途：** 根据已有绑定重新计算网格权重，不更改网格。密集网格通过较轻的代理网格处理，避免静默失败。

**主要控件：** Body 根据现有绑定计算权重；Clothing 从正确加权的来源网格传递权重。设置位于按钮上方。

1. 在 **Mesh to Reweight** 选择目标网格。
2. 在 **Existing Armature** 选择骨架。
3. 选择 Body 或 Clothing 模式。

Body 模式需要选择方法。

Clothing 模式：

1. 在 **Weighted Body** 选择权重正确的来源网格。
2. 选择方法。

两种模式均需：

1. 设置混合。
2. 设置平滑。
3. 设置每顶点最大骨骼影响数。
4. 设置最小权重。
5. 选择是否保留备份。
6. 选择 **Automatic Bone Weight Recalculation**。

CATS 快捷操作 **Smart Automatic Weights** 打开设置目标网格、骨架和模式的对话框，Clothing 模式还包含来源网格。

**位置：** BoneCraft 选项卡 → Skin → Weight Tools

英文原稿图片描述（图片已省略）：选择示例网格和骨架后的 Automatic Bone Weight Recalculation 设置。

*原生测试构建弹出窗口，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。选择示例网格和骨架后的 Automatic Bone Weight Recalculation 设置。*

---

### 镜像权重 {#weight-mirror}

**用途：** 将虚拟形象一侧权重复制到另一侧，适合对称角色。

**主要控件：**

- **Mirror All Weights**——将每个骨骼组镜像到对侧
- **Mirror Active Weight**——仅镜像活动骨骼组
- **Axis** 和 **Direction**——选择反射轴及来源侧
- **Search Distance**——反射顶点位置到空间匹配点的允许距离
- **Select Unmatched**——选择没有对应点的顶点；**Normalize Weights** 随后使权重总和为 1.0

镜像按空间位置匹配，而非网格拓扑。

1. 点击镜像按钮。
2. 在 Adjust Last Operation 选择 **Axis**。
3. 选择 **Direction**。
4. 设置 **Search Distance**。

**Mirror Active Weight** 也位于 Weights → BoneCraft 和 Weights 工具架选项卡。

**位置：** BoneCraft 选项卡，权重绘制模式 → Weight Mirror

英文原稿图片描述（图片已省略）：Weight Mirror 操作。点击后在 Adjust Last Operation 设置轴及搜索选项。

*原生面板弹出窗口，BoneCraft 9.2.18。Weight Mirror 操作。点击后在 Adjust Last Operation 设置轴及搜索选项。*

---

### 传递权重 {#weight-transfer}

**用途：** 将来源网格权重复制到活动网格，适用于将服装连接身体，或从高分辨率网格向低分辨率网格转移权重。

**主要控件：** Adjust Last Operation 中的 **Normalize** 使权重总和保持为 1.0；**Select Problem Vertices** 选择匹配不佳的顶点。

在权重绘制模式保持目标网格为活动对象。

1. 在 **Source Mesh** 选择来源网格。
2. 点击 **Transfer Weights**。
3. 在 Adjust Last Operation 选择传递方法。
4. 选择骨骼筛选器。

结果显示平均和最大距离。

**位置：** BoneCraft 选项卡，权重绘制模式 → Weight Transfer（也位于 Skin → Weight Tools）

英文原稿图片描述（图片已省略）：Transfer Weights 前选择 Source Mesh。本例距离字段仍为初始值。

*原生面板弹出窗口，BoneCraft 9.2.18。Transfer Weights 前选择 Source Mesh。本例距离字段仍为初始值。*

---

### 权重表 {#weight-table}

**用途：** 显示所选顶点对每根骨骼的精确权重，并可设置精确数值。

**使用方法：**

1. 进入权重绘制模式。
2. 启用**顶点选择遮罩**。
3. 选择一个顶点。

表格列出所选顶点的骨骼及权重。

4. 点击骨骼行的手形图标。
5. 在 Adjust Last Operation 设置 **Weight**。

Add Influence 使用您选择的骨骼，操作后也应在 Adjust Last Operation 设置新权重。选择多个顶点时，**Normalize All Vertices** 归一化全部所选顶点。

**位置：** BoneCraft 选项卡，权重绘制模式 → Weight Table

英文原稿图片描述（图片已省略）：选中多个顶点时的 Weight Table。要详细编辑权重，请只选择一个顶点。

*原生面板弹出窗口，BoneCraft 9.2.18。选中多个顶点时的 Weight Table。要详细编辑权重，请只选择一个顶点。*

---

### 整体填充 {#flood-fill}

**用途：** 更改整个网格中活动顶点组的权重，包括未选顶点。

使用任何 Flood Fill 操作前：

1. 选择网格。
2. 进入权重绘制模式。
3. 激活所需顶点组。

**操作：**

- **Flood to 0.0** 移除整个网格中活动组已分配的正权重，其他顶点组不变。
- **Flood to 1.0** 为所有顶点的活动组分配 1.0；对每个顶点，若其他正权重总和超过 1e-6，就移除这些权重。
- **Flood to Custom** 为所有顶点的活动组分配正的 **Value**。启用 **Normalize** 时，还会归一化整个网格的权重。**Value** 为 0 时，不分配也不归一化；清空权重应使用 **Flood to 0.0**。

Weights 菜单和工具架将固定值按钮称为 Flood to Zero 和 Flood to One。

自定义填充：

1. 选择 **Flood to Custom**。
2. 紧接着在 Adjust Last Operation 设置 **Value**。
3. 启用或关闭 **Normalize**。

**位置：** 权重绘制模式：BoneCraft 选项卡 → Skin → Weight Tools；也位于 Weights → BoneCraft 及 Tool Shelf → Weights → BoneCraft

英文原稿图片描述（图片已省略）：Flood Fill 操作。点击后在 Adjust Last Operation 设置自定义数值。

*原生面板弹出窗口，BoneCraft 9.2.18。Flood Fill 操作。点击后在 Adjust Last Operation 设置自定义数值。*

---

### 变形骨骼与控制骨骼 {#deform-vs-control}

**用途：** 区分变形骨骼与控制骨骼。变形骨骼移动网格，动画师操作控制骨骼。工具标记变形骨骼，并按变形骨骼命名方式重命名，也可导出仅含变形骨骼的骨架。

**位置：** BoneCraft 选项卡，姿态模式 → Deform vs Control

英文原稿图片描述（图片已省略）：示例绑定的 Deform 和 Control 列表。此绑定有 19 根变形骨骼，没有控制骨骼。

*原生测试构建弹出窗口，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。示例绑定的 Deform 和 Control 列表。此绑定有 19 根变形骨骼，没有控制骨骼。*

---

### Delta Mush {#delta-mush}

**用途：** 减轻关节夹皱的平滑变形。网格静置时保留外形，运动时变形更平顺。

**使用方法：** 以下操作需要对象模式和活动网格。

1. 点击 **Add Delta Mush**。

工具添加修改器并绑定到静置形状。操作后立即调整选项：

2. 在 Adjust Last Operation 设置 **Iterations**。
3. 设置 **Smooth Strength**。
4. 启用或关闭 **Pin Borders**。
5. 启用或关闭 **Only Smooth Deform**。

修改器存在后，面板显示 **Rebind** 和 **Remove**。Settings 折叠区包含迭代次数、平滑强度和边界固定控件。

**位置：** BoneCraft → Skin → Delta Mush（对象模式；网格）

英文原稿图片描述（图片已省略）：Add Delta Mush 开始设置。点击后立即调整选项。

*原生面板弹出窗口，BoneCraft 9.2.18。Add Delta Mush 开始设置。点击后立即调整选项。*

---

### 邻近包裹 {#proximity-wrap}

**用途：** 使一个网格像第二层皮肤一样跟随另一个网格表面，适用于贴身服装。

**使用方法：** 需要对象模式和活动目标网格。绑定时让驱动网格的骨架保持静置姿态。

1. 选择目标网格。
2. 选择另一个 **Driver Mesh**。
3. 点击 **Bind Proximity Wrap**。

按钮下方 Options 折叠区列出 **Falloff Type** 和 **Max Distance**。在 9.1.2 中，设置会保存这些值，但不会改变 Surface Deform 绑定。绑定后显示 **Rebind** 和 **Unbind**；Unbind 在视口和渲染中禁用修改器，不删除修改器。

**位置：** BoneCraft → Skin → Proximity Wrap（对象模式；网格）

英文原稿图片描述（图片已省略）：Bind Proximity Wrap 前选择 Driver Mesh。Options 折叠区关闭。

*原生面板弹出窗口，BoneCraft 9.2.18。Bind Proximity Wrap 前选择 Driver Mesh。Options 折叠区关闭。*

---

## 绑定控制 {#rig-controls}

以下工具在姿态模式的 BoneCraft 选项卡显示。

---

### 空间切换 {#space-switch}

**用途：** 更改动画中骨骼跟随的空间。例如持物的手可一键从跟随身体切换为固定在世界空间。

**主要控件：**

- **Add Space** 和 **Remove Space**（Manage Spaces 下的 X 图标）——管理骨骼可跟随的空间（World、Origin 或另一骨骼）
- 每个空间一个同名按钮；当前空间带 ● 标记。点击其他空间按钮切换骨骼空间

**位置：** BoneCraft 选项卡，姿态模式 → Space Switch

英文原稿图片描述（图片已省略）：尚未定义空间时的 Space Switch。Add Space 开始设置。

*原生面板弹出窗口，BoneCraft 9.2.18。尚未定义空间时的 Space Switch。Add Space 开始设置。*

---

### 样条 IK {#spline-ik}

**用途：** 让骨骼链沿曲线运动，适用于需要流畅弯曲运动的尾巴、触手、绳索、长发和脊柱。

**使用方法：**

1. 将起始骨骼设为活动骨骼。
2. 点击 **Generate Spline IK**。
3. 在 Adjust Last Operation 设置 **Chain Length**。
4. 设置 **Curve Resolution**。
5. 设置 **Stretch**。
6. 设置 **Volume Preservation**。

**Remove Spline IK** 移除设置。

**位置：** BoneCraft 选项卡，姿态模式 → Spline IK

英文原稿图片描述（图片已省略）：Spline IK 操作。生成后在 Adjust Last Operation 设置骨骼链选项。

*原生面板弹出窗口，BoneCraft 9.2.18。Spline IK 操作。生成后在 Adjust Last Operation 设置骨骼链选项。*

---

### 骨骼链动力学 {#chain-dynamics}

**用途：** 为骨骼链添加类似物理的次级运动。骨骼会滞后于移动的父级，并在父级停止时弹回，适用于发束、尾巴和配饰。

**使用方法：**

1. 选择骨骼链。
2. 点击 **Add Chain Dynamics**。
3. 在 Adjust Last Operation 设置 **Stiffness**。
4. 设置 **Damping**。
5. 设置 **Mass**。
6. 设置 **Gravity Scale**。

操作下方的 Settings 折叠区也列出这些参数。添加动力学后，面板显示 **Bake** 和 **Remove**。碰撞使用简化球体，因此凹面可能无法正确碰撞。

**位置：** BoneCraft 选项卡，姿态模式 → Chain Dynamics

英文原稿图片描述（图片已省略）：Add Chain Dynamics 开始设置。需要参数时展开 Settings。

*原生面板弹出窗口，BoneCraft 9.2.18。Add Chain Dynamics 开始设置。需要参数时展开 Settings。*

---

### 带状绑定 {#ribbon}

**用途：** 创建 Bendy Bones 带状绑定，即能平滑弯曲和扭转的骨骼，用于嘴唇、眉毛、腰带及其他柔软曲面。

**使用方法：**

1. 选择骨骼链。
2. 点击 **Generate Ribbon**。
3. 在 Adjust Last Operation 设置 **Control Bones**。
4. 设置 **Ribbon Width**。

**Remove Ribbon** 移除设置。

**位置：** BoneCraft 选项卡，姿态模式 → Ribbon

英文原稿图片描述（图片已省略）：Ribbon 操作和链长度。点击后立即调整生成的带状绑定。

*原生面板弹出窗口，BoneCraft 9.2.18。Ribbon 操作和链长度。点击后立即调整生成的带状绑定。*

---

### 口形库 {#viseme-library}

**用途：** 创建及管理关联形态键的口形集，也可根据文字生成口型同步关键帧。映射 VRChat 口形请使用 VRChat Viseme Mapping；生成新口形请使用 CATS Visemes 分区。

**主要控件：**

- **New Set** 和 **Delete**——创建或删除口形集
- 每个集合中，每种口形一个带扬声器图标的按钮，用于预览
- Lip Sync——将文字转为口形关键帧，带每音素帧数和平滑设置

**位置：** CATS → Avatar Tools → Viseme Library（骨架）；Lip Sync（姿态模式）

英文原稿图片描述（图片已省略）：Viseme Library 从 New Set 开始；切换到姿态模式使用 Lip Sync。

*原生面板弹出窗口，BoneCraft 9.2.18。Viseme Library 从 New Set 开始；切换到姿态模式使用 Lip Sync。*

英文原稿图片描述（图片已省略）：Lip Sync 文字及 Generate Lip Sync。展开 Options 设置时序和平滑。

*原生面板弹出窗口，BoneCraft 9.2.18。Lip Sync 文字及 Generate Lip Sync。展开 Options 设置时序和平滑。*

---

### 设置驱动关键帧 {#set-driven-key}

**用途：** 不使用 Python 表达式，将一个骨骼变换值关联到另一个。例如控制骨骼沿 X 移动时，使目标骨骼沿 Z 上升。该面板创建骨骼变换目标。

1. 选择 **Driver Bone**。
2. 选择 **Driver Attribute**。
3. 选择 **Target Bone**。
4. 选择 **Target Attribute**。
5. 摆好骨骼姿态。
6. 记录每个点。
7. 选择 **Create SDK**。

**主要控件：**

- **Driver Bone** 和 **Driver Attribute**——驱动来源
- **Target Bone** 和 **Target Attribute**——被驱动目标
- **Set Value** 和 **Record Point**——记录曲线点
- **Create SDK**——构建驱动器

**位置：** BoneCraft 选项卡，姿态模式 → Set Driven Key

英文原稿图片描述（图片已省略）：记录驱动关键帧点前，选择驱动骨骼和目标骨骼。本例字段尚未分配。

*原生面板弹出窗口，BoneCraft 9.2.18。记录驱动关键帧点前，选择驱动骨骼和目标骨骼。本例字段尚未分配。*

---

### 绑定验证器 {#rig-validator}

**用途：** 按规则检查绑定并报告问题，包括命名、缺失骨骼、损坏约束、层级、权重、需要 Python 的驱动器和 Mechanisms 规则。带连字符的骨骼名（如 `DEF-upper_arm.L`）可通过。

**主要控件：**

- **Run Validation**——运行全部检查并列出结果
- **Export Report**——将结果保存到文件

检查失败时，Task Board（BoneCraft 选项卡 → Overview → Task Board）显示验证任务。

**位置：** BoneCraft 选项卡 → Review → Rig Validator

英文原稿图片描述（图片已省略）：验证报告一项集合警告。由于示例骨架没有设为子级的网格，验证跳过权重检查。

*原生测试构建弹出窗口，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。验证报告一项集合警告。由于示例骨架没有设为子级的网格，验证跳过权重检查。*

---

### 绑定笔记 {#rig-notes}

**用途：** 附在绑定骨骼上的书面笔记，用于记录设置、提醒及给协作者的说明。

**主要控件：** **Add Note** 以及每条笔记上的 **Remove**。Rig Readme 将绑定笔记显示为只读页面。

**位置：** BoneCraft 选项卡 → Overview → Rig Notes，以及 Review → Rig Readme

英文原稿图片描述（图片已省略）：姿态模式下附于 Hips 的笔记。Add Note 创建注释，Remove 删除该注释。

*原生测试构建弹出窗口，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。姿态模式下附于 Hips 的笔记。Add Note 创建注释，Remove 删除该注释。*

下一章：[Rig Builder](06-rig-builder.md)
