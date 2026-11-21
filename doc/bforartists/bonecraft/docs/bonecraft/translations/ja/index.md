# BoneCraft マニュアル {#bonecraft-manual}

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
      content: "ページ " counter(page) " / " counter(pages);
      font-family: "Segoe UI", sans-serif;
      font-size: 9pt;
      color: #555;
    }
  }
}
</style>

**BoneCraft 9.2.19 ローカル候補版。** BoneCraft は、Bforartists 用のリギングとアバター制作のツールキットです。

この画像なし版では、BoneCraft 9.2.19 候補版の操作項目、画面内の移動方法、パネルの修正を説明します。全12章とワークショップの文章による手順を収録しています。スクリーンショットの画像ファイルは省略し、英語原本の画像説明とキャプションを注記として残しています。

最初に提供された Bforartists ビルドには BoneCraft 9.2.18 が含まれます。新しいローカルプレビューには9.2.19候補版が含まれます。どちらも初期設定で BoneCraft が有効になります。これらのビルドでは ZIP のインストールは不要です。

**BoneCraft** と **Rig Builder** は、左のツールシェルフ（**T**）から開きます。**CATS** は、右のサイドバー（**N**）から開きます。[付属ビルドのクイックスタート](01-start.md#supplied-build-quick-start)を参照してください。

画面上のパスと設定は同じです。任意ツールと依存アドオンには、それぞれの必要条件が引き続き適用されます。この手順は、ローカルの貢献提案用プレビューを説明しています。公式 Bforartists 5.2.3 パッケージに、この一式は含まれていません。単体版を使う場合は、[BoneCraft のインストール](01-start.md#installing-bonecraft)に従ってください。

ソースレビューの対象は、MMD のインストール、マテリアルアトラスの準備、書き出し時の命名、モードの復元、保存済みのメカニズム形態、現在のパネルの修正です。

インストールと画面構成については、[はじめに](01-start.md)を参照してください。ローカル9.2.19候補版までの変更は、[新機能](11-whats-new.md)を参照してください。

英語原本のワークショップには、過去の検証記録とスクリーンショットのバージョン表示が残っています。この画像なし版では画像を省略し、文章による説明とキャプションを保持しています。すべてのチュートリアルを9.2.19で再実行したことを示すものではありません。

この版は、拡充された第6章のワークショップと第12章を含む、現在の英語版の全12章に対応しています。以前の翻訳版の目次と未完成の章は、過去の版であり、この版の収録範囲を定めるものではありません。

公開済みの単体版リリースは、引き続き9.2.18です。ローカル9.2.19候補版は未公開です。公開版については、[9.2.18 リリースノート](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.18/RELEASE-NOTES.md)を参照してください。

英語原本の Crescent Rose チュートリアルには、9.1.2の画面に照らして確認した、FBX 準備の8手順、Mechanisms の30手順、注釈付きスクリーンショット52枚があります。この画像なし版では、文章による手順、画像説明、キャプションを保持し、画像ファイルを省略しています。

## 章 {#chapters}

動画による補足：[IK/FK 初心者向けの手順と練習ファイル](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/tutorials/ikfk-beginner.md)。

以下の章へのリンクを使用してください。マニュアルを再構築すると、PDF のページ割りは変わります。

1. [はじめに](01-start.md) — BoneCraft の概要、インストール方法、各機能の場所。
2. [ガイド1–7](02-guides-a.md) — 最初のアバター、VRoid、MMD、ボーン名、ヒューマノイドの対応付け、髪、衣装。
3. [ガイド8–13](03-guides-b.md) — リップシンク、パフォーマンス、ポーズ、リグの統合、アップロードの問題、CATS。
4. [CATS パイプライン](04-cats-pipeline.md) — 6つのフェーズ、操作履歴、順序が重要な理由。
5. [リグツール](05-rig-tools.md) — リグ UI、アニメーション、ウェイト、リグ制御のツール。
6. [Rig Builder](06-rig-builder.md) — 新しいリグの作成、Simple Human → マネキン → Auto-Rig → IK/FK の文章によるワークショップ、Bone Merge。
7. [Mechanisms](07-mechanisms.md) — 小道具と機械のジョイントとリンク：ヒンジ、スライド、ギア、シーケンス。
8. [VRChat ツール](08-vrchat.md) — VRChat、VRM、MMD のツール、I/O Hub、Task Board。
9. [CATS ツール](09-cats.md) — CATS の各ツールを個別に説明します。
10. [クイック修正と用語集](10-reference.md) — よくある問題と、このマニュアルで使う用語。
11. [新機能](11-whats-new.md) — バージョンごとの変更点。
12. [チュートリアル：Mechanisms で Crescent Rose を作る](12-crescent-rose.md) — 変形する鎌とライフルを手順に沿ってリギングする実例。文章による手順と、英語原本から保持した画像説明を収録しています。
