# 教程：用机械机构（Mechanisms）制作 Crescent Rose {#tutorial-crescent-rose-with-mechanisms}

[← 目录](index.md)

<!-- 打印布局仅作用于本教程章节；共享渲染器保持不变。 -->
<style>
@media print {
  h3[id^="12-crescent-rose--"] { break-before: page; break-after: avoid; }
  h2:has(+ h3[id^="12-crescent-rose--"]) { break-before: page; break-after: avoid; }
  h2 + h3[id^="12-crescent-rose--"] { break-before: avoid; }
  section.chapter:has(#ch-12-crescent-rose) p:has(> img) { break-after: avoid; }
  section.chapter:has(#ch-12-crescent-rose) p:has(> img) + p { break-before: avoid; }
  section.chapter:has(#ch-12-crescent-rose) table { break-inside: avoid; }
  [id="12-crescent-rose--what-you-built"] { break-before: page; break-after: avoid; }
}
</style>

## 你将制作什么 {#what-you-will-build}

Crescent Rose 将镰刀和步枪合为一体。本教程使用机械机构（Mechanisms）为模型设置绑定。一个滑块将镰刀转换为步枪，第二个滑块再将步枪折叠为紧凑形态。

除 Gear Link（齿轮连接）外，本教程会使用当前提供的每一种关节和连接，包括八个 Hinge（铰链）、三个 Slide（滑动关节）、一个 Telescope（伸缩关节）、一个 Piston（活塞连接）和一个 Follow（跟随连接），并创建两个 Sequence（序列）和三个 Form（形态）。

这些形态是为这一同人模型设计的教学姿态。机械机构不会检测碰撞，也不会生成符合物理工程要求的复制品。将绑定用于其他模型时，请检查各部件之间的间隙。

完成后的文件为 `examples/crescent-rose/CrescentRose_Mechanisms.blend`，可随时打开进行比较。

## 开始之前 {#before-you-start}

- 文件：`examples/crescent-rose/CrescentRose_parts.blend` 包含已拆分为 15 个部件对象的模型。请从此文件开始教程。`CrescentRose_Mechanisms.blend` 是已完成的绑定。
- 时间：建议用一次工作时段准备 FBX，再用另一次完成机械机构课程。这两项练习内容都较多。请在各阶段之间保存检查点。
- 术语：先阅读[机械机构](07-mechanisms.md)中的“机械机构的作用”，了解部件、关节、连接、操控柄、Sequence 和 Form 的定义。
- 语言：本版省略的英文原图展示英文 Bforartists 界面和 BoneCraft 面板。BoneCraft 面板遵循 **Language** 偏好设置，Bforartists 的其他部分遵循其界面语言。若 BoneCraft 不支持所选 Bforartists 语言，其面板仍显示英文。本纯文本版中的书面步骤仍然适用。
- 起始路线：使用原始 FBX 时，按下方 P1-P8 操作；使用准备好的文件时，可直接跳到步骤 1。两条路线使用相同的 15 个部件。
- 英文原版的历史检查：操作说明和真实界面截图曾使用 BoneCraft `9.1.2`，在 Bforartists `5.2.0` 的默认键位映射下检查。本纯文本版没有拍摄新图，也没有重新执行教程。

<strong>当前入口：</strong>在 9.2.18 中，使用 **BoneCraft → Mechanisms** 或 **Properties → Scene → Mechanisms**。如果场景分区被隐藏，请启用 **Tabs → Scene Properties → Show**。Parts、Joints & Links、Sequences 和 Controls 的名称保持不变。本版省略的早期英文原图中，这些分区周围的排列可能与当前版本不同。

本纯文本版保留英文原版对 9.1.2 截图和教程重放的原有限制，并省略图片。9.2.18 的源代码审查不能代替新的教程重放。早期保存的 Form 仍可读取和使用，打开或应用它们不会重新保存其数值。参见[形态](07-mechanisms.md#forms)。

英文原图用红色编号标明需要点击、输入或检查的位置。本纯文本版省略这些图片，保留书面说明和编号操作图注。请按顺序执行书面步骤和编号操作说明（先 1，再 2，然后 3）。这些编号指向英文原图中的标注，每张原图都重新编号。在原始证据中，方框标出需要检查的结果，圆圈标出需要操作的部件或按钮。

## 准备原始 FBX（P1-P8） {#prepare-the-original-fbx-p1-p8}

如果使用 `CrescentRose_parts.blend`，请跳过本节。

1. 在新文件中操作。

2. 将源 FBX 和对应的 `CrescentRoseTextures` 文件夹保存在一起。

这些步骤曾在 Bforartists 5.2.0 的默认键位映射下重放。请使用可见的模式菜单；在此键位映射中，Tab 可能切换叠加显示，而不是进入编辑模式。

### P1 - 导入 FBX {#p1---import-the-fbx}

此操作流程使用 Legacy 导入器。

1. 从空场景开始。

2. 选择 **File > Import > FBX (.fbx) (Legacy)**。

3. 选择 `CrescentRose.fbx`。

4. 将导入 Scale 保持为 `1.00`。

5. 选择 Import FBX。

6. 按 Numpad 3 切换到右视图。

7. 按 Home 框显导入的对象。

大纲视图中会出现一个根对象和三个材质网格：`Black01`、`Blades01` 和 `Red01`。

英文原图说明（图片已省略）：P1：Legacy FBX 导入选项，Scale 为 1.00

*1：选择 CrescentRose.fbx。2：将 Scale 保持为 1.00。3：点击 Import FBX；使用 Legacy 导入器。*

### P2 - 保持位置并设置尺寸 {#p2---preserve-placement-and-set-the-size}

导入的武器高约 `0.32 m`，准备好的快捷起始文件已完成缩放。仅对导入的网格执行一次以下尺寸调整。

1. 切换到对象模式（Object Mode）。

2. 选择全部三个网格。

3. 选择 **Object > Parent > Clear and Keep Transformation**。

4. 从工作场景中移除不再使用的根对象。

5. 保持三个网格全部选中，选择 **Object > Apply > Rotation & Scale**。

6. 在此 Bforartists 键位映射中，按 Ctrl+R 启动缩放。

7. 输入 `6.25`，一起缩放三个网格。

8. 确认缩放。

9. 再次选择 **Object > Apply > Rotation & Scale**。

整把武器现在高约 `1.997 m`。

英文原图说明（图片已省略）：P2：清除父级关系，同时保持位置

*1：按 F3，搜索 Clear Parent Keep Transform。2：选择 Clear and Keep Transformation。移除根对象前，对全部三个网格重复此操作。*

英文原图说明（图片已省略）：P2：导入武器已应用旋转与缩放

*1：将三个网格一起缩放 6.25 倍后，应用 Rotation & Scale；Rotation 必须为 0。2：所有轴上的 Scale 必须为 1。*

单个对象的 Dimensions 字段只测量该材质网格的尺寸。测量武器时，请检查整体从底部到顶部的范围。拆分前，三个对象的旋转都必须为零，缩放都必须为 1。

### P3 - 连接材质 {#p3---connect-the-materials}

1. 切换到 Shading 工作区。

2. 选择 Material Preview。

三个材质中的每一个都使用 `CrescentRoseTextures` 中的四张图像：

| 图像 | 色彩空间 |
|---|---|
| `BaseColor` | **sRGB** |
| `Metallic` | `Non-Color` |
| `Roughness` | `Non-Color` |
| `Normal` | `Non-Color` |

对每个材质，一次处理一张图像：

1. 从 `CrescentRoseTextures` 加载对应图像。

2. 按表格设置该图像的色彩空间。

3. 对 BaseColor、Metallic 或 Roughness 图像，将 Image Texture 的 Color 连接到 Principled BSDF 的对应输入。

对每张 Normal 图像，按以下独立分支连接：

1. 插入一个 **Normal Map** 节点。

2. 将 Normal Map 节点保持为 `Tangent Space`。

3. 将 Normal 图像的 Color 连接到 Normal Map 的 Color。

4. 将 Normal Map 的 Normal 连接到 Principled BSDF 的 Normal。

保留现有 UV。

英文原图说明（图片已省略）：P3：黑色材质已连接四张纹理贴图和 Tangent Space Normal Map

*1：将 BaseColor 的 Color 连接到 BSDF 的 Base Color。2：BaseColor 保持 sRGB。3：所有数据贴图设为 Non-Color。4：按 Normal 图像 > Normal Map > BSDF Normal 连接，并使用 Tangent Space。*

英文原图说明（图片已省略）：P3：Material Preview 中的全部三个材质

*1：检查刀刃材质。2：在 Material Preview 中检查红色和黑色主体材质；不应出现表示缺失纹理的粉红色。*

黑色、刀刃和红色材质都使用此流程。选择每张图像后，请检查其色彩空间。色彩空间设置属于图像。武器应呈现红色、黑色和金属外观，不应有表示缺失纹理的粉红色。

### P4 - 按松散块拆分 {#p4---separate-loose-pieces}

1. 选择全部三个材质网格。

2. 从视口模式菜单选择 **Edit Mode**。

3. 选择全部几何体。

4. 选择 **Mesh > Separate > By Loose Parts**。

5. 返回对象模式。

现在共有 **37** 个网格对象。自动生成的数字后缀可能不同，请根据位置和形状识别对象。

英文原图说明（图片已省略）：P4：进入 Edit Mode，选择 By Loose Parts

*1：切换到 Edit Mode 并选择全部几何体。2：按 F3，搜索 Separate Loose，选择 By Loose Parts。*

英文原图说明（图片已省略）：P4：拆分后的 37 个松散块

*1：检查拆分后的对象总数是否为 37。2：在大纲视图中按形状和位置选择部件；后缀可能不同。*

### P5 - 合并为 15 个运动组 {#p5---join-the-15-moving-groups}

下表列出所有源网格孤岛。材质名称描述外观，并非最终对象名称。

| 最终对象 | 需要合并的部件 | 合并后的网格顶点数 |
|---|---|---:|
| `BladeTip` | 黑色刀尖关节旋钮和金属刀尖刺 | 252 |
| `Blade2` | 两块金属第二刀段板和两个红色外罩 | 1000 |
| `Blade1` | 最靠近头部的两块金属第一刀段板 | 512 |
| `HeadMount` | 黑色后块、顶盖和核心；两块红色内板和两片薄顶盖 | 1395 |
| `PlateL` | X 负方向上的一块红色头部外侧板 | 676 |
| `PlateR` | X 正方向上的一块红色头部外侧板 | 676 |
| `RearSpike` | 两块金属尖刺刀片、两个红色枢轴盖和两块红色安装板 | 1194 |
| `Receiver` | 黑色主体及小旋钮、枪栓上方的金属环、长红色外壳 | 2609 |
| `Grip` | 机匣下方的红色握把块 | 194 |
| `Magazine` | 主体下方的黑色管 | 96 |
| `Bolt` | 红色枪栓圆柱及其两个旋钮部件 | 362 |
| `Pole` | 金属下杆及红色套环 | 148 |
| `ButtSpike` | 底部金属尖刺 | 110 |
| `StrutBase` | 机匣与头部之间的细红杆 | 34 |
| `StrutRod` | 包围细红杆的黑色带缺口套筒 | 108 |

不要将外侧板合并到 Blade1。不要将两个支撑杆部件合并。支撑杆已有两个独立部件，无需剖分。

从刀尖向内依次操作，再处理机匣和长杆。对每个运动组：

1. 选择需要一起运动的部件。

2. 对位于相对两侧的成对部件，旋转视图以选中两者。

3. 合并前检查选择。

4. 选择 **Object > Join**（Ctrl+J）。

5. 在大纲视图中重命名合并后的对象。

总计必须有 **15 个网格和 9,366 个顶点**。步骤 2 会再次列出最终部件名称及后续父级关系。

英文原图说明（图片已省略）：P5：大纲视图中已命名的全部 15 个运动组

*1：在大纲视图中重命名每个合并组，与表中 15 个名称一致。*

英文原图说明（图片已省略）：P5：合并前选中的两块 Blade1 源板

*1：选择相对两侧的两块金属 Blade1 板。2：确认两者均已选中，再使用 Join，并将结果重命名为 Blade1。*

英文原图说明（图片已省略）：P5：Object 菜单中的 Join 命令

*1：只选择某一个组的部件后打开 Object。2：选择 Join（Ctrl+J）。此菜单局部图用于辨认命令；实际操作应使用上方所述的双部件选择。*

### P6 - 将原点居中 {#p6---centre-the-origins}

1. 切换到对象模式。

2. 选择全部 15 个网格。

3. 选择 **Object > Set Origin > Origin to Geometry**。

4. 将该操作的 Center 选项设为 `Bounds Center`。

5. 检查旋转是否为零、缩放是否为 1。

对象仍没有父级，场景中也没有骨架。这些原点用于准备工作。步骤 6 会将机械机构枢轴移到实际关节处。

英文原图说明（图片已省略）：P6：Object > Set Origin > Origin to Geometry

*1：打开 Object。2：悬停 Set Origin。3：选择 Origin to Geometry；在操作选项中设置 Bounds Center。*

英文原图说明（图片已省略）：P6：已居中的 Blade1 原点和已应用的变换

*1：橙色原点现已位于网格中心。2：确认 Rotation 为 0。3：确认 Scale 为 1。机械机构枢轴会在后续移动。*

### P7 - 调整纹理尺寸并打包 {#p7---resize-and-pack-the-textures}

共有 **12 张使用中的贴图**，每个材质四张。不要覆盖源 JPEG。对每张使用中的贴图：

1. 在 Image Editor 中选择贴图。

2. 选择 **Image > Resize**。

3. 将宽度设为 **1024**。

4. 将高度设为 **1024**。

5. 确认尺寸调整。

6. 选择 **Image > Pack**。

打包会将调整后的像素保存在 blend 文件内。处理全部贴图后，请检查 Material Preview。

英文原图说明（图片已省略）：P7：用 Image 菜单打包已调整为 1024 × 1024 的纹理

*1：选择 Image > Resize，宽度和高度均输入 1024。2：检查调整后的尺寸为 1024 x 1024。3：选择 Pack。对全部 12 张使用中的贴图重复此操作。*

### P8 - 保存并重新打开准备好的文件 {#p8---save-and-reopen-the-prepared-file}

1. 将工作副本另存为 `CrescentRose_parts.blend`。

2. 重新打开该文件。

3. 检查 15 个已命名网格、它们的变换，以及红色和黑色材质。

4. 再次选择右视图。

5. 按 Home。

6. 继续步骤 1。

即使没有原始纹理目录，全部 12 张贴图仍应可用。

英文原图说明（图片已省略）：P8：重新打开准备好的文件，带纹理的武器保持完整

*1：打开 File，使用 Save As，然后用 Open 重新加载工作副本。2：确认 15 个已命名网格仍在。3：检查材质；标题栏应标识重新打开的文件。*

## A. 打开文件 {#a-open-the-file}

### 步骤 1 — 打开部件文件 {#step-1--open-the-parts-file}

1. 打开 `examples/crescent-rose/CrescentRose_parts.blend`。

2. 在视口中选择 Material Preview 着色。

3. 按 Numpad 3 切换到右视图。

4. 按 Home 框显武器。

刀刃朝左，底部尖刺朝下。

英文原图说明（图片已省略）：步骤 1：右视图中的部件文件

*1：点击 Material Preview。2：按 Numpad 3，直到视图显示 Right Orthographic；按 Home 框显武器。*

<strong>你应看到的结果：</strong>一把高约 2 m 的红黑色镰刀，没有选中任何对象。

### 步骤 2 — 认识各部件 {#step-2--meet-the-parts}

大纲视图列出 15 个对象，每一个都是作为整体运动的部件：

| 对象 | 部件说明 | Rides on（附着于） |
|---|---|---|
| `Receiver` | 带有瞄准镜、扳机和准星的步枪机匣 | 绑定 |
| `Grip` | 机匣下方的握把 | `Receiver` |
| `Magazine` | 圆柱形弹匣 | `Receiver` |
| `Bolt` | 枪栓 | `Receiver` |
| `Pole` | 下杆及套环 | `Receiver` |
| `ButtSpike` | 底部尖刺 | `Pole` |
| `HeadMount` | 悬挂刀刃的头部块 | `Receiver` |
| `Blade1` | 最靠近头部的第一刀段 | `HeadMount` |
| `Blade2` | 第二刀段 | `Blade1` |
| `BladeTip` | 刀尖 | `Blade2` |
| `RearSpike` | 头部后方的尖刺 | `HeadMount` |
| `PlateL`、`PlateR` | 头部的外侧板 | `HeadMount` |
| `StrutBase` | 机匣与头部之间的细杆 | `Receiver` |
| `StrutRod` | 包围细杆的带缺口套筒 | `HeadMount` |

英文原图说明（图片已省略）：步骤 2：大纲视图中的 15 个部件对象

*1：辨认三个刀段。2：按表格核对主体、头部和长杆的名称。3：保持 StrutBase 和 StrutRod 为独立对象。*

使用原始 FBX 时，按上方 P1-P8 操作。这些界面操作生成了随附的准备文件。仓库中的准备脚本提供参考分组表。

### 步骤 3 — 找到机械机构 {#step-3--find-mechanisms}

如果左侧 Tool Shelf 被隐藏：

1. 将指针移到视口上方，按 T。

2. 从 Region Toggle 菜单选择 Tools。

然后：

1. 打开左侧 Tool Shelf 上的 BoneCraft 选项卡。

2. 展开 **Mechanisms**。

3. 拖动工具架的右边缘，使面板文字清晰可读。

在 BoneCraft 偏好设置中将 Scene Properties 设为 Show 后，**Properties > Scene** 中也会显示相同分区。本版省略的英文原图使用 Tool Shelf。

当活动对象为网格且尚无绑定时，顶部会显示 **Add Parts from Selection**。使用前，请按步骤 4 选择所有部件。添加部件后，各编号子分区才可使用。

英文原图说明（图片已省略）：步骤 3：BoneCraft 选项卡中的 Mechanisms 分区

*1：点击 BoneCraft 选项卡。2：展开 Mechanisms。3：找到 Add Parts from Selection；使用前先选择网格。*

## B. 部件 {#b-parts}

### 步骤 4 — 从选择中添加部件 {#step-4--add-parts-from-selection}

1. 将指针移到视口上方，按 A 选择全部 15 个对象。

2. 选择 **Add Parts from Selection**。

英文原图说明（图片已省略）：步骤 4：全部部件已选中，使用 Add Parts from Selection

*1：将指针悬停在视口上，按 A 选择 15 个网格。2：点击 Add Parts from Selection。*

<strong>你应看到的结果：</strong>大纲视图中出现名为“Mechanism Rig”的新骨架，各部件位于其下。网格对象仍保持选中。**1. Parts** 列出 15 个部件。BoneCraft 选项卡现在以该绑定可折叠的 Overview 分区开头。

### 步骤 5 — 附着关系（Rides on） {#step-5--rides-on}

部件会附着在与其相连的部件上，并随之运动。

1. 在 **1. Parts** 中选择 `Blade1`。

2. 打开列表下方的“Rides on”菜单。

3. 选择 `HeadMount`。

4. 按步骤 2 的表格，对每个部件重复操作。

`Receiver` 保持为“the rig”。

英文原图说明（图片已省略）：步骤 5：Blade1 附着于 HeadMount

*1：在 Parts 列表中选择 Blade1。2：打开 Rides on，选择 HeadMount。按父级关系表重复操作。*

### 步骤 6 — 枢轴 {#step-6--pivots}

铰链围绕所属部件的枢轴旋转。刀段、头部和握把必须绕各自的关节转动，而不是绕部件中心转动。请在正交侧视图中操作，以保持枢轴的侧向位置。

1. 在列表中选择 `Blade1`。

2. 选择 **Edit Pivot**。

3. 选择标记。

4. 在 Bforartists 中按 Ctrl+W 启动 Move。

5. 点击刀段与头部相接的位置。

6. 选择 **Apply Pivot**。

7. 对下表中的部件重复枢轴设置流程。

| 部件 | 枢轴位置 |
|---|---|
| `Blade2` | 与 `Blade1` 相接的位置 |
| `BladeTip` | 与 `Blade2` 相接的位置 |
| `HeadMount` | 最低点，即支撑杆与其相接的位置 |
| `Grip` | 顶部边缘 |
| `RearSpike` | 与头部相接的位置 |
| `PlateL` 和 `PlateR` | 圆形螺栓中心，即 Blade1 与头部相接的位置 |
| `StrutBase` | 底端 |
| `StrutRod` | 顶端 |

本版省略的英文原图中，标记位置仅供参考。几毫米的偏差不会造成可见差异。

英文原图说明（图片已省略）：步骤 6：选择部件并点击 Edit Pivot

*1：在 Parts 中选择 Blade1。2：点击 Edit Pivot，然后按下一段说明移动并应用标记。*

英文原图说明（图片已省略）：步骤 6：Blade1 的枢轴标记位于关节处，使用 Apply Pivot

*1：按 Ctrl+W 将枢轴标记移到刀刃关节处。2：点击 Apply Pivot 保留该位置。*

## C. 头部 {#c-the-head}

### 步骤 7 — Add Joint → Hinge {#step-7--add-joint--hinge}

如需隐藏遮挡物，请在启动引导前隐藏。

打开 **Add Joint → Hinge**。引导式创建流程的标题栏和状态栏会说明每一步。

英文原图说明（图片已省略）：步骤 7：Add Joint 菜单中的 Hinge

*1：打开 Add Joint。2：点击 Hinge。引导式创建流程现在等待选择部件。*

### 步骤 8 — 点击头部 {#step-8--click-the-head}

标题栏提示“点击会转动的部件”。在右视图中，外侧板会遮挡头部。请点击侧板后方的头部后块，即英文原图圆圈标示的位置。

如果标题栏显示 `PlateR`：

1. 按 Esc。

2. 重新启动 **Add Joint > Hinge**。

3. 点击头部更靠后的位置。

引导处于活动状态时，会占用常用键盘快捷键。

英文原图说明（图片已省略）：步骤 8：点击头部的后块

*1：点击红色外侧板后方 HeadMount 的黑色后块。确认引导显示 HeadMount。*

### 步骤 9 — 按 X，再按 Enter {#step-9--press-x-then-enter}

标题栏会要求指定轴。

1. 按 X。

2. 检查循环预览。

3. 按 Enter 保留该铰链。

头部会绕侧向轴转动。

英文原图说明（图片已省略）：步骤 9：指定轴的步骤

*1：按轴提示先按 X，再按 Enter。2：确认前，观察头部绕枢轴转动。*

<strong>你应看到的结果：</strong> **2. Joints & Links** 中出现 `HeadMount Hinge`，对应滑块位于 **4. Controls**。请在对象模式中使用这些滑块。

使用视口中的骨骼操控柄：

1. 选择骨架。

2. 切换到姿态模式（Pose Mode）。

### 步骤 10 — 限制 {#step-10--limits}

1. 在列表中选择 `HeadMount Hinge`。

2. 将 **Min** 设为 0。

3. 将 **Max** 设为 120。

正值会使头部向下、向后转动。请保留 120 度的行程限制。Rifle 序列会将头部的 90 度目标与刀刃铰链配合使用。

英文原图说明（图片已省略）：步骤 10：Min 为 0，Max 为 120

*1：选择 HeadMount Hinge。2：将 Min 设为 0。3：将 Max 设为 120；双击数值、输入，再按 Enter。*

### 步骤 11 — 测试 {#step-11--test}

点击该行的播放按钮。头部会转到 120° 后返回，并恢复原有姿态。

英文原图说明（图片已省略）：步骤 11：铰链所在行的 Test

*1：点击 HeadMount Hinge 行上的小播放三角形。观察它转动并返回。*

## D. 刀刃链 {#d-the-blade-chain}

### 步骤 12 — 再添加三个铰链 {#step-12--three-more-hinges}

对 `Blade1`、`Blade2` 和 `BladeTip`，分别重复步骤 7 至 10：

1. 打开 **Add Joint → Hinge**。

2. 点击刀段。

3. 按 X。

4. 按 Enter。

5. 将 **Max** 设为 120。

每一段都附着于前一段，三个铰链构成一条链。

英文原图说明（图片已省略）：步骤 12：列表中的三个刀段铰链及独立的头部铰链

*1：分别创建并选择 Blade1、Blade2 和 BladeTip 的铰链。2：将各自的 Max 设为 120，轴均使用 X。*

### 步骤 13 — 测试关节链 {#step-13--try-the-chain}

1. 折叠 **2. Joints & Links**，腾出空间。

2. 展开 **4. Controls**。

3. 在对象模式中，将 `Blade1 Hinge`、`Blade2 Hinge` 和 `BladeTip Hinge` 分别设为 60 度。

输入每个数值时：

1. 双击数值字段。

2. 按 Ctrl+A。

3. 输入数值。

4. 按 Enter。

后续刀段会随前面的刀段一起移动，使关节链卷曲。继续前，将三个数值全部重置为 0。

英文原图说明（图片已省略）：步骤 13：Controls 中的三个刀刃铰链均为 60 度

*1：在三个刀刃滑块中分别输入 60。2：确认整条链一起卷曲。将三个滑块全部恢复为 0。*

## E. 侧板与支撑杆 {#e-plates-and-strut}

### 步骤 14 — 侧板上的铰链 {#step-14--hinges-on-the-plates}

在右视图中，`PlateL` 隐藏在头部后方。

1. 按相同流程，为 `PlateR` 添加 Hinge。

2. 将其 **Max** 设为 30。

3. 按 Ctrl+Numpad 3 切换到左视图。

4. 为 `PlateL` 添加 Hinge。

5. 将其 **Max** 设为 30。

6. 按 Numpad 3 返回右视图。

英文原图说明（图片已省略）：步骤 14：PlateL Hinge 和 PlateR Hinge

*1：为 PlateR 和 PlateL 都创建铰链；切换到另一侧视图以选择 PlateL。2：将每个 Max 设为 30。*

### 步骤 15 — Add Link → Follow {#step-15--add-link--follow}

一个操控柄应能同时带动两块侧板。启动引导前，先设置视图：

1. 按 Numpad 1 切换到前视图。

2. 选择 `Blade2`。

3. 使用 F3 > Frame Selected，将头部放大到近处。

两块外侧板会出现在左、右边缘。

1. 打开 **Add Link > Follow**。

2. 点击左边缘的 `PlateL`，将其设为主动部件。

3. 点击右边缘的 `PlateR`，将其设为跟随部件。

4. 按 Enter。

英文原图说明（图片已省略）：步骤 15：前视图露出两块外侧板，供 Follow 依次选择

*1：先点击 PlateL，作为主动部件。2：再点击 PlateR，作为跟随部件。按 Enter。*

### 步骤 16 — 范围 {#step-16--ranges}

1. 选择新建的 Follow。

2. 检查自动填写的 **Source Range** 0…30 和 **Target Range** 0…30。

3. 在 **Name** 中将连接重命名为 `PlateR Follow`。

英文原图说明（图片已省略）：步骤 16：Source Range 和 Target Range

*1：将连接命名为 PlateR Follow。2：确认 Source Range 为 0 至 30。3：确认 Target Range 为 0 至 30。*

### 步骤 17 — Add Link → Piston {#step-17--add-link--piston}

头部折叠时，支撑杆必须始终指向机匣与头部之间。引导处于活动状态时会占用视图导航快捷键。启动引导前：

1. 按 Numpad 3 切换到右视图。

2. 在大纲视图中选择 `StrutRod`。

3. 使用 F3 > Frame Selected，切换到近景。

4. 打开 **Add Link > Piston**。

英文原图说明（图片已省略）：步骤 17：Add Link 菜单中的 Piston

*1：框显 StrutRod 后，打开 Add Link。2：选择 Piston；引导会先要求选择缸体。*

### 步骤 18 — 缸体与活塞杆 {#step-18--the-cylinder-and-the-rod}

引导中的缸体和活塞杆角色描述连接两端的作用；模型对象名称描述原始部件。`StrutBase` 是从套筒缺口中露出的细红杆，`StrutRod` 是黑色套筒。

1. 在近景中，先点击 `StrutBase`，作为缸体部件。

2. 再点击 `StrutRod`，作为活塞杆部件。

3. 按 Enter 接受。

4. 将连接重命名为 `Head Strut`。

5. 保持 **Stretch** 禁用。

1. 在 Controls 中改变 `HeadMount Hinge` 的数值。

2. 检查支撑杆。

3. 将数值重置为零。

<strong>你应看到的结果：</strong>支撑杆跟随头部运动，两个部件始终朝向彼此。

英文原图说明（图片已省略）：步骤 18：Piston 引导，先选择露出的红色缸体，再选择黑色套筒

*1：先点击露出的红色 StrutBase。2：再点击黑色 StrutRod 套筒。按 Enter。*

英文原图说明（图片已省略）：步骤 18：Head Strut 设置，Stretch 关闭

*1：将连接重命名为 Head Strut。2：保持 Stretch 未勾选，然后测试 HeadMount Hinge，并恢复为 0。*

## F. 步枪 {#f-the-rifle}

### 步骤 19 — 握把与后部尖刺的铰链 {#step-19--grip-and-rear-spike-hinges}

对 `Grip` 和 `RearSpike`，分别执行：

1. 打开 **Add Joint → Hinge**。

2. 点击部件。

3. 按 X。

4. 按 Enter。

5. 将 **Min** 设为 0。

6. 将 **Max** 设为 90。

然后：

1. 在列表中选择 `RearSpike Hinge`。

2. 将其 Axis X 设为 -1。

3. Y 和 Z 保持为 0。

4. Grip 保持使用 X 正方向。

5. 确认关节列表中出现 `Grip Hinge` 和 `RearSpike Hinge`。

反转 RearSpike 的 X 轴，会使它在 Compact 形态中向已折叠的头部折拢。这些控件用于在步骤 25 的紧凑形态中折叠握把和后部尖刺。

英文原图说明（图片已省略）：步骤 19：Grip Hinge，Max 为 90

*1：选择 Grip Hinge。2：Axis X 保持为 1，Y 和 Z 保持为 0。3：将 Max 设为 90，Min 保持为 0。*

英文原图说明（图片已省略）：步骤 19：RearSpike Hinge，Axis X 为 -1，Max 为 90

*1：选择 RearSpike Hinge。2：将 Axis X 设为 -1。3：将 Max 设为 90，Min 保持为 0。*

### 步骤 20 — 弹匣与枪栓的滑动关节 {#step-20--magazine-and-bolt-slides}

先对 `Magazine`，再对 `Bolt` 执行：

1. 打开 **Add Joint → Slide**。

2. 点击部件。

3. 按 Z。

4. 按 Enter。

5. Magazine 的 **Max** 设为 0.04，Bolt 的 Max 设为 0.06。

滑动关节使用场景单位，数值 0.06 即 6 cm。

英文原图说明（图片已省略）：步骤 20：Magazine Slide，Z 轴，Max 为 0.04

*1：使用 Add Joint > Slide 后，选择 Magazine Slide。2：使用 Z 轴（Z = 1，X = Y = 0）。3：将 Max 设为 0.04，Min 保持为 0。*

英文原图说明（图片已省略）：步骤 20：Bolt Slide，Z 轴，Max 为 0.06

*1：使用 Add Joint > Slide 后，选择 Bolt Slide。2：使用 Z 轴（Z = 1，X = Y = 0）。3：将 Max 设为 0.06，Min 保持为 0。*

### 步骤 21 — 长杆滑动关节 {#step-21--pole-slide}

1. 打开 **Add Joint → Slide**。

2. 点击 `Pole`。

3. 按 Z。

4. 按 Enter。

5. 将 **Max** 设为 0.6。

6. 在 **4. Controls** 中，将 `Pole Slide` 设为 0.6。

7. 检查已缩回的杆身。

8. 将控件重置为零。

正值会使长杆向上移入机匣。

英文原图说明（图片已省略）：步骤 21：Pole Slide 设置，Z 轴，Max 为 0.6

*1：使用 Add Joint > Slide 后，选择 Pole Slide。2：使用 Z 轴（Z = 1，X = Y = 0）。3：将 Max 设为 0.6，Min 保持为 0。*

### 步骤 22 — 长杆伸缩关节 {#step-22--pole-telescope}

1. 打开 **Add Joint → Telescope**。

2. 点击 `Pole`，作为基座。

3. 点击 `ButtSpike`，作为伸缩段。

4. 按 Enter。

5. 按 Z。

6. 按 Enter。

7. 将 **Length** 设为 0.2。

8. 测试其独立控件。

9. 将控件重置为零。

该控件会沿 Z 正方向将尖刺向上移动最多 20 cm，使其缩入本模型的长杆。

英文原图说明（图片已省略）：步骤 22：Telescope 引导式选择，Pole 为基座，ButtSpike 为伸缩段

*1：点击 Pole 作为基座。2：点击 ButtSpike 作为伸缩段。按 Enter，再按 Z，然后再按 Enter。*

英文原图说明（图片已省略）：步骤 22：Pole Telescope 设置，Z 轴，Length 为 0.2

*1：选择 Pole Telescope。2：确认轴为 Z。3：输入 Length 0.2，测试控件并恢复为零。*

## G. 序列（Sequences） {#g-sequences}

### 步骤 23 — 添加序列 {#step-23--add-sequence}

1. 在 **3. Sequences** 中，选择 **Add Sequence**。

2. 双击列表中的序列名称。

3. 输入 `Scythe to Rifle`。

4. 按 Enter。

英文原图说明（图片已省略）：步骤 23：Add Sequence

*1：点击 Add Sequence。2：双击新名称，输入 Scythe to Rifle。按 Enter。*

### 步骤 24 — 记录一个运动组 {#step-24--record-a-motion-group}

1. 选择 **Move Slider to End**。

序列滑块会移到 `100%`，按钮变为 Record Step 1。

1. 在 **4. Controls** 中，将 `BladeTip Hinge` 设为 70。

2. 将 `Blade2 Hinge` 设为 120。

3. 选择 Record Step 1。

这会存储两个目标条目，每个已移动操控柄对应一个条目。两个关节滑块都重置为零。

英文原图说明（图片已省略）：步骤 24：摆出第一组姿态前，先使用 Move Slider to End

*1：点击一次 Move Slider to End。按钮会变为 Record Step 1。*

英文原图说明（图片已省略）：步骤 24：Record Step 1，Blade2 为 120 度，BladeTip 为 70 度

*1：输入 Blade2 = 120、BladeTip = 70。2：点击 Record Step 1；两个目标都会存储，关节滑块随即重置。*

<em>剩余运动组。</em>每次记录后，记录模式仍处于待记录状态，不要再次启用。对下表中的每个剩余组：

1. 将该组操控柄设置为列出的姿态数值。

2. 选择当前显示的 Record Step 按钮。

| 运动组 | 设置这些操控柄 | 记录完前面各组后显示的按钮 |
|---|---|---|
| 2 | `Blade1 Hinge` 10 和 `PlateL Hinge` 30 | Record Step 3 |
| 3 | `HeadMount Hinge` 90 | Record Step 5 |
| 4 | `Pole Slide` 0.6 | Record Step 6 |

按钮编号等于已存目标条目数加一。记录两个操控柄，编号就增加二，而不是按点击记录的次数计数。四个运动组会生成六个目标条目。如果改变了参与运动的操控柄，请以当前显示的按钮编号为准。

### 步骤 25 — 序列步骤 {#step-25--the-steps}

每个已记录的目标在序列下都有一个条目，显示 **Target**、缓动、**Start** 和 **End**。Start/End 字段使用 0-1，Controls 中的滑块显示 0-100%。

| 运动 | Start | End |
|---|---:|---:|
| 刀刃先折叠 | 0 | 0.25 |
| 侧板和第一刀段随后运动 | 0.25 | 0.5 |
| 头部第三个折叠 | 0.5 | 0.8 |
| 长杆最后移动 | 0.8 | 1 |

同一运动组内的条目使用相同的 Start 和 End。对每个 `Scythe to Rifle` 条目：

1. 将 **Start** 设为表格中该运动组的 Start。

2. 将 **End** 设为表格中该运动组的 End。

3. 保持该条目使用 `Ease In Out`。

在步骤区间之前，条目保持起始值；区间结束后，保持结束值。

每个序列完成后，在记录横幅中选择 **Cancel**。Cancel 会结束记录、保留已存条目，并将该序列滑块归零。记录模式处于待记录状态时，重叠警告描述的是下一次拟记录的区间。不要再添加一个空组。

对于第二个序列，使用步骤 24 的记录流程：

1. 添加 `Rifle to Compact`。

2. 选择一次 **Move Slider to End**，启用记录。

3. 第一组中，将 `Grip Hinge` 设为 90。

4. 将 `RearSpike Hinge` 设为 90。

5. 选择 Record Step 1。

6. 对第一组中的每个条目：

    1. 将 **Start** 设为 0。

    2. 将 **End** 设为 0.5。

7. 第二组中，将 `Magazine Slide` 设为 0.04。

8. 将 `Bolt Slide` 设为 0.06。

9. 选择 Record Step 3。

10. 对第二组中的每个条目：

    1. 将 **Start** 设为 0.5。

    2. 将 **End** 设为 1。

11. 保持每个条目使用 `Ease In Out`。

12. 在记录横幅中选择 **Cancel**，结束记录。

每组会创建两个条目。开始第二组时，记录按钮会从 Record Step 1 变为 Record Step 3。

英文原图说明（图片已省略）：步骤 25：Scythe to Rifle 中的全部六个目标和时间区间

*1：Target 是已记录的关节数值。2：选择 Ease In Out。3：输入 Start。4：输入 End。按给定数值，为全部六个条目填写这些字段。*

英文原图说明（图片已省略）：步骤 25：Rifle to Compact 中的全部四个目标和时间区间

*1：Grip 和 RearSpike 使用 Target 90、Start 0、End 0.5。2：Magazine 和 Bolt 使用 0.04 / 0.06、Start 0.5、End 1。保持 Ease In Out。*

英文原图说明（图片已省略）：步骤 25：使用记录横幅中的 Cancel 结束记录

*1：完成一个序列后，在此记录横幅中点击 Cancel 结束记录。这会保留条目，并将序列归零。*

### 步骤 26 — 测试序列 {#step-26--test-the-sequence}

位于步骤记录按钮旁的 **Test** 会让滑块从 0% 移到 100%，再回到 0%，然后恢复测试前的滑块数值。

1. 从 Scythe 形态开始，对 `Scythe to Rifle` 选择 **Test**。

2. 将第一个序列保持在 100%，对 `Rifle to Compact` 选择 **Test**。

3. 测试后，将两个序列都重置为 0%。

英文原图说明（图片已省略）：步骤 26：折叠过程中序列的 Test 按钮

*1：点击记录按钮旁的 Test。2：观察折叠和返回过程。测试 Compact 时，Scythe to Rifle 必须为 100%。*

<strong>你应看到的结果：</strong>刀刃卷起，侧板闭合，头部向下折到机匣旁，长杆向上滑动，随后所有部件返回原位。

## H. 形态（Forms） {#h-forms}

### 步骤 27 — 保存形态 {#step-27--save-form}

保持所有单独的关节滑块为零，让序列提供运动。将所选序列移到末端，可能会再次启用记录。保存 Form 不会记录新步骤。除非打算添加另一个目标，否则不要选择 Record Step。

在 **4. Controls** 中：

1. 保持所有滑块为 0，选择 **Save Form**。

2. 双击新列表条目。

3. 将其命名为 `Scythe`。

4. 将 `Scythe to Rifle` 设为 `100%`。

5. 选择 **Save Form**。

6. 按相同的命名流程，将新条目命名为 `Rifle`。

7. 再将 `Rifle to Compact` 也设为 `100%`。

8. 选择 **Save Form**。

9. 将新条目命名为 `Compact`。

清除待记录状态：

1. 在形态列表中选择 `Scythe`。

2. 选择 **Go to Form**。

两个序列都会归零。切换到 Rifle 或 Compact 时，由于所选序列为 100%，可能会再次启用记录。

英文原图说明（图片已省略）：步骤 27：所有滑块为 0 时使用 Save Form

*1：开始时，两个序列和每个关节都设为 0。2：点击 Save Form。3：双击新列表条目，命名为 Scythe；对 Rifle 和 Compact 重复操作。*

### 步骤 28 — 切换到形态 {#step-28--go-to-form}

1. 在列表中选择一个形态。

2. 选择 **Go to Form**。

**Go and Key** 还会在当前帧为每个控件插入关键帧，用这些关键帧为变形制作动画。

英文原图说明（图片已省略）：步骤 28：选中 Rifle，使用 Go to Form

*1：选择保存的形态。2：点击 Go to Form。Go and Key 还会插入动画关键帧。*

### 步骤 29 — 步枪形态 {#step-29--the-rifle}

英文原图说明（图片已省略）：步骤 29：Rifle 形态

*1：选择 Rifle。2：点击 Go to Form。3：按原图所示姿态检查序列百分比。*

### 步骤 30 — 紧凑形态 {#step-30--compact}

英文原图说明（图片已省略）：步骤 30：Compact 形态

*1：选择 Compact。2：点击 Go to Form。3：按原图所示姿态检查序列百分比。*

1. 返回 `Scythe`。

2. 保存文件。

## 你已完成什么 {#what-you-built}

| 记录 | 骨骼 | 作用 |
|---|---|---|
| 15 个部件 | `MCH-<part>` 和 `DEF-<part>` | 每个部件的网格都以对应的 `DEF-` 骨骼为父级 |
| 8 个 Hinge、3 个 Slide、1 个 Telescope | `CTRL-<part>` | 操控柄；其数值就是 **4. Controls** 中的滑块 |
| 1 个 Piston | `MCH-<part>-aim` 和 `MCH-<part>-target` | 使支撑杆的两个部件始终朝向彼此 |
| 1 个 Follow | 无 | `PlateR` 随 `PlateL` 一起转动 |
| 2 个 Sequence | `CTRL-SEQ-<name>` | 每个序列一个滑块 |
| 3 个 Form | 无 | 保存的滑块数值 |

更新后的示例通过了 Rig Validator，未报告问题；它也通过了关闭 Auto Run Python Scripts 时的重新加载检查，涵盖每个独立控件和全部三个 Form。

## 接下来可以尝试 {#try-next}

编辑 Follow 映射：

1. 在 `PlateR Follow` 上启用 **Curve**。

2. 在 Graph Editor 中调整映射形状。

如需另一种姿态，可将刀刃折起、头部抬高，再保存第四个形态 `Carry`。

制作动画并导出：

1. 使用 **Go and Key**，在不同帧为各形态插入关键帧。

2. 导出 `DEF-` 骨骼（参见 [VRChat 工具](08-vrchat.md)）。

## 齿轮连接（Gear Link） {#gear-link}

Crescent Rose 没有齿轮配对，因此此绑定没有 Gear Link。Gear Link 会按齿数比，在一个 Hinge 转动时带动另一个 Hinge。例子包括曲柄与转轮，或将旋转转换为滑动的齿条。参见[齿轮连接](07-mechanisms.md#gear-link)。

## 致谢 {#credits}

Crescent Rose 模型作者为 amandangm，https://sketchfab.com/3d-models/crescent-rose-dcb6bfbb3b824c01a182fa131fe35824 ，授权为 CC BY 4.0。本教程使用经过拆分、缩放和绑定的版本。Crescent Rose 是 Rooster Teeth Productions 的设计。本素材是同人教程资产。

[← 目录](index.md)
