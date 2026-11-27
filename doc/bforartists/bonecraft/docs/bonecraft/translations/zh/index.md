# BoneCraft 手册 {#bonecraft-manual}

<!-- Print footer for exported PDFs. -->
<style>
@media print {
  p:has(> img):has(+ p > em:only-child) {
    break-after: avoid;
  }
  p:has(> img) + p:has(> em:only-child) {
    break-before: avoid;
    break-inside: avoid;
  }
  section.chapter > p:last-child {
    break-before: avoid;
  }
  @page {
    @bottom-center {
      content: "第 " counter(page) " 页，共 " counter(pages) " 页";
      font-family: "Segoe UI", sans-serif;
      font-size: 9pt;
      color: #555;
    }
  }
}
</style>

<strong>BoneCraft 9.2.19 本地候选版。</strong>BoneCraft 是用于 Bforartists 的绑定与虚拟形象工具包。

本纯文本版本介绍 BoneCraft 9.2.19 候选版的控件、导航和面板修复。全部 12 章及书面练习步骤均予保留。截图资源已省略，英文原稿中的图片描述和文字图注则保留为说明。

原先提供的 Bforartists 构建内置 BoneCraft 9.2.18；新的本地预览版内置 9.2.19 候选版。两者均通过出厂设置启用 BoneCraft，无需安装 ZIP。

使用 **BoneCraft** 和 **Rig Builder** 时，打开左侧工具架（**T**）；使用 **CATS** 时，打开右侧栏（**N**）。参见[随附构建快速入门](01-start.md#supplied-build-quick-start)。

界面路径和设置保持一致。可选工具及依赖项仍须满足各自要求。本说明针对本地贡献预览版；官方 Bforartists 5.2.3 软件包不包含此套件。独立安装的用户应参阅[安装 BoneCraft](01-start.md#installing-bonecraft)。

源代码审查涵盖 MMD 安装、材质图集准备、导出命名、模式恢复、已保存的机械机构姿态（Form）以及当前面板修复。

安装方法和界面位置请参阅[入门](01-start.md)；截至本地 9.2.19 候选版的更改请参阅[新功能](11-whats-new.md)。

英文原稿中的练习保留其历史检查记录和截图版本标签。本纯文本版本省略这些图片，但保留文字描述和图注；并不表示已使用 9.2.19 重新执行每篇教程。

本版本遵循当前英文原稿的全部 12 章，包括扩展后的第 6 章练习和第 12 章。早期译本的目录及不完整章节属于历史前稿，不代表本版本的范围。

已发布的独立版本仍为 9.2.18；本地 9.2.19 候选版尚未发布。该已发布版本的信息见 [9.2.18 发布说明](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.18/RELEASE-NOTES.md)。

英文原稿的 Crescent Rose 教程包含八步 FBX 准备、30 步 Mechanisms 操作，以及 52 张按 9.1.2 界面检查的标注截图。本纯文本版本保留书面步骤、图片描述和图注，省略图片资源。

## 章节 {#chapters}

视频补充：[IK/FK 新手演示与练习文件](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/tutorials/ikfk-beginner.md)。

请使用下列章节链接。手册重建后，PDF 页码可能变化。

1. [入门](01-start.md) — BoneCraft 是什么、如何安装，以及各功能的位置。
2. [指南 1–7](02-guides-a.md) — 第一个虚拟形象、VRoid、MMD、骨骼名称、人形映射、头发和服装。
3. [指南 8–13](03-guides-b.md) — 口型同步、性能、姿态、合并骨架、上传问题和 CATS。
4. [CATS 流程](04-cats-pipeline.md) — 六个阶段、操作记录，以及顺序为何重要。
5. [绑定工具](05-rig-tools.md) — 绑定界面、动画、权重和绑定控制工具。
6. [Rig Builder](06-rig-builder.md) — 创建新绑定、Simple Human → 人体模型 → Auto-Rig → IK/FK 的书面练习，以及 Bone Merge。
7. [Mechanisms（机械机构）](07-mechanisms.md) — 用于道具和机械的关节与连接：铰链、滑动、齿轮和序列。
8. [VRChat 工具](08-vrchat.md) — VRChat、VRM 和 MMD 工具、I/O Hub 以及 Task Board。
9. [CATS 工具](09-cats.md) — 逐一介绍每项 CATS 工具。
10. [快速修复与术语表](10-reference.md) — 常见问题及本手册使用的术语。
11. [新功能](11-whats-new.md) — 按版本列出的更改。
12. [教程：使用 Mechanisms 制作 Crescent Rose](12-crescent-rose.md) — 完整实例：逐步为变形镰刀步枪绑定骨骼，并保留书面操作说明和英文原稿的图片描述。
