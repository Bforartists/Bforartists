# CATS 工具 {#cats-tools}

[← 目录](index.md)

CATS 工具位于右侧栏的 **CATS → CATS** 分区。按 **N** 显示侧栏。

启用 Preferences → Tabs → Scene Properties → Show 时，工具也显示在 **Properties → Scene** 中。CATS 视口开关和 Scene Properties 开关分别控制各自副本。

工具遵循 [CATS 流程](04-cats-pipeline.md)。在分区顶部选择要处理的骨架。

在 9.1 中，若干面板将可选设置折叠在操作按钮下方，必填输入仍在上方，包括 Fix Model 清理开关、Translate Bone Names 来源语言、嘴部形态和眼部骨骼。

带 Adjust Last Operation 的骨骼工具会立即运行，操作后在该面板调整选项。悬停按钮或选项可阅读工具提示。

---

## 修复模型 {#fix-model}

**流程阶段：** 1（建议先检查清理）

**用途：** 在所选网格上运行已启用的清理操作。干净的虚拟形象可能不需要更改。

**选项（各项均可关闭）：**

- 应用修改器
- Remove doubles — 合并同一位置的重复顶点
- Recalculate normals — 修复内外翻转的表面
- Remove loose geometry — 删除未连接到身体的面
- 删除空顶点组
- Remove zero-weight bones — 删除不移动任何顶点的骨骼
- 删除 VRChat 无法使用的约束和刚体

1. 检查清理选项。

2. 仅启用虚拟形象所需操作。

3. 保存文件检查点。

4. 选择 **Fix Model**，一次性在所选网格上运行已启用操作。

5. 继续前检查结果。

英文原稿图片描述（图片已省略）：Fix Model 选项和操作。执行流程第一阶段前，检查这些选择。

*原生面板弹出窗口，BoneCraft 9.2.18。Fix Model 选项和操作。执行流程第一阶段前，检查这些选择。*

---

## 翻译骨骼名称 {#translate-bone-names}

**用途：** 将骨架中的骨骼名称翻译成英文 VRChat 骨骼名，使用内置已知骨骼名称词典，可离线工作。

**支持语言：** 日文（日本語，最常见于 MMD 及大量社群模型）、中文、韩文（한국어）、葡萄牙文（Português）、西班牙文（Español）和法文（Français）。

**主要控件：**

1. 选择来源名称的 **Language**。

2. 选择 **Translate Bone Names**。

Language 表示模型骨骼名的语言，而非界面语言。日文 MMD 模型应选择 Japanese，与 Bforartists 界面语言无关。

英文原稿图片描述（图片已省略）：Translate Bone Names 前先选择来源命名语言。本例尚未检测到匹配名称。

*原生面板弹出窗口，BoneCraft 9.2.18。Translate Bone Names 前先选择来源命名语言。本例尚未检测到匹配名称。*

---

## 合并网格 {#join-meshes}

**用途：** 将虚拟形象网格对象合成一个网格。VRChat 使用每个虚拟形象一个网格时性能最佳。来源网格形态键不同时，CATS 用中性形态补齐缺失键，使合并网格拥有一致的形态键集合。

**主要控件：** 网格列表、刷新按钮和 **Join Meshes**。

**使用时机：** 完成服装和配饰连接及权重后。

1. 检查来源网格。

2. 合并前，选择来源网格需要的清理操作。

3. 保存文件检查点。

4. 列表需要更新时，用旁边按钮刷新。

5. 选择 **Join Meshes**。

6. 检查合并网格、形态键和权重。

英文原稿图片描述（图片已省略）：Refresh Mesh List 后，列表包含一个已勾选网格，有六个多边形。选择 Join Meshes 前检查该网格。

*原生测试构建弹出窗口，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。Refresh Mesh List 后，列表包含一个已勾选网格，有六个多边形。选择 Join Meshes 前检查该网格。*

---

## 材质图集合并器 {#material-atlas-combiner}

**流程阶段：** 2（可选）

**用途：** 将多种材质烘焙为一张纹理图（图集），减少材质数量，以改善 VRChat 性能等级。

**位置：** **CATS → CATS → Material Atlas**。面板分为 **1. Choose Target**、**2. Choose Materials and Textures** 和 **3. Bake and Review**。

### 分析与选择来源 {#analyze-and-choose-sources}

英文原稿图片描述（图片已省略）：分析前的 Material Atlas。选择目标、保留备份，再运行 Analyze Materials。

*原生面板弹出窗口，BoneCraft 9.2.18。分析前的 Material Atlas。选择目标、保留备份，再运行 Analyze Materials。*

**Target** 提供 **Active Avatar**、**Selected Meshes** 和 **Visible Scene**。Active Avatar 使用活动骨架的子网格；没有活动骨架时，使用活动网格。Visible Scene 使用可见网格；需要指定集合时，选择 Selected Meshes。

1. 保存文件副本。

2. 在 **Target** 选择所需范围。

3. 保持 **Preserve Backup Duplicate** 启用。

4. 选择 **Analyze Materials**。

5. 选择图集组。

6. 要烘焙该组，启用其复选框。

7. 在 **Materials to combine** 下勾选要包含的材质。

8. 在 **Texture images** 下勾选要包含的图像。

9. 对每个已启用组重复检查来源。

**Analyze Materials** 创建来源列表。已有组后，标签变为 **Refresh Analysis**。刷新会重建列表及选择，刷新后须再次检查。

每个列表均有 **Select All** 和 **Deselect All**，仅更改活动组对应列表中的 **Include** 复选框，不改变高亮行。材质与纹理列表相互独立，其他组保留选择；缺失纹理保持未勾选，批量选择不会启用已禁用组。

**Object → Atlas Source Selection** 也提供这些批量操作。更改来源选择前，先 Accept 或 Revert 待确认的图集预览。

启用组至少需要勾选两种材质。烘焙跳过已禁用组和单材质组。排除的材质槽及共享材质引用保持分离。排除图像仅使该图像不参与烘焙，不排除其整个材质。

透明和自发光材质初始分组。为保留绘制顺序，Alpha Blend 组初始禁用；接受可能的绘制顺序变化后，再启用这些组。

**Source Details** 初始关闭，启用后可检查网格诊断、形态键和 UV 警告、材质尺寸、纹理角色及重复来源组。材质的 **Override Size** 显示其尺寸选项；自定义尺寸使用 **Width** 和 **Height**，仅颜色材质使用 **Fallback** 尺寸。

组列表提供 **Resolution** 及添加/删除控件。**Add Group** 和 **Remove Group** 管理组，本身不执行烘焙。

英文原稿图片描述（图片已省略）：来自两个示例网格的已分析来源。检查组、材质及图像复选框，包括 UV 警告。

*BoneCraft 9.2.19 候选版。原生 Bforartists 5.2.3 测试构建，Blender 5.4 Alpha。来自两个示例网格的已分析来源。检查组、材质及图像复选框，包括 UV 警告。*

### 烘焙与检查 {#bake-and-review}

1. 检查来源列表后，选择 **Bake Checked Sources**。

2. 阅读预检摘要。

3. 修正报告的来源或设置错误。

4. 计划更改正确时，确认烘焙。

5. 检查图集、透明度、形态键和导出的 UV 通道。

6. 结果正确时，选择 **Accept — Delete Backup**。

需要原结果时，改选 **Revert — Restore Originals**。Accept 删除备份，Revert 恢复原对象、材质和可见性，并重置材质计数结果。

英文原稿图片描述（图片已省略）：由两个示例网格烘焙的一组 2048 像素 Opaque 图集。面板仍报告材质数量为 2 到 2，等级 Excellent。Accept 或 Revert 前检查 UV 警告。

*BoneCraft 9.2.19 候选版。官方 Bforartists 5.2.3，Blender 5.3 Alpha。由两个示例网格烘焙的一组 2048 像素 Opaque 图集。面板仍报告材质数量为 2 到 2，等级 Excellent。Accept 或 Revert 前检查 UV 警告。*

**Preserve Backup Duplicate** 初始启用，保留可见的图集制作前副本，供检查及 Revert 使用。关闭后，图集完成会移除原对象，且没有 Revert 备份。关闭前请另存文件。

进行下一次分析或烘焙前，先 Accept 或 Revert 当前预览。已分析对象、材质槽或渲染分类发生变化时，预检可在创建备份前取消。

再次烘焙前：

1. 选择 **Refresh Analysis**。

2. 检查重建后的选择。

**Smart Combine Materials** 是尚无分析时的初始自动快捷操作。启用 **Auto Analyze** 时，它会在烘焙前重建分析。使用 **Bake Checked Sources**，可烘焙已检查选择，而不自动重新分析。早期说明称此操作器为 **Bake Atlas**。

**烘焙无法开始时：** 图集烘焙需要 Cycles。若 Bforartists 报告 Cycles 不可用，请使用包含 Cycles 的完整构建。

### 高级选项 {#advanced-options}

**Advanced Options** 替代旧称 Override Inherited Settings，包含可选的工作流程、烘焙、UV 和输出控件。

| 设置 | 用途 |
| --- | --- |
| Auto Analyze | 为自动 Smart Combine 快捷操作重建组。 |
| Debug Report / Copy Debug Report | 启用诊断，并复制最新报告以排查问题。 |
| Albedo (Color) | 必需的基础颜色烘焙通道，保持启用。 |
| Normal Map / Emission / Roughness | 可选独立输出通道，检查支持的来源数据及烘焙结果。 |
| Metallic / Pack ORM Channels | 本构建预检阻止这些选项，保持关闭。 |
| Packing Preset / Bake Padding / UV Margin | 设置图集岛之间的填充与间距。 |
| Pixel Art No-Bleed / Preserve Island Orientation | 控制填充行为及受支持的岛朝向处理。 |
| UV Method / UV Seed / Rotation Step | 选择打包与变化；仅使用种子和旋转的方法显示相应控件。 |
| Keep Source UV Maps | 在输出网格保留来源 UV 层，初始关闭。 |
| Fallback Size | 为无图像的仅颜色材质设置图集分配尺寸。 |
| Format Output | 选择 PNG、TGA 或 EXR；EXR 保留超过 1.0 的自发光，PNG 和 TGA 将其截断。 |
| Material Output Type / Surface Output | 选择生成材质的渲染类型和表面着色器。 |
| Path Output | 设置输出纹理文件夹。 |

关闭 **Keep Source UV Maps** 时，最终图集网格将 `atlas_uv` 用作 FBX、Unity 和 VRChat 的 UV0；启用后，`atlas_uv` 可能留在 UV1。保留来源映射时，请检查引擎 UV 通道。没有预制 UV 的仅颜色网格也会获得生成的图集 UV 层。

### 数据保留与限制 {#preservation-and-limits}

合并器在烘焙时保留已连接的 Principled 色调、纹理映射和 Alpha。渲染隐藏的来源网格通过临时副本烘焙。排除的材质引用仍与其他对象共享。组装时，几何位置、形态键和父级关系受到保护。

VRM / MToon 材质保留专用回退路径。透明度分类考虑实际 Alpha 节点图及纹理 Alpha；仅有 DITHERED 渲染设置并不意味着材质透明。问题贴片可能在烘焙后呈品红色，接受结果前应检查。

文中修复经过生成测试模型的宿主检查，不认证所有生产虚拟形象或着色器图。可见文件浏览器行为、实际窗口布局及交互撤销/重做，仍受所记录测试范围限制。参见历史[修复记录](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-fixes-2026-10-23.md)和 [9.2.15 界面审查](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-ui-review-9.2.15.md)。

**来源致谢：** 此流程延续 CATS 集成脉络，向原 Cats Blender Plugin 致谢。Material Combiner 源流致谢 Grim-es/material-combiner-addon；UV 流程灵感来自 Alexander Belyakov 的 UV Toolkit 及 oRazeD/UVToolkit 归档仓库。BoneCraft 自行实现图集 UV 辅助工具，不包含 UVToolkit 源代码。

---

## 口形 {#visemes}

**流程阶段：** 3

**用途：** 根据三个基础嘴部形态创建 15 个 VRChat 口形。

**生成前：** **A Shape**、**O Shape** 和 **CH Shape** 都需要指定来源，各字段必须指向已有嘴部形态键。

**手动选择来源：**

1. 在 **A Shape** 选择来源键。

2. 在 **O Shape** 选择来源键。

3. 在 **CH Shape** 选择来源键。

**自动替代方法：** 选择 **Auto-Detect**。

**无论使用哪种来源选择方式，随后都应：**

1. 检查三个来源字段均指向已有键。

2. 必要时展开按钮下方的 Options。

3. 必要时更改是否覆盖已有口形。

4. 选择 **Generate Visemes**。

参见[指南 13，阶段 2](03-guides-b.md#phase-2--viseme-generation)。

英文原稿图片描述（图片已省略）：CATS Visemes：Generate Visemes 前，先选择 A、O、CH 来源口形，或使用 Auto-Detect。

*原生面板弹出窗口，BoneCraft 9.2.18。CATS Visemes：Generate Visemes 前，先选择 A、O、CH 来源口形，或使用 Auto-Detect。*

---

## 眼球追踪 {#eye-tracking}

**流程阶段：** 4（在 Fix Model 后运行）

Auto-Detect 搜索常见眼部骨骼名称，不使用网格几何体或骨骼位置。

1. 检查 **Left Eye** 和 **Right Eye**。

2. 分配缺失时，手动选择骨骼。

重命名骨骼后：

1. 重新运行检测。

2. 再次检查两侧分配。

眼球运动错误时，检查骨骼朝向、约束和导出的虚拟形象。

**用途：** 查找眼部骨骼，并按 VRChat 要求命名为 `LeftEye` 和 `RightEye`，创建 VRChat 眼球运动所需旋转约束。

**主要控件：**

- **Auto-Detect** — 搜索常见左右眼骨骼名称
- **Left Eye** 和 **Right Eye** — 手动选择的眼部骨骼
- **Up Limit**、**Down Limit** 和 **Side Limit** — 眼球允许转动的角度
- **Create Eye Tracking** — 重命名骨骼并创建约束

英文原稿图片描述（图片已省略）：骨骼检测前的 Eye Tracking。本例限制为向上 30 度、向下 20 度、侧向 30 度。

*原生测试构建弹出窗口，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。骨骼检测前的 Eye Tracking。本例限制为向上 30 度、向下 20 度、侧向 30 度。*

---

## 姿态与形态键 {#pose--shape-keys}

**流程阶段：** 5（可选）

### Pose to Shape Key {#pose-to-shape-key}

当前按钮捕获所选网格的**当前形态键混合**，不烘焙骨架骨骼变形。

1. 切换到对象模式。

2. 选择目标网格。

3. 将已有形态键数值设为要捕获的混合。

4. 选择 **Pose to Shape Key**。

5. 输入名称。

6. 确认操作。

7. 将原有形态键数值重置为 0。

8. 单独检查新键。

工具将新键设为 1，并让原有键继续启用。保留原数值会再次叠加其变形。

### 保存骨骼变形后的姿态 {#save-a-bone-deformed-pose}

需要保存骨架骨骼产生的变形时，使用此原生流程；修改器必须保留网格拓扑。

**Save as Shape Key** 保留 Armature 修改器，**Apply as Shape Key** 移除它。

1. 为骨架摆姿态。

2. 保存文件检查点。

3. 返回对象模式。

4. 选择已变形网格。

5. 打开 **Properties → Modifiers**。

6. 打开 Armature 修改器下拉菜单。

7. 选择 **Save as Shape Key**。

8. 重置骨骼姿态。

9. 重置原有形态键数值。

10. 将新键数值设为 1。

11. 单独检查新键。

若骨骼姿态或来源混合仍启用，会再次叠加变形。此原生操作不更新 BoneCraft 的 Pose To Shape 流程勾选标记。

英文原稿图片描述（图片已省略）：原生 Armature 修改器菜单分别提供 Save as Shape Key 和 Apply as Shape Key。

*本地预览，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。执行前的原生 Armature 修改器菜单。Save as Shape Key 保留修改器；此图未展示捕获后的姿态结果。*

### Shape Key to Basis {#shape-key-to-basis}

将活动的非 Basis 形态键设为新 Basis，并相对新 Basis 调整其他键。

1. 操作前保存文件检查点。

2. 操作后检查其余形态键。

英文原稿图片描述（图片已省略）：Pose to Shape Key 捕获当前形态键混合；Shape Key to Basis 将活动键设为新 Basis。

*原生面板弹出窗口，BoneCraft 9.2.18。Pose to Shape Key 捕获当前形态键混合；Shape Key to Basis 将活动键设为新 Basis。*

---

## 变换与 FBT {#transforms--fbt}

**流程阶段：** 6（最后）

### 应用全部变换 {#apply-all-transforms}

将位置、旋转和缩放应用到网格及骨架，重置其变换通道。早先工具仍可使用。

1. 操作前保存文件检查点。

2. 比较操作前后的虚拟形象。

导出后尺寸不同时，检查网格变换、骨架变换、导出缩放和导入缩放设置。

### 修复 FBT {#fix-fbt}

全身追踪设置的变换修正，将根骨骼移到地面高度。

### 移除 FBT {#remove-fbt}

移除 Fix FBT 修正。

英文原稿图片描述（图片已省略）：Apply All Transforms、Fix FBT 和 Remove FBT 为流程的最后操作。

*原生面板弹出窗口，BoneCraft 9.2.18。Apply All Transforms、Fix FBT 和 Remove FBT 为流程的最后操作。*

---

## 骨骼工具 {#bone-tools}

- **Create Root Bone** — 在层级底部添加根骨骼，名称由 **Root Name** 指定
- **Merge Bones** — 将短于 **Merge Threshold** 的骨骼合并到父骨骼
- **Duplicate Bones** — 复制所选骨骼

英文原稿图片描述（图片已省略）：Create Root Bone、Merge Bones 和 Duplicate Bones。操作后调整根骨骼名称及阈值。

*原生面板弹出窗口，BoneCraft 9.2.18。Create Root Bone、Merge Bones 和 Duplicate Bones。操作后调整根骨骼名称及阈值。*

---

## 骨架工具 {#armature-tools}

**用途：** 将一个骨架并入另一个，例如将服装骨架并入身体骨架。

**主要控件：**

- **Base / Root** — 保留的骨架，结果沿用其名称
- **Incoming** — 并入基础骨架的骨架，同名骨骼合并到基础骨架
- Naming Prep — 合并前匹配两套绑定的骨骼名称，适用于任意绑定，包括非 Mixamo 来源
- 自动为骨骼设置父级及随后合并网格的选项
- **Merge Incoming Into Base** — 执行合并

使用 Naming Prep：

1. 选择 Mixamo Prefixed。

2. 选择 **Normalize Merge Names**。

3. 选择 Mixamo Stripped。

4. 再次选择 **Normalize Merge Names**。

最终两套绑定具有相同名称。

需要分阶段合并和预览时，使用 Bone Merge（见 [Rig Builder](06-rig-builder.md#bone-merge)）。

英文原稿图片描述（图片已省略）：选择 Base 和 Incoming 骨架，检查 Naming Prep，再运行 Merge Incoming Into Base。

*原生面板弹出窗口，BoneCraft 9.2.18。选择 Base 和 Incoming 骨架，检查 Naming Prep，再运行 Merge Incoming Into Base。*

---

## 网格工具 {#mesh-tools}

- **Separate by Materials** — 每种材质成为一个网格
- **Separate by Loose Parts** — 每个相连块成为一个网格
- **Separate by Shape Keys** — 分离形态键移动的部分

英文原稿图片描述（图片已省略）：按材质、松散部件或形态键分离网格。

*原生面板弹出窗口，BoneCraft 9.2.18。按材质、松散部件或形态键分离网格。*

---

## 智能自动权重 {#smart-automatic-weights}

**Smart Automatic Weights** 打开带智能默认值及隐藏备份的对话框。

1. 检查目标网格和骨架。

2. 要根据现有绑定重新计算权重，选择 Body。

3. 要从已有权重的来源网格传递权重，改选 Clothing。

**Advanced Recalculation** 展开 **BoneCraft → Skin → Weight Tools** 的位置提示，不在这里打开完整控件。参见[绑定工具](05-rig-tools.md#automatic-bone-weight-recalculation)。

英文原稿图片描述（图片已省略）：Smart Automatic Weights 打开设置对话框；Advanced Recalculation 指向完整权重控件。

*原生面板弹出窗口，BoneCraft 9.2.18。Smart Automatic Weights 打开设置对话框；Advanced Recalculation 指向完整权重控件。*

---

## 流程状态与操作记录 {#pipeline-status-and-operation-ledger}

Pipeline Status 显示六个阶段的完成情况。Operation Ledger 列出每次 CATS 操作及其时间和结果：Changed、Clean 或 Failed。**Copy** 将记录复制到剪贴板，**Clear** 清空记录。参见 [CATS 流程](04-cats-pipeline.md)。

下一章：[快速修复与术语表](10-reference.md)
