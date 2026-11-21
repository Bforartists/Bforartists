# 绑定构建器 {#rig-builder}

[← 目录](index.md)

有关这两种绑定类型的讲解演示，请参阅 [IK/FK 入门演练与练习文件](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/tutorials/ikfk-beginner.md)。

## 构建新绑定 {#building-a-new-rig}

Rig Builder 为角色创建新绑定。它的 **Rig Builder** 选项卡位于左侧工具架，按 **T** 可显示工具架。启用 Preferences → Tabs → Scene Properties → Show 后，Rig Builder 也会出现在 **Properties** 编辑器的 **Scene** 选项卡中。工具架较窄时会采用短标签的紧凑布局。最前面是 Auto-Rig Wizard，接着是 Quick Rig 和 Mannequin。视口的 Add → Armature 菜单也提供向导和 Quick Rig。

---

### 自动绑定向导 {#auto-rig-wizard}

**用途：** 逐步引导你在网格上放置标记，再根据这些标记构建包含权重的完整绑定。这是从零开始为角色绑定的主要方式。

[指南 1](02-guides-a.md#guide-1-get-your-first-avatar-into-vrchat) 提供逐步操作说明。

**步骤：** Select Mesh → Rig Type → Body Markers → Finger Markers → Face Markers → Review → Generate

**主要控件：**

- **Start Auto-Rig** 打开向导。顶部有 **Back** 和 **Cancel**。网格、绑定类型和标记步骤的底部有 **Next**。Review 步骤使用 **Generate Rig**，而不是 Next。最后一步使用 **Close Wizard**
- 网格列表——在此单击你的网格。下一步可选择 **Body + Face**、**Body Only** 或 **Face Only**（用于已有骨架）
- **Detect Markers**（位于 Smart Detection 中）——沿网格的四肢检测并放置所有身体标记，为每个标记提供置信度。**Accept High** 保留高置信度标记；**Reset Low** 清除低置信度标记
- **Guess Markers from Mesh** 和 **Guess Precision**（身体）、**Guess Finger Markers**（根据手部形状放置手指标记）以及 **Guess Face Markers**
- Finger Detail——要构建的手指数目，从“0 — No Fingers”到“5 — Full Human Hand”
- 每个标记所在行都有 **Place Marker**（箭头图标）、**Confirm Marker**（勾号）和 **Reset Marker**（圆形箭头）。左右成对的标记还会在第一个位置显示 **Toggle Symmetry** 图标
- **Mirror L to R** 和 **Mirror R to L**——将已确认的标记跨中心线复制到另一侧
- **Confirm All Placed**——确认当前步骤中所有已放置的标记
- **Generate Rig**——根据已确认的标记构建绑定。最后一步提供 **Build Control Rig**（见下文）和 **Close Wizard**

**Generate Rig 构建的内容：**

- 身体绑定，包含你选择的脊柱和颈部节数，以及使用 IK/FK、仅 IK 或仅 FK 的手臂与腿部（由 **Kinematics** 选项决定）
- 与所选手指数目对应的手指骨骼
- 对于 **Body + Face**：面部绑定；启用 **Generate Control Shapes** 时还会生成控制器形状
- 按所选质量生成的蒙皮权重。高密度网格通过较轻的代理网格计算权重，因此一个有 678,000 个顶点的角色大约需要一分钟，而不是无提示地失败。

**Build Control Rig：** Review 步骤还显示 **Twist Bones**、**Skirt Bones**、**Face Controls** 和 **Joint Correctives**。Generate Rig 不会应用这些选项；它们属于引擎控制绑定。该绑定包括扭转骨骼、随腿部运动的裙摆骨骼、眼睛朝向与眨眼控制器，以及关节修正形态键。完成 Generate Rig 后，最后一步提供 **Build Control Rig**。该命令在生成的骨架上按你选择的选项构建控制绑定。单击 **Close Wizard** 之前，请先单击 **Build Control Rig**；关闭向导会重置其选项。只有以这种方式构建的绑定才会显示 Control Layer 面板（位于 Rig Tools 中）。

**位置：** Rig Builder → Auto-Rig Wizard

**使用视口工具连续放置多个标记：**

1. 启动向导。
2. 进入身体、手指或面部标记步骤。
3. 在 Object Mode 中，激活视口工具栏的 Place Rig Markers。

工具标题栏会显示下一个尚未确认的标记名称，并提供轴锁定和镜像开关。

4. 单击向导所用的网格，放置并确认该标记。
5. 工具提示当前步骤完成后，在向导中按 **Next**。

对称行为遵循向导设置。每个标记的 Place 按钮仍然可用。单击其他位置不会放置标记。

---

### 快速绑定 {#quick-rig}

**用途：** 一键添加 BoneCraft 的 Basic Humanoid 或 Rigify 的一种元绑定。Basic Humanoid 有 19 根骨骼，无需 Rigify。Quick Rig 比向导更快，但对网格的适配程度较低。

**主要控件：**

- Basic Humanoid 按钮和 Rigify 元绑定预设。Rigify 未启用时，要使用其预设，请先选择 **Enable Rigify**
- 单击绑定按钮会立即添加相应绑定。Adjust Last Operation 中包含适配、自动权重、**Add IK/FK Controllers** 和 **Initial Pose**
- **T-Pose** 和 **A-Pose**——切换所选绑定的静置姿态
- 展开 Troubleshooting 可找到 **Diagnose Quick Rig (print to console)**。活动对象是非元绑定的骨架时，这里还会显示 **Inspect Active Rig Controls**
- 活动对象是 Rigify 元绑定时，Troubleshooting 显示 **Generate Control Rig (active metarig)**，而不是 Inspect Active Rig Controls。该命令会生成 Rigify 控制绑定

**BoneCraft Rigs 入门绑定目录：** 随附的全部九个入门绑定共用原生底部资产架中的 **Starter Rigs** 目录。

1. 打开资产架左侧的目录菜单。
2. 选择 **All** 资产库。
3. 启用一次 **Starter Rigs**，将其选项卡添加到现有目录选项卡旁。
4. 选择该选项卡，浏览入门绑定。

**Add → Armature → Starter Rig Catalog** 打开会检查依赖项的弹窗，用于适配并添加入门绑定。

Basic Humanoid 无需 Rigify。其他缩略图带有 **Rigify** 标签。Rigify 未激活时，在目录弹窗中选择或拖放其中一个预设，会出现 **Enable Rigify & Add Rig** 和 Cancel。接受后会启用已安装的 Rigify，并继续添加该入门绑定；取消则不添加任何内容。**Quick Rig** 也提供 **Enable Rigify**。Rigify 不可用时，目录弹窗的上下文菜单同样提供此选项。缺少依赖项或预设时会显示说明。已安装的版本没有某个预设时，弹窗不会用其他绑定代替它。

原生底部资产架会导入骨架资产。要使用下文所述的依赖项检查流程，请使用 **Add → Armature → Starter Rig Catalog**。

选中网格后添加入门绑定，工具会将绑定适配到该网格。在弹窗中单击缩略图即可添加，也可将其拖入视口。自动权重和控制器生成默认关闭，随后可在 **Adjust Last Operation** 中调整这些选项。

如果此前未选中网格：

1. 选择新添加的入门绑定。
2. 在 Quick Rig 中选择 **Mesh**。
3. 单击 **Fit Dropped Rig**。

适配会缩放骨架并调整其位置。生成控制器或权重之前：

1. 检查关节位置。
2. 按需编辑关节位置。

将绑定拖到视口外、按 Esc 或右键单击，都会取消操作，不添加任何内容。

**位置：** Rig Builder → Quick Rig；Add → Armature → Quick Rig 也可添加预制绑定

---

### 人体模型 {#mannequin}

**用途：** 围绕已有绑定构建预览网格，让你在没有成品角色网格时检查变形。如果还没有绑定，先用 Quick Rig 添加一个。使用 Mannequin 前，请选择骨架或以该骨架为父对象的网格。人体模型仅供预览；最终使用前请替换为你自己的网格。

**主要控件：**

- **Quick Mannequin**——使用固定默认值构建预览，并替换此绑定原有的人体模型
- **Add Mannequin**——使用场景设置构建预览。默认替换已有的人体模型。单击后可在 Adjust Last Operation 中找到 Replace Existing
- **Regenerate**——使用已保存的设置重建现有预览
- **Remove**——删除人体模型网格，保留骨架
- 按钮下方的 Options 包含 **Mode**、**Body Type**、密度和 **Radius Scale**。Options 内的 Advanced 包含各区域缩放和输出设置。更改场景设置后，要应用这些设置，请再次单击 **Add Mannequin**

**位置：** Rig Builder → Mannequin

---

## 人体模型练习：文字说明 {#illustrated-mannequin-workshop}

<!-- Keep each illustrated step together and preserve the manual's print scale. -->
<style>
section.chapter:has(#ch-06-rig-builder) img { max-width: 100%; max-height: 155mm; width: auto; height: auto; }
@media print {
  [id="06-rig-builder--illustrated-mannequin-workshop"] { break-before: page; break-after: avoid; }
  h4[id^="06-rig-builder--"] { break-before: page; break-after: avoid; }
  h3[id^="06-rig-builder--part-"] { break-before: page; break-after: avoid; }
  h3[id^="06-rig-builder--part-"] + h4 { break-before: avoid; }
  section.chapter:has(#ch-06-rig-builder) h4 + p { break-after: avoid; }
  section.chapter:has(#ch-06-rig-builder) p:has(> img) { break-before: avoid; break-after: avoid; }
  section.chapter:has(#ch-06-rig-builder) p:has(> img) + p { break-before: avoid; }
}
</style>

请按顺序完成以下三个部分：

1. [A——从 Simple Human 到人体模型](#part-a-simple-human-to-mannequin)。
2. [B——通过 Auto-Rig 为无绑定人体模型建立绑定](#part-b-rigless-mannequin-through-auto-rig)。
3. [C——测试权重并使用 IK/FK](#part-c-test-weights-and-use-ikfk)。

英文源手册为练习中的每个编号步骤提供真实界面截图，红色数字与图注对应。这些截图使用 **BoneCraft 9.1.2 发布版**，在 `Bforartists 5.2.0` 中拍摄。本纯文字版省略图片，保留书面步骤、图片说明和图注。Blender 的面板布局和快捷键可能不同，请以具名命令为准。

此处省略的英文源截图保留其 9.1.2 拍摄标签。当前导航路径为 **Rig Builder → Quick Rig**、**Rig Builder → Auto-Rig Wizard** 和 **BoneCraft → Skin → Weight Tools**。Starter Rigs 现在使用原生底部目录选项卡。本纯文字版不声称重新执行了 9.2.18 或 9.2.19 版本的操作验证。

本练习创建一个简单的胶囊体预览模型，用于学习绑定。头部、手部和躯干都是占位形状，并非成品角色模型。请从新文件开始。保留两个保存的检查点，以便重复转换而不丢失原始元绑定。

仓库的 `examples/mannequin/` 中包含这两个检查点：`SimpleHuman_Mannequin.blend` 是 A 部分的中立姿态结果，`Mannequin_AutoRig.blend` 是 C 部分完成后的示例，已摆好姿态并修正权重。

### A 部分：从 Simple Human 到人体模型 {#part-a-simple-human-to-mannequin}

#### A1. 启用 Rigify {#a1-enable-rigify}

1. 从新场景开始。
2. 打开 **Scene Properties → Rig Builder → Quick Rig**。
3. 如果 Rigify 预设不可用，单击 **Enable Rigify**。

本教程使用 Rigify 的 `Simple Human` 元绑定。**BoneCraft Basic Humanoid (19 bones)** 是另一个预设。

英文源图片说明（图片已省略）：A1：启用 Rigify

*1——Scene Properties。2——Enable Rigify。*

#### A2. 添加 Simple Human {#a2-add-simple-human}

单击 Quick Rig 下的 `Simple Human`。结果是可编辑的元绑定，还不是网格。在本发布版中，它有 29 根骨骼。

英文源图片说明（图片已省略）：A2：添加 Simple Human

*1——Simple Human 预设。*

#### A3. 检查元绑定 {#a3-inspect-the-metarig}

1. 将指针移入视口。
2. 按 `Numpad 1` 切换到前正交视图。
3. 检查整个骨架是否可见。
4. 使用鼠标滚轮调整视图，使骨架完整显示。

新元绑定可能初始处于 Pose Mode。

英文源图片说明（图片已省略）：A3：检查元绑定

*1——前视图。2——Simple Human 骨架。*

#### A4. 返回 Object Mode {#a4-return-to-object-mode}

更改静置姿态或生成人体模型之前：

1. 在视口模式下拉框中选择 **Object Mode**。
2. 保持 `SimpleHumanArmature` 选中。

英文源图片说明（图片已省略）：A4：返回 Object Mode

*1——模式下拉框。2——Object Mode。*

#### A5. 使用 T 形姿态 {#a5-use-a-t-pose}

在 Quick Rig 中单击 **T-Pose**，手臂会水平伸展。对于自定义身体，请先在 Edit Mode 中适配元绑定，再生成预览。本练习中请保持左右关节对称。

英文源图片说明（图片已省略）：A5：使用 T 形姿态

*1——T-Pose 命令。*

#### A6. 生成人体模型 {#a6-generate-the-mannequin}

1. 展开 **Mannequin → Options**。
2. 设置 `Mode: Universal`。
3. 设置 `Body Type: Neutral`。
4. 选择 **Medium**。
5. 设置 `Radius Scale: 1.00`。
6. 在 Advanced 下，将各区域缩放保持为 1.00。
7. 选择 `Joined (non-manifold)`。
8. 选择 **Flat colour**。
9. 启用 **Joint Smoothing**。
10. 保持 Unified Volume 关闭。
11. 单击 **Add Mannequin**。

已省略的英文源截图展示生成的胶囊体网格。Add 使用当前选项；Regenerate 复用人体模型已保存的设置。

英文源图片说明（图片已省略）：A6：生成人体模型

*1——Add Mannequin。2——Universal 与身体设置。3——Joined 输出与平滑。*

#### A7. 尝试骨骼姿态 {#a7-try-a-bone-pose}

在前视图中，角色的左侧位于你的右侧。

1. 选择骨架。
2. 切换到 **Pose Mode**。
3. 单击左前臂骨骼。
4. 使用 Rotate 工具稍微旋转该骨骼。

附着的人体模型会跟随运动。这是在元绑定上带有权重的预览，尚未包含 C 部分所用的动画控制器。

英文源图片说明（图片已省略）：A7：尝试骨骼姿态

*1——Pose Mode。2——选中的前臂及其变换操纵器。*

#### A8. 恢复并保存预览 {#a8-restore-and-save-the-preview}

1. 将指针放在视口内，选择所有姿态骨骼。
2. 按 **F3**。
3. 搜索 `Clear Pose Transforms`。
4. 选择 **All**。
5. 确认人体模型返回 T 形姿态。
6. 打开 **File → Save As**。
7. 将文件保存为 `SimpleHuman_Mannequin.blend`。

继续之前保留此检查点。

英文源图片说明（图片已省略）：A8：恢复并保存预览

*1——搜索 Clear Pose Transforms。2——All 重置选中的姿态骨骼。*

### B 部分：通过 Auto-Rig 为无绑定人体模型建立绑定 {#part-b-rigless-mannequin-through-auto-rig}

#### B1. 选择人体模型网格 {#b1-select-the-mannequin-mesh}

从 A 部分的中立姿态检查点继续。本部分会先有意移除人体模型的绑定，再运行向导。

1. 切换到 **Object Mode**。
2. 在 Outliner 中选择 `SimpleHumanArmature_Mannequin`。

为保留 A 部分，请用不同的文件名保存结果。

英文源图片说明（图片已省略）：B1：选择人体模型网格

*1——选择网格，而不是骨架。*

#### B2. 将预览烘焙为网格 {#b2-bake-the-preview-into-a-mesh}

保持人体模型为已恢复的 T 形姿态，并且只选中人体模型。

1. 按 **F3**。
2. 搜索 `Convert Mesh`。
3. 执行 `Convert Mesh`。

这会保留可见的中立姿态几何体，并移除 Armature 修改器。

英文源图片说明（图片已省略）：B2：将预览烘焙为网格

*1——Convert Mesh 命令。*

#### B3. 清除父级 {#b3-clear-the-parent}

1. 按 **Alt+P**。
2. 选择 `Clear and Keep Transformation`。

这会将网格与旧元绑定分离，同时保持其位置不变。

英文源图片说明（图片已省略）：B3：清除父级

*1——Clear and Keep Transformation。*

#### B4. 移除旧权重 {#b4-remove-the-old-weights}

此操作针对本练习中可丢弃的训练网格。这些顶点组属于旧元绑定，向导会创建新的顶点组。

1. 打开 **Object Data Properties → Vertex Groups**。
2. 在列表的下拉菜单中选择 `Delete All Groups`。

英文源图片说明（图片已省略）：B4：移除旧权重

*1——Vertex Groups 菜单。2——Delete All Groups。*

#### B5. 验证无绑定检查点 {#b5-verify-the-rigless-checkpoint}

1. 使用 Outliner 中的眼睛图标隐藏旧的 `SimpleHumanArmature`。
2. 检查人体模型是否仍然可见。
3. 检查其 Modifiers 面板中是否已没有 Armature 修改器。
4. 检查其 Vertex Groups 列表是否为空。

这就是无绑定的人体模型输入。BoneCraft 9.1.2 根据骨架生成人体模型；将此预览分离后，就得到了用于训练的无绑定网格。

英文源图片说明（图片已省略）：B5：验证无绑定检查点

*1——隐藏旧元绑定。2——空修改器堆栈。*

#### B6. 启用视口的 Rig Builder 选项卡 {#b6-enable-the-viewport-rig-builder-tab}

在已测试的 9.1.2 宿主中，从 Scene Properties 启动的 Place Marker 不接受视口单击。请使用视口选项卡放置标记。

1. 打开 **Edit → Preferences → Add-ons → BoneCraft → Tabs**。
2. 启用 **Rig Builder**。
3. 选择 **Left**。
4. 关闭 Preferences。
5. 将指针移到视口上方。
6. 如果左侧工具架被隐藏，按 **T**。

英文源图片说明（图片已省略）：B6：启用视口的 Rig Builder 选项卡

*1——启用 Rig Builder。2——放置在左侧工具架。*

#### B7. 启动 Auto-Rig {#b7-start-auto-rig}

选中无绑定的人体模型，单击 **Start Auto-Rig**。已省略的英文源截图显示的是 Scene Properties 中的等效按钮。上一步启用的视口 Rig Builder 选项卡顶部也有相同命令。

英文源图片说明（图片已省略）：B7：启动 Auto-Rig

*1——Start Auto-Rig。*

#### B8. 选择输入网格 {#b8-choose-the-input-mesh}

不要选择控件形状或其他预览对象。

1. 在 `Select Mesh` 中选择人体模型。
2. 检查所选网格的确认标记。
3. 单击 **Next**。

英文源图片说明（图片已省略）：B8：选择输入网格

*1——作为输入的人体模型。2——Next。*

#### B9. 选择同时支持两种方式的身体绑定 {#b9-choose-a-body-rig-with-both-methods}

此胶囊体人体模型没有面部拓扑，因此不需要 Body + Face。

1. 选择 **Body Only**。
2. 选择 `Kinematics: IK + FK`。
3. 保持 **Generate Control Shapes** 启用。
4. 单击 **Next**。

英文源图片说明（图片已省略）：B9：选择同时支持两种方式的身体绑定

*1——Body Only。2——IK + FK。3——Next。*

#### B10. 检测初始身体标记 {#b10-detect-initial-body-markers}

检测得到的猜测只是起点，未经检查不要直接接受。

1. 对于此对称人体模型，保持 **Mirror Symmetry** 启用。
2. 在 Body Markers 中，单击 Smart Detection 下的 **Detect Markers**。

英文源图片说明（图片已省略）：B10：检测初始身体标记

*1——Detect Markers。2——Mirror Symmetry。*

#### B11. 检查检测到的位置 {#b11-review-the-detected-positions}

这种分段预览会产生多个低置信度猜测。生成之前：

1. 对照可见网格，检查头顶、颈根、骨盆、手腕和脚踝。
2. 检查主要定位点和可选的精细定位点。
3. 按需修正定位点。

置信度标签描述最初的检测结果。行首的绿色勾号表示当前放置位置已确认。

英文源图片说明（图片已省略）：B11：检查检测到的位置

*1——检测置信度摘要。2——身体标记行。*

#### B12. 在网格上放置手腕标记 {#b12-place-a-wrist-on-the-mesh}

在前视图中，角色的左手腕位于屏幕右侧。

1. 如果标记已确认，重置该行以显示放置按钮。
2. 在视口的 **Rig Builder** 选项卡中，单击 Wrist Left 的 **Place Marker** 吸管。
3. 在视口中单击手腕表面。

英文源图片说明（图片已省略）：B12：在网格上放置手腕标记

*1——Wrist Left 放置控件。2——单击手腕表面。*

#### B13. 检查镜像手腕和脚踝 {#b13-check-the-mirrored-wrist-and-ankles}

1. 确认两行手腕标记均显示绿色勾号，且 X 坐标互为相反数。
2. 在 `Ankle Left` 的关节处重复放置，不要放在脚趾处。

对称功能会提供 Ankle Right。请对照网格检查对称结果，不要将示例坐标复制到尺寸不同的角色上。

英文源图片说明（图片已省略）：B13：检查镜像手腕和脚踝

*1——已确认的手腕标记对。2——网格上的镜像手腕标记。*

#### B14. 细调肩部和手肘 {#b14-refine-shoulders-and-elbows}

1. 滚动到 Precision Markers。
2. 重置 `Shoulder Left`。
3. 将 `Shoulder Left` 放在上臂旋转中心。
4. 重置 `Elbow Left`。
5. 将 `Elbow Left` 放在肘部间隙。
6. 确认它们的镜像对应标记。
7. 保持手腕标记位于前臂的手部一端。

这些点决定手臂链。若肩部或手肘被猜测到错误的胶囊体上，请加以修正。

英文源图片说明（图片已省略）：B14：细调肩部和手肘

*1——肩部和手肘标记行。2——肩部。3——手肘。*

#### B15. 细调髋部和膝盖 {#b15-refine-hips-and-knees}

1. 将 `Hip Left` 放在大腿顶部。
2. 将 `Knee Left` 放在大腿与小腿之间的间隙。
3. 检查对称功能提供的另一侧。
4. 保持骨盆位于两侧髋部之间的中心线上。

英文源图片说明（图片已省略）：B15：细调髋部和膝盖

*1——髋部和膝盖标记行。2——髋部表面。3——膝部间隙。*

#### B16. 从侧面检查深度和脚趾 {#b16-check-depth-and-toes-from-the-side}

1. 将指针放在视口上方，按 `Numpad 3`。
2. 除前视图外，还要在右正交视图中检查定位点。
3. 将 `Toe Left` 放在靠近脚掌前端的位置。
4. 验证其镜像对应标记。

某个标记从前方看可能正确，但相对身体仍可能过于靠前或靠后。

英文源图片说明（图片已省略）：B16：从侧面检查深度和脚趾

*1——右正交视图。2——脚趾标记行。3——脚部表面。*

#### B17. 放置脚跟标记 {#b17-place-the-heels}

1. 如果脚跟猜测不正确，重置该脚跟。
2. 在侧视图中，将 `Heel Left` 放在靠近脚后端的位置。
3. 验证 Heel Right。

这些标记是可选的。在已测试发布版中，两者均保持为零会产生距离过近警告，将它们放在脚上即可清除该警告。

英文源图片说明（图片已省略）：B17：放置脚跟标记

*1——已确认的脚跟标记对。2——脚跟位置。*

#### B18. 确认并继续 {#b18-confirm-and-continue}

1. 检查头顶、颈根、骨盆以及每一对定位点。
2. 单击 **Confirm All Placed**。
3. 单击 **Next**。

名称旁的绿色勾号显示确认状态。在 9.1.2 中，原有的 REVIEW/ADJUST 置信度标签可能仍然可见。

英文源图片说明（图片已省略）：B18：确认并继续

*1——Confirm All Placed。2——Next。*

#### B19. 对此网格跳过手指 {#b19-skip-fingers-for-this-mesh}

此人体模型有手部胶囊体，但没有手指几何体。

1. 选择 `0 — No Fingers`。
2. 单击 **Next**。

如果使用真实手部网格：

1. 选择合适的手指数目。
2. 放置手指标记。

英文源图片说明（图片已省略）：B19：对此网格跳过手指

*1——No Fingers。2——Next。*

#### B20. 检查并生成 {#b20-review-and-generate}

继续之前，必须显示 **All checks passed**。以下设置适用于这个简单的训练人体模型，并非通用导出要求。

1. 选择 **IK + FK**。
2. 启用控制器形状。
3. 设置 `Spine Segments: 3`。
4. 设置 `Neck Segments: 1`。
5. 选择 `No Fingers`。
6. 选择 **Game Ready**。
7. 禁用 Twist Bones。
8. 禁用 Skirt Bones。
9. 禁用 Preserve Volume。
10. 禁用 Joint Correctives。
11. 单击 **Generate Rig**。

英文源图片说明（图片已省略）：B20：检查并生成

*1——标记检查。2——生成设置。3——Generate Rig。*

#### B21. 构建动画控制器 {#b21-build-the-animator-controls}

生成后，单击 **Build Control Rig**。Generate Rig 提供身体绑定和权重；Build Control Rig 添加下文所用的控制层。输入网格已经存在，即使完成面板仍显示其通用的人体模型创建选项，也不要再次单击 Quick Mannequin。

英文源图片说明（图片已省略）：B21：构建动画控制器

*1——Build Control Rig。*

#### B22. 完成向导 {#b22-finish-the-wizard}

1. 等待控制绑定完成消息。
2. 单击 **Close Wizard**。
3. 保持旧的 Simple Human 元绑定隐藏。

新骨架会出现在 Outliner 中。新绑定必须能使网格变形；仅仅看见骨骼并不能证明变形正常。

英文源图片说明（图片已省略）：B22：完成向导

*1——构建按钮现已禁用。2——Close Wizard。*

### C 部分：测试权重并使用 IK/FK {#part-c-test-weights-and-use-ikfk}

在已测试发布版中，生成的骨架使用以下对象名称（在 Outliner 和权重工具中使用该名称）：

```text
BoneForge_Rig
```

`FK (Forward Kinematics)` 沿层级传递旋转。上臂旋转会影响前臂，继而影响手部，适合大幅摆动和自由运动的四肢。`IK (Inverse Kinematics)` 从末端出发。移动手腕或脚踝目标时，求解器会弯曲骨骼链以到达目标，适合固定脚部或需要接触表面的手部。

| 任务 | 使用的控制器 | 观察要点 |
|---|---|---|
| 摆动手臂 | FK 肩部和手肘控制器 | 子控制器跟随其父级 |
| 放置手部 | IK 手腕目标 | 肩部和手肘朝目标求解 |
| 固定脚部 | 对应腿部的 IK 脚踝目标 | 在目标保持就位且可达时移动身体 |
| 指定手肘或膝盖的弯曲方向 | IK 极向控制器 | 极向控制器决定弯曲方向，不是手腕或脚踝目标 |
| 更改控制方式 | 该肢体的 IK/FK 按钮 | 插入动画关键帧前，检查吸附后的姿态 |

下面的练习比较同一条手臂在两种模式下的表现。每个肢体都有独立开关。`Bake IK / Bake FK` 是动画转换工具。切换单个姿态不能代替动画烘焙或插入关键帧。其他控件请参阅[控制层](05-rig-tools.md#control-layer-ikfk)。

#### C1. 打开控制层 {#c1-open-the-control-layer}

1. 选择**生成的骨架**。
2. 选择 **Pose Mode**。
3. 打开 **BoneCraft → Review → Control Layer**。
4. 选择 **arm-L → FK**。

每条手臂和腿部都有单独的 IK/FK 开关。左右均以角色自身为准。在前视图中，arm-L 位于你的右侧。

英文源图片说明（图片已省略）：C1：打开控制层

*1——Pose Mode。2——Control Layer 和 arm-L 开关。*

#### C2. 显示动画控制器 {#c2-show-the-animator-controls}

1. 打开骨架的 **Object Data Properties → Bone Collections**。
2. 选择 `Controls` 的 Solo 星号。
3. 选择 **FK** 的 Solo 星号。
4. 如果网格遮挡了控制器，在 Viewport Display 下启用 **In Front**。
5. 稍后使用目标时，还要包含 **IK**。

这些 Solo 选择会单独显示对应的控制器形状。即使 BoneCraft Collections 面板在此宿主中无法绘制，仍可使用这个原生集合列表。

英文源图片说明（图片已省略）：C2：显示动画控制器

*1——Controls 和 FK 的 Solo 星号。2——In Front。*

#### C3. 选择前臂 FK 控制器 {#c3-select-the-forearm-fk-control}

1. 在前视图中，单击角色左手肘处的圆形控制器。
2. 检查视口中所选对象的名称是否为 **forearm.fk-L**。

前臂 FK 控制器围绕手肘旋转。如果选择肩部控制器，旋转的则是上臂及其子级。

英文源图片说明（图片已省略）：C3：选择前臂 FK 控制器

*1——选中的 forearm.fk-L 控制器。2——arm-L 当前启用 FK。*

#### C4. 旋转并检查变形 {#c4-rotate-and-inspect-the-deformation}

本前视图示例的目标是绕全局 **Y** 轴旋转约 `−45°`。使用以下任一种方式：

- 使用 Rotate 工具旋转选中的 FK 控制器。
- 对于图示的 Bforartists 键位映射，按以下步骤操作：

1. 按 **Ctrl+E**。
2. 按 **Y**。
3. 输入 **-45**。
4. 按 **Enter**。

Blender 的默认旋转快捷键是 **R**。已省略的英文源截图有意展示初始权重问题：上臂胶囊体随前臂一起倾斜。不要将此状态视为完成的绑定。

英文源图片说明（图片已省略）：C4：旋转并检查变形

*1——FK 测试中错误的上臂运动。*

#### C5. 重新计算人体模型权重 {#c5-recalculate-the-mannequin-weights}

如果上述姿态测试失败，请按以下步骤操作：

1. 切换到 **Object Mode**。
2. 选择网格。
3. 打开 **BoneCraft → Skin → Weight Tools → Automatic Bone Weight Recalculation**。
4. 将 Mesh to Reweight 设置为人体模型。
5. 将 Existing Armature 设置为**生成的骨架**。
6. 选择 **Body**。
7. 选择 `Body Method: Bone Heat`。
8. 设置 `New Weight Strength: 1.00`。
9. 设置 `Smooth Passes: 0`。
10. 设置 `Max Bones per Vertex: 0`。
11. 设置 `Minimum Weight: 0.001`。
12. 保持 **Keep Weight Backup** 启用。
13. 运行 **Automatic Bone Weight Recalculation**。

在已测试发布版中，这修复了分段预览的权重。

英文源图片说明（图片已省略）：C5：重新计算人体模型权重

*1——网格和骨架。2——Bone Heat。3——替换设置和备份。4——重新计算。*

#### C6. 验证修复后的 FK 弯曲 {#c6-verify-the-repaired-fk-bend}

1. 再次选择生成的骨架。
2. 返回 **Pose Mode**。

现在，上臂应从肩部到手肘保持水平，而前臂从手肘向上抬起。隐藏的 `WEIGHTS_BACKUP_…` 对象保留旧权重。为自己的角色制作动画之前，也要测试其他肢体。仅生成骨架并不能证明蒙皮正确。

英文源图片说明（图片已省略）：C6：验证修复后的 FK 弯曲

*1——上臂保持原位。2——前臂在手肘处弯曲。*

#### C7. 将同一条手臂切换为 IK {#c7-switch-the-same-arm-to-ik}

单击 **arm-L → IK**。切换会将目标吸附到当前姿态，因此手臂应保持抬起。如果目标被隐藏，将 **IK** 加入可见的 Solo 集合。切换会更改驱动骨骼链的控制器，但不会记录新的动画。

英文源图片说明（图片已省略）：C7：将同一条手臂切换为 IK

*1——arm-L 的 IK 开关。2——切换时保留姿态。*

#### C8. 选择手腕 IK 目标 {#c8-select-the-wrist-ik-target}

1. 单击手腕处的控制器。
2. 检查所选对象的名称是否为 **forearm.ik-L**。

虽然名称中含有 forearm，它实际上是手臂链的末端目标。移动此目标来放置手部；求解器会更改肩部和手肘角度以到达目标。

英文源图片说明（图片已省略）：C8：选择手腕 IK 目标

*1——选中的手腕目标。2——所选对象名称。*

#### C9. 移动目标并比较 {#c9-move-the-target-and-compare}

将目标保持在手臂可达范围内。目标是让手腕目标沿全局 **X** 轴略微向内移动。本示例中，`−0.15 m` 会产生明显不同的弯曲。使用以下任一种方式：

- 拖动 Move 工具的 X 轴箭头。
- 对于图示键位映射，按以下步骤操作：

1. 按 **Ctrl+W**。
2. 按 **X**。
3. 输入 `-0.15`。
4. 按 **Enter**。

Blender 的默认移动快捷键是 **G**。将整条手臂与 FK 示例比较：末端引导运动，两段手臂随之响应。

英文源图片说明（图片已省略）：C9：移动目标并比较

*1——手腕末端。2——骨骼链响应。3——X 轴移动示例。*

#### C10. 切换回来并保存示例 {#c10-switch-back-and-save-the-example}

1. 再次单击 **arm-L → FK**。

FK 控制器会吸附到当前 IK 姿态。

2. 验证网格没有跳动。
3. 打开 **File → Save As**。
4. 保存 `Mannequin_AutoRig.blend`。

已省略的英文源截图展示启用 FK 后保存的示例。要创建中立姿态的训练副本：

1. 将四个肢体都保持为 FK。
2. 选择所有可见的姿态控制器。
3. 按 **F3**。
4. 像 A 部分一样搜索 `Clear Pose Transforms`。
5. 选择 **All**。
6. 用单独的名称保存中立姿态副本。

英文源图片说明（图片已省略）：C10：切换回来并保存示例

*1——再次启用 FK。2——姿态保留。3——保存的文件名。*

**完成检查：** 原始元绑定预览仍然保存在文件中。分离的人体模型已有新的身体绑定和控制器，预览权重已修正。你已比较过 FK 旋转和 IK 目标移动。请将保存的绑定作为学习示例保留。用于正式制作时，应将预览替换为合适的角色几何体。

---

### 动画重定向 {#animation-retargeting}

将动画从一个骨架转移到另一个骨架的操作，见[绑定工具：重定向](05-rig-tools.md#retarget)。

有关片段控件，请参阅[重定向配图](05-rig-tools.md#retarget)。

---

## 骨骼合并 {#bone-merge}

**用途：** 将两个骨架合并为一个，例如身体绑定与衣物或头发绑定，同时保留所有权重。

[指南 11](03-guides-b.md#guide-11-merge-two-rigs-together) 提供逐步操作说明。

**三个阶段：**

- Scope——选择两个骨架并检查其差异
- Rename——解决名称冲突并识别新增骨骼
- Merge——先预览，再执行最终合并

**主要控件：**

- **Base**——保留的骨架。另一个骨架会合并到它，然后被隐藏
- **Analyze**——比较两个骨架。**Acknowledge Scope — Proceed to Rename** 打开阶段 2
- **Normalize Both Armatures**——按同一种命名标准重命名两个绑定的标准骨骼（Mixamo Prefixed、Mixamo Stripped 或自定义）
- **Auto-Propose Renames**——为待合并绑定自身的骨骼建议名称
- **Apply Rename**——重命名一个条目（一个撤销步骤）。**Apply Batch Pattern** 使用模式批量重命名（可用 `{bone}`、`{side}` 和 `{index}`）
- **Mark as Unique**——将某根骨骼保留为新骨骼，而不是合并它
- **Verify Rename — Proceed to Merge**——打开阶段 3
- **Run Merge Preview**——报告合并将执行的操作，不做任何修改
- **Merge Armatures**——备份两个骨架，然后合并

**位置：** BoneCraft → Setup Rigging → Bone Merge

英文源图片说明（图片已省略）：Bone Merge 从 Stage 1: Scope 开始；后续阶段会保持锁定，直到前面的检查完成。

*原生面板弹窗，BoneCraft 9.2.18。Bone Merge 从 Stage 1: Scope 开始；后续阶段会保持锁定，直到前面的检查完成。*

下一章：[机构](07-mechanisms.md)
