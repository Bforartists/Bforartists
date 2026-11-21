# ガイド8–13 {#guides-813}

[← 目次](index.md)

## ガイド8：リップシンクを設定する {#guide-8-set-up-lip-sync}

> **所要時間：** 約10–20分
> **結果：** VRChat で話したとき、アバターの口が正しく動きます。

**始める前の確認：**

- [ ] 頭のメッシュに、発話用の口形のシェイプキー（ブレンドシェイプ、モーフターゲットとも呼ぶ）がある。
- [ ] シェイプキーのおおよその名前が分かる（メッシュの Object Data プロパティの Shape Keys 一覧を確認）。

> ビジームは、音に対応する口形です。`aa` は「あー」、`O` は「おー」の音などに対応します。VRChat は15個のビジームで、アバターのリップシンクを動かします。
>
> シェイプキー（ブレンドシェイプ）は、メッシュの別の形状を保存したものです。口を開くシェイプキーは、口を開けた状態のメッシュです。

---

### 手順1 — VRChat Viseme Mapping を開く {#step-1--open-vrchat-viseme-mapping}

[Viseme Mapping と Face Tracking の操作項目](08-vrchat.md#vrchat-viseme-mapping)を参照してください。

**CATS → VRChat Tools → Facial → VRChat Viseme Mapping** を開きます。

---

### 手順2 — ビジームを自動で対応付ける {#step-2--auto-map-visemes}

**Auto-Map All Visemes** をクリックします。BoneCraft がメッシュのシェイプキーを読み、名前で VRChat の15個のビジームスロットに対応付けます。

**確認できる表示：** ビジーム一覧の多くのスロットに、対応付けたシェイプキーが表示されます。

---

### 手順3 — 空のスロットを埋める {#step-3--fill-in-missing-slots}

空のスロットには「(unmapped)」と表示されます。

1. スロットのボタンを選択し、メッシュのシェイプキー検索一覧を開きます。

2. 入力して一覧を絞り込みます。

3. 最も近いシェイプキーを選択します。

割り当てを消すには、「(unmapped)」を選択します。よくある対応は次のとおりです。

| VRChat ビジーム | 音や形 | 探すシェイプキー |
|---|---|---|
| `aa` | 「あー」 | mouth_open, A, aa |
| `O` | 「おー」 | mouth_o, OH, oh |
| `CH` | 「ch」／「sh」 | mouth_ch, CH |
| `PP` | 唇を閉じる（P、B、M） | mouth_m, MM, lips_together |
| `SS` | 「sss」／「zzz」 | mouth_s, SS |

**ビジーム用のシェイプキーがない場合：** CATS → **Visemes** は、A、O、CH の3つの基本形から15個のキーを作ります。口形がなければ、先にこの3つを作ってください。[ガイド13、フェーズ2](#phase-2--viseme-generation)を参照してください。

---

### 手順4 — 口形を確認する {#step-4--check-a-mouth-shape}

1. **Properties → Object Data → Shape Keys** で、対応付けたキーの値を1.0にします。

2. 口形を確認します。

3. 値を0に戻します。

---

### 手順5 — フェイストラッキング（任意） {#step-5--face-tracking-optional}

ビジーム一覧の下にある **Face Tracking (SteamVR)** は、フェイストラッキング機器用の表情シェイプを準備します。任意の機能で、多くのユーザーには不要です。

**次にできること：** VRChat で話すと、アバターの口が動きます。表情も、対応付けたシェイプキーを基に作れます。

---

## ガイド9：アバターのパフォーマンスを改善する {#guide-9-improve-your-avatars-performance}

> **所要時間：** 約15–25分
> **結果：** VRChat のパフォーマンスランクを改善し、他のプレイヤーでの読み込みを速くします。

**始める前の確認：**

- [ ] アバターが完成している（リギング、衣装、リップシンクの設定が済んでいる）。
- [ ] 目標のランクが分かる（多くのユーザーには Good または Excellent）。

> パフォーマンスランクは、アバターの負荷に対する VRChat の評価です。Very Poor のアバターは、他のプレイヤーから非表示にされる場合があります。Good や Excellent のアバターは読み込みが速く、常に表示されます。

---

### 手順1 — 現在のランクを確認する {#step-1--check-the-current-rank}

1. **CATS → VRChat Tools** を開きます。

2. Performance で、**Calculate Performance Rank** を選択します。

BoneCraft が、全体のランクと、各指標が次の段階までどれだけ離れているかを報告します。指標には、ポリゴン、スキン付きメッシュ、マテリアルスロット、ボーン、PhysBones、Contacts があります。

[Performance の操作項目](08-vrchat.md#check-performance)を参照してください。

---

### 手順2 — クリーンアップする {#step-2--clean-up}

同じセクションの VRChat Optimizer には、クリーンアップツールがあります。**What-If Mode** は最初から有効で、各修正は変更を適用せず、予定する変更を報告します。

1. 必要な修正を What-If Mode で実行します。

2. 報告を確認します。

3. 変更を適用するには、What-If Mode を無効にします。

4. 修正を再実行します。

使用できる修正：

1. **Remove Zero-Weight Bones** — メッシュを動かさないボーンを削除します。
2. **Merge Same-Material Meshes** — 同じマテリアルを使うメッシュを結合します。
3. **Remove Unused Shape Keys** — 変形が Basis と同じ、空のシェイプキーを削除します。他のツールからの参照は確認しません。
4. **Remove Unused Vertex Groups** — 空のウェイトグループを削除します。

---

### 手順3 — ポリゴン数を減らす（必要な場合） {#step-3--reduce-the-polygon-count-if-needed}

[Performance と Decimation の操作項目](08-vrchat.md#check-performance)を参照してください。

ポリゴンが多すぎる場合：

1. メッシュを選択します。

2. VRChat Decimation で目標の比率を設定します。

3. **Preview** を選択します。

4. 結果を確認します。

5. 結果を保持するには、**Apply** を選択します。

比率0.5はポリゴン数を半分にし、0.8は20%を削減します。Decimation は、シェイプキーを保護します。

> 0.8から始めてください。外見を確認しながら、少しずつ比率を下げます。小さな削減でも、見た目をあまり変えずにパフォーマンスを改善できます。

---

### 手順4 — マテリアルをまとめる（任意） {#step-4--merge-materials-optional}

マテリアルが多い場合は、1枚のテクスチャシート（アトラス）にまとめます。**CATS** タブ → **CATS** → **Material Atlas** で：

1. ファイルのコピーを保存します。
2. **Target** を、処理するメッシュに設定します。
3. **Preserve Backup Duplicate** を有効のままにします。
4. **Analyze Materials** をクリックします。
5. アトラスグループを選択します。
6. 有効なそのグループ内で、2つ以上のマテリアルにチェックを入れます。
7. 含めるテクスチャ画像にチェックを入れます。
8. 必要なら、どちらかの一覧の上の **Select All** または **Deselect All** を使います。
9. **Bake Checked Sources** をクリックします。
10. ベイクを確定する前に、事前確認の概要を確認します。
11. ベイクしたマテリアル、透明度、UV を確認します。
12. 結果を保持するには、**Accept — Delete Backup** をクリックします。

結果を修正したい場合は、代わりに **Revert — Restore Originals** を使います。Accept はバックアップを削除します。**Preserve Backup Duplicate** を無効にすると、Revert は使えなくなります。

一括選択が影響するのは、アクティブグループ内の対象ソース一覧だけです。欠落したテクスチャは、未チェックのままです。もう一方の一覧と他のグループは変わりません。

**Refresh Analysis** は、ソース一覧と選択を再構築します。選択を確認してから **Bake Checked Sources** を使います。**Smart Combine Materials** は、最初の自動処理へのショートカットです。

各設定は、[CATS ツール：Material Atlas Combiner](09-cats.md#material-atlas-combiner)で説明します。

---

### 手順5 — ランクを再確認する {#step-5--check-the-rank-again}

再び **Calculate Performance Rank** をクリックし、改善を確認します。

**次にできること：** ランクが良くなると、より多くのプレイヤーにアバターが表示されます。Good や Excellent のアバターは読み込みが速く、GPU 負荷が低く、他のプレイヤーに既定で表示されます。

---

## ガイド10：ポーズを保存して再利用する {#guide-10-save-and-reuse-poses}

> **所要時間：** 約5–10分
> **結果：** 1クリックで適用できるポーズライブラリを保存します。

**始める前の確認：**

- [ ] アバターのスケルトンが完成している。
- [ ] **Pose Mode** になっている。

ポーズモードに入るには：

1. アーマチュアを選択します。

2. Ctrl+Tab を押します。

ビューポート左上のモード一覧から、**Pose Mode** を選ぶ方法もあります。

---

### 手順1 — Pose Library を開く {#step-1--open-the-pose-library}

左のツールシェルフの **BoneCraft** タブで、**Review** → **Pose Library** を展開します。

[Pose Library の操作項目](05-rig-tools.md#pose-library)を参照してください。

---

### 手順2 — アバターにポーズを付ける {#step-2--pose-your-avatar}

保存したいポーズになるように、ボーンを動かします。腕の回転、頭の傾き、他のボーンの位置を組み合わせられます。

---

### 手順3 — ポーズを保存する {#step-3--save-the-pose}

1. **Save** を選択します。

2. 「Peace Sign」や「Thinking」など、ポーズ名を入力します。

**Category** は、「Greetings」などの名前でポーズを分類します。**Filter** は、1つのカテゴリーを表示します。保存したポーズには、ビューポートのサムネイルが付きます。

---

### 手順4 — 保存したポーズを適用する {#step-4--apply-a-saved-pose}

1. ポーズを選択します。

2. **Apply** を選択します。

- **Blend** — 部分的な強さでポーズを適用し、2つのポーズを混ぜます。
- **Mirror** — 左右を反転して適用します。

**Rename** と **Delete** で一覧を管理します。

---

### 手順5 — ポーズを書き出し、読み込む {#step-5--export-and-import-poses}

**Export** は、プロジェクトと保存したり共有したりできる `.bfpose` ファイルに、ライブラリを書き出します。**Import** は、`.bfpose` ファイルからポーズを読み込みます。

**次にできること：** プロジェクト間で再利用したり、アニメーションのキー用にブレンドしたり、他の BoneCraft ユーザーと共有したりできる、自分のポーズライブラリができました。

---

## ガイド11：2つのリグを統合する {#guide-11-merge-two-rigs-together}

> **所要時間：** 複雑さに応じて約25–40分
> **結果：** すべてのウェイトを保持し、2つのスケルトンを1つにまとめます。

**始める前の確認：**

- [ ] 基本アバターと、2つ目のリグ（衣装やアクセサリーのリグ）が同じファイルにある。
- [ ] 両方がリギング済みで、ウェイトが設定されている。

> リグの統合は、片方のスケルトンをもう片方に取り込み、1つにまとめる操作です。体のリグと、髪や衣装のリグを統合したいときに使います。

---

### 手順1 — Bone Merge を開く {#step-1--open-bone-merge}

**BoneCraft → Setup Rigging → Bone Merge** を開きます。3つの段階は、完了するごとに順番に開きます。

[段階式の Bone Merge の操作項目](06-rig-builder.md#bone-merge)を参照してください。

---

### 手順2 — 段階1：Scope {#step-2--stage-1-scope}

1. 残す体のスケルトンである **Base** アーマチュアを選択します。

2. 取り込む衣装や髪のアーマチュアを選択します。

3. **Analyze** を選択します。

最後の統合では、取り込むアーマチュアが基本のアーマチュアに統合され、その後で非表示になります。

Analyze は、2つのスケルトンを比較し、次を一覧表示します。

- ✓ Matched — 両方に存在し、位置が合うボーン。
- \+ Source only — 基本のリグに対応がない、取り込むリグのボーン。
- − Target only — 取り込むリグにない、基本のリグのボーン。

一覧を読んだら、**Acknowledge Scope — Proceed to Rename** をクリックします。

---

### 手順3 — 段階2：Rename {#step-3--stage-2-rename}

各 source-only ボーンについて、該当する方法を選びます。

基本リグに同等のボーンがある場合：

1. そのボーン名を入力します。

2. **Apply Rename** を選択します。

同等のボーンがなければ、代わりに **Mark as Unique** を選択します。名前を変えずに基本リグに追加します。

**Normalize Both Armatures** は、両方のリグで、背骨、腕、脚などの認識された標準ボーンの名前を変更します。**Auto-Propose Renames** は、他のボーンの位置から名前を提案します。**Apply Batch Pattern** は、1つのパターンで複数のボーンの名前を変更します。

すべての source-only ボーンを解決したら、**Verify Rename — Proceed to Merge** をクリックします。

---

### 手順4 — 段階3：Merge {#step-4--stage-3-merge}

先に **Run Merge Preview** をクリックします。データを変えずに、統合で行う内容を報告します。

報告が正しければ、**Merge Armatures** をクリックします。BoneCraft は、両方のアーマチュアをバックアップしてから統合します。

**確認できる表示：** 両方のスケルトンの全ボーンを持つ1つのアーマチュアに、すべてのメッシュのウェイトが関連付けられます。

**次にできること：** 編集と書き出しがしやすい1つのリグになります。独立した衣装やアクセサリーのリグを持つアバターに必要です。

---

## ガイド12：アップロードの問題を修正する {#guide-12-fix-upload-problems}

> **所要時間：** 問題に応じて約5–15分

**始める前に：** 下の一覧で問題を探し、その節に進んでください。

---

### 「アップロード失敗 — ボーンが認識されない」 {#upload-failed--bones-not-recognized}

ボーン名を VRChat が認識できません。→ [ガイド4：アバターのボーン名を修正する](02-guides-a.md#guide-4-fix-your-avatars-bone-names)。

---

### 「VRChat でTポーズのまま、自分に合わせて動かない」 {#avatar-is-in-t-pose--not-moving-with-me-in-vrchat}

ヒューマノイドの対応付けがないか、誤っています。→ [ガイド5：アバターを VRChat の体のシステムに対応付ける](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system)。

---

### 「メッシュが不自然に変形する、肌が伸びる」 {#mesh-is-deforming-weirdly--skin-stretching-wrong}

ボーンのウェイトの調整が必要です。→ [リグツール](05-rig-tools.md)の Weight Transfer と Weight Mirror、または CATS タブの **Smart Automatic Weights** を使います。

---

### 「髪が頭を突き抜ける」 {#hair-is-clipping-through-the-head}

髪用コライダーがないか、小さすぎます。→ [ガイド6：髪の物理を追加する](02-guides-a.md#guide-6-add-hair-physics)の手順5。

---

### 「パフォーマンスが Very Poor で、他のプレイヤーに非表示にされる」 {#avatar-is-very-poor-performance-and-being-blocked-by-other-players}

→ [ガイド9：アバターのパフォーマンスを改善する](#guide-9-improve-your-avatars-performance)。

---

### 「リップシンクが動かない」 {#lip-sync-not-working}

ビジームの対応付けが誤っています。→ [ガイド8：リップシンクを設定する](#guide-8-set-up-lip-sync)。

---

### 「Rig Validator がエラーを表示する」 {#rig-validator-shows-errors}

1. **BoneCraft → Review → Rig Validator** を開きます。

2. **Run Validation** を選択します。

3. 結果の提案に従うか、[クイック修正インデックス](10-reference.md#quick-fix-index)を確認します。

各結果には、問題とボーン名が表示されます。**Export Report** は、結果をファイルに保存します。

---

### 「VRM を読み込めない」 {#vrm-import-not-working}

VRM アドオンが未インストールの可能性があります。→ [ガイド2](02-guides-a.md#guide-2-bring-a-vroid-avatar-into-vrchat)の手順1。

---

### 「MMD を読み込めない」 {#mmd-import-not-working}

**mmd_tools** がインストールされ、有効か確認します。ブリッジは、新方式の Extensions と旧方式のパッケージに対応しています。再試行する前に、インストールメッセージを確認してください。[ガイド3](02-guides-a.md#guide-3-bring-an-mmd-avatar-into-vrchat)の手順1を参照してください。

---

## ガイド13：CATS でアバターを VRChat 対応にする {#guide-13-get-your-avatar-vrchat-ready-with-cats}

> **所要時間：** パイプライン全体で約20–35分
> **結果：** 選択したクリーンアップ、リップシンク、アイトラッキング、適切なトランスフォームを備えた、最適化されたアバターを、VRChat アップロード用に準備します。

**始める前に読むこと：**

CATS のツールには、推奨パイプラインがあります。Pipeline Status は、Fix Model、Material Atlas、Visemes、Eye Tracking、Pose To Shape、Apply Transforms の完了を示します。Operation Ledger は、CATS の各操作を記録します。

前のフェーズが未完了でもツールは動き、「Run Fix Model first for best results」のような警告を表示します。

まず、Fix Model のクリーンアップオプションを確認してください。アバターを変更する前に、ファイルをチェックポイントとして保存します。

続ける前に、[CATS パイプライン](04-cats-pipeline.md)を読んでください。

**始める前の確認：**

- [ ] アバターが読み込まれ、3Dビューポートに見えている。
- [ ] 右サイドバーの CATS タブを開いている（サイドバーがなければ N を押す）。
- [ ] アバターを選択している（ビューポートまたはアウトライナーでクリック）。

---

### フェーズ1 — Fix Model {#phase-1--fix-model}

Fix Model は、推奨するクリーンアップのフェーズです。読み込んだアバターに合わせてオプションを確認し、実行結果を確認してから続けます。

**Fix Model の処理内容**（各項目はオプションで無効にできます）：

- モディファイアーの適用。
- 重複頂点と独立した形状（体から離れて浮いた三角形）の削除。
- 法線（メッシュの外側を向く面を決める方向）の再計算。
- 空の頂点グループとゼロウェイトボーンの削除。
- VRChat が使えないコンストレイントと剛体の削除。

**手順：**

1. **CATS → CATS → Fix Model** を開きます。

2. アバターのメッシュを選択します。

3. **Fix Model** を選択します。

4. 操作が完了するまで待ちます。

5. Pipeline Status の Fix Model に ✓ が付くことを確認します。

大きなメッシュでは、数秒かかる場合があります。

**確認できる表示：** アバターの外見は同じか、少しきれいになります。Pipeline Status の Fix Model にチェックが付き、Operation Ledger に実行が記録されます。

**Fix Model 後にモデルが消えたり、裏返って見えたりする場合：**

その症状だけでは、原因を特定できません。

1. 有効なクリーンアップオプション、オブジェクトの表示、形状、法線を確認します。

2. 復元が必要なら、元に戻す操作か、保存済みのチェックポイントを使います。

3. 再試行の前に、特定した問題を修正します。

[Fix Model の操作項目](09-cats.md#fix-model)を参照してください。

---

### フェーズ2 — ビジームの生成 {#phase-2--viseme-generation}

実行する時点：Fix Model ✓ の後。

Visemes は、既存の3つの基本形から、VRChat のリップシンク用口形15個をすべて作ります。アバターに完全なビジームのシェイプキーがあれば、このフェーズを省略できます。ただし、VRChat Viseme Mapping（ガイド8）で確認してください。

VRChat が発話時に口を動かすには、15個の口形（ビジーム）が必要です。多くのアバターには、少数の基本形しかありません。CATS は、それらを組み合わせて残りを作ります。

3つの基本形：

- **A Shape** — 大きく口を開ける形（「あー」）。
- **O Shape** — 丸い口（「おー」）。
- **CH Shape** — 歯が見える、狭く開いた口（「ch」／「sh」）。

**口のシェイプキーがない場合：** 先に A、O、CH を、シェイプキーとしてスカルプトまたは編集します。CATS は、それを基に残りを生成します。用語集の Shape Key を参照してください。

**手順：**

1. **CATS → CATS → Visemes** を開きます。

2. 以下の自動または手動のソース選択を使います。

   自動選択には、**Auto-Detect** を選択し、3つのソース形状を埋めます。

   手動選択には、各ソース形状で最も近いものを選択します。

   キー名の例には、`mouth_open`、`vrc.v_O`、`mouth_wide` があります。

3. **Generate Visemes** を選択します。

4. Pipeline Status が Visemes ✓ を示すことを確認します。

CATS は、`vrc.v_aa`、`vrc.v_O`、`vrc.v_CH` など、VRChat の名前が付いた15個のシェイプキーを作成します。

**確認できる表示：** メッシュの Shape Keys 一覧（Properties → Object Data → Shape Keys）に、新しいシェイプキー15個が表示されます。

[CATS Visemes の操作項目](09-cats.md#visemes)を参照してください。

---

### フェーズ3 — アイトラッキング {#phase-3--eye-tracking}

実行する時点：Fix Model ✓ の後。

Eye Tracking は、VRChat の標準アイトラッキング用に目のボーンを設定します。目を動かし、他のプレイヤーを見られるようになります。

**処理内容：**

- 左右の目のボーンを見つけます。
- VRChat が必要とする名前（`LeftEye` と `RightEye`）を付けます。
- VRChat が目を動かすための回転コンストレイントを追加します。
- 自然な上下左右の範囲に回転を制限します。

Auto-Detect は、よく使われる目のボーン名を検索します。メッシュの形状や、ボーンの位置は調べません。

ボーン名を変えた場合：

1. 検出を再実行します。

2. 両方の目のボーンの割り当てを確認します。

目の動きがおかしい場合は、ボーンの向き、コンストレイント、書き出したアバターを確認してください。

**手順：**

1. **CATS → CATS → Eye Tracking** を開きます。

2. **Auto-Detect** を選択し、よく使われる左右の目のボーン名を検索します。

3. **Left Eye** と **Right Eye** の欄を確認します。

4. 割り当てが誤っていれば、正しいボーンを手動で選択します。

5. 必要なら、**Up Limit**、**Down Limit**、**Side Limit** を設定します。

6. **Create Eye Tracking** を選択します。

7. Pipeline Status が Eye Tracking ✓ を示すことを確認します。

**確認できる表示：** 両目のボーン名が変わり、Bone Constraints パネルに回転コンストレイントがあります。

> **CATS が目のボーンを見つけられない場合：** スケルトンに存在しない可能性があります。一部の形式、特に古い MMD モデルは、ボーンではなくシェイプキーでまばたきします。このフェーズは省略してください。目のボーンがなければ、VRChat はシェイプキーによる目のアニメーションを使います。

---

### フェーズ4 — Pose to Shape Key {#phase-4--pose-to-shape-key}

実行する時点：Fix Model ✓ の後。

現在の **Pose to Shape Key** ボタンは、選択中メッシュの現在のシェイプキーの混合状態を記録します。アーマチュアのボーンによる変形をベイクしません。ボーンで変形したポーズには、検証済みの[標準機能の Save as Shape Key 手順](09-cats.md#save-a-bone-deformed-pose)を使ってください。

**手順：**

1. オブジェクトモードに切り替えます。

2. 対象メッシュを選択します。

3. 既存のシェイプキーを、記録したい混合状態に設定します。

4. メッシュをアクティブに保ちます。

5. **CATS → CATS → Pose & Shape Keys** を開きます。

6. **Pose to Shape Key** を選択します。

7. 新しいシェイプキー名を入力します。

8. 操作を確定します。

9. 元のシェイプキーの値を0に戻します。

10. 新しいキーだけで結果を確認します。

11. Pipeline Status が Pose To Shape ✓ を示すことを確認します。

ツールは、新しいキーをすでに1にしています。

**確認できる表示：** 記録したシェイプキーの混合状態を再現する、新しいシェイプキー。元のキーを有効にしたままだと、その変形がもう一度加算されます。

> **Shape Key to Basis：** アクティブな Basis 以外のシェイプキーを、新しい Basis にします。他のキーを、その Basis に対して調整します。実行前にチェックポイントを保存し、実行後に残りのキーを確認してください。

[Pose to Shape Key の操作項目](09-cats.md#pose-to-shape-key)を参照してください。

---

### フェーズ5 — トランスフォームを適用する {#phase-5--apply-transforms}

実行する時点：必要な以前のフェーズがすべて終わった後。

Apply Transforms は、推奨する準備作業の最後のフェーズです。メッシュとスケルトンに、位置、回転、スケールを適用します。それぞれのチャンネルは、0、0、1に戻ります。

実行前にチェックポイントを保存し、前後のアバターを比較します。前のツールは、引き続き使用できます。

書き出したアバターの大きさが違う場合は、メッシュとアーマチュアのトランスフォーム、書き出しと読み込みのスケール設定を確認します。以前の状態への復元が必要なら、元に戻す操作か保存済みのチェックポイントを使います。

**Transforms & FBT のツール：**

- **Apply All Transforms** — メッシュとアーマチュアの位置、回転、スケールをまとめて適用します。
- **Fix FBT** — Full Body Tracking 設定用のトランスフォーム補正（ルートボーンを床の高さに移動）。
- **Remove FBT** — その補正を取り除きます。

Material Atlas と Pose To Shape は任意です。既存のビジームを対応付けた場合、Visemes は未チェックのままです。

**手順：**

1. Pipeline Status で、アバターに必要なフェーズにチェックが付いていることを確認します。

2. **CATS → CATS → Transforms & FBT** を開きます。

3. **Apply All Transforms** を選択します。

4. Pipeline Status が Apply Transforms ✓ を示すことを確認します。

5. **CATS → Import / Export → Game Engine Export → Unity / VRChat** から書き出します（ガイド1、手順9）。

**確認できる表示：** 必要なフェーズの後で Apply Transforms にチェックが付きます。VRChat Creator Companion で、書き出したアバターを確認します。

[トランスフォームと FBT の操作項目](09-cats.md#apply-all-transforms)を参照してください。

---

**次にできること：** 選んだクリーンアップ、口形、アイトラッキング、表情を備えたアバターが、書き出し確認用に準備できました。アップロード前に、対象アプリケーションで検証してください。

次へ：[CATS パイプライン](04-cats-pipeline.md)
