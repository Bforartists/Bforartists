# VRChatツール {#vrchat-tools}

[← 目次](index.md)

## VRChatツール {#vrchat-tools-1}

VRChat用ツールは、右サイドバーの **CATS** タブ内、 **Avatar Tools** セクションにあります。 **N** でサイドバーを表示します。Avatar Toolsにはヒューマノイドボーン、髪の物理、Viseme Library / Lip Syncがあります。VRChatへの出力はCATS → Import / Export → Unity / VRChatです。その下にある別の **VRChat Tools** セクションには、Check Performance、Attach Clothing、Facial、VRChat Naming Extrasをまとめています。Preferences → Tabs → Scene Properties → Showがオンなら、このセクションは **Properties** エディターの **Scene** タブにも表示されます。このスイッチでビューポートのCATSタブは隠れません。

---

### Set Up Humanoid Bones {#set-up-humanoid-bones}

スケルトンのボーンをVRChatのヒューマノイドスロットに対応付け、マッピングを検証します。

[ガイド5：アバターをVRChatの身体システムに対応付ける](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system)を参照してください。

英語原本の画像説明（画像は省略）：Auto-Map Allの実行前の必須ヒューマノイドスロット。対応付け後に各スロットを確認し、残った空欄を埋めます。

*BoneCraft 9.2.18のネイティブパネルのポップオーバー。Auto-Map Allの実行前の必須ヒューマノイドスロット。対応付け後に各スロットを確認し、残った空欄を埋めます。*

---

### Add Hair Physics {#add-hair-physics}

髪、耳、尾、アクセサリーにPhysBoneチェーンとコライダーを設定します。

[ガイド6：髪に物理を追加する](02-guides-a.md#guide-6-add-hair-physics)を参照してください。

英語原本の画像説明（画像は省略）：Hair Physicsのチェーン、生成操作、プリセット、コライダー操作。物理を適用する前に検出したチェーンを確認します。

*BoneCraft 9.2.19候補版のネイティブテストビルドのポップオーバー。Bforartists 5.2.3、Blender 5.4 Alpha。Hair Physicsのチェーン、生成操作、プリセット、コライダー操作。物理を適用する前に検出したチェーンを確認します。*

---

### Attach Clothing {#attach-clothing}

 **場所：** CATSタブ → VRChat Tools → Clothing

衣服をアバターのスケルトンへ統合し、ウェイトを転送します。

[ガイド7：身体と一緒に動く衣服を付ける](02-guides-a.md#guide-7-attach-clothing-that-moves-with-your-body)を参照してください。

英語原本の画像説明（画像は省略）：Clothingの操作とPre-Mergeの選択順。衣服を統合する前にボーンを対応付け、ボーン名の衝突を確認します。

*BoneCraft 9.2.19候補版のローカルプレビュー。Bforartists 5.2.3、Blender 5.4 Alpha。Clothingの操作とPre-Mergeの選択順。衣服を統合する前にボーンを対応付け、ボーン名の衝突を確認します。*

---

### VRChat Naming Extras {#vrchat-naming-extras}

 **場所：** CATSタブ → VRChat Tools → Naming

 **機能：** スケルトンの命名形式を検出し、ボーン名を一括変更します。

[ガイド4：アバターのボーン名を修正する](02-guides-a.md#guide-4-fix-your-avatars-bone-names)を参照してください。

 **一括操作：**   **Find and Replace** 、 **Add Prefix** 、 **Remove Prefix** 、 **Add Suffix** 、 **Remove Suffix** 、 **Regex Replace**

英語原本の画像説明（画像は省略）：この例ではNamingがUnity Humanoidを確信度16/24で検出しています。一括操作を使う前に名前を確認します。

*BoneCraft 9.2.19候補版のローカルプレビュー。Bforartists 5.2.3、Blender 5.4 Alpha。この例ではNamingがUnity Humanoidを確信度16/24で検出しています。一括操作を使う前に名前を確認します。*

---

### VRChat Viseme Mapping {#vrchat-viseme-mapping}

 **場所：** CATS → VRChat Tools → Facial。Face Trackingも同じセクションにあります。

 **機能：** メッシュのシェイプキーをVRChatの15種類のリップシンク用ビジームに対応付けます。

[ガイド8：リップシンクを設定する](03-guides-b.md#guide-8-set-up-lip-sync)を参照してください。アバターにまだないビジームの作成は、[CATSツール：Visemes](09-cats.md#visemes)を参照してください。

 **VRChatの15ビジームスロット：** `sil`、`PP`、`FF`、`TH`、`DD`、`kk`、`CH`、`SS`、`nn`、`RR`、`aa`、`E`、`I`、`O`、`U`

英語原本の画像説明（画像は省略）：対応付け前のVisemeスロットとFace Tracking。この例ではビジームが未対応で、55種類の表情のうち0個が対応付けられています。

*BoneCraft 9.2.19候補版のローカルプレビュー。Bforartists 5.2.3、Blender 5.4 Alpha。対応付け前のVisemeスロットとFace Tracking。この例ではビジームが未対応で、55種類の表情のうち0個が対応付けられています。*

---

### Check Performance {#check-performance}

 **場所：** CATSタブ → VRChat Tools → Performance

 **機能：** アバターのVRChatパフォーマンスランクを測定し、修正を提示します。

[ガイド9：アバターのパフォーマンスを改善する](03-guides-b.md#guide-9-improve-your-avatars-performance)を参照してください。

 **ランク（良い順）：** Excellent → Good → Medium → Poor → Very Poor

 **ツール：**

-  **Calculate Performance Rank**  — 現在のランクと、ポリゴン、スキンメッシュ、マテリアルスロット、ボーン、PhysBone、Contact別の内訳を表示します。
- 最適化には **Remove Zero-Weight Bones** 、 **Merge Same-Material Meshes** 、 **Remove Unused Shape Keys** 、 **Remove Unused Vertex Groups** があります。 **What-If Mode** はこれらの修正で何が変わるかを表示します。
- VRChat Decimation — シェイプキーを保護しながら、指定した比率でポリゴン数を減らします。

VRChat Decimationの手順：

1. アバターのメッシュを選択します。
2.  **Preview** を選択します。
3.  **Apply** を選択します。

英語原本の画像説明（画像は省略）：パフォーマンス指標とWhat-Ifの操作。メッシュの整理操作を使うにはアバターのメッシュを選択します。

*BoneCraft 9.2.18のネイティブパネルのポップオーバー。パフォーマンス指標とWhat-Ifの操作。メッシュの整理操作を使うにはアバターのメッシュを選択します。*

英語原本の画像説明（画像は省略）：PreviewまたはApply前のDecimation設定。この例はRatio 0.50とShape Key Safetyを使用しています。下の整理操作ではWhat-If Modeが有効です。

*BoneCraft 9.2.19候補版のローカルプレビュー。Bforartists 5.2.3、Blender 5.4 Alpha。PreviewまたはApply前のDecimation設定。この例はRatio 0.50とShape Key Safetyを使用しています。下の整理操作ではWhat-If Modeが有効です。*

---

### Export to VRChat {#export-to-vrchat}

 **機能：** 完成したアバターを、UnityのVRChat SDK向けのFBXとして出力します。 **Remove Shape Keys** がオンでなければ、シェイプキー（ブレンドシェイプ）を保持します。

 **設定：**

-  **Folder**  — 出力先フォルダー。
-  **Avatar**  — 出力ファイル名。
-  **Sidecar**  — BoneCraftのUnityインポーター用の`.bfvrc`設定ファイルも書き出します。
-  **Merge Meshes**  — 出力用コピーのメッシュを1つに結合します。
-  **Separate Clothing**  — 衣服を別メッシュとして保持します。
-  **Remove Shape Keys**  — 出力用コピーのBasisへシェイプキーを適用します。
-  **Embed Textures**  — Unityで見つかるよう、テクスチャをFBXに埋め込みます。
-  **Helper Meshes**  — 非表示または補助用のメッシュを含めます。通常のアバターではオフにします。
-  **Bone Names**  —  **Keep Original Names** 、 **Unity-Preset** 、 **Unreal-Preset** から選び、出力用コピーに適用します。

 **場所：** CATS → Import / Export → Game Engine Export → Unity / VRChat。

出力前：

1. 必須スロットが不足していれば、ここで **Auto-Map Humanoid** を実行します。
2. スロットを確認します。

出力前にパフォーマンスを確認するには **Check Performance Rank** を選択します。 **Bone Names** プリセットを使う前に、マッピングや名前の衝突を修正してください。詳しくは後述の「出力時のボーン命名」を参照してください。出力前にリンクされたオブジェクトをローカル化します。 **Export to VRChat (Unity)** でFBXを書き出します。

 **Normalize Names** は作業中のリグを改名します。 **Bone Names** プリセットは出力用コピーを改名します。

Unity/VRChatの出力はアニメーションなしのレストポーズです。メインのUnityとUnreal出力ボタンはObject、Pose、Edit Modeで使えます。一時的にObject Modeを使い、その後、元のモードと選択を復元します。

英語原本の画像説明（画像は省略）：フォルダーとヒューマノイドマッピングを設定する前のUnity / VRChat設定。この例では必須15スロット中0個が対応付けられています。

*BoneCraft 9.2.19候補版のローカルプレビュー。Bforartists 5.2.3、Blender 5.4 Alpha。フォルダーとヒューマノイドマッピングを設定する前のUnity / VRChat設定。この例では必須15スロット中0個が対応付けられています。*

---

### 整理 {#cleanup}

出力前のメッシュ整理はCATSツールの **Fix Model** 、 **Join Meshes** 、 **Apply All Transforms** で行います。[CATSツール](09-cats.md)を参照してください。

---

## VRMブリッジ {#vrm-bridge}

VRMツールは **CATS** タブ →  **Import / Export**  →  **VRM / VRoid** にあります。VRMアドオンが必要です。無効なブリッジには **Auto-Install Latest from GitHub** 、 **Open Add-on Preferences** 、 **Website** 、 **Show Manual Instructions** が表示されます。

オフラインのパッケージは標準のPreferencesから導入します。従来型のアドオンZIPは **Add-ons → Install from Disk…** 、新しい拡張機能パッケージは標準のExtensionsのインストールメニューを使います。

1. 対応する標準メニューからパッケージをインストールします。
2. 必要な依存アドオンを有効にします。
3. ブリッジの表示が **Active** になったことを確認します。

無効なハブカードにはZIPのインストールボタンはありません。

英語原本の画像説明（画像は省略）：この例では、どちらの形式ブリッジも有効になっていません。必要なブリッジを導入すると、その読み込みと書き出しの操作が表示されます。

*BoneCraft 9.2.19候補版のローカルプレビュー。Bforartists 5.2.3、Blender 5.4 Alpha。この例では、どちらの形式ブリッジも有効になっていません。必要なブリッジを導入すると、その読み込みと書き出しの操作が表示されます。*

---

### VRMとVRoidの読み込み {#vrm-and-vroid-import}

 **機能：** `.vrm`アバター（VRoid Studio、Virtual CastなどのVRMアバター）を、マテリアル、スケルトン、シェイプキーとともに読み込みます。

-  **Import VRM…**  — `.vrm`ファイル。
-  **Import VRoid (.vroid / .zip)…**  — VRoid Hubからのダウンロード（`.zip`）。VRoid Studioのプロジェクト（`.vroid`）には、先にVRMへ出力する方法を説明するカードを表示します。

---

### VRMの出力 {#vrm-export}

 **機能：** リギング済みのキャラクターをVRM、または対象アプリ用の形式へ出力します。

 **設定：**

-  **Folder** と **File**  — 出力先とファイル名。拡張子は対象に応じて決まります。
-  **Target**  — VRM 1.0、VRM 0.x、VRChat FBX、VSeeFace、Warudo、Resonite。
-  **Scope**  — アクティブなアーマチュア、またはVRMデータを持つすべてのアーマチュア。
- Skip lint — 対象向けのチェックをせずに出力します。報告されたリスクを理解している場合だけ使用してください。

 **Export…** をクリックします。

---

### VRM Lint {#vrm-lint}

 **機能：** 出力前に、選択した対象に対してアーマチュアを検査します。ヒューマノイドマッピング、VRMメタデータ、対象のビジーム、対象アプリの要件を検査します。

 **Lint Now** は何も変更せずに検査します。lintをスキップしない限り、エラーがあれば出力を止めます。警告は、対象アプリで取り込めてもパフォーマンスが下がる可能性のある内容を示します。

実在するヒューマノイドボーンが不足と報告されたら、 **Fix Humanoid Map** をクリックします。BoneCraftはスロットを再検出してマッピングを保存します。ボーン名は変更しません。

 **同じ場所の機能：**   **Convert SpringBones → PhysBones** （VRoidの髪の物理をVRChat向けに変換）、 **Map VRoid Visemes** 。

---

## MMDブリッジ {#mmd-bridge}

MMDツールは **CATS → Import / Export → MMD / PMX** にあります。 **mmd_tools** のインストールと有効化が必要です。BoneCraftは従来型パッケージと新しいBlender Extensionsの両方を認識します。

無効なブリッジには **Auto-Install Latest from GitHub** 、 **Open Add-on Preferences** 、 **Website** 、 **Show Manual Instructions** があります。独立したブリッジの内容を表示した場合は **Install from .zip on Disk...** もあります。インストールとローカル拡張リポジトリの確認は[ガイド3](02-guides-a.md#step-1--install-mmd_tools)を参照してください。

---

### MMDの読み込み {#mmd-import}

-  **Import PMX / PMD...**  — MMDモデル。
-  **Import VMD Motion...**  — MMDアニメーション。
-  **Import VPD Pose...**  — MMDポーズ。

読み込みが正常に完了したことを確認します。PMXの読み込みをキャンセルした場合やインストールエラーがある場合、タスクは未完了です。読み込んだモデルは、変換前にマテリアルやボーンマッピングの確認が必要な場合があります。

---

### MMDの出力 {#mmd-export}

 **設定：**   **Folder** は出力先です。各形式にファイル名と範囲の設定があります。

-  **PMX File** と **PMX Scope** 。
-  **VMD File** と **VMD Scope** 。
-  **VPD File** と **VPD Scope** 。

各範囲は、アクティブなモデル、またはシーンのすべてのMMDモデルから選びます。

 **ボタン：**   **Export PMX...** 、 **Export VMD Motion...** 、 **Export VPD Pose...**

 **同じ場所の機能：**   **Convert Bone Names -> Unity** 、 **Convert Physics -> PhysBones** 。

---

## ゲームエンジンへの出力 {#game-engine-export}

 **Game Engine Export** は **CATS → Import / Export** 内に直接表示される領域で、 **Unity / VRChat** と **Unreal Engine 5** を含みます。別の **Game Export** 子パネルでは、検証付きのプロファイル出力を行えます。

### Unreal Engine 5 {#unreal-engine-5}

 **Bake Anim** が有効なら、アクティブなアクションをベイクします。別のNLAストリップは不要です。無関係なアクションをすべて出力するわけではありません。

 **Bone Names** プリセットを使う前に、マッピングや名前の衝突を修正してください。詳しくは後述の「出力時のボーン命名」を参照してください。出力前にリンクされたオブジェクトをローカル化します。

1. アーマチュアとそのメッシュを選択します。
2.  **CATS → Import / Export → Game Engine Export → Unreal Engine 5** を開きます。
3.  **Folder** を設定します。
4.  **File** にFBX名を設定します。
5.  **Bone Names** とそのプレビューを確認します。
6. アクティブなアニメーションも出力するなら **Bake Anim** を有効にします。
7.  **Export to Unreal (FBX)** をクリックします。

 **Selected Only** は初めから有効です。メッシュと一緒にアーマチュアも含めてください。 **Unit Scale** は初めから有効、 **Leaf Bones** は無効、 **Embed Textures** は有効です。パネルでは **Bake Animation** を **Bake Anim** と略記します。

 **Import from Unreal (FBX)** は読み込み用ファイルブラウザーを開きます。

英語原本の画像説明（画像は省略）：出力フォルダーを選ぶ前のUnreal Engine 5設定。出力前にBone Names、Selected Only、Bake Animを確認します。

*BoneCraft 9.2.19候補版のローカルプレビュー。Bforartists 5.2.3、Blender 5.4 Alpha。出力フォルダーを選ぶ前のUnreal Engine 5設定。出力前にBone Names、Selected Only、Bake Animを確認します。*

### 出力時のボーン命名 {#export-bone-naming}

両エンジンのセクションに同じ **Bone Names** の選択肢があります。

| 選択肢 | 出力結果 |
| --- | --- |
| Keep Original Names | 既存のボーン名を保持します。既定値です。 |
| Unity-Preset | `Hips`、`LeftUpperArm`、`LeftIndexProximal`など、認識したUnity Humanoidの名前を使います。 |
| Unreal-Preset | `pelvis`、`spine_01`、`upperarm_l`、`index_01_l`、`ball_l`など、認識したUnrealヒューマノイドの名前を使います。 |

アーマチュアを選択すると、 **Recognized / renamed** の件数と最大3件の変更案をプレビューします。認識できないボーンの名前はそのままです。

保存済みのヒューマノイドマッピングは、名前による検出より優先します。認識した任意の胸、首、肩、目、顎、指、足指のボーンも対象です。別のルートとして認識した`Root`は、 **Unreal-Preset** で`root`になります。

変更先の名前の衝突、曖昧なボーン、ヒューマノイドスロットの重複使用があると改名を止めます。出力前にマッピングまたは名前の衝突を修正してください。BoneCraftは衝突を解決するために`.001`接尾辞を追加しません。

出力前にリンクされたオブジェクトをローカル化します。プリセットが改名するのは一時的な出力用コピーです。作業中のリグのボーン名は保ちます。出力する頂点グループ、アニメーションチャンネル、Unityサイドカーのボーン参照も選んだ名前に従います。成功時も失敗時も一時データを削除します。

これらのプリセットが変更するのは名前だけです。階層、ボーンの向き、レストポーズは保ちます。不足する関節の追加や、完全なManny/Quinnスケルトンの構築は行いません。UnityのAvatarマッピングやUnrealのリターゲットが引き続き必要な場合があります。

### 検証付きプロファイル出力 {#validated-profile-export}

 **機能：** Unreal humanoidまたはuniversal、Unity humanoid、Godot humanoid、generic FBX、GLBの検証付きプロファイルで出力します。検出結果リストには利用できる修正が表示されます。修正は明示的に操作した場合にだけ実行します。

このプロファイルのワークフローはObject Modeで行ってください。Object/Pose/Editのモード復元保証は、メインの2つのエンジン出力ボタンに適用されます。

 **Bone Names** プリセットを使う前に、マッピングや名前の衝突を修正してください。詳しくは前述の「出力時のボーン命名」を参照してください。出力前にリンクされたオブジェクトをローカル化します。

 **ファイルブラウザーの設定：**   **Profile** 、 **Animation** 、 **Bone Names** 、 **Root Motion** 、 **Interpolation** 、 **T-Pose** 。 **Bone Names** の初期値はUnrealセクションの選択に従います。出力形式のプロファイルは別の選択です。

命名プリセットを使う場合は **Active Action** または **No Animation** を選びます。 **All Actions** は他のリグのアクションを含む可能性があるため、 **Keep Original Names** が必要です。

既定の **T-Pose** はプロファイルに従います。Unity humanoidとVRChatのプロファイルはTポーズを使います。Tポーズ出力にはアニメーションなしのレストポーズが含まれます。モデリング時のレストポーズが必要なら **Export as modelled** を選択します。

1. アーマチュアとそのメッシュを選択します。
2.  **CATS → Import / Export → Game Export** を開きます。
3.  **Check for Export** をクリックします。
4. 検出結果と明示的な修正を確認します。
5.  **Export (Profile)** をクリックします。
6. ファイルブラウザーで設定を選択します。
7. 出力ファイルを選択します。
8. 出力を確定します。

英語原本の画像説明（画像は省略）：確定前のプロファイル出力設定。この例はGeneric FBX、Active Action、Keep Original Namesを使用しています。

*BoneCraft 9.2.19候補版のローカルプレビュー。Bforartists 5.2.3、Blender 5.4 Alpha。確定前のプロファイル出力設定。この例はGeneric FBX、Active Action、Keep Original Namesを使用しています。*

 **ボタン：**

-  **Check for Export**  — プロファイルに対してリグを検査し、結果を列挙します。
-  **Apply Transforms (Fix)**  — 検査で提示される明示的な修正の1つです。
-  **Export (Profile)**  — プロファイルを使って出力します。

 **場所：**   **CATS** タブ →  **Import / Export**  →  **Game Export**

命名の詳細と過去のホスト検証は、[独立した出力時の命名ガイド](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/export-bone-naming.md)を参照してください。

英語原本の画像説明（画像は省略）：Check for Export、明示的な修正、Export (Profile)。この例ではまだプロファイル検査結果はありません。

*BoneCraft 9.2.18のネイティブパネルのポップオーバー。Check for Export、明示的な修正、Export (Profile)。この例ではまだプロファイル検査結果はありません。*

---

## Task Board {#task-board}

 **機能：** 現在のリグを、健全性スコア、すぐに改善できる項目、分類別タスクで要約します。タスクには不足するヒューマノイドボーン、未解決の名前、不足するビジーム、Rig Validatorの警告が含まれます。 **Quick Wins** は最大3件の推奨タスク、 **Remaining Tasks** はそれ以外のタスクだけを表示します。 **Open Health Check** は検証を実行して結果を開きます。 **Refresh Task Board** は再検査します。

 **場所：**   **BoneCraft** タブ →  **Overview**  →  **Task Board**

英語原本の画像説明（画像は省略）：アクティブな作例リグについて、Task Boardが健全性の検出結果と簡単な操作を列挙しています。

*BoneCraft 9.2.18のネイティブパネルのポップオーバー。アクティブな作例リグについて、Task Boardが健全性の検出結果と簡単な操作を列挙しています。*

---

### Bone Inspector {#bone-inspector}

 **機能：** アクティブなポーズボーンのレスト時の寸法、親、コンストレイント、カスタムデータ、ドライバー、スキンウェイトを表示します。

情報は読み取り専用です。Pose Modeでボーンをアクティブにしてパネルを開きます。名前をコピーするにはヘッダーの **Copy Name** を選びます。

 **場所：**   **BoneCraft** タブ →  **Review**  →  **Bone Inspector**

英語原本の画像説明（画像は省略）：Bone Inspectorはレストボーンの詳細、コンストレイント、カスタムデータ、ドライバー、スキンウェイトを表示します。ヘッダーにはCopy Nameがあります。

*BoneCraft 9.2.19候補版のネイティブテストビルドのポップオーバー。Bforartists 5.2.3、Blender 5.4 Alpha。Bone Inspectorはレストボーンの詳細、コンストレイント、カスタムデータ、ドライバー、スキンウェイトを表示します。ヘッダーにはCopy Nameがあります。*

次：[CATSツール](09-cats.md)
