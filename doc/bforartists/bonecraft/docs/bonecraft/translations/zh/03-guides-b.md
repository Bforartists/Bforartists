# 指南 8–13 {#guides-813}

[← 目录](index.md)

## 指南 8：设置口型同步 {#guide-8-set-up-lip-sync}

> **用时：** 约 10–20 分钟
> **结果：** 在 VRChat 说话时，虚拟形象的嘴部正确运动

**开始前检查：**

- [ ] 头部网格已有嘴部形态键（也称混合形状或变形目标，即说话时不同的嘴部位置）
- [ ] 大致了解这些形态键的名称（在网格 Object Data 属性的 Shape Keys 列表查看）

> Viseme 是对应一种语音的口形。`aa` 对应“ahh”，`O` 对应“ohh”等。VRChat 使用 15 个口形驱动虚拟形象口型同步。
>
> Shape key（混合形状）是网格在另一位置的保存版本；张嘴形态键就是张开嘴巴的网格状态。

---

### 步骤 1 — 打开 VRChat Viseme Mapping {#step-1--open-vrchat-viseme-mapping}

参见[口形映射与面部追踪控件](08-vrchat.md#vrchat-viseme-mapping)。

打开 **CATS → VRChat Tools → Facial → VRChat Viseme Mapping**。

---

### 步骤 2 — 自动映射口形 {#step-2--auto-map-visemes}

点击 **Auto-Map All Visemes**，BoneCraft 读取网格形态键，按名称匹配 VRChat 的 15 个口形槽位。

**应看到的界面：** 口形列表中多数槽位显示已映射的形态键。

---

### 步骤 3 — 填充缺失槽位 {#step-3--fill-in-missing-slots}

空槽位显示“(unmapped)”。

1. 点击槽位按钮，打开网格形态键搜索列表。

2. 输入文字筛选列表。

3. 选择最接近的形态键。

清空槽位时，选择“(unmapped)”。常见匹配如下：

| VRChat 口形 | 发音特征 | 查找的形态键 |
|---|---|---|
| `aa` | “ahh” | mouth_open, A, aa |
| `O` | “ohh” | mouth_o, OH, oh |
| `CH` | “ch” / “sh” | mouth_ch, CH |
| `PP` | 双唇闭合（P、B、M） | mouth_m, MM, lips_together |
| `SS` | “sss” / “zzz” | mouth_s, SS |

**缺少口形形态键时：** CATS → **Visemes** 根据 A、O、CH 三个基础口形生成全部 15 个键。网格没有嘴部形态时，先创建这三项。参见[指南 13，阶段 2](#phase-2--viseme-generation)。

---

### 步骤 4 — 检查嘴部形态 {#step-4--check-a-mouth-shape}

1. 在 **Properties → Object Data → Shape Keys**，将已映射键的数值设为 1.0。

2. 检查嘴部形态。

3. 将数值重置为 0。

---

### 步骤 5 — 面部追踪（可选） {#step-5--face-tracking-optional}

口形列表下方的 **Face Tracking (SteamVR)** 为面部追踪硬件准备表情形态。这是可选功能，多数用户不需要。

**接下来可以做什么：** 在 VRChat 说话时，虚拟形象的嘴巴会运动。表情可建立在刚映射的形态键之上。

---

## 指南 9：改善虚拟形象性能 {#guide-9-improve-your-avatars-performance}

> **用时：** 约 15–25 分钟
> **结果：** 更好的 VRChat 性能等级，以及其他玩家更快的加载速度

**开始前检查：**

- [ ] 虚拟形象已完成（有绑定、服装和口型同步）
- [ ] 确定目标等级（多数用户以 Good 或 Excellent 为目标）

> 性能等级是 VRChat 对虚拟形象资源需求的评级。其他玩家可能隐藏 Very Poor 虚拟形象；Good 和 Excellent 虚拟形象加载快，并始终显示。

---

### 步骤 1 — 检查当前等级 {#step-1--check-the-current-rank}

1. 打开 **CATS → VRChat Tools**。

2. 在 Performance 中选择 **Calculate Performance Rank**。

BoneCraft 报告整体等级，以及各指标距下一等级的差距。指标包括多边形、蒙皮网格、材质槽、骨骼、PhysBones 和接触组件。

参见[性能控件](08-vrchat.md#check-performance)。

---

### 步骤 2 — 清理 {#step-2--clean-up}

同一分区的 VRChat Optimizer 列出清理工具。**What-If Mode** 初始启用；每项修复只报告拟进行的更改，不应用它们。

1. 在 What-If Mode 中运行所需修复。

2. 检查报告。

3. 要应用更改，关闭 What-If Mode。

4. 再次运行修复。

可用修复：

1. **Remove Zero-Weight Bones** — 删除不驱动任何网格部分的骨骼
2. **Merge Same-Material Meshes** — 合并共享材质的网格
3. **Remove Unused Shape Keys** — 删除变形与 Basis 相同的空形态键，不检查其他工具的引用
4. **Remove Unused Vertex Groups** — 删除空权重组

---

### 步骤 3 — 减少多边形（如有需要） {#step-3--reduce-the-polygon-count-if-needed}

参见[性能与减面控件](08-vrchat.md#check-performance)。

多边形过多时：

1. 选择网格。

2. 在 VRChat Decimation 中设置目标比例。

3. 选择 **Preview**。

4. 检查结果。

5. 要保留结果，选择 **Apply**。

0.5 将多边形数量减半；0.8 移除 20%。减面会保护形态键。

> 从 0.8 开始，逐步降低比例，同时检查外观。小幅减少就可能改善性能，而外观变化很小。

---

### 步骤 4 — 合并材质（可选） {#step-4--merge-materials-optional}

若虚拟形象使用大量材质，可合并为一张纹理图（图集）。在 **CATS** 选项卡 → **CATS** → **Material Atlas**：

1. 保存文件副本。
2. 将 **Target** 设为要处理的网格。
3. 保持 **Preserve Backup Duplicate** 启用。
4. 点击 **Analyze Materials**。
5. 选择图集组。
6. 在该启用组中至少勾选两种材质。
7. 勾选要包含的纹理图像。
8. 必要时，使用相应列表上方的 **Select All** 或 **Deselect All**。
9. 点击 **Bake Checked Sources**。
10. 确认烘焙前，检查预检摘要。
11. 检查烘焙材质、透明度和 UV。
12. 点击 **Accept — Delete Backup** 保留结果。

结果需要更改时，改用 **Revert — Restore Originals**。Accept 会删除备份；关闭 **Preserve Backup Duplicate** 将不再提供 Revert。

批量选择只影响活动组中的对应来源列表。缺失纹理保持未勾选，另一列表及其他组不变。

**Refresh Analysis** 会重建来源列表和选择。检查选择后，使用 **Bake Checked Sources**；**Smart Combine Materials** 是初始自动快捷操作。

各项设置见 [CATS 工具：材质图集合并器](09-cats.md#material-atlas-combiner)。

---

### 步骤 5 — 再次检查等级 {#step-5--check-the-rank-again}

再次点击 **Calculate Performance Rank** 查看改善情况。

**接下来可以做什么：** 等级改善意味着更多玩家能看到您的虚拟形象。Good 或 Excellent 虚拟形象加载快、GPU 占用更低，默认会向其他玩家显示。

---

## 指南 10：保存与复用姿态 {#guide-10-save-and-reuse-poses}

> **用时：** 约 5–10 分钟
> **结果：** 建立可一键应用的个人姿态库

**开始前检查：**

- [ ] 虚拟形象已有完整骨架
- [ ] 处于 **Pose Mode**

进入姿态模式：

1. 选择骨架。

2. 按 Ctrl+Tab。

也可在视口左上角的模式下拉菜单选择 **Pose Mode**。

---

### 步骤 1 — 打开姿态库 {#step-1--open-the-pose-library}

在左侧工具架的 **BoneCraft** 选项卡中，展开 **Review** → **Pose Library**。

参见[姿态库控件](05-rig-tools.md#pose-library)。

---

### 步骤 2 — 摆好姿态 {#step-2--pose-your-avatar}

移动骨骼，摆出要保存的姿态。姿态可以结合手臂旋转、头部倾斜和其他骨骼位置。

---

### 步骤 3 — 保存姿态 {#step-3--save-the-pose}

1. 选择 **Save**。

2. 输入姿态名称，例如“Peace Sign”或“Thinking”。

**Category** 使用“Greetings”等名称将姿态分组；**Filter** 一次显示一个类别。保存的姿态包含视口缩略图。

---

### 步骤 4 — 应用已保存姿态 {#step-4--apply-a-saved-pose}

1. 选择姿态。

2. 选择 **Apply**。

- **Blend** — 以部分强度应用姿态，用于混合两种姿态
- **Mirror** — 应用左右翻转的姿态

**Rename** 和 **Delete** 管理列表。

---

### 步骤 5 — 导出与导入姿态 {#step-5--export-and-import-poses}

**Export** 将姿态库保存为 `.bfpose` 文件，可随项目保存或分享。**Import** 从 `.bfpose` 文件加载姿态。

**接下来可以做什么：** 建立跨项目复用的个人姿态库，混合姿态制作动画关键帧，或与其他 BoneCraft 用户分享。

---

## 指南 11：合并两套绑定 {#guide-11-merge-two-rigs-together}

> **用时：** 约 25–40 分钟，视复杂度而定
> **结果：** 两个骨架合为一个，并保留全部权重

**开始前检查：**

- [ ] 基础虚拟形象和第二套绑定（服装或配饰绑定）在同一文件
- [ ] 两者均已绑定并设置权重

> 绑定合并是将一个骨架并入另一个，最终得到单个组合骨架，适用于身体绑定需与头发或服装绑定合一的情况。

---

### 步骤 1 — 打开 Bone Merge {#step-1--open-bone-merge}

打开 **BoneCraft → Setup Rigging → Bone Merge**。完成前一阶段后，三个阶段依次展开。

参见[分阶段 Bone Merge 控件](06-rig-builder.md#bone-merge)。

---

### 步骤 2 — 阶段 1：范围 {#step-2--stage-1-scope}

1. 选择将保留的身体骨架 **Base**。

2. 选择要并入的服装或头发骨架。

3. 选择 **Analyze**。

最终合并时，传入骨架并入基础骨架，随后隐藏。

Analyze 比较两个骨架并列出：

- ✓ Matched — 两套骨架中都存在且对齐的骨骼
- \+ Source only — 传入绑定中在基础骨架找不到对应项的骨骼
- − Target only — 基础骨架中传入绑定没有的骨骼

阅读列表后，点击 **Acknowledge Scope — Proceed to Rename**。

---

### 步骤 3 — 阶段 2：重命名 {#step-3--stage-2-rename}

对每根仅来源骨骼选择适用分支。

若基础骨架中有对应骨骼：

1. 输入该基础骨骼名称。

2. 选择 **Apply Rename**。

没有对应骨骼时，改选 **Mark as Unique**，它将以原名加入基础骨架。

**Normalize Both Armatures** 重命名两套绑定中已识别的脊柱、手臂、腿等标准骨骼。**Auto-Propose Renames** 根据位置为其他骨骼建议名称；**Apply Batch Pattern** 用同一规则重命名多根骨骼。

处理完全部仅来源骨骼后，点击 **Verify Rename — Proceed to Merge**。

---

### 步骤 4 — 阶段 3：合并 {#step-4--stage-3-merge}

先点击 **Run Merge Preview**，只报告将进行的合并，不更改数据。

报告正确时，点击 **Merge Armatures**。BoneCraft 先备份两个骨架，再将其合并。

**应看到的结果：** 一个包含两套骨架全部骨骼的骨架，所有网格均绑定到它。

**接下来可以做什么：** 获得更便于导出和编辑的单一绑定；包含独立服装或配饰绑定的虚拟形象需要此操作。

---

## 指南 12：解决上传问题 {#guide-12-fix-upload-problems}

> **用时：** 约 5–15 分钟，视问题而定

**开始前：** 在下列列表找到问题并前往相应小节。

---

### “上传失败——无法识别骨骼” {#upload-failed--bones-not-recognized}

骨骼名称无法被 VRChat 理解。→ [指南 4：修复虚拟形象的骨骼名称](02-guides-a.md#guide-4-fix-your-avatars-bone-names)

---

### “虚拟形象保持 T 姿态 / 在 VRChat 中不随我运动” {#avatar-is-in-t-pose--not-moving-with-me-in-vrchat}

缺少人形映射或映射错误。→ [指南 5：将虚拟形象映射到 VRChat 身体系统](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system)

---

### “网格变形异常 / 皮肤拉伸不对” {#mesh-is-deforming-weirdly--skin-stretching-wrong}

需要调整骨骼权重。→ 参见[绑定工具](05-rig-tools.md)中的 Weight Transfer 和 Weight Mirror，或运行 CATS 选项卡的 **Smart Automatic Weights**。

---

### “头发穿入头部” {#hair-is-clipping-through-the-head}

缺少头发碰撞体，或碰撞体过小。→ [指南 6：添加头发物理](02-guides-a.md#guide-6-add-hair-physics)，步骤 5。

---

### “虚拟形象性能为 Very Poor，被其他玩家屏蔽” {#avatar-is-very-poor-performance-and-being-blocked-by-other-players}

→ [指南 9：改善虚拟形象性能](#guide-9-improve-your-avatars-performance)

---

### “口型同步不工作” {#lip-sync-not-working}

口形映射错误。→ [指南 8：设置口型同步](#guide-8-set-up-lip-sync)

---

### “绑定验证器显示错误” {#rig-validator-shows-errors}

1. 打开 **BoneCraft → Review → Rig Validator**。

2. 选择 **Run Validation**。

3. 按结果建议处理，或查阅[快速修复索引](10-reference.md#quick-fix-index)。

每项结果注明问题及骨骼。**Export Report** 将结果保存到文件。

---

### “VRM 导入不工作” {#vrm-import-not-working}

可能未安装 VRM 插件。→ [指南 2](02-guides-a.md#guide-2-bring-a-vroid-avatar-into-vrchat)，步骤 1。

---

### “MMD 导入不工作” {#mmd-import-not-working}

检查 **mmd_tools** 是否已安装并启用。桥接支持现代 Extensions 和旧式软件包。重试前阅读安装消息。参见[指南 3](02-guides-a.md#guide-3-bring-an-mmd-avatar-into-vrchat)，步骤 1。

---

## 指南 13：通过 CATS 准备 VRChat 虚拟形象 {#guide-13-get-your-avatar-vrchat-ready-with-cats}

> **用时：** 完整流程约 20–35 分钟
> **结果：** 获得干净、优化后且具有口型同步、眼球追踪及正确变换的虚拟形象，为 VRChat 上传做好准备

**开始前先阅读：**

CATS 工具提供建议流程。Pipeline Status 标记已完成阶段：Fix Model、Material Atlas、Visemes、Eye Tracking、Pose To Shape 和 Apply Transforms。Operation Ledger 记录每次 CATS 操作。

前一阶段未完成时，工具仍可运行，但显示“Run Fix Model first for best results”等警告。

先检查 Fix Model 清理选项；修改虚拟形象前保存文件检查点。

继续前请阅读 [CATS 流程](04-cats-pipeline.md)。

**开始前检查：**

- [ ] 虚拟形象已导入，并显示在 3D 视口中
- [ ] 右侧栏的 CATS 选项卡已打开（侧栏隐藏时按 N）
- [ ] 已选中虚拟形象（在视口或大纲视图中点击）

---

### 阶段 1 — Fix Model {#phase-1--fix-model}

Fix Model 是建议的清理阶段。根据导入的虚拟形象检查选项，并在继续前检查结果。

**Fix Model 的功能**（各项均可在选项中关闭）：

- 应用修改器
- 删除重复顶点和松散几何体（漂浮在身体外的三角面）
- 重算法线（决定网格哪一侧朝外的方向）
- 删除空顶点组和零权重骨骼
- 删除 VRChat 无法使用的约束和刚体

**步骤：**

1. 打开 **CATS → CATS → Fix Model**。

2. 选择虚拟形象网格。

3. 选择 **Fix Model**。

4. 等待完成。

5. 确认 Pipeline Status 为 Fix Model 标记 ✓。

大网格可能需要几秒。

**应看到的结果：** 虚拟形象外观不变或稍显整洁。Pipeline Status 勾选 Fix Model，Operation Ledger 列出本次操作。

**若 Fix Model 后模型消失或看起来内外翻转：**

仅凭此症状不能确定原因。

1. 检查启用的清理选项、对象可见性、几何体和法线。

2. 若需恢复，使用 Undo 或已保存的检查点恢复早先状态。

3. 重试前修正已识别的问题。

参见 [Fix Model 控件](09-cats.md#fix-model)。

---

### 阶段 2 — 口形生成 {#phase-2--viseme-generation}

前置：Fix Model ✓

Visemes 根据已有的三个基础口形生成全部 15 个 VRChat 口型同步形态。若已有完整口形形态键，可跳过此阶段，但应在 VRChat Viseme Mapping 中检查（指南 8）。

VRChat 需要 15 个嘴部形态（口形）来驱动说话时的嘴唇。多数虚拟形象只有少量基础口形，CATS 通过混合基础形态生成其余形态。

三个基础口形：

- **A Shape** — 嘴巴大张（“ahh”形态）
- **O Shape** — 圆形嘴巴（“ohh”形态）
- **CH Shape** — 嘴巴窄开并露齿（“ch” / “sh”形态）

**没有嘴部形态键时：** 先雕刻或编辑 A、O、CH 为形态键，CATS 再据此生成其他形态。参见术语表的 Shape Key。

**步骤：**

1. 打开 **CATS → CATS → Visemes**。

2. 在以下方法中选择自动或手动来源选择。

   自动选择时，使用 **Auto-Detect** 填充三个来源口形。

   手动选择时，分别为三个来源口形选择最接近的匹配。

   示例键名包括 `mouth_open`、`vrc.v_O` 和 `mouth_wide`。

3. 选择 **Generate Visemes**。

4. 确认 Pipeline Status 显示 Visemes ✓。

CATS 创建 15 个 VRChat 命名的形态键，包括 `vrc.v_aa`、`vrc.v_O` 和 `vrc.v_CH`。

**应看到的结果：** 网格 Shape Keys 列表新增 15 个形态键（Properties → Object Data → Shape Keys）。

参见 [CATS Visemes 控件](09-cats.md#visemes)。

---

### 阶段 3 — 眼球追踪 {#phase-3--eye-tracking}

前置：Fix Model ✓

Eye Tracking 为 VRChat 内置眼球追踪配置眼部骨骼，使眼睛能运动并看向其他玩家。

**功能：**

- 查找左右眼骨骼
- 按 VRChat 要求命名为 `LeftEye` 和 `RightEye`
- 添加 VRChat 转动眼球所需的旋转约束
- 将上下及侧向眼球旋转限制在自然范围

Auto-Detect 搜索常见眼部骨骼名称，不检查网格几何体或骨骼位置。

重命名骨骼后：

1. 重新运行检测。

2. 检查两侧眼部骨骼分配。

眼球运动错误时，检查骨骼朝向、约束及导出的虚拟形象。

**步骤：**

1. 打开 **CATS → CATS → Eye Tracking**。

2. 选择 **Auto-Detect** 搜索常见的左右眼骨骼名称。

3. 检查 **Left Eye** 和 **Right Eye** 字段。

4. 分配错误时，手动选择正确骨骼。

5. 必要时设置 **Up Limit**、**Down Limit** 和 **Side Limit**。

6. 选择 **Create Eye Tracking**。

7. 确认 Pipeline Status 显示 Eye Tracking ✓。

**应看到的结果：** 两根眼部骨骼已重命名，Bone Constraints 面板中有旋转约束。

> **CATS 找不到眼部骨骼时：** 骨架可能没有眼部骨骼。有些格式，尤其较早的 MMD 模型，使用形态键而非骨骼眨眼。可跳过此阶段；没有眼部骨骼时，VRChat 会回退到形态键眼部动画。

---

### 阶段 4 — Pose to Shape Key {#phase-4--pose-to-shape-key}

前置：Fix Model ✓

当前 **Pose to Shape Key** 按钮捕获选中网格当前的形态键混合，不烘焙骨架骨骼变形。骨骼变形后的姿态应使用已验证的[原生 Save as Shape Key 流程](09-cats.md#save-a-bone-deformed-pose)。

**步骤：**

1. 切换到对象模式。

2. 选择目标网格。

3. 将现有形态键数值设为要捕获的混合。

4. 保持网格为活动对象。

5. 打开 **CATS → CATS → Pose & Shape Keys**。

6. 选择 **Pose to Shape Key**。

7. 输入新形态键名称。

8. 确认操作。

9. 将原有形态键数值重置为 0。

10. 单独检查新键。

11. 确认 Pipeline Status 显示 Pose To Shape ✓。

工具已将新键设为 1。

**应看到的结果：** 新形态键重现捕获的形态键混合。若原有键仍启用，其变形会再次叠加。

> **Shape Key to Basis：** 将活动的非 Basis 形态键设为新 Basis，并让其他键相对该 Basis 调整。操作前保存检查点，操作后检查其他形态键。

参见 [Pose to Shape Key 控件](09-cats.md#pose-to-shape-key)。

---

### 阶段 5 — 应用变换 {#phase-5--apply-transforms}

前置：您需要的所有较早阶段

Apply Transforms 是建议的最终准备阶段，将位置、旋转和缩放应用到网格及骨架，通道分别重置为 0、0、1。

操作前保存检查点，并比较操作前后的虚拟形象。早期工具仍可使用。

导出尺寸错误时，检查网格和骨架变换及导出、导入缩放设置。需要恢复早先状态时，使用 Undo 或已保存的检查点。

**Transforms & FBT 中的工具：**

- **Apply All Transforms** — 同时应用网格和骨架的位置、旋转及缩放
- **Fix FBT** — 全身追踪设置的变换修正，将根骨骼移到地面高度
- **Remove FBT** — 移除该修正

Material Atlas 和 Pose To Shape 可选。若映射已有口形，Visemes 仍不打勾。

**步骤：**

1. 在 Pipeline Status 确认虚拟形象需要的阶段均已勾选。

2. 打开 **CATS → CATS → Transforms & FBT**。

3. 选择 **Apply All Transforms**。

4. 确认 Pipeline Status 显示 Apply Transforms ✓。

5. 通过 **CATS → Import / Export → Game Engine Export → Unity / VRChat** 导出（指南 1，步骤 9）。

**应看到的结果：** 在所需阶段之后，Apply Transforms 已勾选。在 VRChat Creator Companion 中检查导出结果。

参见[变换与 FBT 控件](09-cats.md#apply-all-transforms)。

---

**接下来可以做什么：** 虚拟形象已按您的选择完成清理、口形、眼球追踪和表情准备，可进行导出检查。上传前，在目标应用中验证。

下一章：[CATS 流程](04-cats-pipeline.md)
