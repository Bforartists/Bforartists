# 更新履歴 {#whats-new}

[← 目次](index.md)

新しいものから順に掲載しています。

## 9.2.19 — パネル操作（ローカル候補版） {#9219--panel-controls-local-candidate}

このローカル候補版は未公開です。単独配布の公開版は引き続き9.2.18です。

- CollectionsとVisibility Bookmarksは、パネル描画の外で設定を初期化します。
- グループ化したパネルは独自の操作を使い、現在の選択とモードを確認します。
- Hair Physicsは現在のホストで選択中のポーズボーンを読み取ります。
- Bone Inspectorはレストボーンのロールを表示し、ヘッダーのボタンで名前をコピーします。
- Eye Trackingは保存済み設定を保ちながら、値を度で表示します。

英語マニュアルでは、ツールと設定に対応する画像を追加しています。以前の画像は元のバージョン表記を保っています。

## 9.2.18 — 保存済みのメカニズムフォーム {#9218--saved-mechanism-forms}

以前に保存したフォームを、現在のBforartistsビルドでも読み込み、利用できます。フォームを開いたり適用したりしても再保存はしません。 **Save Form** は現在の形式で現在の値を記録します。既存のハンドル、スライダー、パネルの場所は変わりません。

このリリースは新しいホストでの互換性診断を修正します。その診断だけで、以前のホストが保存済みフォームを使えなかったと証明されたわけではありません。[フォーム](07-mechanisms.md#forms)と[リリースノート](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.18/RELEASE-NOTES.md)を参照してください。

これはToolkitの単独リリースです。公式Bforartistsへの採用を示すものではありません。過去のスクリーンショットとチュートリアルの検証範囲は、各章に記載したままです。

## 9.2.17 — 出力時の命名とモード復元 {#9217--export-naming-and-mode-restoration}

 **Unity / VRChat** と **Unreal Engine 5** に **Bone Names** を追加し、 **Keep Original Names** 、 **Unity-Preset** 、 **Unreal-Preset** から選べるようにしました。プレビューは認識したボーンと提案名を表示します。改名は頂点グループ、アニメーションチャンネル、Unityサイドカー参照を含む出力用コピーに適用します。作業中のリグの名前は保ちます。

メインの2つのエンジン出力ボタンはObject、Pose、Edit Modeで使えます。出力または後処理の後、元のモードと選択を復元します。アクティブアクションのFBXベイクには、別のNLAストリップが不要になりました。

認識した任意のヒューマノイドボーン、指、足指も命名の対象です。名前の衝突や曖昧なマッピングがあると改名を止めます。これらのプロファイルは階層、向き、レストポーズを保ちます。Manny/Quinnスケルトンを構築するものではありません。

 **Export (Profile)** の改名付き出力は **Active Action** と **No Animation** に対応します。 **All Actions** には **Keep Original Names** が必要です。[ゲームエンジンへの出力](08-vrchat.md#game-engine-export)と[9.2.17のノート](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.17/RELEASE-NOTES.md)を参照してください。

## 9.2.15 — 確認を挟むマテリアルアトラスのワークフロー {#9215--reviewed-material-atlas-workflow}

パネルは対象の選択、マテリアルとテクスチャの選択、ベイクと確認の3段階になりました。 **Smart Combine Materials** は初回の自動ショートカットです。解析後は **Refresh Analysis** でリストを作り直します。 **Bake Checked Sources** は確認した選択内容をベイクします。

両方の入力元リストに **Select All** と **Deselect All** があります。変更するのは、アクティブなグループと入力元リスト内のIncludeチェックだけです。不足したテクスチャは未チェックのままです。一括選択は無効なグループを有効にしません。 **Object → Atlas Source Selection** にも同じ操作があります。

 **Source Details** は初めは折りたたまれています。 **Copy Debug Report** は **Advanced Options** の中にあります。バックアップ、Accept、Revertは表示したままです。これらのUI変更は、既存のベイク手順と保持の制約を変えません。

## 9.2.14 — 色のみのメッシュ {#9214--color-only-meshes}

作成済みのUVを持たない色のみのメッシュにも、最終組み立て時にベイクしたアトラスUVレイヤーを付けます。

## 9.2.13 — マテリアル数 {#9213--material-counts}

マテリアルの推定と結果は、すべての出力メッシュのアトラススロットを数えます。Revertで結果をリセットします。

## 9.2.12 — 出力のUV0 {#9212--export-uv0}

 **Keep Source UV Maps** が無効なら、再構築したアトラスメッシュは`atlas_uv`をUV0として出力します。元のマップを保持すると、アトラスがUV1になる場合があります。

## 9.2.11 — 入力元の変更検査 {#9211--changed-source-checks}

事前検査は、解析したマテリアル入力元の不足や変更を、アトラスのバックアップを作る前に拒否します。

1. 解析を更新します。

2. 入力元の選択を再確認します。

## 9.2.10 — 除外したマテリアル {#9210--excluded-materials}

アトラスの組み立ては、除外したマテリアルと共有マテリアル参照を保持します。

## 9.2.9 — レンダーで非表示の入力元 {#929--render-hidden-sources}

コンバイナーは一時コピーを使って、レンダーで非表示の入力元をベイクします。Revertは元の表示状態を復元します。

## 9.2.8 — 接続されたシェーダー入力 {#928--connected-shader-inputs}

コンバイナーは、接続されたPrincipledの色合い、マッピング、アルファのノード構成をベイク時に保持します。MToonは専用のフォールバック経路を保ちます。 **Metallic** と **Pack ORM Channels** は、引き続き事前検査で阻止します。

## 9.2.7 — 透明度の分類 {#927--transparency-classification}

マテリアル分類は、新しいDITHEREDの不透明度と、接続されたアルファまたは定数のアルファを処理します。レンダー設定だけを理由に、不透明なマテリアルを透明グループに入れなくなりました。

## 9.2.6 — MMDとPMXの導入 {#926--mmd-and-pmx-installation}

インストーラーは新しいMMD Extensionsと従来型アドオンを認識します。拡張機能の導入では依存関係を保持し、使えないローカルリポジトリを報告します。従来型のアドオンメタデータがなくても、有効な拡張機能を認識します。キャンセルされたPMXの読み込みは、成功と報告せず、キャンセルのままにします。

[日付付きの修正記録](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-fixes-2026-10-23.md)は、9.2.6–9.2.15と生成テストデータによる検査を扱います。[9.2.15 UIレビュー](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-ui-review-9.2.15.md)は、オペレーターの検査と視覚検証の限界を記録しています。これらの過去の記録は、9.2.18でマニュアル全体を新たに再実行したという主張ではありません。

## 9.2.5 — Starter Rigsのカタログタブ {#925--starter-rigs-catalog-tab}

Starter Rigsは、標準の下部アセットシェルフに1つのカタログタブを使うようになりました。左上のビューポート操作を置き換えます。他のカタログと並べて表示するには、シェルフのカタログメニューで一度 **Starter Rigs** を有効にします。標準のアセット読み込みと **Add → Armature → Starter Rig Catalog** も引き続き使えます。

## 9.2.4 — Task Boardと標準ツール {#924--task-board-and-native-tools}

 **Open Health Check** はリグ検証を実行して結果を開くようになりました。使用前にアーマチュア、またはそれにバインドしたメッシュを選択します。 **Quick Wins** は最大3件の推奨項目を表示します。 **Remaining Tasks** にはそのカードを重複表示しません。 **Refresh Task Board** で再検査します。

Place Rig MarkersとBuild Mechanismは引き続きビューポートツールとして利用できます。その登録によって、Object/Poseモードの標準Grab/Moveやツール切り替えが壊れることはなくなりました。

## 9.2.3 — VRChat出力の場所 {#923--vrchat-export-location}

Avatar Tools内の重複したExport to VRChatパネルを削除します。出力は引き続きCATS → Import / Export → Unity / VRChatにあります。

## 9.2.2 — 現在のインターフェース {#922--current-interface}

各タブにはワークスペースのグループがあります。Setup Rigging、Skin、Review、Avatar Tools、Facialは、タブ内で展開できるセクションです。以下の経路は英語のUIラベルです。翻訳ラベルはLanguage環境設定に依存します。

- Bone Merge → BoneCraft → Setup Rigging
- Delta Mush / Proximity Wrap → BoneCraft → Skin
- Viseme Library / Lip Sync → CATS → Avatar Tools
- VRChat Viseme Mapping / Face Tracking → CATS → VRChat Tools → Facial

## 9.2.0（2026年10月） {#920-october-2026}

-  **完全なスターターカタログ：** 同梱の9種類のスケルトン／メタリグすべてに、初めからサムネイルがあります。Basic Humanoid、Simple Human、Full Human、Basic Quadruped、Cat、Horse、Wolf、Bird、Sharkです。カタログの選択はHumans、Quadrupeds、Other Animalsに分類されています。
-  **必要なときだけRigify：** Basic Humanoidは独立して動きます。Rigifyが無効でもRigify用スターターは表示されます。選択すると **Enable Rigify & Add Rig** またはCancelを提示します。キャンセル、有効化の失敗、プリセットが使えない場合にはリグを追加しません。
-  **任意のシェルフ、過去の9.2.0での場所：** ビューポートヘッダーの **Starter Rigs** スイッチが通常のアセットシェルフに戻りました。選択は環境設定に保存されました。9.2.5ではこのスイッチを標準のカタログタブで置き換えています。 **Add → Armature → Starter Rig Catalog** は、引き続きポップアップの選択画面を開きます。
-  **クリックまたはドラッグ：** スターターはクリックでも、ビューポート内へのドロップでも追加できます。メッシュへのフィットは初めから有効、ウェイト付けとコントロール生成は無効です。Adjust Last Operationで設定します。標準のクリック、ドロップ、キャンセル、取り消し・やり直しの検査はBforartists 5.2.0で行いました。

## 9.1.2（2026年10月） {#912-october-2026}

-  **Scene Propertiesスイッチ：** Preferences > TabsにScene Properties行を追加しました。Showボタンは、Properties > Sceneタブ内のBoneCraft全セクションを制御します。対象はRig Builder、Mechanisms、CATS、Avatar Tools、VRChat Tools、Import / Exportです。初めから有効で、有効時は青く表示します。アドオンを無効にしたり、ビューポートのタブやArmatureタブを変更したりはしません。[各機能の場所](01-start.md#where-things-are)を参照してください。

## 9.1.1（2026年10月） {#911-october-2026}

-  **明確なアイコン：** 各アイコンの意味をインターフェース全体で統一しました。約60個のボタンを、機能に合ったBforartistsアイコンに変更しました。例はApply All Transforms、Decimate、Normalize Names、Translate、Merge、Separate、Blend Pose、Lip Syncです。同じボタンはどのパネルでも同じアイコンです。
-  **落ち着いたパネル：** 見出しや固定文からトピック用アイコンを外しました。状態を報告するヒントには、情報、警告、チェックのアイコンを使います。
-  **読みやすいアイコングリッド：** PoseとWeightsのTool Shelfタブでは、すべてのボタンに独自のアイコンがあり、狭いシェルフでも読み取れます。

## 9.1.0（2026年10月） {#910-october-2026}

-  **Bforartistsの標準機能と同じ場所に：** Add → ArmatureとPose、Weights、Objectメニューに項目を追加します。BforartistsのPose/Weights Tool Shelfタブにもボタンパネルを追加します。
-  **実行してから調整：** Quick Rig、Fit Dropped Rig、ウェイトツールは前回の値ですぐに実行します。Ribbon、Spline IK、Delta Mush、CATSのボーンツールも同様です。その後にAdjust Last Operationで設定を調整します。確認ポップアップを減らしました。
-  **実行を先に、設定は折りたたむ：** いくつかのパネルは、任意の設定を折りたたみ、その上にボタンを表示します。必須入力とFix Modelの整理スイッチは実行操作より上です。設定はボタンではなくチェックボックスを使います。パネル見出しにアイコンはありません。
-  **ジェスチャーツール：** Place Rig MarkersとBuild Mechanismをビューポートのツールバーに配置しました。Place Rig Markersは、メッシュをクリックするとAuto-Rig Wizardの次のマーカーを置きます。Build Mechanismはパーツのクリックでジョイントまたはリンクを開始します。
-  **アバターのセクション、過去の9.1.0での場所：** Avatar Toolsにはヒューマノイドマッピング、髪、ビジーム、出力がありました。別のVRChat ToolsにはPerformance、Clothing、Namingの機能をまとめています。現在の出力は **Import / Export → Game Engine Export → Unity / VRChat** にあります。
-  **ツールチップ：** すべてのオペレーターとオプションが、それぞれの機能を説明します。
-  **隠さず案内：** リグがなくてもセクションを表示し、選択する対象を説明します。Auto-Rig WizardはRig Builderの先頭です。シェルフは読みやすい幅で開始します。
-  **修正：** Generate Spline IKが再び動作します。Add Influenceは選択したボーンを使います。ビジームのプレビューは対応するセットを使います。

## 9.0.0（2026年10月） {#900-october-2026}

-  **Mechanisms：** BoneCraftタブとPropertiesのSceneタブの新セクションで、小道具や機械をリギングします。種類はHinge、Slide、Telescope、Piston、Gear Link、Follow、Sequenceです。案内に従って生成し、Testで動きを確認します。手動変更は自動で上書きしません。 **Keep mine** は変更を保持し、 **Restore** はメカニズムを再生成します。[Mechanisms](07-mechanisms.md)を参照してください。
-  **作例ファイル：** `examples/crescent-rose/`にはMechanismsでリギングしたCrescent Rose（鎌、ライフル、収納形態）があり、マニュアルの[第12章](12-crescent-rose.md)で順に作成します。
-  **タブの配置：** 各ビューポートタブは、左のTool Shelfまたは右のサイドバーに配置できます（Preferences → Tabs → Left / Right）。初期状態ではBoneCraftとRig Builderが左、CATSが右です。
-  **Rig Builder：** 常にPropertiesのSceneタブに表示し、独自のビューポートタブもあります。コンパクトな配置で狭いTool Shelfに収まります。BoneCraft RigsアセットライブラリにはBasic Humanoidがあります。Fit Dropped Rigは、アセットシェルフからドロップしたリグをフィットします。
-  **CATSタブ：** Import / ExportをCATSタブへ移しました。CATS、VRChat、Import / ExportはSceneタブにも常にあります。
-  **Show Helpers：** 1つの環境設定で、BoneCraftの学習用説明を表示または非表示にします。Compact Modeも同じ設定を制御します。
-  **Rig Validator：** ハイフン付きのボーン名を許可します。ドライバーはPythonが必要な式だけに警告します。Mechanismsリグも検査します。Task Boardの検証タスクも再び報告します。
-  **名称：** アドオン名はBoneCraftです。

## 8.9.x（2026年9月–10月） {#89x-septemberoctober-2026}

-  **8.9.6：** スカートのボーンにドレス全体が追従し、腰の食い込みを防ぎます。顎を開くときの口角補正はsticky lipsに対応します。
-  **8.9.5：** 肘のIK/FK切り替えでポーズが飛ばなくなりました。肩の検出は左右対称です。目のマーカーが急に移動しなくなりました。Control Pickerは選択を表示します。このほか、丸みのある口角、太ももに重なるドレスの補正、リターゲット時の自然な鎖骨、Tポーズ出力があります。
-  **8.9.4：** Preserve Volumeを補正シェイプで置き換え、膝を丸くします。深い曲げ用の接触キーと肩の縫い目のブレンドも追加します。
-  **8.9.3：** 2節のスカートボーンが脚に追従します。脚はこのボーンを押すこともできます。
-  **8.9.2：** シェイプキーで、まぶたの折れのないまばたきを作ります。口の開きは楕円形です。
-  **8.9.1：** 高密度メッシュのスキニングを高速化しました（678,000頂点：232秒から57秒）。Bone Heatは黙って失敗する代わりに、軽量な代理メッシュを使います。
-  **8.9.0：** 関節の補正シェイプキー、目の向き、まばたき、唇の追従用の顔コントロールを追加します。衣服は関節と一緒に曲がります。
- 8.9では、ボーンウェイトの自動再計算と、より明確なアトラス選択も追加しています。

## 8.7–8.8（2026年9月） {#8788-september-2026}

-  **8.8.0：** Blender 5ホストでリターゲットパネルが動作します。指のマーカー配置は手の形を使います。このほか、皮膚まで伸びるIK、Preserve Volumeオプション、Delta Mushのバインド修正があります。
-  **8.7.0：** 統合コントロールリグ、四肢をたどる関節検出、方向を合わせたリターゲット、ツイストボーンを追加します。

## 8.5–8.6（2026年7月） {#8586-july-2026}

-  **8.6.1–8.6.3：** Material Atlasはベイク後のタイル診断と、混在マテリアルのより適切な分割を追加します。MToonの透明度を実際のテクスチャのアルファと照合し、アトラス化でも保持します。
-  **8.5.5–8.5.10：** VRM / MToonマテリアルはアルファモードを尊重します。Blender 5ホストでアルファが動作します。このほか、過剰な発光の防止、マゼンタの診断表示、安全なアトラス名があります。
-  **8.5.4：** ヒューマノイドマッピングを正しく読み込みます。Naming Prepの案内も追加します。
-  **8.5.2–8.5.3：** VRoidダウンロード（.zip）の読み込みと、VRoidプロジェクトの引き継ぎカードを追加します。
-  **8.5.1：** FBX出力でブレンドシェイプを保持します。

## 以前のバージョン {#earlier-versions}

 **8.5.0：** ベイク後、Smart Combineは既定で`atlas_uv`を出力のUV0にします。Advanced設定の **Keep Source UV Maps** を有効にしていなければ、生成したアトラスメッシュからアトラス化前の元UVマップを削除します。公開Blenderビルドでも、CATS / Material Combiner / UVToolkit由来の操作を共有するようになりました。制作向けのリギング、コントロール、リターゲット／出力、B4Artists専用リリースの仕組みは、引き続きB4Artists限定です。

8.5.0では出力と検証も更新します。VRChat、VRM、MMD、Unrealの出力に、BoneCraftのパネル内でフォルダーとファイル名を設定できるようになりました。出力設定はBlenderのファイルブラウザーの既定値だけに依存しません。VRChat/UnityとUnrealのFBX出力は、マテリアルを取り込みやすくするため、既定で **Embed Textures** を有効にします。 **Helper Meshes** を有効にしない限り、VRChat出力は補助／コントロール形状用メッシュをFBXから除外します。VRMパネルには **Lint Now** と **Fix Humanoid Map** を追加します。Fix Humanoid Mapは、ボーン名を変えず、出力前に古いヒューマノイドの別名マッピングを修正します。

 **8.4.5：** Smart Combineはベイク中、元のテクスチャが保持したアトラス化前のUVを参照するようにします。元データを隠す前に生成したアトラスメッシュを検証します。全アトラス面を最終アトラスマテリアルのスロットへ設定し直します。これにより、ローブや衣服の部分が灰色になったり乱れたりするのを防ぎます。

 **8.4.4：** Material Atlas Combinerは品質をそろえるため、ベイク前の確認操作を追加します。シェーダー／マテリアル診断、テクスチャの役割ラベル、重複／共有入力元の印、マテリアル別のサイズ指定、配置プリセットがあります。任意の出力ベイクはNormal/Emission/Roughnessに対応します。Metallic/ORMのチャンネルパッキングは、その経路の検証が済むまで事前検査で止めます。

 **8.4.3：** Material Atlas Combinerは既存のワークフローにUV配置方式の選択を追加します。Smart Pack、Grid Pack、Seeded Variation、Oriented Pack、Fit 0-1 Bounds、Advanced Variation、Rotation Stepから選べます。デバッグ報告とベイク台帳にUV方式の詳細を記録します。

 **8.4.2：** Material Atlas Combinerはベイク中、生成したアトラスUVを対象にします。コピーした元テクスチャノードは、明示的にアトラス化前のUVを読みます。元テクスチャとベイク済みアトラスが異なるUVマップを参照することで生じる、ローブや衣服のアトラス不具合を修正します。8.4.1のマテリアルとテクスチャの選択行は引き続き使えます。

 **7.1.3（環境設定のラベル整理）：** アドオン環境設定の2つのスイッチを、サイドバーのタブに合う名前へ変更しました。「VRChat Avatar Tools」はCATSサイドバーの **CATS** 、「Task Board & Sidebar」はRig Builderサイドバーの **Rig Builder** になります。変更したのはEdit > Preferences > Add-ons > BoneCraft内のラベルだけで、ツールは削除していません。

 **7.1.1：** VRChatアバターの整理、最適化、設定に向け、完全なCATSツール群を追加します。CATSには独自のサイドバータブがあり、パイプラインが操作順を案内します。

次：[チュートリアル：MechanismsでCrescent Roseを作る](12-crescent-rose.md)
