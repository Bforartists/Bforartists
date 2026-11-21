# CATS 流程 {#the-cats-pipeline}

[← 目录](index.md)

**首次使用任何 CATS 工具前，请先阅读本章。**

CATS 工具提供建议的准备流程。请按以下顺序检查各阶段，跳过虚拟形象不需要的阶段。修改网格或绑定数据前，先保存文件检查点，并检查每一步的结果。即使前一阶段尚未完成，工具仍可使用。

---

## 按顺序进行的六个阶段 {#the-six-phases-in-order}

CATS 选项卡中的 Pipeline Status 列出各阶段，完成后在相应阶段打勾：

1. **Fix Model** — 检查清理选项，例如删除重复项和修正法线。操作后检查网格。

2. **Material Atlas** — 将虚拟形象的材质合并到一张纹理图中（可选，用于优化性能）。

    1. 检查结果前，保持 **Preserve Backup Duplicate** 启用。

    2. 选择 **Analyze Materials**。

    3. 选择来源。

    4. 选择 **Bake Checked Sources**。

    5. 检查结果。

    6. 进行下一次烘焙前，选择 Accept 或 Revert。

    参见[材质图集合并器](09-cats.md#material-atlas-combiner)。

3. **Visemes** — 根据三个基础口形（A、O、CH）生成 VRChat 口型同步所需的 15 个嘴部形态。

4. **Eye Tracking** — 使用虚拟形象的眼部骨骼设置 VRChat 眼球运动。

5. **Pose to Shape Key** — 将网格当前的形态键混合状态保存为新的形态键。此按钮不烘焙骨架骨骼变形。需要保存骨骼变形时，参见[原生骨骼姿态流程](09-cats.md#save-a-bone-deformed-pose)。

6. **Apply All Transforms** — 将位置、旋转和缩放应用到网格及骨架。导出前对比结果。

---

## Pipeline Status 与 Operation Ledger {#pipeline-status-and-the-operation-ledger}

Pipeline Status 为每个阶段显示一行。阶段完成后，该行出现勾选标记。场景会将这些状态保存在文件中。

Operation Ledger 按时间记录每次 CATS 操作，最新记录位于末尾，包含时间和结果。Changed 表示操作修改了模型；Clean 表示无需更改；Failed 表示操作失败。**Copy** 将记录复制到剪贴板，便于请求支持；**Clear** 清空记录。

该顺序是建议，而非硬性限制。若前一阶段未完成，工具仍会运行，但会显示诸如“Run Fix Model first for best results”的警告。继续前请先阅读警告。

英文原稿图片描述（图片已省略）：Pipeline Status 按建议顺序列出六个阶段。

*原生面板弹出窗口，BoneCraft 9.2.18。Pipeline Status 按建议顺序列出六个阶段。*

英文原稿图片描述（图片已省略）：尚无条目时的 Operation Ledger。Copy 和 Clear 针对已记录的条目操作。

*原生面板弹出窗口，BoneCraft 9.2.18。尚无条目时的 Operation Ledger。Copy 和 Clear 针对已记录的条目操作。*

---

## 为什么采用这个顺序 {#why-this-order}

该顺序便于一次检查一类更改：

- <strong>先检查清理。</strong>Fix Model 可能根据选项更改几何体或删除数据。生成更多数据前，检查网格及其已有形态键。

- <strong>先检查口形，再检查眼睛。</strong>测试生成或映射的口形。Eye Auto-Detect 按骨骼名称搜索；Left Eye 和 Right Eye 的分配应与骨骼朝向及约束分开检查。

- <strong>接着检查表情捕获。</strong>Pose to Shape Key 捕获的是形态键混合，而不是骨骼变形。

    1. 将原有形态键数值重置为 0。

    2. 将新形态键设为 1 进行测试。

    要保存骨骼变形后的姿态，请使用上文链接的原生流程。

- <strong>导出前检查变换。</strong>应用变换会更改对象数据，并重置变换通道。先前工具仍可使用。请对比结果及导出设置；需要恢复早先状态时，使用 Undo 或已保存的检查点。

---

## 跳过阶段前 {#before-skipping-a-phase}

**跳过 Fix Model：**
检查导入的几何体、法线、权重、修改器及已有形态键。选择虚拟形象需要的清理操作。嘴部形态和眼球运动问题需分别检查；流程中某阶段未打勾，本身并不能确定这些问题的原因。

**跳过 Visemes：**
若既未生成也未映射口形，虚拟形象便没有口型同步。若口形形态键已存在，请在 VRChat Viseme Mapping 中映射（指南 8），不必重新生成。此时 Pipeline Status 中的 Visemes 仍不打勾，属于预期状态。

**跳过 Eye Tracking：**
虚拟形象在 VRChat 中不会转动眼睛，只会直视前方。没有眼部骨骼时，这样是可以的。

**跳过 Pose to Shape：**
此阶段可选。如果不需要保存当前形态键混合状态的快照，可以跳过。无需另建形态键，也能检查和使用已有表情。

下一章：[绑定工具](05-rig-tools.md)
