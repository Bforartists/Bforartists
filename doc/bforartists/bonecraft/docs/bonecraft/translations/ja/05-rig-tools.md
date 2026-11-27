# リグツール {#rig-tools}

[← 目次](index.md)

この章では、BoneCraft のリギング、アニメーション、ウェイトの各ツールを説明します。機能の詳細や、ガイドにない状況で参照してください。

各項目は、目的、用途、主な操作項目、場所を説明します。「場所」には、必要なモードも示します。リグの操作にはポーズモード、Weight Mirror と Weight Transfer にはウェイトペイントモード、Delta Mush にはオブジェクトモードが必要です。実行できない場合でも、一部のセクションは表示を保ち、必要な選択を案内します。

9.1以降、多くのツールは即座に実行し、Adjust Last Operation パネルにオプションを表示します。次の操作の前に、クリック直後にオプションを変更してください。よく使う操作は Pose → BoneCraft と Weights → BoneCraft のメニューにもあります。Bforartists の Pose と Weights のツールシェルフにも BoneCraft のボタンパネルがあります。[はじめに](01-start.md#where-things-are)に、これらの入口を示しています。

画像は、リグとツール設定の例です。各ツールのパスに従って操作項目を開いてください。

ゲームエンジンへの書き出しは、[VRChat ツール：Game Engine Export](08-vrchat.md#game-engine-export)を使います。**Bone Names** プリセットが変更するのは、書き出し用コピーです。作業中リグの名前を変更するツールとは、目的が異なります。

---

## リグ UI ツール {#rig-ui-tools}

アーマチュアの作業中に、ボーンの表示、整理、素早いアクセスを制御するツールです。

---

### Bone Collections {#bone-collections}

**機能：** スケルトンのボーンコレクションを行として表示します。コレクション名をクリックすると、そのボーンを選択します。目のアイコンは、表示を切り替えます。

> ボーンコレクションは、「IK Controls」「Face Bones」「Deform Bones」などの名前付きボーングループです。隠すと、そのボーンがビューポートで非表示になり、リグの一部に集中できます。

**主な操作項目：**

- 各行：アクセントカラー、**Toggle Collection Visibility**（目のアイコン）、コレクション名、**Solo Collection**、**Rename Collection Display**。名前はボーンを選択し、**Rename Collection Display** は行の表示名を設定します。アイコンだけのボタンは、マウスを重ねてツールチップで確認します。
- **Show All Collections** と **Hide All Collections**（一覧上の開いた目と閉じた目） — 全体をまとめて切り替えます。
- Sections — 複数のコレクションを、折りたたみ可能な見出しの下にまとめます。

**場所：** BoneCraft タブ → Review → Collections。

英語原本の画像説明（画像は省略）：ボーンコレクションと、表示、選択、ソロ、表示名の操作項目。

*標準テストビルドのポップオーバー、BoneCraft 9.2.19候補版。Bforartists 5.2.3、Blender 5.4 Alpha。ボーンコレクションと、表示、選択、ソロ、表示名の操作項目。*

---

### Visibility Bookmarks {#visibility-bookmarks}

**機能：** 表示中のボーンコレクションを保存し、保存した表示をまとめて切り替えます。

**使用例：** 「Face Only」には、表情作業用に顔のボーンだけの表示、「Full Rig」にはウェイトペイント用に全ボーンの表示を保存できます。1クリックで切り替えます。

**主な操作項目：** 各スロットが1行です。

- ブックマーク名 — クリックして保存した表示を適用します。
- **Save Bookmark** — 現在の表示をスロットに保存します。アイコンにマウスを重ねると、ツールチップが表示されます。
- 色見本 — 色でブックマークを区別します。
- **Clear Bookmark** と **Remove Bookmark**（閉じるアイコン） — スロットを空にするか、追加したスロットを削除します。
- **Add Bookmark** — スロットを追加します。

**既定のブックマーク：** FK Arms、IK Body、Face Only、Full Rig。

**場所：** BoneCraft タブ → Review → Collections → Visibility Bookmarks。

英語原本の画像説明（画像は省略）：Full Rig の表示が1つ保存され、3つの空きスロットがある Visibility Bookmarks。

*標準テストビルドのポップオーバー、BoneCraft 9.2.19候補版。Bforartists 5.2.3、Blender 5.4 Alpha。Full Rig の表示が1つ保存され、3つの空きスロットがある Visibility Bookmarks。*

---

### ホットキーのクイックパネル {#hotkey-quick-panel}

**機能：** カーソルの位置で、コレクションとブックマークを含む BoneCraft のリグパネルをポップアップ表示します。

**使い方：**

1. 3Dビューポートで **Ctrl+Shift+R** を押します。
2. 外側をクリックして閉じます。

**場所：** 3Dビューポートの **Ctrl+Shift+R** ショートカット（独立したパネルはありません）。

クイックパネルは、[上記のブックマーク操作項目](#visibility-bookmarks)を使います。

---

## アニメーションツール {#animation-tools}

---

### Pose Library {#pose-library}

**機能：** 名前とサムネイル付きのポーズを保存し、1クリックでリグに適用します。

**主な操作項目：**

- **Save** — 現在のボーン位置を、ビューポートのサムネイル付きで名前を付けて保存します。
- **Apply** — ボーンを保存済みポーズに合わせます。
- **Blend** — 現在の位置と混ぜ、部分的な強さで適用します。
- **Mirror** — 左右を反転して適用します。
- **Delete**、**Rename**、**Category** — 一覧を管理します。**Filter** は1つのカテゴリーを表示します。
- **Export** と **Import** — `.bfpose` ファイルに保存するか、そこから読み込みます。

Blend は即座に適用します。クリック後、Adjust Last Operation で強さを設定します。

**場所：** BoneCraft タブ → Review → Pose Library。

英語原本の画像説明（画像は省略）：保存したポーズ例に、Apply、Mirror、Blend とライブラリの操作項目が表示されています。

*標準パネルのポップオーバー、BoneCraft 9.2.18。保存したポーズ例に、Apply、Mirror、Blend とライブラリの操作項目が表示されています。*

---

### Control Picker {#control-picker}

**機能：** リグの操作項目を、クリックできるマップとして表示します。形状をクリックすると、対応するボーンを選択します。選択中の操作項目は強調表示します。

**主な操作項目：**

- **Generate Picker** — リグからレイアウトを作ります。
- **Edit Layout** — レイアウトを編集します。各行に **Move Picker Control**、**Resize Picker Control**、**Relabel Picker Control** のアイコンがあります。**Snap** はグリッドに揃え、**Rebuild Layout** は作り直します。
- **Mirror Selection** — 対称側の操作項目を選択します。
- **Pop-up Picker** — フローティングウィンドウで開きます。そこには **Add Selection Set** もあります。

**場所：** BoneCraft タブ → Review → Control Picker。

英語原本の画像説明（画像は省略）：生成した Control Picker に、操作項目の例、レイアウト編集、対称選択、ポップアップピッカーの操作が表示されています。

*標準パネルのポップオーバー、BoneCraft 9.2.18。生成した Control Picker に、操作項目の例、レイアウト編集、対称選択、ポップアップピッカーの操作が表示されています。*

---

### Control Layer（IK/FK） {#control-layer-ikfk}

文章による実践的な比較は、[ウェイトのテストと IK/FK](06-rig-builder.md#part-c-test-weights-and-use-ikfk)を参照してください。

**機能：** **Build Control Rig** で作成したリグの手足を制御します。跳ねずに IK と FK を切り替え、フレーム範囲内の IK アニメーションを FK に、またはその逆に変換します。

**主な操作項目：**

- **IK** と **FK** — 手足を切り替え、新しい操作項目を現在の位置に合わせます。ひじや膝は跳ねません。
- **Bake IK** と **Bake FK** — フレーム範囲内のアニメーションを IK または FK に変換します。
- **Pole Follow**、**Pin**、**Lock-Free**、および保護されたロックを維持する **Global Rig Scale**。

**場所：** BoneCraft タブ → Review → Control Layer（**Build Control Rig** で作成したリグを選択。[Rig Builder](06-rig-builder.md)を参照）。

英語原本の画像説明（画像は省略）：Control Layer に、手足の IK/FK 切り替え、ベイク操作、リグ設定が表示されています。

*過去のワークショップのキャプチャー。Control Layer に、手足の IK/FK 切り替え、ベイク操作、リグ設定が表示されています。*

---

### Rigify Tools {#rigify-tools}

**機能：** Rigify の制御リグを検出し、BoneCraft のコレクションパネル、ブックマーク、プロパティスライダーを、Rigify の標準操作項目に結び付けます。

> Rigify は、アニメーション用リグを生成する Bforartists 内蔵の仕組みです。Rigify で作ったリグなら、BoneCraft の UI を IK/FK の操作項目に接続します。

**主な操作項目：**

- **Auto-Enhance** — 選択中の Rigify リグ用に、BoneCraft のパネルを設定します。
- **Re-run Enhancement** — 最初から作り直します。
- **Enable Rigify** は Quick Rig にあります。Troubleshooting の折りたたみ欄には **Generate Control Rig (active metarig)** があります（[Rig Builder](06-rig-builder.md)参照）。
- Rigify Properties — IK/FK、伸縮、親空間、頭／首の追従のスライダー。

**場所：** BoneCraft タブ → Setup Rigging → Rigify Tools（および Rigify Properties セクション）。

英語原本の画像説明（画像は省略）：Rigify Tools の拡張機能への入口。適切な操作項目を使うには、生成済みの Rigify リグを選択します。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Rigify Tools の拡張機能への入口。適切な操作項目を使うには、生成済みの Rigify リグを選択します。*

---

### Retarget {#retarget}

**機能：** モーションキャプチャーのクリップをアバターに移すなど、スケルトン間でアニメーションを転送します。名前と向きでボーンを対応付け、手足の向きを維持します。鎖骨は緩やかに対応付け、肩の過剰な回転を防ぎます。

**主な操作項目：**

- **Import Clip** と **Browse Library** — クリップを読み込むか、ライブラリフォルダーを設定します。クリップ名をクリックして選択します。
- **Auto-Match Bones**（クリップ行のチェック） — ソースと対象のボーンを対応付けます。Bone Mapping 一覧にペアを表示します。
- **Preview** と **Stop Preview** — 結果を試します。
- **Apply** — リグにクリップをベイクします。

**場所：** BoneCraft タブ → Setup Rigging → Retarget。

英語原本の画像説明（画像は省略）：Retarget は Import Clip と Browse Library から始まります。クリップを読み込むと、対応付けとプレビューが表示されます。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Retarget は Import Clip と Browse Library から始まります。クリップを読み込むと、対応付けとプレビューが表示されます。*

---

### Corrective Shape Keys {#corrective-shape-keys}

**機能：** ボーンがある角度に達すると有効になるシェイプキーで、極端なポーズでのつぶれや挟み込みを補正します。

**使用例：** ひじを深く曲げると崩れる場合、腕のボーンに結び付けた、スカルプトしたひじの補正が自動で適用されます。

**主な操作項目：**

- New Corrective — **Shape Key**、**Driver Bone**、回転軸、最大強度になる角度、徐々に立ち上がる範囲の設定。
- 補正一覧 — 下の **Edit** と **Delete** は、選択した補正に作用します。

アーマチュアの子メッシュには、Basis シェイプキーが必要です。アーマチュアを選ぶと New Corrective を表示し、子メッシュからシェイプキーを取得します。

補正を作るには：

1. **Shape Key** を選択します。
2. **Driver Bone** を選択します。
3. 回転軸を選択します。
4. 最大強度になる角度を設定します。
5. 徐々に有効になる範囲を設定します。
6. **Create Corrective** を選択します。

既存の補正を選ぶには、一覧でシェイプキー名をクリックします。

Edit は、現在の値から始まります。クリック後：

1. Adjust Last Operation で角度を変更します。
2. 減衰を変更します。

**場所：** BoneCraft タブ → Skin → Correctives（メッシュに Basis シェイプキーが必要）。

英語原本の画像説明（画像は省略）：アーマチュアを選択すると New Corrective が表示されます。子メッシュがシェイプキーを提供します。

*標準パネルのポップオーバー、BoneCraft 9.2.18。アーマチュアを選択すると New Corrective が表示されます。子メッシュがシェイプキーを提供します。*

---

### Graph Tools {#graph-tools}

**機能：** キーフレームとカーブのアニメーションを調整します。

- **Interactive Breakdown**（Breakdowner） — 左右のドラッグで、現在のポーズを前後のキーフレーム間で混ぜます。3Dビューポートのショートカットは **Ctrl+Shift+B** です。
- **Apply Delta**（Delta Mover） — 選択中ボーンを、画面空間またはワールド空間で正確な量だけ移動します。ショートカットは **Ctrl+Shift+D** です。
- **Capture** と **Swap**（Buffer Curves） — カーブのコピーを保持し、編集内容と入れ替えます。
- **Smart Bake** — コンストレイントによるアニメーションをキーにベイクし、冗長なキーを除きます（**Tol** で程度を設定）。
- **Euler Filter** — ジンバルロックによる回転の反転を修正します。
- Tangent Handles — 選択キーのハンドルを **Auto**、**Vector**、**Aligned**、**Free**、**Auto Clamped** にします。

**場所：** BoneCraft タブ → Review → Graph Tools。

英語原本の画像説明（画像は省略）：Interactive Breakdown は、選択中のポーズボーンでドラッグを開始します。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Interactive Breakdown は、選択中のポーズボーンでドラッグを開始します。*

英語原本の画像説明（画像は省略）：Apply Delta と、オフセットのオプション。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Apply Delta と、オフセットのオプション。*

英語原本の画像説明（画像は省略）：Buffer Curves、Euler Filter、Smart Bake。Options の折りたたみ欄は閉じています。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Buffer Curves、Euler Filter、Smart Bake。Options の折りたたみ欄は閉じています。*

英語原本の画像説明（画像は省略）：Tangent Handles の Auto、Vector、Aligned、Free、Auto Clamped。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Tangent Handles の Auto、Vector、Aligned、Free、Auto Clamped。*

---

## ウェイトツール {#weight-tools}

ボーンを動かしたときのメッシュの変形を制御します。ウェイトは、各部分がどのボーンにどれだけ追従するかを定めます。

---

### Automatic Bone Weight Recalculation {#automatic-bone-weight-recalculation}

**機能：** 既存リグからメッシュのウェイトを再計算し、メッシュ自体は変更しません。高密度メッシュでは軽いプロキシを使い、無言で失敗することを防ぎます。

**主な操作項目：** Body は既存リグから計算します。Clothing は、正しくウェイト設定されたソースメッシュから転送します。設定はボタンの上にあります。

1. **Mesh to Reweight** で、対象メッシュを選択します。
2. **Existing Armature** で、アーマチュアを選択します。
3. Body または Clothing モードを選択します。

Body モードでは、方式を選択します。

Clothing モードでは：

1. **Weighted Body** で、正しくウェイト設定されたソースメッシュを選択します。
2. 方式を選択します。

どちらのモードでも：

1. ブレンドを設定します。
2. スムージングを設定します。
3. 頂点ごとのボーン影響数の上限を設定します。
4. 最小ウェイトを設定します。
5. バックアップを保持するか選択します。
6. **Automatic Bone Weight Recalculation** を選択します。

CATS のショートカット **Smart Automatic Weights** は、対象メッシュ、アーマチュア、モードを選ぶダイアログを開きます。Clothing モードでは、ソースメッシュも含みます。

**場所：** BoneCraft タブ → Skin → Weight Tools。

英語原本の画像説明（画像は省略）：例のメッシュとアーマチュアを選択した Automatic Bone Weight Recalculation の設定。

*標準テストビルドのポップオーバー、BoneCraft 9.2.19候補版。Bforartists 5.2.3、Blender 5.4 Alpha。例のメッシュとアーマチュアを選択した Automatic Bone Weight Recalculation の設定。*

---

### Weight Mirror {#weight-mirror}

**機能：** アバターの片側から反対側へウェイトをコピーします。左右対称のキャラクターに使います。

**主な操作項目：**

- **Mirror All Weights** — 全ボーングループを反対側にミラー反転します。
- **Mirror Active Weight** — アクティブなボーングループだけをミラー反転します。
- **Axis** と **Direction** — 反射軸と、元になる側を選びます。
- **Search Distance** — 反射した頂点位置と、その空間的な対応点の間に許す距離。
- **Select Unmatched** — 対応点がない頂点を選択します。**Normalize Weights** は、その後で合計を1.0にします。

メッシュのトポロジーではなく、空間内の位置を使います。

1. ミラーのボタンをクリックします。
2. Adjust Last Operation で **Axis** を選択します。
3. **Direction** を選択します。
4. **Search Distance** を設定します。

**Mirror Active Weight** は、Weights → BoneCraft と Weights のツールシェルフにもあります。

**場所：** ウェイトペイントモードの BoneCraft タブ → Weight Mirror。

英語原本の画像説明（画像は省略）：Weight Mirror の操作。クリック後、Adjust Last Operation で軸と検索オプションを設定します。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Weight Mirror の操作。クリック後、Adjust Last Operation で軸と検索オプションを設定します。*

---

### Weight Transfer {#weight-transfer}

**機能：** ソースメッシュからアクティブメッシュにウェイトをコピーします。体に衣装を付ける場合や、高解像度メッシュから低解像度へ移す場合に使います。

**主な操作項目：** Adjust Last Operation の **Normalize** は、合計を1.0に保ちます。**Select Problem Vertices** は、対応が不適切な頂点を選択します。

ウェイトペイントモードで、対象メッシュをアクティブに保ちます。

1. **Source Mesh** で、ソースメッシュを選択します。
2. **Transfer Weights** をクリックします。
3. Adjust Last Operation で、転送方式を選択します。
4. ボーンのフィルターを選択します。

結果には、平均距離と最大距離を表示します。

**場所：** ウェイトペイントモードの BoneCraft タブ → Weight Transfer（Skin → Weight Tools にもあります）。

英語原本の画像説明（画像は省略）：Transfer Weights の前に Source Mesh を選択します。この例では、距離欄は初期値のままです。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Transfer Weights の前に Source Mesh を選択します。この例では、距離欄は初期値のままです。*

---

### Weight Table {#weight-table}

**機能：** 選択頂点の各ボーンに対する正確なウェイトを表示し、精密な値を設定できます。

**使い方：**

1. ウェイトペイントモードに入ります。
2. **vertex-selection masking** を有効にします。
3. 頂点を1つ選択します。

選択頂点のボーンとウェイトが表に並びます。

4. ボーン行の手のアイコンをクリックします。
5. Adjust Last Operation で **Weight** を設定します。

Add Influence は、選んだボーンを使います。実行後は、新しいウェイトも Adjust Last Operation で設定します。複数頂点を選択すると、**Normalize All Vertices** が、そのすべてを正規化します。

**場所：** ウェイトペイントモードの BoneCraft タブ → Weight Table。

英語原本の画像説明（画像は省略）：複数頂点を選択した Weight Table。詳細なウェイト編集には、頂点を1つ選択します。

*標準パネルのポップオーバー、BoneCraft 9.2.18。複数頂点を選択した Weight Table。詳細なウェイト編集には、頂点を1つ選択します。*

---

### Flood Fill {#flood-fill}

**機能：** 未選択頂点も含め、メッシュ全体でアクティブ頂点グループのウェイトを変更します。

どの Flood Fill 操作でも、先に：

1. メッシュを選択します。
2. ウェイトペイントモードに入ります。
3. 必要な頂点グループをアクティブにします。

**操作：**

- **Flood to 0.0** は、メッシュ全体で、アクティブグループに割り当てられた正のウェイトを除去します。他の頂点グループは変わりません。
- **Flood to 1.0** は、全頂点でアクティブグループに1.0を割り当てます。各頂点で、他の正のウェイトの合計が1e-6を超えていれば、それらを除去します。
- **Flood to Custom** は、全頂点でアクティブグループに正の **Value** を割り当てます。**Normalize** が有効なら、メッシュ全体のウェイトも正規化します。**Value** が0なら、割り当ても正規化も行いません。クリアするには **Flood to 0.0** を使います。

Weights のメニューとシェルフでは、固定値ボタンを Flood to Zero と Flood to One と呼びます。

任意値で塗りつぶすには：

1. **Flood to Custom** を選択します。
2. すぐに Adjust Last Operation で **Value** を設定します。
3. **Normalize** を有効または無効にします。

**場所：** ウェイトペイントモードの BoneCraft タブ → Skin → Weight Tools。Weights → BoneCraft と Tool Shelf → Weights → BoneCraft にもあります。

英語原本の画像説明（画像は省略）：Flood Fill の操作。クリック後、Adjust Last Operation で任意値を設定します。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Flood Fill の操作。クリック後、Adjust Last Operation で任意値を設定します。*

---

### Deform vs Control {#deform-vs-control}

**機能：** 変形用と制御用のボーンを区別します。デフォームボーンはメッシュを動かし、制御ボーンはアニメーターが動かします。ツールはデフォームボーンにタグを付け、変形用の命名方式に変更します。デフォームボーンだけのスケルトンも書き出せます。

**場所：** ポーズモードの BoneCraft タブ → Deform vs Control。

英語原本の画像説明（画像は省略）：例のリグの Deform と Control の一覧。このリグにはデフォームボーンが19本あり、制御ボーンはありません。

*標準テストビルドのポップオーバー、BoneCraft 9.2.19候補版。Bforartists 5.2.3、Blender 5.4 Alpha。例のリグの Deform と Control の一覧。このリグにはデフォームボーンが19本あり、制御ボーンはありません。*

---

### Delta Mush {#delta-mush}

**機能：** 関節の挟み込みを軽減する、滑らかな変形です。静止時の形を保ち、動作時の変形を整えます。

**使い方：** オブジェクトモードと、アクティブなメッシュが必要です。

1. **Add Delta Mush** をクリックします。

モディファイアーを追加し、静止形状にバインドします。直後にオプションを調整します。

2. Adjust Last Operation で **Iterations** を設定します。
3. **Smooth Strength** を設定します。
4. **Pin Borders** を有効または無効にします。
5. **Only Smooth Deform** を有効または無効にします。

追加後は、**Rebind** と **Remove** が表示されます。Settings の折りたたみ欄には、反復数、強度、境界固定の操作項目があります。

**場所：** BoneCraft → Skin → Delta Mush（オブジェクトモード、メッシュ）。

英語原本の画像説明（画像は省略）：Add Delta Mush で設定を開始します。クリック直後にオプションを調整します。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Add Delta Mush で設定を開始します。クリック直後にオプションを調整します。*

---

### Proximity Wrap {#proximity-wrap}

**機能：** 1つのメッシュを、別のメッシュの表面に第2の皮膚のように追従させます。体に密着する衣装に適しています。

**使い方：** オブジェクトモードと、アクティブな対象メッシュが必要です。バインド時は、駆動側のアーマチュアをレストポーズに保ちます。

1. 対象メッシュを選択します。
2. 別の **Driver Mesh** を選択します。
3. **Bind Proximity Wrap** をクリックします。

ボタン下の Options には、**Falloff Type** と **Max Distance** があります。9.1.2では値を保存しますが、Surface Deform のバインドは変わりません。バインド後は、**Rebind** と **Unbind** が表示されます。Unbind は、ビューポートとレンダーでモディファイアーを無効にしますが、削除しません。

**場所：** BoneCraft → Skin → Proximity Wrap（オブジェクトモード、メッシュ）。

英語原本の画像説明（画像は省略）：Bind Proximity Wrap の前に Driver Mesh を選択します。Options の折りたたみ欄は閉じています。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Bind Proximity Wrap の前に Driver Mesh を選択します。Options の折りたたみ欄は閉じています。*

---

## リグ制御 {#rig-controls}

これらのツールは、ポーズモードの BoneCraft タブに表示されます。

---

### Space Switch {#space-switch}

**機能：** アニメーション中に、ボーンが追従する空間を変更します。小道具を持つ手を、体への追従からワールド内の静止へ、1クリックで切り替えられます。

**主な操作項目：**

- **Add Space** と **Remove Space**（Manage Spaces の下のXアイコン） — World、Origin、別のボーンなど、追従先の空間。
- 各空間の名前が付いたボタン。現在の空間には ● が付きます。別のボタンをクリックして切り替えます。

**場所：** ポーズモードの BoneCraft タブ → Space Switch。

英語原本の画像説明（画像は省略）：空間をまだ定義していない Space Switch。Add Space で設定を開始します。

*標準パネルのポップオーバー、BoneCraft 9.2.18。空間をまだ定義していない Space Switch。Add Space で設定を開始します。*

---

### Spline IK {#spline-ik}

**機能：** ボーンチェーンをカーブに沿わせます。しっぽ、触手、ロープ、長い髪、背骨など、滑らかな大きい動きに使います。

**使い方：**

1. 開始ボーンをアクティブにします。
2. **Generate Spline IK** をクリックします。
3. Adjust Last Operation で **Chain Length** を設定します。
4. **Curve Resolution** を設定します。
5. **Stretch** を設定します。
6. **Volume Preservation** を設定します。

**Remove Spline IK** は、設定を取り除きます。

**場所：** ポーズモードの BoneCraft タブ → Spline IK。

英語原本の画像説明（画像は省略）：Spline IK の操作。生成後、Adjust Last Operation でチェーンのオプションを設定します。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Spline IK の操作。生成後、Adjust Last Operation でチェーンのオプションを設定します。*

---

### Chain Dynamics {#chain-dynamics}

**機能：** 物理に似た二次的な動きをボーンチェーンに追加します。親の移動に遅れて動き、親が止まると跳ね返ります。髪、しっぽ、アクセサリーなどに使います。

**使い方：**

1. ボーンチェーンを選択します。
2. **Add Chain Dynamics** をクリックします。
3. Adjust Last Operation で **Stiffness** を設定します。
4. **Damping** を設定します。
5. **Mass** を設定します。
6. **Gravity Scale** を設定します。

ボタン下の Settings にも、これらのパラメーターがあります。追加後は **Bake** と **Remove** が表示されます。衝突は簡略化した球を使うため、凹面で正しく衝突しない場合があります。

**場所：** ポーズモードの BoneCraft タブ → Chain Dynamics。

英語原本の画像説明（画像は省略）：Add Chain Dynamics で設定を開始します。パラメーターが必要なら Settings を展開します。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Add Chain Dynamics で設定を開始します。パラメーターが必要なら Settings を展開します。*

---

### Ribbon {#ribbon}

**機能：** 滑らかに曲がり、ねじれる Bendy Bones の帯を作ります。唇、眉、ベルトなど、柔らかい曲線部分に使います。

**使い方：**

1. ボーンチェーンを選択します。
2. **Generate Ribbon** をクリックします。
3. Adjust Last Operation で **Control Bones** を設定します。
4. **Ribbon Width** を設定します。

**Remove Ribbon** は、設定を取り除きます。

**場所：** ポーズモードの BoneCraft タブ → Ribbon。

英語原本の画像説明（画像は省略）：Ribbon の操作とチェーンの長さ。クリック直後に、生成したリボンを調整します。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Ribbon の操作とチェーンの長さ。クリック直後に、生成したリボンを調整します。*

---

### Viseme Library {#viseme-library}

**機能：** シェイプキーに関連付けたビジームセット（口形）を作成・管理します。文章からリップシンクのキーも生成します。VRChat への対応付けには VRChat Viseme Mapping、新しいビジームの生成には CATS の Visemes セクションを使います。

**主な操作項目：**

- **New Set** と **Delete** — セットを作成または削除します。
- 各セット内のビジームごとのスピーカーアイコン付きボタン — プレビューします。
- Lip Sync — 文章からビジームのキーを生成し、音素ごとのフレーム数とスムージングを設定します。

**場所：** CATS → Avatar Tools → Viseme Library（アーマチュア）。Lip Sync（ポーズモード）。

英語原本の画像説明（画像は省略）：Viseme Library は New Set から始まります。Lip Sync を使うには、ポーズモードに切り替えます。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Viseme Library は New Set から始まります。Lip Sync を使うには、ポーズモードに切り替えます。*

英語原本の画像説明（画像は省略）：Lip Sync の文章と Generate Lip Sync。時間とスムージングの設定には、Options を展開します。

*標準パネルのポップオーバー、BoneCraft 9.2.18。Lip Sync の文章と Generate Lip Sync。時間とスムージングの設定には、Options を展開します。*

---

### Set Driven Key {#set-driven-key}

**機能：** Python 式を使わず、ボーンのトランスフォーム値同士を関連付けます。たとえば、制御ボーンをX方向に動かすと、対象ボーンをZ方向に上げられます。このパネルは、ボーンのトランスフォームを対象に設定します。

1. **Driver Bone** を選択します。
2. **Driver Attribute** を選択します。
3. **Target Bone** を選択します。
4. **Target Attribute** を選択します。
5. ボーンにポーズを付けます。
6. 各点を記録します。
7. **Create SDK** を選択します。

**主な操作項目：**

- **Driver Bone** と **Driver Attribute** — 駆動する側。
- **Target Bone** と **Target Attribute** — 駆動される側。
- **Set Value** と **Record Point** — カーブ上の点を記録します。
- **Create SDK** — ドライバーを作ります。

**場所：** ポーズモードの BoneCraft タブ → Set Driven Key。

英語原本の画像説明（画像は省略）：ドリブンキーの点を記録する前に、駆動元と対象のボーンを選択します。この例の欄は未割り当てです。

*標準パネルのポップオーバー、BoneCraft 9.2.18。ドリブンキーの点を記録する前に、駆動元と対象のボーンを選択します。この例の欄は未割り当てです。*

---

### Rig Validator {#rig-validator}

**機能：** 規則に照らしてリグを確認し、問題を報告します。命名、欠落ボーン、壊れたコンストレイント、階層、ウェイト、Python が必要なドライバー、Mechanisms の規則を確認します。`DEF-upper_arm.L` のようなハイフン入りのボーン名も通ります。

**主な操作項目：**

- **Run Validation** — 全確認を実行し、結果を一覧にします。
- **Export Report** — 結果をファイルに保存します。

確認に失敗すると、Task Board（BoneCraft タブ → Overview → Task Board）にバリデーターのタスクが表示されます。

**場所：** BoneCraft タブ → Review → Rig Validator。

英語原本の画像説明（画像は省略）：検証で、コレクションの警告が1件報告されています。例のリグには子メッシュがなく、ウェイトの確認は省略されます。

*標準テストビルドのポップオーバー、BoneCraft 9.2.19候補版。Bforartists 5.2.3、Blender 5.4 Alpha。検証で、コレクションの警告が1件報告されています。例のリグには子メッシュがなく、ウェイトの確認は省略されます。*

---

### Rig Notes {#rig-notes}

**機能：** 設定内容、覚え書き、共同作業者への説明などの文章を、リグのボーンに付けます。

**主な操作項目：** **Add Note** と、各注記の **Remove**。Rig Readme は、注記を読み取り専用ページとして表示します。

**場所：** BoneCraft タブ → Overview → Rig Notes、および Review → Rig Readme。

英語原本の画像説明（画像は省略）：ポーズモードで Hips に付けた注記。Add Note は注記を作成し、Remove はその注記を削除します。

*標準テストビルドのポップオーバー、BoneCraft 9.2.19候補版。Bforartists 5.2.3、Blender 5.4 Alpha。ポーズモードで Hips に付けた注記。Add Note は注記を作成し、Remove はその注記を削除します。*

次へ：[Rig Builder](06-rig-builder.md)
