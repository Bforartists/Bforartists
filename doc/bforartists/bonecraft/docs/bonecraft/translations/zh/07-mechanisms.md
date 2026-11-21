# Mechanisms（机械机构） {#mechanisms}

[← 目录](index.md)

## Mechanisms 的用途 {#what-mechanisms-does}

Mechanisms 根据硬表面部件构建机械绑定，支持铰链、滑动、伸缩、活塞、齿轮、跟随连接，以及由单个滑块控制的完整变形。它生成普通 Blender 骨骼和约束；您可以检查和修改全部生成内容，绑定在 Blender 中无需脚本即可工作。引擎接收 `DEF-` 骨骼；向引擎导出烘焙机械运动的功能将在以后提供（见本版本限制）。

BoneCraft 提供工具，武器部件由您准备。

含书面步骤及保留英文原稿图片描述的完整实例见[教程：使用 Mechanisms 制作 Crescent Rose](12-crescent-rose.md)。

面板和本页所用术语：

| 术语 | 含义 |
|---|---|
| *Part（部件）* | 作为一个刚性整体运动的部分：一个对象，或单个网格中的一个松散块。部件可以附属于其他部件。 |
| *Joint（关节）* | 部件允许运动的方式：Hinge（旋转）、Slide（移动）、Telescope（嵌套节段伸出）。 |
| *Link（连接）* | 自动驱动部件的机构：Piston、Gear Link、Follow。 |
| *Handle（控制柄）* | 在视口拖动的骨骼。每个关节有一个，其数值也作为面板滑块显示。 |
| *Sequence（序列）* | 由多个步骤组成、使用一个滑块播放的变形。 |
| *Form（形态）* | 保存的一组控制柄及 Sequence 数值，例如“Stowed”或“Rifle”。 |

## 功能位置 {#where-it-is}

- 3D 视口中的 **BoneCraft 选项卡 → Mechanisms**。除非在偏好设置移到右侧栏（**N**），否则 BoneCraft 位于左侧工具架（按 **T**）。Mechanisms 位于 Skin 与 Review 之间。活动对象为网格（用于开始绑定）或包含机械机构的骨架时显示工具；否则说明应选择什么。
- **Properties 编辑器 → Scene 选项卡 → Mechanisms**，紧接 Rig Builder。Preferences → Tabs → Scene Properties → Show 开启时显示。未选择可用内容时显示“Select a mesh to start, or an armature with mechanisms.”。关闭 BoneCraft 视口选项卡不会移除它；Scene Properties 开关只隐藏 Scene 副本。`mechanisms` 工具开关（**Preferences → Add-ons → BoneCraft → Tools**）则从所有位置移除此工具。Scene 选项卡的分区初始折叠，点击 **Mechanisms** 展开。
- **Object 菜单 → Mechanisms** 提供添加部件、关节、连接及测试运动的快捷入口。
- **视口工具栏 → Build Mechanism** 可在对象或姿态模式点击部件，开始引导创建关节或连接。

准备 Build Mechanism：

1. 添加部件。
2. 选择机械机构绑定或其中一个部件。
3. 在工具标题栏选择类型。

Mechanisms 包含四个子分区：**1. Parts**、**2. Joints & Links**、**3. Sequences** 和 **4. Controls**。绑定已有部件后才显示；此前仅显示 **Add Parts from Selection**。

每个按钮对应一步撤销。构建失败时，BoneCraft 恢复构建所更改的全部内容，并在面板显示原因。

英文原稿图片描述（图片已省略）：BoneCraft 选项卡中的 Mechanisms。

*历史练习截图。BoneCraft 选项卡中的 Mechanisms。*

## 部件 {#parts}

1. 在对象模式选择部件对象（或由松散块组成的一个网格）。
2. 点击 **Add Parts from Selection**。
    - 多个对象：每个对象成为一个部件，父级设为其部件骨骼，同时保持原位置。
    - 一个包含松散块的网格：每个松散块成为一个部件，获得对应骨骼的顶点组，网格增加 Armature 修改器。
    - 首次操作时，BoneCraft 自动创建绑定（骨架）。
3. 在列表选择部件进行编辑。

每个部件的设置：

- **Rides on：** 选择该部件随哪个部件运动。子部件跟随父部件；“the rig”表示附属于绑定根部。
- **Size** 设置骨骼长度，进而设置控制柄大小。
- **Edit Pivot** 在部件上放置标记；**Apply Pivot** 将部件骨骼移到标记位置，对象保持不动。
- 对象部件的旋转或缩放未应用时，显示 **Apply Transforms**。未应用变换会使轴倾斜；出现按钮时，点击 **Apply Transforms**。
- **X** 删除部件。若有关节、连接或其他部件使用它，会拒绝删除并列出使用者。
- **Merge for VRChat** 需要至少两个对象部件。仅合并只绑定到该机械机构骨架的部件，并在最后执行。操作将对象部件合成一个网格，每个原对象对应一个顶点组，并添加 Armature 修改器。合并部件成为单个网格中的松散块。合并会移除以该骨架骨骼命名的顶点组，但保留部件自身 `DEF-` 骨骼的组。

更改部件枢轴：

1. 选择 **Edit Pivot**。
2. 将标记拖到部件应绕其旋转或从其滑动的位置。
3. 点击 **Apply Pivot**。

可以重命名部件对象：对象带有部件标记，因此部件能再次找到对象。对象副本（Shift+D）不会接管该部件。若删除部件对象，部件显示“Part '&lt;name&gt;' is missing”，并提供 **Reassign** 和 **Delete**，其他机械机构继续工作。

- **Reassign** 使用当前选择的网格。非网格或已被另一对象部件使用的对象会被拒绝；同一网格的松散部件可共享该网格。
- **Delete** 删除部件（拒绝条件见下方编辑说明）。

英文原稿图片描述（图片已省略）：已添加的部件及所选部件的枢轴控件。

英文原稿图片描述（图片已省略）：已添加的部件及所选部件的枢轴控件。

*历史练习截图。已添加的部件及所选部件的枢轴控件。*

## 关节与连接：逐个实例 {#joints-and-links-one-example-each}

**Add Joint** 开始引导创建关节，**Add Link** 开始引导创建连接。两者均可从视口选项卡及属性编辑器的 Scene 选项卡使用。从 Scene 启动时，引导使用屏幕上最大的 3D 视口。

也可使用工具栏：

1. 激活视口工具栏的 Build Mechanism。
2. 在工具标题栏选择关节或连接类型。
3. 点击其第一个部件。

该点击会启动相同引导，并提供第一次选择。随后按视口提示继续选择部件和轴。Add Joint 和 Add Link 菜单仍可使用。

**Align to Selection** 支持倾斜铰链。按 **A** 时，部件网格必须处于编辑模式，且只选中一条边或一个面。引导忽略 **Tab**。使用 **Align to Selection** 前，先准备网格：

1. 在部件网格上进入编辑模式。
2. 选择一条边或一个面。
3. 保持编辑模式，启动 **Add Joint → Hinge**。
4. 点击部件。
5. 按 **A**。

没有可用选择时，引导显示消息；之后仍可按其他键。

每种引导构建的简要规则：

- 在视口点击部件，已点击部件会出现轮廓和编号。
- 步骤需要轴时，按 **X**、**Y** 或 **Z**。
- 按上述方法准备 **Align to Selection** 后，按 **A** 对齐到选择。
- 最后一步循环预览机械运动。**Enter** 保留，**Esc** 移除。
- 标题栏和状态栏为每一步显示完整句子。关闭 Show Helpers 时，改为简短标签。

Joints & Links 列表每行有四个图标按钮：**Test**（播放三角形）、**Edit**（铅笔，显示设置）、**Detach**（断链）和 **Delete**（X）。

构建后，列表中的选中项仅显示其类型实际使用的设置。

### 铰链 {#hinge}

Blade Hinge，0°…90°：

1. 对 Blade 部件使用 Add Parts from Selection。
2. 选择 **Add Joint → Hinge**。
3. 点击 Blade。
4. 按 **X**。
5. 按 **Enter**。

构建创建半圆控制柄 `CTRL-Blade`，列表中出现 *Blade Hinge*。

6. 将 **Min** 设为 0。
7. 将 **Max** 设为 90（Hinge 的单位为 °）。
8. 拖动半圆控制柄测试铰链。

控制柄在 90° 停止。**Set Min** 和 **Set Max** 将控制柄当前姿态复制到限制中。

不足整圈的限制必须位于 −180°…180° 之内。170°…190° 等限制会被拒绝并显示消息。范围达到一整圈或以上（例如 −180°…180°）时，可不受限地自由旋转。

英文原稿图片描述（图片已省略）：Hinge 限制和控制柄控件。

*历史练习截图。Hinge 限制和控制柄控件。*

### 滑动关节 {#slide}

Barrel Slide，0…0.3：

1. 选择 **Add Joint → Slide**。
2. 点击 Barrel 部件。
3. 按 **Y**。
4. 按 **Enter**。

构建创建箭头控制柄。

5. 将 **Min** 设为 0。
6. 将 **Max** 设为 0.3（场景单位）。
7. 拖动箭头测试滑动。

枪管滑动，并在 0.3 停止。

英文原稿图片描述（图片已省略）：所选部件的 Slide 行程限制。

*历史练习截图。所选部件的 Slide 行程限制。*

### 伸缩关节 {#telescope}

带三个节段的桅杆：

1. 创建底座及三个节段部件。
2. 选择 **Add Joint → Telescope**。
3. 点击底座。
4. 从底座向外，依次点击各节段。
5. 按 **Enter**。
6. 按轴键。
7. 要保留构建，按 **Enter**。

构建在底座上创建一个箭头控制柄。**Length** 是总行程；**Shares (empty = even)** 在节段间分配行程。

测试自定义份额：

1. 将 **Length** 设为 1。
2. 在 **Shares (empty = even)** 输入 `0.5, 0.25, 0.25`。
3. 拖动箭头控制柄。

三个节段分别伸出其份额。份额总和必须等于 Length，使末端移动完整长度。`0.5, abc` 等无效文字会产生消息。每个节段需要一个数值份额，且份额总和必须等于 Length。**Set Max** 根据控制柄姿态设置 Length。

英文原稿图片描述（图片已省略）：Telescope 长度与节段份额。

*历史练习截图。Telescope 长度与节段份额。*

### 活塞连接 {#piston}

举升装置：缸体位于框架，活塞杆位于手臂。

1. 为手臂添加 Hinge。
2. 将手臂设为附属于框架。
3. 选择 **Add Link → Piston**。
4. 点击框架上的缸体部件。
5. 点击手臂上的活塞杆部件。

构建创建没有控制柄的 Piston。两个部件分别指向彼此的连接点。可选的 **Stretch** 拉伸活塞杆，适用于弹簧和缆线。

6. 移动手臂控制柄，测试 Piston。

活塞会随动。若尚无东西驱动 Piston，构建仍成功，但没有预览；**Test** 会报告此情况。

英文原稿图片描述（图片已省略）：连接部件的 Piston 设置。

*历史练习截图。连接部件的 Piston 设置。*

### 齿轮连接 {#gear-link}

齿轮 20:40：

两个部件首先都需要关节。驱动部件需要 Hinge；Gear 和 Belt 的从动部件需要 Hinge，Rack 的从动部件需要 Slide。

1. 选择 **Add Link → Gear Link**。
2. 点击驱动部件。
3. 点击从动部件。

使用齿数方法：

1. 在连接设置中，将 **Source Teeth** 设为 20。
2. 将 **Target Teeth** 设为 40。

也可直接输入 **Ratio**。**Kind** 可选 Gear、Belt 或 Rack；**Reverse** 反转方向。转动来源部件测试连接。

**Kind** 为 Gear 时，目标转过来源角度的 −0.5×（Belt 为 +0.5×）。Gear 反转方向，Belt 保持方向，Rack 将旋转转换为滑动；每弧度距离等于 **Ratio** × **Pinion Radius**。

BoneCraft 的构建方式取决于来源 Hinge 的范围：

- 不足整圈：使用 Transform 约束，跟随一切驱动来源的内容，包括 Sequence。
- 一整圈或以上：使用无需 Python 的驱动器，目标随来源持续旋转，仅跟随控制柄和齿轮。当 Sequence 或 Follow 的影响会丢失时，Rig Validator 发出警告。

英文原稿图片描述（图片已省略）：输入 20:40 示例前的 Gear Link 控件。图中比例为 1.00，两项齿数均为 0。

*原生测试构建弹出窗口，BoneCraft 9.2.19 候选版。Bforartists 5.2.3，Blender 5.4 Alpha。输入 20:40 示例前的 Gear Link 控件。图中比例为 1.00，两项齿数均为 0。*

### 跟随连接 {#follow}

Blade 0–90° 带动 Cover 0–40°：

两个部件都需要 Hinge 或 Slide。来源 Hinge 的限制必须不足整圈；BoneCraft 拒绝自由旋转的来源。

1. 选择 **Add Link → Follow**。
2. 点击领动部件（Blade）。
3. 点击跟随部件（Cover）。

初始时，各映射范围覆盖对应关节的完整范围。

4. 将 **Source Range** 设为 0…90。
5. 将 **Target Range** 设为 0…40。
6. 移动 Blade 控制柄，测试 Follow。

Cover 随之运动。超出任一范围端点后，目标保持。启用 **Curve**，可在曲线编辑器中重塑映射。BoneCraft 不会覆盖您的曲线（见下方编辑说明）。

英文原稿图片描述（图片已省略）：Follow 的来源与目标范围。

*历史练习截图。Follow 的来源与目标范围。*

### 序列 {#sequence}

录制折叠武器的步骤：

1. 在 **3. Sequences** 点击 **Add Sequence**。

创建名为 `CTRL-SEQ-<name>` 的滑块控制柄。

2. 点击 **Move Slider to End**。

滑块跳至末端（1），按钮变为 Record Step 加上下一个步骤编号。

3. 为第一步摆好关节控制柄姿态。
4. 点击 Record Step 1。

每个发生移动的控制柄各成为一个带目标值的步骤，控制柄随后回零。

每次后续录制：

1. 点击 **Move Slider to End**。
2. 为下一步摆好关节控制柄姿态。
3. 点击当前编号的 Record Step 按钮。

默认每个新步骤占据滑块的下一个四分之一区间。对每个录制步骤：

1. 设置 **Target**。
2. 选择缓动：Linear、Ease In、Ease Out、Ease In Out 或 Snap。
3. 设置 **Start**。
4. 设置 **End**。

在自己的区间之外，步骤保持末端值。多个 Sequence 可以叠加。点击 **Test** 测试序列，滑块播放 0 → 1 → 0。

所选 Sequence 在录制步骤按钮及 **Test** 旁还提供 **Detach**（断链）和 **Delete**（X）。受保护而暂挂的 Sequence（例如重塑了某步骤曲线）会显示消息及 **Restore**。Restore 根据记录重新生成步骤；Sequence 不提供 Keep mine。

英文原稿图片描述（图片已省略）：Sequence 创建、已录制步骤和时序。

英文原稿图片描述（图片已省略）：Sequence 创建、已录制步骤和时序。

*历史练习截图。Sequence 创建、已录制步骤和时序。*

## 测试 {#test}

**Test**（列表及 3. Sequences 中的播放按钮）让一个机械机构遍历完整范围再返回，不写入关键帧，并在结束时恢复姿态。按 **Esc** 提前停止，也会恢复姿态。Gear Link 和 Follow 测试来源；Piston 测试驱动它的关节。BoneCraft 不检测碰撞，请观察是否有部件相撞。

英文原稿图片描述（图片已省略）：在运动范围内测试所选机械机构。

*历史练习截图。在运动范围内测试所选机械机构。*

## 形态 {#forms}

在 **4. Controls** 中：

- 每个关节和 Sequence 有一个滑块，使用控制柄本身的通道，因此拖动控制柄与使用滑块等效。
- **Save Form** 按名称记录全部控制柄和 Sequence 滑块值，可在列表重命名。
- **Go to Form** 将所有控件设为保存值。
- **Go and Key** 同样设置控件，并在当前帧插入关键帧。
- 列表旁的 **X** 删除形态。

**早期保存文件：** BoneCraft 9.2.18 读取和应用早期版本捕获的形态。打开或应用不会重新保存；**Save Form** 使用当前格式捕获当前控件值。以已有形态名保存时，会替换该形态捕获的值。

控件仍位于 **Mechanisms → 4. Controls**。兼容性修复不改变绑定控制柄、Sequence 滑块或面板位置。

英文原稿图片描述（图片已省略）：Forms 控件包含滑块、Save Form、Go to Form 和 Go and Key。

*历史练习截图。Forms 控件包含滑块、Save Form、Go to Form 和 Go and Key。*

## BoneCraft 构建的内容 {#what-bonecraft-builds}

每个部件：

| 骨骼 | 作用 | 可见 |
|---|---|---|
| `CTRL-<part>` | 控制柄，其值对应面板滑块。只有 Hinge、Slide 和 Telescope 创建此骨骼。 | 是 |
| `MCH-<part>` | 叠加控制柄及各连接的贡献，然后应用限制。 | 隐藏 |
| `DEF-<part>` | 复制 `MCH-<part>`，网格绑定于此，引擎接收此骨骼。 | 隐藏 |

骨骼位于 `Mechanism Controls`、`Mechanism MCH` 和 `Mechanism DEF` 集合。没有关节的部件只有 `MCH-` 和 `DEF-` 骨骼。Telescope 控制柄为 `CTRL-<telescope name>`，Sequence 为 `CTRL-SEQ-<name>`。Piston 为两个部件分别增加 `MCH-<part>-aim` 和 `MCH-<part>-target` 骨骼。

`MCH-<part>` 上的约束始终按相同顺序排列：先从控制柄 Copy Transforms，再叠加各连接的贡献，最后应用关节 Limit Rotation 或 Limit Location。`DEF-<part>` 有一个来自 `MCH-<part>` 的 Copy Transforms。

BoneCraft 生成的一切都带记录标记：约束名以 `BC·<id>·<role>` 开头，骨骼带有 `bc_mech_id` 和 `bc_mech_role` 属性。BoneCraft 按标记而非名称查找骨骼，因此可以任意重命名；重建仍能找到，不创建重复项。

启用 Show Helpers 时，每个关节和连接都有 **How this works** 说明，按名称列出约束、说明各自作用，并提供 **Select** 按钮（箭头图标）检查骨骼。

您自行添加的约束、驱动器和骨骼不会被修改。添加到 MCH 骨骼的自定义约束在重建后仍位于 BoneCraft 约束下方。

## 编辑与手工修改 {#editing-and-hand-edits}

- **数值修改**（限制、比例、范围、时序、缓动、控制柄外观）直接更新现有约束，不重建。
- **结构修改**（Gear Link 的 **Kind**、Follow 的 **Curve**、Piston 的 **Stretch**）替换该机构的约束，仅重建该机构。
- **手工改动。** 修改 BoneCraft 约束（例如 Limit）后，机构消息末尾出现“(changed by hand)”。BoneCraft 不会静默覆盖。请选择：
    - **Keep mine** 将您的值写入记录。无法读回的内容会被拒绝，并提示使用 Restore 或 Detach。
    - **Restore** 放弃您的改动，按记录重建。
- 机构处于暂挂状态时，所有使用其骨骼的机构也会暂挂，直到处理完毕。
- 重塑的曲线同样受保护。启用 **Curve** 后可在曲线编辑器重塑 Follow 曲线；随后更改 Target Range 等设置会替换曲线，因此 Follow 消息将以“(changed by hand)”结尾。**Keep mine** 保留您的曲线，**Restore** 重新生成。
- 暂挂的 Sequence 在 **3. Sequences** 显示消息及 **Restore**，旁边有 **Detach** 和 **Delete**。Sequence 不提供 Keep mine。
- **Detach**（断链按钮）删除记录和标记，但保留骨骼及约束，成为您的手工绑定。若记录被其他记录使用，Detach 和 Delete 都会拒绝，并列出使用者。
- **Delete**（X 按钮）删除记录及 BoneCraft 为它构建的一切。
- 连接成环会在构建任何内容前被拒绝，并注明环，例如“Blade Hinge → Cover Follow → Blade Hinge would loop.”。

Rig Validator 和 Task Board 报告：

- 连接环。
- 缺失部件。
- DEF 骨骼被机构外部驱动。
- 需要 Python 的驱动器。
- 会丢失 Sequence 或 Follow 影响的 Gear Link。

验证器名称检查接受连字符（`CTRL-`、`MCH-`、`DEF-`）。驱动器检查仅警告需要 Python 的表达式。正常的 Mechanisms 绑定没有验证错误，只显示“本版本限制”所述 `root` 骨骼警告。

## 显示帮助 {#show-helpers}

**Show Helpers** 是全 BoneCraft 共用的偏好设置：**Preferences → Add-ons → BoneCraft → Helpers**。关闭后，隐藏各处教学文字：用途/使用时机、**How this works** 说明和完整引导句子（改为简短标签）。步骤本身、列表、Test、警告及 Blender 悬停提示始终保留。

VRChat 的 **Compact Mode** 是快捷开关：Compact Mode 开启即 Show Helpers 关闭。

## 本版本限制 {#limits-of-this-version}

- Click Turn、Track 和 Linkage 机械机构将在以后提供。
- 烘焙机械运动的引擎导出将在桌面人工检查后提供；在此之前，应导出 `DEF-` 骨骼。
- BoneCraft 不检测碰撞。检查方法：
    1. 使用 Test。
    2. 观察部件。
- 自由旋转的 Gear Link 仅跟随控制柄和齿轮。
- 绑定的 `root` 骨骼不属于任何骨骼集合，因此 Rig Validator 的集合检查会发出警告，Task Board 显示“Rig validation warnings (1)”。

下一章：[VRChat 工具](08-vrchat.md)
