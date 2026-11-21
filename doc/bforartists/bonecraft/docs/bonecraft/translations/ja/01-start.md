# はじめに {#getting-started}

[← 目次](index.md)

## BoneCraft とは {#what-is-bonecraft}

BoneCraft は Bforartists 用のアドオンです。キャラクターや小道具をリギングし、VRChat、VRoid / VRM、MMD 用の3Dアバターを準備します。パネルから、リグの作成、ウェイトペイント、ボーンの命名、リップシンク、アイトラッキング、書き出しを自動化できます。

**BoneCraft にできないこと：**

- アバターの体型をモデリングしたり、スカルプトしたりすることはできません。
- テクスチャやマテリアルを一から作ることはできません。
- VRChat に直接アップロードすることはできません（VRChat Creator Companion / SDK が必要です）。

---

## BoneCraft と BoneForge {#bonecraft-and-boneforge}

BoneCraft は、Blender のフォークである Bforartists でのみ動作します。BoneForge は、標準 Blender 用の別のアドオンで、含まれるツールは少なくなります。インストールするのは、どちらか一方だけにしてください。標準 Blender では、BoneCraft は案内と Bforartists を入手するためのボタンを表示し、ツールは読み込みません。

BoneForge 9.0.0以降は、標準 Blender を対象としています。BoneCraft は、それとは別の Bforartists 用アドオンです。どちらにも Auto-Rig Wizard、Quick Rig、Mannequin、共通の CATS/Material Atlas ツールがあります。BoneCraft にはさらに、Mechanisms、Control Picker、制作向けの制御リグ、関節検出、プロファイル別書き出しのツールがあります。画面上の配置が似ていても、それらのツールが BoneForge に追加されるわけではありません。

## 付属ビルドのクイックスタート {#supplied-build-quick-start}

最初に提供された Bforartists ビルドには BoneCraft 9.2.18 が含まれます。新しいローカルプレビューには9.2.19候補版が含まれます。どちらも初期設定で BoneCraft が有効になります。これらのビルドでは、ZIP のインストールや BoneCraft の手動での有効化は不要です。

1. 付属の Bforartists ビルドを開きます。
2. **T** を押して、左のツールシェルフを表示します。
3. **BoneCraft** または **Rig Builder** を選択します。
4. **N** を押して、右のサイドバーを表示します。
5. アバターツールと **Import / Export** には、**CATS** を選択します。

このマニュアルに記載した画面上のパスと設定を、そのまま使います。任意のツールパッケージと依存アドオンには、それぞれの必要条件が引き続き適用されます。Rigify のスターターリグと VRM/MMD のブリッジには、記載された依存アドオンが必要です。

この手順は、ローカルの貢献提案用プレビューを説明しています。公式 Bforartists 5.2.3 パッケージに、この一式は含まれていません。レビューの経緯は、[貢献提案](https://github.com/Bforartists/Bforartists/pull/7067)を参照してください。

## BoneCraft のインストール {#installing-bonecraft}

この節は、単体版 Toolkit ZIP 用です。付属ビルドを使う場合は、上記の既存タブから始められます。

リンク先の公開 ZIP は9.2.18です。9.2.19候補版の修正を使うには、公開されるまでローカルプレビューを使用してください。

**必要なもの：**

- Bforartists（BoneCraft は Bforartists 5.2 でテストされています）。
- 単体版の [BoneCraft-BFA-9.2.18.zip](https://github.com/Axleonex/B4Artists_Toolkit/releases/download/bonecraft-v9.2.18/BoneCraft-BFA-9.2.18.zip) ファイル。

**手順：**

更新する場合：

1. 作業内容を保存します。

2. 古い単体版 BoneCraft アドオンを無効にします。

3. 古い単体版 BoneCraft アドオンを削除します。

4. 新しい ZIP をインストールする前に、Bforartists を再起動します。

初めてインストールする場合は、ここから始めます。

1. Bforartists を開きます。
2. **Edit** → **Preferences** → **Add-ons** を開きます。
3. **Install from Disk…** を選択します。

4. BoneCraft の `.zip` ファイルを選択します。

5. BoneCraft の横のチェックボックスを有効にします。
6. リンク先の公開 ZIP を使った場合、プリファレンスに **9.2.18** と表示されることを確認します。

7. BoneCraft の項目を展開し、**Language**、**Tabs**、**Shelf Width**、**Show Helpers**、**Tools** を確認します。

この手順でインストールするのは、単体版 Toolkit ZIP です。提供されたビルドに BoneCraft がすでに含まれている場合は、付属ビルドのクイックスタートを使用してください。単体版と組み込み版を重複して有効にしないでください。

**表示されるもの：** 左のツールシェルフ（**T**）に BoneCraft と Rig Builder のタブ、右のサイドバー（**N**）に CATS タブが表示されます。

## 各機能の場所 {#where-things-are}

各タブには、作業用の機能グループがあります。Setup Rigging、Skin、Review、Avatar Tools、Facial は、タブ内の展開可能なセクションです。以下のパスでは英語 UI のラベルを使います。翻訳されたラベルは、Language プリファレンスによって変わります。

| タブ | 既定の場所 | セクション |
| --- | --- | --- |
| Rig Builder | 左のツールシェルフ（T） | Auto-Rig Wizard, Quick Rig - premade armatures, Mannequin |
| BoneCraft | 左のツールシェルフ（T） | Overview, Setup Rigging, Skin, Mechanisms, Review |
| CATS | 右のサイドバー（N） | CATS, Avatar Tools, VRChat Tools, Import / Export |

英語原本の画像説明（画像は省略）：左のツールシェルフで BoneCraft、右のサイドバーで CATS が選択されています。T または N を押すと、それぞれの側を表示できます。

*ローカルプレビュー、BoneCraft 9.2.19候補版。Bforartists 5.2.3、Blender 5.4 Alpha。左のツールシェルフで BoneCraft、右のサイドバーで CATS が選択されています。T または N を押すと、それぞれの側を表示できます。*

| ツール | 開くパス |
| --- | --- |
| Bone Merge | BoneCraft → Setup Rigging → Bone Merge |
| Delta Mush / Proximity Wrap | BoneCraft → Skin → Delta Mush / Proximity Wrap |
| Viseme Library / Lip Sync | CATS → Avatar Tools → Viseme Library → Lip Sync |
| VRChat Viseme Mapping / Face Tracking | CATS → VRChat Tools → Facial |
| Humanoid / Hair | CATS → Avatar Tools → Set Up Humanoid Bones / Add Hair Physics |
| VRChat export | CATS → Import / Export → Game Engine Export → Unity / VRChat |
| Unreal export and Bone Names | CATS → Import / Export → Game Engine Export → Unreal Engine 5 |
| Validated profile export | CATS → Import / Export → Game Export → Export (Profile) |
| Material Atlas | CATS → CATS → Material Atlas → Analyze Materials / Refresh Analysis → Bake Checked Sources |
| VRM / MMD / I/O Hub | CATS → Import / Export → VRM / VRoid, MMD / PMX, Game Engine Export |
| Performance / Clothing / Naming | CATS → VRChat Tools → Check Performance / Attach Clothing / VRChat Naming Extras |

リグとビジームライブラリの操作項目には、アーマチュアを選択します。Delta Mush と Proximity Wrap には、オブジェクトモードのメッシュを選択します。Lip Sync には、ポーズモードのアーマチュアが必要です。セクションの三角を展開すると、ボタンを表示します。Options の折りたたみ欄には、任意の設定があります。ツールがすぐに実行される場合は、次の操作を行う前に Adjust Last Operation で調整してください。

顔に関する3つの作業には、それぞれ異なる目的があります。CATS のビジーム生成は、口のシェイプキーを作成します。Viseme Library / Lip Sync は、ポーズを保存し、アニメーションにキーを挿入します。Facial は、既存のシェイプキーを VRChat に対応付けるか、フェイストラッキングを設定します。

UV パッキングの操作項目は、**CATS → CATS → Material Atlas → Advanced Options → UV Packing** にあります。古い手順では、この折りたたみ欄を Override Inherited Settings と呼んでいます。BoneCraft が提供するのは共通のアトラス用 UV 補助機能であり、単体版 UVToolkit アドオンの全機能ではありません。

**Starter Rigs：**

1. 下部のアセットシェルフのカタログメニューで、**Starter Rigs** を有効にします。

2. 必要なら、ライブラリを **All** にします。

バージョン9.2.5で、左上にあった古い Starter Rigs の操作項目は削除されました。**Add → Armature → Starter Rig Catalog** では、依存アドオンを確認しながら、フィッティングと生成を行えます。

**タブを移動する：**

1. **Edit** → **Preferences** → **Add-ons** → BoneCraft → **Tabs** を開きます。

2. タブを **Left** または **Right** に設定します。

各タブには、表示の切り替えもあります。変更はすぐに適用されます。タブが非表示の場合、Left と Right のボタンは灰色になりますが、引き続き使用できます。

**プロパティエディター：** Preferences → Tabs の **Scene Properties** は、最初から有効です。プロパティエディターの Scene タブに、Rig Builder、Mechanisms、CATS、Avatar Tools、VRChat Tools、Import / Export を表示します。

**Show** を選択すると、これらのセクションの表示を切り替えます。青色は、セクションが表示されていることを示します。この切り替えは、ビューポートのタブや Armature データタブには影響しません。

アーマチュアを選択している場合、BoneCraft のアーマチュア用ツールは Armature データタブにも表示されます。これらのツールは、表示切り替えには従いません。Rig Builder、Mechanisms、CATS の各セクションは、Scene タブを使います。

すべての場所からツールを取り除くには、**Tools** でそのパッケージを無効にします。アドオン自体を無効にする方法もあります。

**Shelf Width：** Widen Narrow Shelves は、最初から有効です。BoneCraft のタブを含むシェルフが Left または Right の最小幅より狭いとき、1回だけ幅を広げます。UI スケール1×では、既定値は Left が240ピクセル、Right が260ピクセルです。その後でシェルフを狭くドラッグすると、選んだ幅が保持されます。幅を手動で調整するには、この切り替えを無効にします。幅の設定欄は無効になります。

英語原本の画像説明（画像は省略）：Tabs では BoneCraft と Rig Builder を左、CATS を右に配置します。その下に Shelf Width と Show Helpers があります。

*ローカルプレビュー、BoneCraft 9.2.19候補版。Bforartists 5.2.3、Blender 5.4 Alpha。Tabs では BoneCraft と Rig Builder を左、CATS を右に配置します。その下に Shelf Width と Show Helpers があります。*

**メニューと標準ツールシェルフのタブ：** 3Dビューポートのヘッダーメニューからも、ツールを使えます。

| 場所 | ツール |
| --- | --- |
| Add → Armature | Quick Rig, Auto-Rig Wizard, Mannequin for Active Rig |
| Pose → BoneCraft（ポーズモード） | ポーズツール、ピッカー、ボーンコレクション、リグのセットアップと確認 |
| Weights → BoneCraft（ウェイトペイントモード） | 塗りつぶし、ウェイトのミラー反転と正規化 |
| Object → Mechanisms（オブジェクトモード） | パーツ、ジョイント、リンクの追加と、動作テスト |
| Tool Shelf → Pose or Weights → BoneCraft | よく使うポーズ操作、ウェイト操作のボタン |

Pose と Weights のシェルフボタンは、幅の広いシェルフでは文字を表示します。幅が狭い場合は、アイコンのグリッドを表示します。アイコンにマウスを重ねると、ツールチップを読めます。これらの場所から使うのは、BoneCraft のタブと同じツールです。有効なツールパッケージだけが使用できます。

**ビューポートツール：** Place Rig Markers は、メッシュをクリックすると、Auto-Rig Wizard の次のマーカーを配置します。Build Mechanism は、パーツをクリックすると、案内に沿ったジョイントまたはリンクの作成を開始します。セットアップと操作項目については、[Rig Builder](06-rig-builder.md#auto-rig-wizard)と[Mechanisms](07-mechanisms.md#joints-and-links-one-example-each)を参照してください。

**先に実行し、その後で調整する：** Quick Rig、Fit Dropped Rig、Weight Mirror、Weight Transfer、Flood to Custom、Ribbon、Spline IK、Delta Mush は、すぐに実行されます。

1. ツールを選択します。

2. すぐに、ビューポートの Adjust Last Operation パネルでオプションを調整します。

3. 次の操作を行う前に、調整を終えます。

他のパネルでは、操作ボタンの下の折りたたみ欄に任意の設定があります。その設定を使うには、欄を展開します。別の選択対象が必要なパネルは、表示を維持し、何を選択するかを案内する場合があります。

**Show Helpers：** BoneCraft は、短い「何をするか／いつ使うか」の文章や「How this works」の注記で、各セクションを説明します。この注記を隠すには、アドオンのプリファレンスで **Show Helpers** を無効にします。Avatar Tools の **Compact Mode** も、同じ切り替えを制御します。

**Language：** アドオンのプリファレンスにある **Language** で、BoneCraft 自身のパネルを English、日本語、한국어、中文、Français、Português、Español に変更できます。

英語原本の画像説明（画像は省略）：ローカルプレビューには BoneCraft 9.2.19 と、Language が English であることが表示されています。

*ローカルプレビュー、BoneCraft 9.2.19候補版。Bforartists 5.2.3、Blender 5.4 Alpha。ローカルプレビューには BoneCraft 9.2.19 と、Language が English であることが表示されています。*

**クリーンアップの前に確認する：**

1. Fix Model のオプションを確認します。

2. アバターに必要な操作を選択します。

3. 変更前に、ファイルをチェックポイントとして保存します。

4. 操作後に、結果を確認します。

Pipeline Status と Operation Ledger は、進捗を記録します。[CATS パイプライン](04-cats-pipeline.md)を参照してください。

**クイックパネル：** 3Dビューポートで **Ctrl+Shift+R** を押すと、カーソルの下に BoneCraft のリグパネルがポップアップします。

---

## どこから始めるか {#where-should-i-start}

作業に合ったガイドを選択してください。

> **新しい FBX、OBJ、Blender モデルを VRChat 用にリギングする。**
> → [ガイド1：最初のアバターを VRChat に入れる](02-guides-a.md#guide-1-get-your-first-avatar-into-vrchat)へ。

> **VRoid Studio から書き出した VRM アバターを準備する。**
> → [ガイド2：VRoid アバターを VRChat に入れる](02-guides-a.md#guide-2-bring-a-vroid-avatar-into-vrchat)へ。

> **MMD モデル（PMX ファイル）を VRChat 用に準備する。**
> → [ガイド3：MMD アバターを VRChat に入れる](02-guides-a.md#guide-3-bring-an-mmd-avatar-into-vrchat)へ。

> **リギング済みアバターのアップロードを妨げるボーン名を修正する。**
> → [ガイド4：アバターのボーン名を修正する](02-guides-a.md#guide-4-fix-your-avatars-bone-names)へ。

> **リギング済みアバターのリップシンク、アイトラッキング、メッシュを VRChat 用に準備する。**
> → [ガイド13：CATS でアバターを VRChat 対応にする](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats)へ。

> **特定の問題の解決策を探す。**
> → [クイック修正インデックス](10-reference.md#quick-fix-index)へ。

次へ：[ガイド1–7](02-guides-a.md)
