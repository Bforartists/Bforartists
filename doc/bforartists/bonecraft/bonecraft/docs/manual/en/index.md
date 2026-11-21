# BoneCraft Manual

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
      content: "Page " counter(page) " of " counter(pages);
      font-family: "Segoe UI", sans-serif;
      font-size: 9pt;
      color: #555;
    }
  }
}
</style>

**BoneCraft 9.2.19 local candidate.** BoneCraft is a rigging and avatar toolkit for Bforartists.

This English edition covers the BoneCraft 9.2.19 candidate controls, navigation and panel repairs. It retains all 12 chapters and the illustrated workshops.

The original supplied Bforartists build includes BoneCraft 9.2.18. The new local preview includes the 9.2.19 candidate. Both enable BoneCraft through factory settings. These builds need no ZIP installation.

For **BoneCraft** and **Rig Builder**, open the left Tool Shelf (**T**). For **CATS**, open the right sidebar (**N**). See [Supplied build quick start](01-start.md#supplied-build-quick-start).

The interface paths and settings are the same. Optional tools and dependencies retain their requirements. These instructions describe the local contribution preview. The official Bforartists 5.2.3 package does not include this bundle. Standalone users should follow [Installing BoneCraft](01-start.md#installing-bonecraft).

The source review covers MMD installation, material-atlas preparation, export naming, mode restoration, saved mechanism forms and current panel repairs.

For installation and the interface map, read [Getting Started](01-start.md). For changes through the local 9.2.19 candidate, read [What's New](11-whats-new.md).

The workshops retain their historical checks and screenshot versions. Earlier pictures keep their original version labels. This edition does not claim that every tutorial was replayed with 9.2.19.

The six translated indexes remain at 9.2.4. Their chapter 6 workshop expansion and chapter 12 remain incomplete. Use English for current instructions.

The published standalone release remains 9.2.18. The local 9.2.19 candidate has not been published. Read the [9.2.18 release notes](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.18/RELEASE-NOTES.md) for that release.

The Crescent Rose tutorial includes eight FBX preparation steps, 30 Mechanisms steps and 52 annotated screenshots checked against the 9.1.2 interface.

## Chapters

Video supplement: [IK/FK beginner walkthrough and practice file](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/tutorials/ikfk-beginner.md).

Use the chapter links below. PDF pagination changes when the manual is rebuilt.

1. [Getting Started](01-start.md) — what BoneCraft is, installing it, and where everything is.
2. [Guides 1–7](02-guides-a.md) — first avatar, VRoid, MMD, bone names, humanoid mapping, hair, clothing.
3. [Guides 8–13](03-guides-b.md) — lip sync, performance, poses, merging rigs, upload problems, CATS.
4. [The CATS Pipeline](04-cats-pipeline.md) — the six phases, the ledger, and why the order matters.
5. [Rig Tools](05-rig-tools.md) — rig UI, animation, weight and rig-control tools.
6. [Rig Builder](06-rig-builder.md) — building a new rig, an illustrated Simple Human → mannequin → Auto-Rig → IK/FK workshop, and Bone Merge.
7. [Mechanisms](07-mechanisms.md) — joints and links for props and machines: hinges, slides, gears, sequences.
8. [VRChat Tools](08-vrchat.md) — VRChat, VRM and MMD tools, the I/O Hub and the Task Board.
9. [CATS Tools](09-cats.md) — every CATS tool, one by one.
10. [Quick Fixes and Glossary](10-reference.md) — common problems and the words this manual uses.
11. [What's New](11-whats-new.md) — changes by version.
12. [Tutorial: Crescent Rose with Mechanisms](12-crescent-rose.md) — a worked example: rig a transforming scythe-rifle step by step, with screenshots.
