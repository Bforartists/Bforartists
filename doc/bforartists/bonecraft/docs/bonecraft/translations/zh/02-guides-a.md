# 指南 1–7 {#guides-17}

[← 目录](index.md)

## 指南 1：将第一个虚拟形象带入 VRChat {#guide-1-get-your-first-avatar-into-vrchat}

需要练习网格时，请按照[书面人体模型练习](06-rig-builder.md#illustrated-mannequin-workshop)操作。其阶段为 Simple Human、无绑定人体模型、Auto-Rig 和 IK/FK。

> **用时：** 首次完整操作约 45–60 分钟
> **结果：** 为已绑定、可用于 VRChat 的虚拟形象完成导出，供 VRChat SDK 使用

**开始前检查：**

- [ ] 已将 3D 模型导入 Bforartists（File > Import，选择相应格式）
- [ ] 模型处于 T 姿态（双臂向两侧伸出、身体直立），或接近此姿态
- [ ] 模型没有明显损坏的几何体（没有随机漂浮的三角面）
- [ ] 在 3D 视口中能看到呈灰色实体的模型

---

### 步骤 1 — 打开 Rig Builder {#step-1--open-the-rig-builder}

1. 在 3D 视口按 **T** 显示左侧工具架。

2. 打开 **Rig Builder**。

启用 Preferences → Tabs → Scene Properties → Show 时，Rig Builder 也显示在 **Properties → Scene** 中。它分为 **Auto-Rig Wizard**、Quick Rig（预制骨架）和 **Mannequin** 三部分。

3. 展开 **Auto-Rig Wizard**。

4. 选择 **Start Auto-Rig**。

也可通过 3D 视口的 Add → Armature → Auto-Rig Wizard 菜单启动向导，再在 Rig Builder 中继续。

英文原稿图片描述（图片已省略）：Rig Builder 选项卡中的 Auto-Rig Wizard。

*历史练习截图。Rig Builder 选项卡中的 Auto-Rig Wizard。*

---

### 步骤 2 — 选择网格 {#step-2--select-your-mesh}

向导列出场景中的网格。

1. 在列表中选择虚拟形象的网格。

2. 选择 **Next**。

**应看到的界面：** 一行“Selected:”及网格名称，随后进入绑定类型步骤。

英文原稿图片描述（图片已省略）：为 Auto-Rig Wizard 选择输入网格。

*历史练习截图。为 Auto-Rig Wizard 选择输入网格。*

---

### 步骤 3 — 选择绑定类型 {#step-3--choose-the-rig-type}

1. 需要眨眼、表情和口型同步时，选择 **Body + Face**。

2. 仅需要身体而不需要面部控制时，选择 **Body Only**。

3. 在 Generation Options 下，将 **Kinematics** 设为 IK/FK、IK only 或 FK only。

4. 选择 **Next**。

英文原稿图片描述（图片已省略）：选择身体绑定类型和 IK/FK 方法。

*历史练习截图。选择身体绑定类型和 IK/FK 方法。*

---

### 步骤 4 — 放置身体标记 {#step-4--place-body-markers}

标记用于定位骨盆、脊柱、颈部、头部、肩部、手臂、手、腿和脚。BoneCraft 根据这些位置构建骨骼，请仔细检查每个标记。

**智能检测：**

1. 选择 **Detect Markers**。

2. 选择 **Accept High**，保留高置信度标记。

3. 选择 **Reset Low**，清除低置信度标记，改为手动放置。

BoneCraft 沿网格肢体追踪，为每个标记分配置信度。**Guess Markers from Mesh** 则根据网格比例估算位置。

**使用视口工具：**

1. 在对象模式下，激活视口工具栏的 Place Rig Markers。

2. 点击网格，放置并确认工具标题栏中指定的标记。

3. 对下一个未确认标记重复操作。

4. 完成标记步骤后，在向导中选择 **Next**。

工具标题栏还包含轴锁和镜像开关。

**逐个标记放置：** 每个标记行包含一组图标按钮。悬停可阅读提示。

1. 选择标记行中的箭头图标 **Place Marker**。

2. 点击虚拟形象上需要的位置。

3. 位置正确后，选择勾选图标 **Confirm Marker**。

圆形箭头 **Reset Marker** 清除已放置的标记，便于重新放置。

**对称：** **Toggle Symmetry** 会在放置标记时同时放置对侧标记，是各左侧或右侧标记行的第一个图标。**Mirror L to R** 和 **Mirror R to L** 将所有已确认标记复制到另一侧。

1. 放好全部标记后，选择 **Confirm All Placed**。

2. 选择 **Next**。

英文原稿图片描述（图片已省略）：调整前检查已检测的身体标记。

*历史练习截图。调整前检查已检测的身体标记。*

---

### 步骤 5 — 放置手指标记 {#step-5--place-finger-markers}

1. 在 Finger Detail 下，选择手指数，从“0 — No Fingers”到“5 — Full Human Hand”。

2. 选择 **Guess Finger Markers**。

3. 调整位置不正确的标记。

4. 选择 **Next**。

BoneCraft 根据手部形状，从指根到指尖追踪每根手指。标准人手使用“5 — Full Human Hand”。

---

### 步骤 6 — 放置面部标记（仅 Body + Face） {#step-6--place-face-markers-body--face-only}

1. 选择 **Guess Face Markers**。

2. 按需调整眼睛、眼睑、眉毛、嘴角和下颌。

3. 选择 **Next**。

眼部标记保留手动指定的位置。

---

### 步骤 7 — 检查并生成 {#step-7--review-and-generate}

检查步骤列出警告及生成选项。点击 **Generate Rig**。

**应看到的界面：** 虚拟形象内部出现橙色骨骼，包括 IK/FK 肢体和手指骨骼。Body + Face 还包含面部绑定。骨骼移动时，已连接的蒙皮随之变形。

最后一步提供 **Build Control Rig** 和 **Close Wizard**。Build Control Rig 应用 Generate Rig 未应用的检查选项。[Rig Builder](06-rig-builder.md)介绍这两个控件。

> **蒙皮权重** 定义每部分网格由哪些骨骼驱动。BoneCraft 自动设置权重。需要细调时，使用[绑定工具](05-rig-tools.md)中的权重工具。

英文原稿图片描述（图片已省略）：生成前检查绑定设置。

*历史练习截图。生成前检查绑定设置。*

---

### 步骤 8 — 映射到 VRChat 人形骨骼 {#step-8--map-to-vrchats-humanoid-bones}

1. 按 **N** 显示右侧栏。

2. 打开 **CATS → Avatar Tools → Set Up Humanoid Bones**。

3. 选择 **Auto-Map All**。

4. 选择 **Normalize Names**。

5. 选择 **Validate**。

Auto-Map All 将骨骼连接到 VRChat 身体槽位；Normalize Names 为已映射骨骼设置 VRChat 预期的名称。

**应看到的界面：** Hips、Spine、Head、LeftUpperArm 等必需槽位均显示一根骨骼。指南 5 介绍这些槽位。

参见[人形映射控件](08-vrchat.md#set-up-humanoid-bones)。

---

### 步骤 9 — 导出供 VRChat 使用 {#step-9--export-for-vrchat}

参见 [Unity / VRChat 导出设置](08-vrchat.md#export-to-vrchat)。

1. 选择虚拟形象骨架。
2. 打开 **CATS → Import / Export → Game Engine Export → Unity / VRChat**。
3. 设置 **Folder**。
4. 将 **Avatar** 设为导出名称。
5. 选择 **Bone Names**。
6. 使用预设时，检查命名预览。
7. 点击 **Export to VRChat (Unity)**。

默认使用 **Keep Original Names**。**Unity-Preset** 和 **Unreal-Preset** 在导出副本上重命名已识别的骨骼，工作绑定保留原名。

主要 Unity 和 Unreal 导出按钮支持对象、姿态和编辑模式，并恢复原模式和选择。

冲突、映射和动画限制见[导出命名及限制](08-vrchat.md#export-bone-naming)。

**应看到的结果：** 所选文件夹中生成导出的虚拟形象，可交给 VRChat Creator Companion 和 Unity 中的 VRChat SDK。

---

**接下来可以做什么：** 您已有一套绑定好的 VRChat 虚拟形象，可继续添加头发物理（指南 6）、服装（指南 7）、口型同步（指南 8）或检查性能（指南 9）。CATS 清理及 VRChat 设置见[指南 13](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats)。

---

## 指南 2：将 VRoid 虚拟形象带入 VRChat {#guide-2-bring-a-vroid-avatar-into-vrchat}

> **用时：** 约 15–25 分钟
> **结果：** 为 VRoid 虚拟形象完成 VRChat 导出准备

**开始前检查：**

- [ ] 已从 VRoid Studio 导出 `.vrm` 文件，或从 VRoid Hub 下载 `.zip`
- [ ] 已安装并启用 BoneCraft

---

### 步骤 1 — 安装 VRM 插件 {#step-1--install-the-vrm-add-on}

BoneCraft 需要 VRM 插件读取 `.vrm` 文件。

1. 打开 **CATS → Import / Export → VRM / VRoid**。

2. 导入前安装依赖项。

3. 启用依赖项。

未激活的桥接提供 **Auto-Install Latest from GitHub**、**Open Add-on Preferences**、**Website** 和 **Show Manual Instructions**。

使用离线软件包时：

1. 打开原生偏好设置。

2. 旧式插件 ZIP 通过 **Add-ons → Install from Disk…** 安装。

3. 现代扩展包改用原生 Extensions 安装菜单。

4. 返回桥接。

5. 确认桥接报告 **Active**。

参见[格式桥接安装控件](08-vrchat.md#vrm-bridge)。

---

### 步骤 2 — 导入虚拟形象 {#step-2--import-your-avatar}

1. 在 **VRM / VRoid** 中选择 **Import VRM…**。

2. 选择 `.vrm` 文件。

使用 VRoid 下载文件时：

1. 改选 **Import VRoid (.vroid / .zip)…**。

2. 选择下载的 `.zip` 文件。

若选择 VRoid Studio 项目文件（`.vroid`），BoneCraft 会显示“VRoid Studio Project”卡片。项目尚不是可直接使用的虚拟形象。

处理项目文件时：

1. 在 VRoid Studio 中将项目导出为 VRM。

2. 导入该 VRM 文件。

**应看到的界面：** VRoid 角色及其骨架出现在视口中。

---

### 步骤 3 — 映射到 VRChat 人形骨骼 {#step-3--map-to-vrchats-humanoid-bones}

1. 打开 **CATS → Avatar Tools → Set Up Humanoid Bones**。

2. 选择 **Auto-Map All**。

VRoid 骨架遵循标准布局，因此通常会填满所有槽位。槽位有误时，在 **VRM / VRoid** 的 Lint 下选择 **Fix Humanoid Map**，修复常见的 VRoid 名称映射错误。

---

### 步骤 4 — 修正骨骼名称 {#step-4--fix-bone-names}

在 **Set Up Humanoid Bones** 中选择 **Normalize Names**，将已映射骨骼的 VRoid 名称替换为 VRChat 预期名称。

---

### 步骤 5 — 设置口形（口型同步） {#step-5--set-up-visemes-lip-sync}

VRoid 虚拟形象已有用于口型同步的嘴部形态。在 **VRM / VRoid** 分区点击 **Map VRoid Visemes**，BoneCraft 将 VRoid 形态键匹配到 VRChat 口形。

---

### 步骤 6 — 头发物理（可选） {#step-6--hair-physics-optional}

VRoid 头发使用 SpringBones。**VRM / VRoid** 分区的 **Convert SpringBones → PhysBones** 将其转换为 VRChat PhysBones。指南 6 更详细介绍头发物理。

---

### 步骤 7 — 导出 {#step-7--export}

按指南 1，步骤 9 导出。

**接下来可以做什么：** VRoid 虚拟形象已可交给 VRChat Creator Companion。上传前还可检查性能（指南 9）。

---

## 指南 3：将 MMD 虚拟形象带入 VRChat {#guide-3-bring-an-mmd-avatar-into-vrchat}

> **用时：** 约 20–30 分钟
> **结果：** 为 MMD `.pmx` 模型完成 VRChat 准备

**开始前检查：**

- [ ] 已有 `.pmx` 或 `.pmd` MMD 模型文件
- [ ] 已安装 BoneCraft

---

### 步骤 1 — 安装 mmd_tools {#step-1--install-mmd_tools}

BoneCraft 需要 **mmd_tools** 读取 MMD 文件，支持旧式插件及现代 Blender Extensions。

1. 打开 **CATS → Import / Export → MMD / PMX**。
2. 桥接报告缺少依赖项时，点击 **Auto-Install Latest from GitHub**。
3. 使用 **Open Add-on Preferences** 启用已安装但被禁用的副本。
4. 导入前确认桥接报告 **Active**。

手动安装时：

1. 在未激活的桥接卡片选择 **Website** 或 **Show Manual Instructions**。

2. 通过 **Preferences → Get Extensions** 安装官方 MMD 扩展。

使用离线 ZIP 时：

1. 现代扩展包使用扩展安装菜单。

2. 旧式插件包则使用 **Add-ons → Install from Disk…**。

独立桥接内容在显示时还提供 **Install from .zip on Disk...**。

若安装报告没有本地扩展存储库：

1. 打开 **Preferences → Get Extensions → Repositories**。

2. 添加或启用本地存储库。

3. 重试安装。

使用上游发布软件包。安装错误或取消导入，不算导入成功。

参见[格式桥接安装控件](08-vrchat.md#vrm-bridge)。

---

### 步骤 2 — 导入 PMX 文件 {#step-2--import-your-pmx-file}

1. 在 **MMD / PMX** 中选择 **Import PMX / PMD...**。

2. 选择模型。

**应看到的界面：** MMD 角色出现在视口中，骨骼名称为日文。

---

### 步骤 3 — 修正骨骼名称 {#step-3--fix-bone-names}

导出 VRChat 前，将 MMD 骨骼映射到 Unity 人形槽位。

1. 在 **MMD / PMX** 中选择 **Convert Bone Names -> Unity**。

名称为其他语言时：

1. 打开 **CATS → CATS → Translate Bone Names**。

2. 选择来源 **Language**。

3. 选择 **Translate Bone Names**。

---

### 步骤 4 — 清理模型 {#step-4--clean-up-the-model}

MMD 模型经常有多余几何体和分离的部件。

1. 打开 **CATS → CATS**。

2. 检查 **Fix Model** 选项。

3. 选择虚拟形象需要的清理操作。

4. 运行 **Fix Model**。

5. 选择 **Join Meshes**，按 VRChat 建议将身体各部件合并成一个网格。

完整 CATS 流程见[指南 13](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats)。

---

### 步骤 5 — 映射到 VRChat 人形骨骼 {#step-5--map-to-vrchats-humanoid-bones}

1. 打开 **CATS → Avatar Tools → Set Up Humanoid Bones**。

2. 选择 **Auto-Map All**。

3. 空槽位请点击其按钮。

4. 选择对应骨骼。

MMD 骨架与 VRChat 骨架相似，因此多数槽位会自动填充。

---

### 步骤 6 — 物理与导出 {#step-6--physics-and-export}

**MMD / PMX** 分区中的 **Convert Physics -> PhysBones** 将 MMD 刚体头发和裙装物理转换为 VRChat PhysBones，随后按指南 1，步骤 9 导出。

**接下来可以做什么：** MMD 虚拟形象已可用于 VRChat。上传前还可添加头发物理（指南 6）及口型同步（指南 8）。

---

## 指南 4：修复虚拟形象的骨骼名称 {#guide-4-fix-your-avatars-bone-names}

> **用时：** 约 5–15 分钟
> **结果：** 将 VRChat 所需骨骼改为兼容名称

**开始前检查：**

- [ ] 已打开虚拟形象，且其骨架可见

---

### 步骤 1 — 检测当前命名风格 {#step-1--detect-the-current-naming-style}

参见[命名控件](08-vrchat.md#vrchat-naming-extras)。

1. 打开 **CATS → VRChat Tools**。

2. 在 Naming 中选择 **Detect**。

3. 名称更改后，选择 **Force Rescan** 再次检查。

BoneCraft 报告检测到的 Mixamo、VRoid 或 Unity 等命名风格及评分。

骨骼名为日文、中文、韩文、葡萄牙文、西班牙文或法文时：

1. 打开 **CATS → CATS → Translate Bone Names**。

2. 选择来源 **Language**。

3. 选择 **Translate Bone Names**。

这会将识别到的名称转换为英文。

---

### 步骤 2 — 改为 VRChat 名称 {#step-2--rename-to-vrchat-names}

若仅需更改导出名称，请保留工作名称，改在导出分区选择 **Unity-Preset**。参见[导出骨骼命名](08-vrchat.md#export-bone-naming)。

1. 按指南 5，步骤 2 映射骨骼。

2. 在 **Set Up Humanoid Bones** 中选择 **Normalize Names**。

每根已映射骨骼均获得 VRChat 预期名称。

**应看到的结果：** 骨骼名例如 `Hips`、`Spine`、`Chest` 和 `LeftUpperArm`。

---

### 步骤 3 — 手动修正（如有需要） {#step-3--manual-fixes-if-needed}

**VRChat Tools** 中的 Naming 组还提供批量工具，处理剩余骨骼：

- **Find and Replace** — 替换所有骨骼名称中的一段文字
- **Add Prefix** 和 **Add Suffix** — 在所有骨骼名称开头或结尾添加文字
- **Remove Prefix** 和 **Remove Suffix** — 移除相应前缀或后缀
- **Regex Replace** — 使用正则表达式执行同类替换

**接下来可以做什么：** 正确名称可让人形映射（指南 5）自动工作；名称不正确时，VRChat 无法判断角色应如何运动。

---

## 指南 5：将虚拟形象映射到 VRChat 身体系统 {#guide-5-map-your-avatar-to-vrchats-body-system}

> **用时：** 约 10–15 分钟
> **结果：** 将虚拟形象骨架连接到 VRChat 人形运动系统

**开始前检查：**

- [ ] 骨骼命名合理（否则参见指南 4）
- [ ] 已选择骨架
- [ ] 处于 **Object Mode**（查看视口左上角下拉菜单）

---

### 步骤 1 — 打开 Set Up Humanoid Bones {#step-1--open-set-up-humanoid-bones}

在 **CATS** 选项卡展开 **Avatar Tools** → **Set Up Humanoid Bones**。

---

### 步骤 2 — 自动映射 {#step-2--auto-map}

点击 **Auto-Map All**，BoneCraft 扫描骨架并填入身体槽位。

> 人形槽位标识身体部位，例如 Hips、Head 或 Left Hand。BoneCraft 将骨骼分配到这些槽位。重新打开文件时，已保存的人形映射会正确加载。

**应看到的界面：** 骨骼分配情况及必需槽位填充比例。共有 15 个必需槽位：Hips、Spine、Head，以及两侧上臂、前臂、手、大腿、小腿和脚。可选槽位包括 Chest、UpperChest 和 Neck。

---

### 步骤 3 — 检查映射 {#step-3--check-the-mapping}

点击 **Validate**，检查每个必需槽位是否都有骨骼，且层级是否合理。

---

### 步骤 4 — 手动填充空槽位 {#step-4--fill-empty-slots-by-hand}

空槽位显示“(click to map)”。

1. 选择空槽位。

2. 选择正确骨骼。

3. 再次选择 **Validate**。

4. 选择 **Normalize Names**，为已映射骨骼设置 VRChat 名称。

---

### 步骤 5 — 设置眼球追踪（可选） {#step-5--set-up-eye-tracking-optional}

若虚拟形象有眼部骨骼：

1. 打开 **CATS → CATS → Eye Tracking**。

2. 选择 **Auto-Detect**，按名称搜索眼部骨骼。

3. 检查 **Left Eye** 和 **Right Eye** 分配。

4. 必要时手动选择正确骨骼。

5. 设置旋转限制。

6. 选择 **Create Eye Tracking**。

设置说明见[指南 13，阶段 3](03-guides-b.md#phase-3--eye-tracking)。

**接下来可以做什么：** 人形映射让虚拟形象在 VRChat 中跟随您的动作。IK（反向运动学）使游戏中的手跟随控制器。

---

## 指南 6：添加头发物理 {#guide-6-add-hair-physics}

> **用时：** 约 15–25 分钟
> **结果：** 虚拟形象的头发及其他柔软部位在 VRChat 中自然摆动

**开始前检查：**

- [ ] 已打开虚拟形象并选择骨架
- [ ] 已完成 Set Up Humanoid Bones（指南 5）

> PhysBone 是 VRChat 中让骨骼像有重量一样弹跳和摆动的组件。BoneCraft 可为头发、耳朵、尾巴、裙装和配饰的骨骼链设置它。

---

### 步骤 1 — 打开 Add Hair Physics {#step-1--open-add-hair-physics}

在 **CATS** 选项卡展开 **Avatar Tools** → **Add Hair Physics**。它分为 Hair Chain Detection、Hair Chain Generation、PhysBone Configuration 和 Hair Physics Colliders 四部分。

---

### 步骤 2 — 查找头发骨骼链 {#step-2--find-the-hair-chains}

若头发已有骨骼，选择 **Detect Hair Physics Chains**。BoneCraft 搜索从根部首尾相接、类似头发的骨骼链；列表显示各链的根骨骼和长度。

若头发没有骨骼：

1. 选择头发网格。

2. 在 Hair Chain Generation 中选择 **Generate**。

3. 立即在 **Adjust Last Operation** 中将 **Chain Density** 设为 Low、Medium 或 High。

**Replace** 会要求确认，但当前只创建新链，不删除早先的链。

再次生成前：

1. 检查骨骼列表。

2. 若有不需要的链，将其删除。

---

### 步骤 3 — 选择 PhysBone 预设 {#step-3--choose-a-physbone-preset}

1. 选择链中的一根骨骼。

2. 在 PhysBone Configuration 下选择 **Hair**、**Skirt** 或 **Tail**。

Skirt 适用于裙装和披风，Tail 适用于尾巴和绳索。

**应看到的界面：** 链参数包括 Pull、Spring、Stiffness、Gravity 和 Max Angle。

---

### 步骤 4 — 微调（可选） {#step-4--fine-tune-optional}

面板显示链的数值，但不能编辑。较高 Stiffness 减少弯曲，较高 Gravity 将链向下拉，较小 Max Angle 限制摆动。要更改数值，请选择另一预设，或在导入虚拟形象后，于 Unity 编辑其 PhysBone 组件。

---

### 步骤 5 — 添加碰撞体（建议） {#step-5--add-colliders-recommended}

碰撞体是防止头发穿过头部和身体的不可见形状。在 Hair Physics Colliders 中选择 **Place Default Colliders**，为头部、肩部和胸部添加碰撞体。**Add Collider** 和 **Remove Collider** 每次添加或删除一个碰撞体。

**接下来可以做什么：** 转头、跳跃或跳舞时，头发能在 VRChat 中自然运动。同样步骤也适用于尾巴、耳朵、裙装和悬挂配饰。

---

## 指南 7：添加随身体运动的服装 {#guide-7-attach-clothing-that-moves-with-your-body}

> **用时：** 约 20–30 分钟
> **结果：** 将服装连接到虚拟形象骨架，使其随身体运动

**开始前检查：**

- [ ] 基础虚拟形象已有完整骨架，身体已绘制权重
- [ ] 服装位于同一文件（若附带骨架，也一并保留）
- [ ] 服装已大致贴合虚拟形象身体

---

### 步骤 1 — 打开 Attach Clothing {#step-1--open-attach-clothing}

参见[服装控件和选择顺序](08-vrchat.md#attach-clothing)。

在 **CATS** 选项卡展开 **VRChat Tools**，找到 Clothing 组，包含 Bone Matching、Collision Detection 和 Clothing Merge 三部分。

---

### 步骤 2 — 匹配骨骼 {#step-2--match-bones}

若服装有骨架：

1. 切换到对象模式。

2. 同时选择服装骨架和虚拟形象骨架。

3. 选择 **Match Bones**，比较其骨骼名称。

**应看到的界面：** 报告 HIGH、MEDIUM、LOW 和 UNMATCHED 匹配数量；面板不显示骨骼配对列表。服装无骨架时，跳过此步骤。

合并两个骨架前：

1. 选择 **Detect Collisions**，检查骨骼名称冲突。

2. 检查拟用的新名称。

3. 将服装骨架设为活动对象。

4. 选择 **Resolve Collisions**，向该骨架应用重命名。

Detect Collisions 仅检查名称，不检查网格相交。

---

### 步骤 3 — 合并服装 {#step-3--merge-the-clothing}

1. 服装有骨架时，选择服装骨架及其网格。

2. 服装无骨架时，仅选择服装网格。

3. 最后按住 Shift 点击虚拟形象骨架，使其成为活动对象。

4. 选择 **Merge Clothing**。

有服装骨架时，BoneCraft 将服装移到虚拟形象骨架上并合并骨骼；没有时，将身体权重传递到服装网格。

> 权重（权重绘制）是描述每根骨骼对每个网格点移动影响的数值。例如左袖在左臂骨骼上有权重，移动该骨骼就会带动袖子。

**应看到的结果：** 服装位于虚拟形象骨架之下；移动骨骼时，身体和服装一同移动。

---

### 步骤 4 — 检查穿插 {#step-4--check-for-clipping}

1. 为虚拟形象摆姿态。

2. 检查服装穿过身体的位置。

3. 若有穿插，调整相应位置的服装贴合或权重。

参见[绑定工具](05-rig-tools.md)中的权重工具。**Detect Collisions** 不检查物理穿插。

**接下来可以做什么：** 服装能自然随身体运动。对每件服装重复以上步骤。

下一章：[指南 8–13](03-guides-b.md)
