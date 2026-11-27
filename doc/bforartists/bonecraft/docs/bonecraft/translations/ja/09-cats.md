# CATSツール {#cats-tools}

[← 目次](index.md)

CATSツールは右サイドバーの **CATS → CATS** セクションにあります。 **N** でサイドバーを表示します。

Preferences → Tabs → Scene Properties → Showが有効なら、 **Properties → Scene** にも表示されます。ビューポートのCATSスイッチとScene Propertiesスイッチは、それぞれの表示を独立して制御します。

各ツールは[ CATSパイプライン](04-cats-pipeline.md)の順に並んでいます。セクション上部で処理するアーマチュアを選択します。

9.1では、いくつかのパネルで、任意の設定を実行ボタンの下の折りたたみ領域へ移しました。必須入力はボタンの上に残っています。Fix Modelの整理スイッチ、Translate Bone Namesの元言語、口のシェイプ、目のボーンなどが該当します。

Adjust Last Operationに対応するボーンツールは、すぐに実行されます。実行後にそこでオプションを調整します。ボタンやオプションにポインターを合わせるとツールチップを読めます。

---

## Fix Model {#fix-model}

 **パイプライン段階：** 1（整理内容の確認を推奨）

 **機能：** 選択したメッシュに、有効な整理処理を実行します。きれいなアバターには変更が不要な場合もあります。

 **オプション（それぞれオフにできます）：**

- モディファイアーを適用。
- Remove doubles — 同じ位置の重複頂点を統合。
- Recalculate normals — 裏返った面を修正。
- Remove loose geometry — 身体につながっていない面を除去。
- 空の頂点グループを除去。
- Remove zero-weight bones — どの頂点も動かさないボーンを除去。
- VRChatが使えないコンストレイントとリジッドボディを除去。

1. 整理オプションを確認します。

2. アバターに必要な処理だけを有効にします。

3. ファイルをチェックポイントとして保存します。

4.  **Fix Model** で、選択したメッシュに有効な処理をまとめて実行します。

5. 続行前に結果を確認します。

英語原本の画像説明（画像は省略）：Fix Modelのオプションと実行操作。パイプラインの最初の段階に進む前に選択を確認します。

*BoneCraft 9.2.18のネイティブパネルのポップオーバー。Fix Modelのオプションと実行操作。パイプラインの最初の段階に進む前に選択を確認します。*

---

## Translate Bone Names {#translate-bone-names}

 **機能：** スケルトンのボーン名を、英語のVRChat用の名前へ翻訳します。既知のボーン名の内蔵辞書を使い、オフラインで動作します。

 **対応言語：** 日本語（MMDや多くのコミュニティモデルで最も一般的）、中国語（中文）、韓国語（한국어）、ポルトガル語（Português）、スペイン語（Español）、フランス語（Français）。

 **主な操作：**

1. 元の名前の **Language** を選択します。

2.  **Translate Bone Names** を選択します。

Languageはモデルのボーン名の言語であり、インターフェースの言語ではありません。日本語のMMDモデルなら、Bforartistsの表示言語に関係なくJapaneseを選択します。

英語原本の画像説明（画像は省略）：Translate Bone Namesの前に元の命名言語を選択。この例では一致する名前はまだ検出されていません。

*BoneCraft 9.2.18のネイティブパネルのポップオーバー。Translate Bone Namesの前に元の命名言語を選択。この例では一致する名前はまだ検出されていません。*

---

## Join Meshes {#join-meshes}

 **機能：** アバターのメッシュオブジェクトを1つに結合します。VRChatではアバターごとにメッシュが1つの場合、最も効率的です。元メッシュのシェイプキーが異なる場合は、不足するキーをニュートラルな形状で補い、結合後に一貫したキーの集合を持たせます。

 **主な操作：** メッシュリスト、更新ボタン、 **Join Meshes** 。

 **使用時期：** 衣服やアクセサリーを取り付け、ウェイトを設定した後。

1. 元メッシュを確認します。

2. 結合前に元メッシュに必要な整理を選びます。

3. ファイルをチェックポイントとして保存します。

4. リストの更新が必要なら、横のボタンで更新します。

5.  **Join Meshes** を選択します。

6. 結合したメッシュ、シェイプキー、ウェイトを確認します。

英語原本の画像説明（画像は省略）：Refresh Mesh Listの後、6ポリゴンのメッシュ1つがチェック付きでリストに表示されています。Join Meshesを選ぶ前に確認します。

*BoneCraft 9.2.19候補版のネイティブテストビルドのポップオーバー。Bforartists 5.2.3、Blender 5.4 Alpha。Refresh Mesh Listの後、6ポリゴンのメッシュ1つがチェック付きでリストに表示されています。Join Meshesを選ぶ前に確認します。*

---

## Material Atlas Combiner {#material-atlas-combiner}

 **パイプライン段階：** 2（任意）

 **機能：** 複数のマテリアルを1枚のテクスチャシート（アトラス）にベイクします。マテリアルを減らすとVRChatのパフォーマンスランクが改善します。

 **場所：**   **CATS → CATS → Material Atlas** 。パネルは **1. Choose Target** 、 **2. Choose Materials and Textures** 、 **3. Bake and Review** に分かれています。

### 解析と入力元の選択 {#analyze-and-choose-sources}

英語原本の画像説明（画像は省略）：解析前のMaterial Atlas。対象を選択し、バックアップを保持してからAnalyze Materialsを実行します。

*BoneCraft 9.2.18のネイティブパネルのポップオーバー。解析前のMaterial Atlas。対象を選択し、バックアップを保持してからAnalyze Materialsを実行します。*

 **Target** は **Active Avatar** 、 **Selected Meshes** 、 **Visible Scene** から選びます。Active Avatarはアクティブなアーマチュアの子メッシュを使います。アーマチュアがアクティブでなければ、アクティブなメッシュを使います。Visible Sceneは表示中のメッシュを使います。特定の組み合わせならSelected Meshesを選択します。

1. ファイルのコピーを保存します。

2.  **Target** で必要な範囲を選択します。

3.  **Preserve Backup Duplicate** を有効のままにします。

4.  **Analyze Materials** を選択します。

5. アトラスグループを選択します。

6. そのグループをベイクするにはチェックボックスを有効にします。

7.  **Materials to combine** で含めるマテリアルを有効にします。

8.  **Texture images** で含める画像を有効にします。

9. 有効にした各グループで入力元の確認を繰り返します。

 **Analyze Materials** は入力元リストを作成します。グループができるとラベルは **Refresh Analysis** に変わります。更新するとリストと選択内容を作り直すため、再確認してください。

各リストに **Select All** と **Deselect All** があります。これらはアクティブなグループの、そのリストの **Include** チェックを変えます。選択行は変えません。マテリアルとテクスチャのリストは独立しています。他のグループの選択は保ちます。不足したテクスチャは未チェックのままです。一括選択で無効なグループが有効になることはありません。

同じ一括操作は **Object → Atlas Source Selection** にもあります。アトラスのプレビューが保留中なら、入力元を変更する前にAcceptまたはRevertを実行します。

有効なグループには、チェック済みのマテリアルが2つ以上必要です。無効なグループやマテリアル1つだけのグループはベイクをスキップします。除外したマテリアルスロットと共有マテリアル参照は別のままです。画像を除外すると、その画像をベイクしません。マテリアル全体が除外されるわけではありません。

透明マテリアルと発光マテリアルは、初めから別グループです。Alpha Blendグループは描画順を保つため、初めは無効です。描画順が変わる可能性を受け入れる場合は有効にします。

 **Source Details** は初めは無効です。有効にするとメッシュ診断、シェイプキーとUVの警告、マテリアルのサイズ、テクスチャの役割、重複入力元グループを確認できます。マテリアルの **Override Size** でサイズの選択肢を表示します。独自サイズは **Width** と **Height** で指定します。色のみのマテリアルは **Fallback** サイズを使います。

グループリストには **Resolution** と追加・削除操作があります。 **Add Group** と **Remove Group** はグループを管理するだけで、それ自体ではベイクしません。

英語原本の画像説明（画像は省略）：2つの作例メッシュから解析した入力元。UV警告を含め、グループ、マテリアル、画像のチェックを確認します。

*BoneCraft 9.2.19候補版。ネイティブのBforartists 5.2.3テストビルド、Blender 5.4 Alpha。2つの作例メッシュから解析した入力元。UV警告を含め、グループ、マテリアル、画像のチェックを確認します。*

### ベイクと確認 {#bake-and-review}

1. 入力元リストを確認したら **Bake Checked Sources** を選択します。

2. 事前検査の要約を読みます。

3. 報告された入力元または設定のエラーを修正します。

4. 予定される変更が正しければベイクを確定します。

5. アトラス、透明度、シェイプキー、出力UVチャンネルを確認します。

6. 結果が正しければ **Accept — Delete Backup** を選択します。

元の状態が必要なら、代わりに **Revert — Restore Originals** を選択します。Acceptはバックアップを削除します。Revertは元のオブジェクト、マテリアル、表示状態を復元し、マテリアル数の結果もリセットします。

英語原本の画像説明（画像は省略）：2つの作例メッシュからベイクした2048ピクセルのOpaqueグループ1つ。パネルはまだマテリアル数2から2、ランクExcellentと報告しています。AcceptまたはRevertの前にUV警告を確認します。

*BoneCraft 9.2.19候補版。公式Bforartists 5.2.3、Blender 5.3 Alpha。2つの作例メッシュからベイクした2048ピクセルのOpaqueグループ1つ。パネルはまだマテリアル数2から2、ランクExcellentと報告しています。AcceptまたはRevertの前にUV警告を確認します。*

 **Preserve Backup Duplicate** は初めから有効です。アトラス化前の複製を表示したまま残し、確認とRevertに使います。無効にするとアトラス化後に元データを削除し、Revert用バックアップは残りません。無効にする前に別ファイルへ保存してください。

再解析や再ベイクの前に現在のプレビューをAcceptまたはRevertで処理します。解析後にオブジェクト、マテリアルスロット、レンダー分類が変わっている場合、バックアップ作成前の事前検査で中止することがあります。

再ベイク前：

1.  **Refresh Analysis** を選択します。

2. 作り直した選択内容を確認します。

 **Smart Combine Materials** は、解析がまだない場合の最初の自動ショートカットです。 **Auto Analyze** が有効なら、ベイク前に解析を作り直します。自動で再解析せず、確認済みの選択でベイクするには **Bake Checked Sources** を使います。古い説明ではこのオペレーターを **Bake Atlas** と呼んでいます。

 **ベイクを開始できない場合：** アトラスのベイクにはCyclesが必要です。BforartistsがCyclesを利用できないと報告する場合は、Cyclesを含む完全なビルドを使ってください。

### Advanced Options {#advanced-options}

 **Advanced Options** は以前のOverride Inherited Settingsという表記を置き換えたものです。任意のワークフロー、ベイク、UV、出力の設定があります。

| 設定 | 用途 |
| --- | --- |
| Auto Analyze | 自動のSmart Combineショートカット用にグループを作り直します。 |
| Debug Report / Copy Debug Report | 診断を有効にし、最新の報告をコピーして問題調査に使います。 |
| Albedo (Color) | 必須のベースカラーのベイクパス。有効のままにします。 |
| Normal Map / Emission / Roughness | 任意の別出力パス。対応する元データとベイク結果を確認します。 |
| Metallic / Pack ORM Channels | このビルドでは事前検査が阻止します。無効のままにします。 |
| Packing Preset / Bake Padding / UV Margin | アトラスアイランドのパディングと間隔を設定します。 |
| Pixel Art No-Bleed / Preserve Island Orientation | パディングの挙動と、対応するアイランド方向の処理を制御します。 |
| UV Method / UV Seed / Rotation Step | 配置方法と変化を選びます。Seedと回転設定は、それを使う方式でのみ表示します。 |
| Keep Source UV Maps | 出力メッシュに元のUVレイヤーを保持します。初めは無効です。 |
| Fallback Size | 画像のない色のみのマテリアルに割り当てるアトラスサイズです。 |
| Format Output | PNG、TGA、EXRから選びます。EXRは1.0を超える発光値を保持します。PNGとTGAは上限で切り詰めます。 |
| Material Output Type / Surface Output | 生成マテリアルの描画方式とサーフェスシェーダーを選択します。 |
| Path Output | 出力テクスチャのフォルダーを設定します。 |

 **Keep Source UV Maps** が無効なら、最終アトラスメッシュはFBX、Unity、VRChat向けのUV0として`atlas_uv`を使います。有効にすると`atlas_uv`がUV1になる場合があります。元マップを保持する場合はエンジン側のUVチャンネルを確認してください。作成済みUVのない色のみのメッシュにも、生成したアトラスUVレイヤーを付けます。

### 保持されるものと制限 {#preservation-and-limits}

このコンバイナーは、接続されたPrincipledの色合い、テクスチャマッピング、アルファをベイク時に保持します。レンダーで非表示の入力メッシュは一時的なベイク用コピーで処理します。除外したマテリアル参照は他のオブジェクトと共有したままです。組み立て時も形状の位置、シェイプキー、親子関係を保護します。

VRM / MToonマテリアルは専用のフォールバック経路を保ちます。透明の分類では実際のアルファのノード構成とテクスチャのアルファを考慮します。DITHEREDというレンダー設定だけでは透明と分類しません。ベイク後に問題のあるタイルがマゼンタになる場合があります。Acceptの前に確認してください。

記載した修正は、生成したテスト用データによるホスト検査を行っています。すべての制作アバターやシェーダーノード構成を保証するものではありません。表示されるファイルブラウザーの動作、実ウィンドウの配置、対話的な取り消し・やり直しには、記録された検証範囲の制限が残ります。過去の[修正記録](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-fixes-2026-10-23.md)と[9.2.15 UIレビュー](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-ui-review-9.2.15.md)を参照してください。

 **系譜のクレジット：** このワークフローはCATS統合の系譜を継ぎ、原作のCats Blender Pluginをクレジットしています。Material Combinerの系譜はGrim-es/material-combiner-addonをクレジットしています。UVワークフローはAlexander BelyakovのUV ToolkitとoRazeD/UVToolkitのアーカイブリポジトリを参考にしています。BoneCraftは独自のアトラスUVヘルパーを実装し、UVToolkitのソースは含みません。

---

## Visemes {#visemes}

 **パイプライン段階：** 3

 **機能：** 3つの基本的な口形からVRChatの15種類のビジームを作成します。

 **生成前：**   **A Shape** 、 **O Shape** 、 **CH Shape** のそれぞれに入力元の割り当てが必要です。各欄には既存の口のシェイプキー名を指定します。

 **手動で入力元を選ぶ場合：**

1.  **A Shape** で入力元キーを選択します。

2.  **O Shape** で入力元キーを選択します。

3.  **CH Shape** で入力元キーを選択します。

 **自動の代替手段：** 代わりに **Auto-Detect** を選択します。

 **どちらの選択方法でも、その後に：**

1. 3つの入力元欄すべてが既存のキー名になっているか確認します。

2. 必要ならボタンの下のOptionsを展開します。

3. 必要なら既存ビジームの上書き設定を変更します。

4.  **Generate Visemes** を選択します。

[ガイド13、段階2](03-guides-b.md#phase-2--viseme-generation)を参照してください。

英語原本の画像説明（画像は省略）：CATS Visemes。Generate Visemesの前にA、O、CHの入力元シェイプを選ぶか、Auto-Detectを使います。

*BoneCraft 9.2.18のネイティブパネルのポップオーバー。CATS Visemes。Generate Visemesの前にA、O、CHの入力元シェイプを選ぶか、Auto-Detectを使います。*

---

## Eye Tracking {#eye-tracking}

 **パイプライン段階：** 4（Fix Modelの後に実行）

Auto-Detectは一般的な目のボーン名を探します。メッシュの形状やボーン位置は使いません。

1.  **Left Eye** と **Right Eye** を確認します。

2. 未割り当てなら、そのボーンを手動で選択します。

ボーンを改名した場合：

1. 検出を再実行します。

2. 両方の割り当てを再確認します。

目の動きが正しくない場合は、ボーンの向き、コンストレイント、出力したアバターを確認します。

 **機能：** 目のボーンを見つけ、VRChatが求める`LeftEye`と`RightEye`へ改名します。VRChatで目を動かすための回転コンストレイントを作成します。

 **主な操作：**

-  **Auto-Detect**  — 一般的な左右の目のボーン名を探します。
-  **Left Eye** 、 **Right Eye**  — 手動で選ぶ場合の目のボーン。
-  **Up Limit** 、 **Down Limit** 、 **Side Limit**  — 目が回転できる角度（度）。
-  **Create Eye Tracking**  — ボーンを改名し、コンストレイントを作成します。

英語原本の画像説明（画像は省略）：ボーン検出前のEye Tracking。例の制限は上30度、下20度、横30度です。

*BoneCraft 9.2.19候補版のネイティブテストビルドのポップオーバー。Bforartists 5.2.3、Blender 5.4 Alpha。ボーン検出前のEye Tracking。例の制限は上30度、下20度、横30度です。*

---

## Pose & Shape Keys {#pose--shape-keys}

 **パイプライン段階：** 5（任意）

### Pose to Shape Key {#pose-to-shape-key}

現在のボタンは、選択メッシュの **現在のシェイプキーの組み合わせ** を取り込みます。アーマチュアのボーンによる変形はベイクしません。

1. Object Modeに切り替えます。

2. 対象メッシュを選択します。

3. 取り込みたい組み合わせになるよう、既存のシェイプキーの値を設定します。

4.  **Pose to Shape Key** を選択します。

5. 名前を入力します。

6. 操作を確定します。

7. 元のシェイプキーの値を0へ戻します。

8. 新しいキーだけを確認します。

新しいキーの値を1に設定しますが、元のキーも有効のままです。元の値を残すと、その変形が再び加算されます。

### ボーンで変形したポーズを保存する {#save-a-bone-deformed-pose}

アーマチュアのボーンによる変形を保存するには、次の標準機能を使います。モディファイアーはメッシュのトポロジーを保つ必要があります。

 **Save as Shape Key** はArmatureモディファイアーを保持します。 **Apply as Shape Key** は削除します。

1. アーマチュアのポーズを付けます。

2. ファイルをチェックポイントとして保存します。

3. Object Modeへ戻ります。

4. 変形したメッシュを選択します。

5.  **Properties → Modifiers** を開きます。

6. Armatureモディファイアーのドロップダウンメニューを開きます。

7.  **Save as Shape Key** を選択します。

8. ボーンのポーズをリセットします。

9. 元のシェイプキーの値もリセットします。

10. 新しいキーの値を1にします。

11. 新しいキーだけで結果を確認します。

ボーンのポーズや元のキーの組み合わせが有効のままだと、変形が再び加算されます。この標準操作では、BoneCraftのPose To Shapeのパイプライン完了印は更新されません。

英語原本の画像説明（画像は省略）：標準のArmatureモディファイアーメニューでは、Save as Shape KeyとApply as Shape Keyが別の操作です。

*BoneCraft 9.2.19候補版のローカルプレビュー。Bforartists 5.2.3、Blender 5.4 Alpha。実行前の標準Armatureモディファイアーメニュー。Save as Shape Keyはモディファイアーを保持します。この画像はポーズを取り込んだ結果を示していません。*

### Shape Key to Basis {#shape-key-to-basis}

アクティブなBasis以外のシェイプキーを新しいBasisにします。他のキーも、そのBasisに対する相対値になるよう調整します。

1. 実行前にファイルをチェックポイントとして保存します。

2. 実行後に残ったキーを確認します。

英語原本の画像説明（画像は省略）：Pose to Shape Keyは現在のキーの組み合わせを取り込みます。Shape Key to Basisはアクティブなキーを新しいBasisにします。

*BoneCraft 9.2.18のネイティブパネルのポップオーバー。Pose to Shape Keyは現在のキーの組み合わせを取り込みます。Shape Key to Basisはアクティブなキーを新しいBasisにします。*

---

## Transforms & FBT {#transforms--fbt}

 **パイプライン段階：** 6（最後）

### Apply All Transforms {#apply-all-transforms}

メッシュとアーマチュアに位置、回転、スケールを適用し、トランスフォームのチャンネルをリセットします。前の段階のツールも引き続き使えます。

1. 実行前にファイルをチェックポイントとして保存します。

2. 実行前後のアバターを比較します。

出力後に大きさが違う場合は、メッシュとアーマチュアのトランスフォーム、出力時と読み込み時のスケール設定を確認します。

### Fix FBT {#fix-fbt}

Full Body Tracking用のトランスフォーム修正です。ルートボーンを床の高さに移動します。

### Remove FBT {#remove-fbt}

Fix FBTの修正を取り除きます。

英語原本の画像説明（画像は省略）：Apply All Transforms、Fix FBT、Remove FBTはパイプラインの最後の操作です。

*BoneCraft 9.2.18のネイティブパネルのポップオーバー。Apply All Transforms、Fix FBT、Remove FBTはパイプラインの最後の操作です。*

---

## Bone Tools {#bone-tools}

-  **Create Root Bone**  — 階層の最下部に、 **Root Name** で指定した名前のルートボーンを追加します。
-  **Merge Bones**  —  **Merge Threshold** より短いボーンを親へ統合します。
-  **Duplicate Bones**  — 選択したボーンを複製します。

英語原本の画像説明（画像は省略）：Create Root Bone、Merge Bones、Duplicate Bones。実行後にルート名やしきい値を調整します。

*BoneCraft 9.2.18のネイティブパネルのポップオーバー。Create Root Bone、Merge Bones、Duplicate Bones。実行後にルート名やしきい値を調整します。*

---

## Armature Tools {#armature-tools}

 **機能：** 例えば衣服のアーマチュアを身体のアーマチュアへ統合するなど、1つのアーマチュアを別のものへ統合します。

 **主な操作：**

-  **Base / Root**  — 残すアーマチュア。結果もこの名前を保ちます。
-  **Incoming**  — ベースへ統合するアーマチュア。同名のボーンはベース側へ統合します。
- Naming Prep — 統合前に2つのリグのボーン名を合わせます。Mixamo以外からのリグを含め、どのリグにも使えます。
- ボーンの自動親子付けと、その後のメッシュ結合のオプション。
-  **Merge Incoming Into Base**  — 統合を実行します。

Naming Prepの手順：

1. Mixamo Prefixedを選択します。

2.  **Normalize Merge Names** を選択します。

3. Mixamo Strippedを選択します。

4. もう一度 **Normalize Merge Names** を選択します。

両方のリグが同じ名前になります。

プレビューを使う段階的な統合はBone Mergeを使います（[Rig Builder](06-rig-builder.md#bone-merge)を参照）。

英語原本の画像説明（画像は省略）：BaseとIncomingのアーマチュアを選び、Naming Prepを確認してからMerge Incoming Into Baseを実行します。

*BoneCraft 9.2.18のネイティブパネルのポップオーバー。BaseとIncomingのアーマチュアを選び、Naming Prepを確認してからMerge Incoming Into Baseを実行します。*

---

## Mesh Tools {#mesh-tools}

-  **Separate by Materials**  — マテリアルごとにメッシュを分離。
-  **Separate by Loose Parts**  — つながった部分ごとにメッシュを分離。
-  **Separate by Shape Keys**  — シェイプキーで動く部分を切り離します。

英語原本の画像説明（画像は省略）：マテリアル、分離した部分、シェイプキーでメッシュを分離。

*BoneCraft 9.2.18のネイティブパネルのポップオーバー。マテリアル、分離した部分、シェイプキーでメッシュを分離。*

---

## Smart Automatic Weights {#smart-automatic-weights}

 **Smart Automatic Weights** は、適切な初期値と非表示のバックアップを使うダイアログを開きます。

1. 対象のメッシュとアーマチュアを確認します。

2. 既存のリグからウェイトを再計算するならBodyを選択します。

3. ウェイト付きの元メッシュから転送するなら、代わりにClothingを選択します。

 **Advanced Recalculation** は、 **BoneCraft → Skin → Weight Tools** への場所の案内を展開します。この場所に詳細設定を開くわけではありません。[Rig Tools](05-rig-tools.md#automatic-bone-weight-recalculation)を参照してください。

英語原本の画像説明（画像は省略）：Smart Automatic Weightsは設定ダイアログを開きます。Advanced Recalculationは詳細なウェイト操作の場所を案内します。

*BoneCraft 9.2.18のネイティブパネルのポップオーバー。Smart Automatic Weightsは設定ダイアログを開きます。Advanced Recalculationは詳細なウェイト操作の場所を案内します。*

---

## Pipeline StatusとOperation Ledger {#pipeline-status-and-operation-ledger}

Pipeline Statusは6段階の完了状況を表示します。Operation Ledgerは各CATS操作の時刻と結果（Changed、Clean、Failed）を列挙します。 **Copy** は台帳をクリップボードへコピーし、 **Clear** は空にします。[CATSパイプライン](04-cats-pipeline.md)を参照してください。

次：[よくある問題の対処と用語集](10-reference.md)
