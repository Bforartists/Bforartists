# ガイド1–7 {#guides-17}

[← 目次](index.md)

## ガイド1：最初のアバターを VRChat に入れる {#guide-1-get-your-first-avatar-into-vrchat}

練習用メッシュには、[文章によるマネキンのワークショップ](06-rig-builder.md#illustrated-mannequin-workshop)を使ってください。Simple Human、リグのないマネキン、Auto-Rig、IK/FK の順に進みます。

> **所要時間：** 初回の全手順で約45–60分
> **結果：** リギング済みで VRChat 対応のアバターを、VRChat SDK 用に書き出します。

**始める前の確認：**

- [ ] 3Dモデルを Bforartists に読み込んでいる（File > Import で形式を選択）。
- [ ] モデルがTポーズ（両腕を横に広げ、体を起こした姿勢）、またはそれに近い。
- [ ] 明らかに壊れた形状がない（無関係な三角形が浮いていない）。
- [ ] 3Dビューポートで、モデルが灰色の立体として見える。

---

### 手順1 — Rig Builder を開く {#step-1--open-the-rig-builder}

1. 3Dビューポートで **T** を押して、左のツールシェルフを表示します。

2. **Rig Builder** を開きます。

Preferences → Tabs → Scene Properties → Show が有効なら、**Properties → Scene** にも Rig Builder が表示されます。構成は、**Auto-Rig Wizard**、Quick Rig（作成済みアーマチュア）、**Mannequin** の3つです。

3. **Auto-Rig Wizard** を展開します。

4. **Start Auto-Rig** を選択します。

3Dビューポートの Add → Armature → Auto-Rig Wizard メニューから開始し、その後 Rig Builder で続ける方法もあります。

英語原本の画像説明（画像は省略）：Rig Builder タブの Auto-Rig Wizard。

*過去のワークショップのキャプチャー。Rig Builder タブの Auto-Rig Wizard。*

---

### 手順2 — メッシュを選択する {#step-2--select-your-mesh}

ウィザードに、シーン内のメッシュが一覧表示されます。

1. 一覧でアバターのメッシュを選択します。

2. **Next** を選択します。

**確認できる表示：** 「Selected:」の行にメッシュ名が表示され、リグの種類を選ぶ手順に進みます。

英語原本の画像説明（画像は省略）：Auto-Rig Wizard の入力メッシュを選択します。

*過去のワークショップのキャプチャー。Auto-Rig Wizard の入力メッシュを選択します。*

---

### 手順3 — リグの種類を選択する {#step-3--choose-the-rig-type}

1. まばたき、表情、リップシンクを使うには、**Body + Face** を選択します。

2. 顔の操作項目がない体だけのリグには、**Body Only** を選択します。

3. Generation Options で、**Kinematics** を IK/FK、IK only、FK only のいずれかにします。

4. **Next** を選択します。

英語原本の画像説明（画像は省略）：体のリグの種類と IK/FK の方式を選択します。

*過去のワークショップのキャプチャー。体のリグの種類と IK/FK の方式を選択します。*

---

### 手順4 — 体のマーカーを配置する {#step-4--place-body-markers}

マーカーは、骨盤、背骨、首、頭、肩、腕、手、脚、足を示します。BoneCraft は、その位置を使ってボーンを作ります。各マーカーを慎重に確認してください。

**Smart Detection：**

1. **Detect Markers** を選択します。

2. 信頼度の高いマーカーを保持するには、**Accept High** を選択します。

3. 信頼度の低いマーカーを消して手動で配置するには、**Reset Low** を選択します。

BoneCraft はメッシュの手足をたどり、各マーカーに信頼度を割り当てます。一方、**Guess Markers from Mesh** は、メッシュの比率から位置を推定します。

**ビューポートツールを使う場合：**

1. オブジェクトモードで、ビューポートのツールバーの Place Rig Markers を有効にします。

2. メッシュをクリックし、ツールヘッダーに名前が表示されたマーカーを配置して確定します。

3. 次の未確定マーカーでも繰り返します。

4. マーカーの手順が完了したら、ウィザードで **Next** を選択します。

ツールヘッダーには、軸のロックとミラーの切り替えもあります。

**1つずつ配置する場合：** 各マーカーの行には、アイコンボタンがあります。ボタンにマウスを重ねると、ツールチップを読めます。

1. マーカーの行にある矢印アイコン **Place Marker** を選択します。

2. アバター上の必要な位置をクリックします。

3. 位置が正しければ、チェックマークの **Confirm Marker** を選択します。

円形矢印の **Reset Marker** は、配置済みマーカーを消し、再配置できるようにします。

**対称：** **Toggle Symmetry** は、マーカーを配置するとき、反対側にも配置します。左右のマーカー行の最初のアイコンです。**Mirror L to R** と **Mirror R to L** は、確定済みの全マーカーを反対側にコピーします。

1. 全マーカーを配置したら、**Confirm All Placed** を選択します。

2. **Next** を選択します。

英語原本の画像説明（画像は省略）：検出された体のマーカーを、調整する前に確認します。

*過去のワークショップのキャプチャー。検出された体のマーカーを、調整する前に確認します。*

---

### 手順5 — 指のマーカーを配置する {#step-5--place-finger-markers}

1. Finger Detail で、指の数を「0 — No Fingers」から「5 — Full Human Hand」の間で選択します。

2. **Guess Finger Markers** を選択します。

3. マーカーの位置が誤っていれば調整します。

4. **Next** を選択します。

BoneCraft は手の形状を使い、指の付け根から先端まで各指をたどります。標準的な手には「5 — Full Human Hand」を使います。

---

### 手順6 — 顔のマーカーを配置する（Body + Face のみ） {#step-6--place-face-markers-body--face-only}

1. **Guess Face Markers** を選択します。

2. 必要に応じて、目、まぶた、眉、口角、顎を調整します。

3. **Next** を選択します。

目のマーカーには、手動で割り当てた位置が保持されます。

---

### 手順7 — 確認して生成する {#step-7--review-and-generate}

確認の手順には、警告と生成オプションが表示されます。**Generate Rig** をクリックします。

**確認できる表示：** アバター内に、IK/FK の手足や指を含むオレンジ色のボーンが表示されます。Body + Face リグには、顔のリグもあります。ボーンを動かすと、関連付けたスキンが変形します。

最後の手順には、**Build Control Rig** と **Close Wizard** があります。Build Control Rig は、Generate Rig が適用しない確認画面のオプションを適用します。両方の操作は、[Rig Builder](06-rig-builder.md)で説明します。

> **スキンウェイト** は、メッシュの各部分をどのボーンが動かすかを定めます。BoneCraft はウェイトを自動設定します。調整には、[リグツール](05-rig-tools.md)の Weight Tools を使ってください。

英語原本の画像説明（画像は省略）：生成前に、リグの設定を確認します。

*過去のワークショップのキャプチャー。生成前に、リグの設定を確認します。*

---

### 手順8 — VRChat のヒューマノイドボーンに対応付ける {#step-8--map-to-vrchats-humanoid-bones}

1. **N** を押して、右のサイドバーを表示します。

2. **CATS → Avatar Tools → Set Up Humanoid Bones** を開きます。

3. **Auto-Map All** を選択します。

4. **Normalize Names** を選択します。

5. **Validate** を選択します。

Auto-Map All は、ボーンを VRChat の体のスロットに結び付けます。Normalize Names は、対応付けたボーンを VRChat が期待する名前にします。

**確認できる表示：** Hips、Spine、Head、LeftUpperArm などの必須スロットに、それぞれボーンが表示されます。スロットは、ガイド5で説明します。

[ヒューマノイドの対応付けの操作項目](08-vrchat.md#set-up-humanoid-bones)を参照してください。

---

### 手順9 — VRChat 用に書き出す {#step-9--export-for-vrchat}

[Unity / VRChat の書き出し設定](08-vrchat.md#export-to-vrchat)を参照してください。

1. アバターのアーマチュアを選択します。
2. **CATS → Import / Export → Game Engine Export → Unity / VRChat** を開きます。
3. **Folder** を設定します。
4. **Avatar** を書き出し名にします。
5. **Bone Names** を選択します。
6. プリセットを使う場合は、命名のプレビューを確認します。
7. **Export to VRChat (Unity)** をクリックします。

既定は **Keep Original Names** です。**Unity-Preset** と **Unreal-Preset** は、書き出し用コピー内の認識されたボーンの名前を変更します。作業用リグの名前は保持されます。

メインの Unity と Unreal の書き出しボタンは、オブジェクトモード、ポーズモード、編集モードで使用できます。以前のモードと選択を復元します。

競合、対応付け、アニメーションの制限は、[書き出し時の命名と制限](08-vrchat.md#export-bone-naming)を参照してください。

**確認できる結果：** 選択したフォルダーに、Unity の VRChat Creator Companion と VRChat SDK に渡せるアバターが書き出されます。

---

**次にできること：** リギング済みの VRChat アバターができました。髪の物理（ガイド6）、衣装（ガイド7）、リップシンク（ガイド8）、パフォーマンス確認（ガイド9）へ進めます。CATS のクリーンアップと VRChat の設定は、[ガイド13](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats)を参照してください。

---

## ガイド2：VRoid アバターを VRChat に入れる {#guide-2-bring-a-vroid-avatar-into-vrchat}

> **所要時間：** 約15–25分
> **結果：** VRoid アバターを VRChat 書き出し用に準備します。

**始める前の確認：**

- [ ] VRoid Studio からアバターを `.vrm` ファイルとして書き出しているか、VRoid Hub から `.zip` としてダウンロードしている。
- [ ] BoneCraft がインストールされ、有効になっている。

---

### 手順1 — VRM アドオンをインストールする {#step-1--install-the-vrm-add-on}

BoneCraft が `.vrm` ファイルを読むには、VRM アドオンが必要です。

1. **CATS → Import / Export → VRM / VRoid** を開きます。

2. 読み込み前に、依存アドオンをインストールします。

3. 依存アドオンを有効にします。

無効なブリッジには、**Auto-Install Latest from GitHub**、**Open Add-on Preferences**、**Website**、**Show Manual Instructions** があります。

オフラインパッケージの場合：

1. 標準の Preferences を開きます。

2. 旧方式のアドオン ZIP は、**Add-ons → Install from Disk…** からインストールします。

3. 新方式の拡張機能パッケージは、標準の Extensions のインストールメニューを使います。

4. ブリッジに戻ります。

5. ブリッジが **Active** と表示することを確認します。

[形式ブリッジのインストール操作項目](08-vrchat.md#vrm-bridge)を参照してください。

---

### 手順2 — アバターを読み込む {#step-2--import-your-avatar}

1. **VRM / VRoid** で、**Import VRM…** を選択します。

2. `.vrm` ファイルを選択します。

VRoid からダウンロードした場合：

1. 代わりに **Import VRoid (.vroid / .zip)…** を選択します。

2. ダウンロードした `.zip` ファイルを選択します。

VRoid Studio のプロジェクトファイル（`.vroid`）を選ぶと、「VRoid Studio Project」カードが表示されます。プロジェクトは、まだアバターではありません。

そのプロジェクトファイルを使うには：

1. VRoid Studio で、プロジェクトを VRM に書き出します。

2. その VRM ファイルを読み込みます。

**確認できる表示：** スケルトンを備えた VRoid キャラクターが、ビューポートに表示されます。

---

### 手順3 — VRChat のヒューマノイドボーンに対応付ける {#step-3--map-to-vrchats-humanoid-bones}

1. **CATS → Avatar Tools → Set Up Humanoid Bones** を開きます。

2. **Auto-Map All** を選択します。

VRoid のスケルトンは標準的な構造に従うため、通常は全スロットが埋まります。誤りがある場合は、**VRM / VRoid** の Lint の下にある **Fix Humanoid Map** を選択します。よくある VRoid の名前の対応付けエラーを修正します。

---

### 手順4 — ボーン名を修正する {#step-4--fix-bone-names}

**Set Up Humanoid Bones** で、**Normalize Names** を選択します。対応付けたボーンの VRoid 名を、VRChat が期待する名前に置き換えます。

---

### 手順5 — ビジーム（リップシンク）を設定する {#step-5--set-up-visemes-lip-sync}

VRoid アバターには、リップシンク用の口形がすでにあります。**VRM / VRoid** で **Map VRoid Visemes** をクリックします。BoneCraft が VRoid のシェイプキーを、VRChat のリップシンク用口形に対応付けます。

---

### 手順6 — 髪の物理（任意） {#step-6--hair-physics-optional}

VRoid の髪は SpringBones を使います。**VRM / VRoid** の **Convert SpringBones → PhysBones** で、VRChat の PhysBones に変換します。髪の物理の詳細は、ガイド6を参照してください。

---

### 手順7 — 書き出す {#step-7--export}

ガイド1の手順9と同様に書き出します。

**次にできること：** VRoid アバターを VRChat Creator Companion に渡す準備ができました。アップロード前に、パフォーマンスも確認できます（ガイド9）。

---

## ガイド3：MMD アバターを VRChat に入れる {#guide-3-bring-an-mmd-avatar-into-vrchat}

> **所要時間：** 約20–30分
> **結果：** MMD の `.pmx` モデルを、VRChat 用に準備します。

**始める前の確認：**

- [ ] `.pmx` または `.pmd` の MMD モデルファイルがある。
- [ ] BoneCraft がインストールされている。

---

### 手順1 — mmd_tools をインストールする {#step-1--install-mmd_tools}

BoneCraft が MMD ファイルを読むには、**mmd_tools** が必要です。旧方式のアドオンと、新方式の Blender Extensions の両方を認識します。

1. **CATS → Import / Export → MMD / PMX** を開きます。
2. ブリッジが依存アドオンの欠落を報告したら、**Auto-Install Latest from GitHub** をクリックします。
3. インストール済みだが無効なものは、**Open Add-on Preferences** で有効にします。
4. 読み込む前に、ブリッジが **Active** と表示することを確認します。

手動でインストールする場合：

1. 無効なブリッジのカードで、**Website** または **Show Manual Instructions** を選択します。

2. **Preferences → Get Extensions** から、公式の MMD 拡張機能をインストールします。

オフライン ZIP の場合：

1. 新方式の拡張機能パッケージは、拡張機能のインストールメニューを使います。

2. 旧方式のアドオンパッケージは、代わりに **Add-ons → Install from Disk…** を使います。

単体版ブリッジの画面には、表示される場合、**Install from .zip on Disk...** もあります。

インストールが、ローカル拡張機能リポジトリがないと報告する場合：

1. **Preferences → Get Extensions → Repositories** を開きます。

2. ローカルリポジトリを追加または有効にします。

3. インストールを再試行します。

上流のリリースパッケージを使ってください。インストールエラーや、読み込みのキャンセルは、読み込み成功には数えません。

[形式ブリッジのインストール操作項目](08-vrchat.md#vrm-bridge)を参照してください。

---

### 手順2 — PMX ファイルを読み込む {#step-2--import-your-pmx-file}

1. **MMD / PMX** で、**Import PMX / PMD...** を選択します。

2. モデルを選択します。

**確認できる表示：** 日本語のボーン名を持つ MMD キャラクターが、ビューポートに表示されます。

---

### 手順3 — ボーン名を修正する {#step-3--fix-bone-names}

VRChat に書き出す前に、MMD ボーンを Unity のヒューマノイドスロットに対応付けます。

1. **MMD / PMX** で、**Convert Bone Names -> Unity** を選択します。

他の言語の名前の場合：

1. **CATS → CATS → Translate Bone Names** を開きます。

2. 元の **Language** を選択します。

3. **Translate Bone Names** を選択します。

---

### 手順4 — モデルをクリーンアップする {#step-4--clean-up-the-model}

MMD モデルには、余分な形状や分離したパーツがあることがよくあります。

1. **CATS → CATS** を開きます。

2. **Fix Model** のオプションを確認します。

3. アバターに必要なクリーンアップ操作を選択します。

4. **Fix Model** を実行します。

5. **Join Meshes** を選択し、VRChat 向けに推奨される、体の各パーツを1つのメッシュにまとめる操作を行います。

CATS パイプライン全体は、[ガイド13](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats)で説明します。

---

### 手順5 — VRChat のヒューマノイドボーンに対応付ける {#step-5--map-to-vrchats-humanoid-bones}

1. **CATS → Avatar Tools → Set Up Humanoid Bones** を開きます。

2. **Auto-Map All** を選択します。

3. 空のスロットがあれば、そのボタンを選択します。

4. 対応するボーンを選択します。

MMD のスケルトンは VRChat のスケルトンに似ているため、多くのスロットは自動で埋まります。

---

### 手順6 — 物理と書き出し {#step-6--physics-and-export}

**MMD / PMX** の **Convert Physics -> PhysBones** は、MMD の剛体による髪とスカートの物理を、VRChat の PhysBones に変換します。その後、ガイド1の手順9と同様に書き出します。

**次にできること：** MMD アバターを VRChat 用に準備できました。アップロード前に、髪の物理（ガイド6）やリップシンク（ガイド8）を設定できます。

---

## ガイド4：アバターのボーン名を修正する {#guide-4-fix-your-avatars-bone-names}

> **所要時間：** 約5–15分
> **結果：** VRChat が必要とするボーンを、VRChat 対応の名前に変更します。

**始める前の確認：**

- [ ] アバターを開き、スケルトン（アーマチュア）が見えている。

---

### 手順1 — 現在の命名方式を検出する {#step-1--detect-the-current-naming-style}

[命名の操作項目](08-vrchat.md#vrchat-naming-extras)を参照してください。

1. **CATS → VRChat Tools** を開きます。

2. Naming で、**Detect** を選択します。

3. 名前を変更した後は、**Force Rescan** を選択して再確認します。

BoneCraft が、Mixamo、VRoid、Unity などの検出した命名方式と、スコアを報告します。

日本語、中国語、韓国語、ポルトガル語、スペイン語、フランス語のボーン名の場合：

1. **CATS → CATS → Translate Bone Names** を開きます。

2. 元の **Language** を選択します。

3. **Translate Bone Names** を選択します。

認識された名前を英語に変換します。

---

### 手順2 — VRChat の名前に変更する {#step-2--rename-to-vrchat-names}

書き出し時だけ命名を変えるには、作業中の名前を保持し、書き出しセクションで **Unity-Preset** を選びます。[書き出し時のボーン命名](08-vrchat.md#export-bone-naming)を参照してください。

1. ガイド5の手順2に従って、ボーンを対応付けます。

2. **Set Up Humanoid Bones** で、**Normalize Names** を選択します。

対応付けた全ボーンに、VRChat が期待する名前が付きます。

**確認できる表示：** `Hips`、`Spine`、`Chest`、`LeftUpperArm` などのボーン名。

---

### 手順3 — 手動修正（必要な場合） {#step-3--manual-fixes-if-needed}

**VRChat Tools** の Naming グループには、残ったボーン用の一括ツールもあります。

- **Find and Replace** — 全ボーン名の一部の文字列を、別の文字列に置き換えます。
- **Add Prefix** と **Add Suffix** — 全ボーン名の先頭または末尾に文字列を追加します。
- **Remove Prefix** と **Remove Suffix** — 追加したものを取り除きます。
- **Regex Replace** — 正規表現で同様の置き換えを行います。

**次にできること：** ボーン名が正しければ、ヒューマノイドの対応付け（ガイド5）が自動で動作します。正しくなければ、VRChat はキャラクターの動かし方を判断できません。

---

## ガイド5：アバターを VRChat の体のシステムに対応付ける {#guide-5-map-your-avatar-to-vrchats-body-system}

> **所要時間：** 約10–15分
> **結果：** アバターのスケルトンを、VRChat のヒューマノイドの動作システムに結び付けます。

**始める前の確認：**

- [ ] ボーンに適切な名前が付いている（そうでなければガイド4を参照）。
- [ ] スケルトンを選択している。
- [ ] **Object Mode** になっている（ビューポート左上の一覧を確認）。

---

### 手順1 — Set Up Humanoid Bones を開く {#step-1--open-set-up-humanoid-bones}

**CATS** タブで、**Avatar Tools** → **Set Up Humanoid Bones** を展開します。

---

### 手順2 — 自動で対応付ける {#step-2--auto-map}

**Auto-Map All** をクリックします。BoneCraft がスケルトンを調べ、体のスロットを埋めます。

> ヒューマノイドのスロットは、Hips、Head、Left Hand のような体の部位を示します。BoneCraft が、各スロットにボーンを割り当てます。保存済みのヒューマノイド対応付けは、ファイルを開き直したときに正しく読み込まれます。

**確認できる表示：** ボーンの割り当てと、必須スロットが埋まっている割合。必須スロットは15個で、Hips、Spine、Head、左右の上腕、前腕、手、大腿、下腿、足です。任意スロットには Chest、UpperChest、Neck があります。

---

### 手順3 — 対応付けを確認する {#step-3--check-the-mapping}

**Validate** をクリックします。BoneCraft が、すべての必須スロットにボーンがあり、階層が適切か確認します。

---

### 手順4 — 空のスロットを手動で埋める {#step-4--fill-empty-slots-by-hand}

空のスロットには「(click to map)」と表示されます。

1. 空のスロットを選択します。

2. 正しいボーンを選択します。

3. 再び **Validate** を選択します。

4. **Normalize Names** を選択し、対応付けたボーンを VRChat の名前にします。

---

### 手順5 — アイトラッキングを設定する（任意） {#step-5--set-up-eye-tracking-optional}

アバターに目のボーンがある場合：

1. **CATS → CATS → Eye Tracking** を開きます。

2. **Auto-Detect** を選択し、目のボーン名を検索します。

3. **Left Eye** と **Right Eye** の割り当てを確認します。

4. 必要なら、正しいボーンを手動で選択します。

5. 回転の制限を設定します。

6. **Create Eye Tracking** を選択します。

設定は、[ガイド13、フェーズ3](03-guides-b.md#phase-3--eye-tracking)で説明します。

**次にできること：** ヒューマノイドの対応付けにより、VRChat 内でアバターが自分の動きに追従します。IK（インバースキネマティクス）は、ゲーム内の手をコントローラーに追従させます。

---

## ガイド6：髪の物理を追加する {#guide-6-add-hair-physics}

> **所要時間：** 約15–25分
> **結果：** VRChat で、アバターの髪や他の柔らかい部分が自然に揺れます。

**始める前の確認：**

- [ ] アバターを開き、スケルトンを選択している。
- [ ] Set Up Humanoid Bones が完了している（ガイド5）。

> PhysBone は、ボーンに重さがあるように弾んだり揺れたりさせる、VRChat のコンポーネントです。BoneCraft は、髪、耳、しっぽ、スカート、アクセサリーのボーンチェーンに設定します。

---

### 手順1 — Add Hair Physics を開く {#step-1--open-add-hair-physics}

**CATS** タブで、**Avatar Tools** → **Add Hair Physics** を展開します。Hair Chain Detection、Hair Chain Generation、PhysBone Configuration、Hair Physics Colliders の4つで構成されます。

---

### 手順2 — 髪のチェーンを見つける {#step-2--find-the-hair-chains}

髪にすでにボーンがあれば、**Detect Hair Physics Chains** を選択します。BoneCraft が、根元から末端へつながった髪らしいボーンチェーンを検索します。一覧には、各チェーンのルートボーンと長さが表示されます。

髪にボーンがない場合：

1. 髪のメッシュを選択します。

2. Hair Chain Generation で、**Generate** を選択します。

3. すぐに **Adjust Last Operation** で、**Chain Density** を Low、Medium、High のいずれかに設定します。

**Replace** は確認を求めますが、現在は、以前のチェーンを削除せず、新しいチェーンを作ります。

再生成する前に：

1. ボーン一覧を確認します。

2. 不要なチェーンがあれば削除します。

---

### 手順3 — PhysBone プリセットを選択する {#step-3--choose-a-physbone-preset}

1. チェーン内のボーンを選択します。

2. PhysBone Configuration で、**Hair**、**Skirt**、**Tail** のいずれかを選択します。

Skirt はスカートとケープ、Tail はしっぽとロープに適しています。

**確認できる表示：** チェーンの Pull、Spring、Stiffness、Gravity、Max Angle の各パラメーター。

---

### 手順4 — 微調整（任意） {#step-4--fine-tune-optional}

パネルは、チェーンの値を表示しますが、編集はできません。Stiffness を高くすると曲がりにくくなり、Gravity を高くすると下へ引かれ、Max Angle を小さくすると揺れる範囲が制限されます。値を変えるには、別のプリセットを選択します。アバターを読み込んだ後、Unity で PhysBone コンポーネントを編集する方法もあります。

---

### 手順5 — コライダーを追加する（推奨） {#step-5--add-colliders-recommended}

コライダーは、髪が頭や体を通り抜けるのを防ぐ、見えない形状です。Hair Physics Colliders で、**Place Default Colliders** を選択します。頭、肩、胸にコライダーを追加します。**Add Collider** と **Remove Collider** は、1つずつ追加または削除します。

**次にできること：** 頭を回したり、跳んだり、踊ったりしたときに、髪が VRChat 内で自然に動きます。しっぽ、耳、スカート、ぶら下がるアクセサリーにも、同じ手順を使えます。

---

## ガイド7：体に合わせて動く衣装を取り付ける {#guide-7-attach-clothing-that-moves-with-your-body}

> **所要時間：** 約20–30分
> **結果：** アバターのスケルトンに衣装を関連付け、体に合わせて動かします。

**始める前の確認：**

- [ ] 基本のアバターに完成したスケルトンがあり、体のウェイトが設定されている。
- [ ] 衣装が同じファイルにある（付属していたなら、衣装自身のアーマチュアもある）。
- [ ] 衣装が、おおむねアバターの体に合っている。

---

### 手順1 — Attach Clothing を開く {#step-1--open-attach-clothing}

[衣装の操作項目と選択順](08-vrchat.md#attach-clothing)を参照してください。

**CATS** タブの **VRChat Tools** を展開し、Clothing グループを探します。Bone Matching、Collision Detection、Clothing Merge の3つがあります。

---

### 手順2 — ボーンを対応付ける {#step-2--match-bones}

衣装にアーマチュアがある場合：

1. オブジェクトモードに切り替えます。

2. 衣装とアバターの両方のアーマチュアを選択します。

3. **Match Bones** を選択して、ボーン名を比較します。

**確認できる表示：** HIGH、MEDIUM、LOW、UNMATCHED の対応数が報告されます。パネルは、ボーンのペア一覧を表示しません。アーマチュアがない衣装では、この手順を省略します。

2つのアーマチュアを統合する前に：

1. **Detect Collisions** を選択して、競合するボーン名を確認します。

2. 提案された名前変更を確認します。

3. 衣装のアーマチュアをアクティブにします。

4. **Resolve Collisions** を選択し、そのアーマチュアに名前変更を適用します。

Detect Collisions が確認するのは名前だけです。メッシュの交差は確認しません。

---

### 手順3 — 衣装を統合する {#step-3--merge-the-clothing}

1. 衣装にアーマチュアがあれば、そのアーマチュアとメッシュを選択します。

2. なければ、衣装のメッシュだけを選択します。

3. 最後に Shift を押してアバターのアーマチュアをクリックし、アクティブにします。

4. **Merge Clothing** を選択します。

衣装のアーマチュアがある場合、BoneCraft は衣装をアバターのスケルトンに移し、ボーンを統合します。ない場合は、体のウェイトを衣装のメッシュに転送します。

> ウェイト（ウェイトペイント）は、メッシュの各点を各ボーンが動かす強さを示す数値です。左の袖に左腕のボーンのウェイトがあれば、そのボーンを動かすと、袖も引かれて動きます。

**確認できる表示：** 衣装がアバターのスケルトンの下に置かれます。ボーンを動かすと、体と衣装の両方が動きます。

---

### 手順4 — 貫通を確認する {#step-4--check-for-clipping}

1. アバターにポーズを付けます。

2. 衣装が体を通り抜ける箇所を確認します。

3. 貫通があれば、その箇所のフィットやウェイトを調整します。

[リグツール](05-rig-tools.md)の Weight Tools を参照してください。**Detect Collisions** は、物理的な貫通を確認しません。

**次にできること：** 体に自然に追従する衣装ができました。各衣装パーツでも繰り返します。

次へ：[ガイド8–13](03-guides-b.md)
