# Rig Builder {#rig-builder}

[← 目次](index.md)

両方の種類のリグを音声付きの実演で確認するには、[IK/FK の初心者向け解説と練習ファイル](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/tutorials/ikfk-beginner.md)を参照してください。

## 新しいリグを作る {#building-a-new-rig}

Rig Builder は、キャラクター用の新しいリグを作成します。左のツールシェルフにある <strong>Rig Builder</strong> タブから使います。シェルフを表示するには <strong>T</strong> を押します。Preferences → Tabs → Scene Properties → Show が有効な場合は、<strong>Properties</strong> エディターの <strong>Scene</strong> タブにも Rig Builder が表示されます。ツールシェルフの幅が狭いと、短いラベルを使ったコンパクトな配置になります。Auto-Rig Wizard が先頭にあり、その後に Quick Rig、Mannequin が続きます。ビューポートの Add → Armature メニューからも、ウィザードと Quick Rig を開けます。

---

### Auto-Rig Wizard {#auto-rig-wizard}

<strong>できること：</strong> メッシュ上にマーカーを配置し、それを基にウェイト付きの完全なリグを作る、段階式のガイドです。キャラクターを一からリギングする場合の基本的な方法です。

[ガイド1](02-guides-a.md#guide-1-get-your-first-avatar-into-vrchat)で、手順を順番に説明しています。

<strong>手順：</strong> Select Mesh → Rig Type → Body Markers → Finger Markers → Face Markers → Review → Generate

<strong>主な操作項目：</strong>

- <strong>Start Auto-Rig</strong> でウィザードを開きます。上部に <strong>Back</strong> と <strong>Cancel</strong> があります。メッシュ、リグの種類、マーカーの各段階では、下部に <strong>Next</strong> があります。Review では Next の代わりに <strong>Generate Rig</strong> を使います。最後の段階では <strong>Close Wizard</strong> を使います。
- メッシュ一覧では、対象のメッシュをクリックします。次の段階では、<strong>Body + Face</strong>、<strong>Body Only</strong>、または既存のアーマチュア用の <strong>Face Only</strong> を選べます。
- Smart Detection 内の <strong>Detect Markers</strong> は、メッシュの手足をたどり、各ボディマーカーを信頼度付きで配置します。<strong>Accept High</strong> は信頼度の高いマーカーを保持し、<strong>Reset Low</strong> は信頼度の低いマーカーを解除します。
- ボディ用の <strong>Guess Markers from Mesh</strong> と <strong>Guess Precision</strong>、手の形状から指マーカーを配置する <strong>Guess Finger Markers</strong>、および <strong>Guess Face Markers</strong> があります。
- Finger Detail は、作成する指の本数です。「0 — No Fingers」から「5 — Full Human Hand」まで選べます。
- 各マーカーの行には、矢印アイコンの <strong>Place Marker</strong>、チェックマークの <strong>Confirm Marker</strong>、円形矢印の <strong>Reset Marker</strong> があります。左右のマーカーでは、先頭に <strong>Toggle Symmetry</strong> アイコンもあります。
- <strong>Mirror L to R</strong> と <strong>Mirror R to L</strong> は、確定済みのマーカーを中心線の反対側へコピーします。
- <strong>Confirm All Placed</strong> は、その段階で配置済みのすべてのマーカーを確定します。
- <strong>Generate Rig</strong> は、確定済みマーカーからリグを作成します。最後の段階には、後述の <strong>Build Control Rig</strong> と <strong>Close Wizard</strong> があります。

<strong>Generate Rig が作成するもの：</strong>

- 選択した数の背骨と首のセグメント、および IK/FK、IK のみ、FK のみの腕と脚を持つボディリグ。方式は <strong>Kinematics</strong> オプションで指定します。
- 選択した本数に応じた指のボーン。
- <strong>Body + Face</strong> ではフェイスリグ。<strong>Generate Control Shapes</strong> が有効なら、コントロールシェイプも作成します。
- 選択した品質のスキンウェイト。高密度のメッシュは軽量なプロキシメッシュを介してウェイトを付けるため、678,000頂点のキャラクターでも、無言で失敗するのではなく、約一分で処理されます。

<strong>Build Control Rig：</strong> Review の段階には、<strong>Twist Bones</strong>、<strong>Skirt Bones</strong>、<strong>Face Controls</strong>、<strong>Joint Correctives</strong> も表示されます。Generate Rig は、これらのオプションを適用しません。これらはエンジン向けコントロールリグ用です。このリグには、ツイストボーン、脚に追従するスカートボーン、目の注視とまばたきのコントロール、関節補正用シェイプキーが含まれます。Generate Rig の後、最後の段階に <strong>Build Control Rig</strong> が表示されます。このコマンドは、選択したオプションを使い、生成済みアーマチュア上にコントロールリグを作成します。<strong>Close Wizard</strong> の前に、<strong>Build Control Rig</strong> をクリックしてください。ウィザードを閉じると、オプションはリセットされます。Rig Tools の Control Layer パネルは、この方法で作成したリグでのみ表示されます。

<strong>場所：</strong> Rig Builder → Auto-Rig Wizard

<strong>ビューポートツールで複数のマーカーを配置する：</strong>

1. ウィザードを開始します。
2. ボディ、指、または顔のマーカーを配置する段階まで進みます。
3. Object Mode で、ビューポートのツールバーにある Place Rig Markers を有効にします。

ツールヘッダーには、次の未確定マーカーの名前、軸ロック、ミラー切り替えが表示されます。

4. ウィザードで指定したメッシュをクリックし、そのマーカーを配置して確定します。
5. ツールがその段階の完了を示したら、ウィザードの <strong>Next</strong> を押します。

対称配置はウィザードの設定に従います。各マーカーの Place ボタンも引き続き使えます。メッシュ以外の場所をクリックしても、マーカーは配置されません。

---

### Quick Rig {#quick-rig}

<strong>できること：</strong> BoneCraft の Basic Humanoid または Rigify のメタリグを、一度のクリックで追加します。Basic Humanoid は19本のボーンで構成され、Rigify は不要です。Quick Rig はウィザードより速い方法ですが、メッシュに合わせた個別調整は少なくなります。

<strong>主な操作項目：</strong>

- Basic Humanoid ボタンと Rigify のメタリグがあります。Rigify が無効な状態で Rigify のプリセットを使う場合は、先に <strong>Enable Rigify</strong> を選択します。
- リグのボタンを押すと、すぐにリグが追加されます。Adjust Last Operation には、フィッティング、自動ウェイト、<strong>Add IK/FK Controllers</strong>、<strong>Initial Pose</strong> があります。
- <strong>T-Pose</strong> と <strong>A-Pose</strong> は、選択したリグのレストポーズを切り替えます。
- Troubleshooting を展開すると、<strong>Diagnose Quick Rig (print to console)</strong> があります。メタリグではないアーマチュアがアクティブな場合は、<strong>Inspect Active Rig Controls</strong> も表示されます。
- Rigify のメタリグがアクティブな場合、Troubleshooting には Inspect Active Rig Controls の代わりに <strong>Generate Control Rig (active metarig)</strong> が表示されます。これにより、Rigify のコントロールリグを生成します。

<strong>BoneCraft Rigs のスターターカタログ：</strong> 同梱された九種類のスターターは、すべて標準の下部アセットシェルフにある <strong>Starter Rigs</strong> カタログにまとめられています。

1. シェルフの左側にあるカタログメニューを開きます。
2. ライブラリで <strong>All</strong> を選びます。
3. <strong>Starter Rigs</strong> を一度有効にして、既存のカタログタブの隣にタブを追加します。
4. そのタブを選ぶと、スターターを一覧できます。

<strong>Add → Armature → Starter Rig Catalog</strong> は、依存アドオンの状態を確認しながら、スターターをフィットして追加するポップアップを開きます。

Basic Humanoid に Rigify は不要です。それ以外のサムネイルには <strong>Rigify</strong> のラベルがあります。Rigify が無効な場合、カタログのポップアップでそれらを選択またはドロップすると、<strong>Enable Rigify & Add Rig</strong> と Cancel が表示されます。承認すると、インストール済みの Rigify を有効にし、そのスターターの追加を続けます。キャンセルすると何も追加しません。<strong>Quick Rig</strong> にも <strong>Enable Rigify</strong> があります。Rigify が利用できない場合は、カタログポップアップのコンテキストメニューにも表示されます。必要な依存アドオンやプリセットがない場合は、理由が説明されます。インストール済みバージョンにそのプリセットがない場合、ポップアップが代わりのリグを追加することはありません。

標準の下部アセットシェルフは、アーマチュアのアセットをインポートします。以下のように依存アドオンを考慮した手順を使う場合は、<strong>Add → Armature → Starter Rig Catalog</strong> を開いてください。

メッシュを選択した状態でスターターを追加すると、そのメッシュにフィットします。ポップアップ内のサムネイルをクリックして追加するか、ビューポートへドラッグします。自動ウェイトとコントロール生成は、最初は無効です。後から <strong>Adjust Last Operation</strong> で変更してください。

メッシュを選択していなかった場合：

1. 新しいスターターを選択します。
2. Quick Rig で <strong>Mesh</strong> を選びます。
3. <strong>Fit Dropped Rig</strong> をクリックします。

フィッティングは、スケルトンの大きさと位置を調整します。コントロールやウェイトを生成する前に：

1. 関節の配置を確認します。
2. 必要に応じて、関節の配置を編集します。

ビューポートの外へドラッグするか、Esc を押すか、右クリックすると、何も追加せずにキャンセルします。

<strong>場所：</strong> Rig Builder → Quick Rig。Add → Armature → Quick Rig からも、用意されたリグを追加できます。

---

### Mannequin {#mannequin}

<strong>できること：</strong> 既存のリグの周囲にプレビューメッシュを作り、完成したキャラクターメッシュがなくても変形を確認できるようにします。リグがまだない場合は、Quick Rig で追加してください。Mannequin を使う前に、アーマチュア、またはそれを親に持つメッシュを選択します。マネキンはプレビュー専用です。最終的に使う前に、自分のメッシュに置き換えてください。

<strong>主な操作項目：</strong>

- <strong>Quick Mannequin</strong> は、固定の初期設定でプレビューを作り、このリグの前のマネキンを置き換えます。
- <strong>Add Mannequin</strong> は、シーンの設定を使ってプレビューを作ります。初期設定では、既存のマネキンを置き換えます。クリック後、Adjust Last Operation に Replace Existing が表示されます。
- <strong>Regenerate</strong> は、保存済みの設定を使って、既存のプレビューを再生成します。
- <strong>Remove</strong> は、マネキンのメッシュを削除し、アーマチュアを残します。
- ボタンの下にある Options には、<strong>Mode</strong>、<strong>Body Type</strong>、密度、<strong>Radius Scale</strong> があります。Options 内の Advanced には、部位ごとのスケールと出力設定があります。変更したシーン設定を使うには、もう一度 <strong>Add Mannequin</strong> をクリックします。

<strong>場所：</strong> Rig Builder → Mannequin

---

## マネキンのワークショップ：文章による手順 {#illustrated-mannequin-workshop}

<!-- Keep each illustrated step together and preserve the manual's print scale. -->
<style>
section.chapter:has(#ch-06-rig-builder) img { max-width: 100%; max-height: 155mm; width: auto; height: auto; }
@media print {
  [id="06-rig-builder--illustrated-mannequin-workshop"] { break-before: page; break-after: avoid; }
  h4[id^="06-rig-builder--"] { break-before: page; break-after: avoid; }
  h3[id^="06-rig-builder--part-"] { break-before: page; break-after: avoid; }
  h3[id^="06-rig-builder--part-"] + h4 { break-before: avoid; }
  section.chapter:has(#ch-06-rig-builder) h4 + p { break-after: avoid; }
  section.chapter:has(#ch-06-rig-builder) p:has(> img) { break-before: avoid; break-after: avoid; }
  section.chapter:has(#ch-06-rig-builder) p:has(> img) + p { break-before: avoid; }
}
</style>

次の三つのパートを、順番に進めてください。

1. [A — Simple Human からマネキンを作る](#part-a-simple-human-to-mannequin)。
2. [B — リグのないマネキンを Auto-Rig に通す](#part-b-rigless-mannequin-through-auto-rig)。
3. [C — ウェイトを確認して IK/FK を使う](#part-c-test-weights-and-use-ikfk)。

英語原本には、ワークショップの番号付き手順ごとに、実際のインターフェースのスクリーンショットがあります。赤い番号は、そのキャプションに対応しています。これらの画像は、<strong>BoneCraft 9.1.2 リリース</strong>と `Bforartists 5.2.0` で撮影されました。この画像なし版では、画像を省略し、文章による手順、画像説明、キャプションを残しています。Blender では、パネルの配置やショートカットが異なる場合があります。名前で示したコマンドを基準にしてください。

ここでは省略した英語原本の画像には、撮影時の9.1.2のラベルが残っています。現在の移動先は、<strong>Rig Builder → Quick Rig</strong>、<strong>Rig Builder → Auto-Rig Wizard</strong>、<strong>BoneCraft → Skin → Weight Tools</strong> です。Starter Rigs は、現在は標準の下部カタログタブを使います。この画像なし版は、9.2.18 または9.2.19でチュートリアルを新たに再実行したと主張するものではありません。

この練習では、リギングを学ぶための、単純なカプセル形状のプレビューを作ります。頭、手、胴体は仮の形状です。完成したキャラクターモデルではありません。新しいファイルで始めてください。元のメタリグを失わずに変換を繰り返せるよう、二つのチェックポイントを両方保存しておきます。

リポジトリの `examples/mannequin/` に、両方のチェックポイントがあります。`SimpleHuman_Mannequin.blend` はパートA終了時のニュートラルな状態で、`Mannequin_AutoRig.blend` はウェイトを修正し、ポーズを付けたパートC終了時の作例です。

### パートA：Simple Human からマネキンを作る {#part-a-simple-human-to-mannequin}

#### A1. Rigify を有効にする {#a1-enable-rigify}

1. 新しいシーンで始めます。
2. <strong>Scene Properties → Rig Builder → Quick Rig</strong> を開きます。
3. Rigify のプリセットが使えない場合は、<strong>Enable Rigify</strong> をクリックします。

このチュートリアルでは、Rigify の `Simple Human` メタリグを使います。<strong>BoneCraft Basic Humanoid (19 bones)</strong> は、別のプリセットです。

英語原本の画像説明（画像省略）：A1：Rigify を有効にする

*1 — Scene Properties。2 — Enable Rigify。*

#### A2. Simple Human を追加する {#a2-add-simple-human}

Quick Rig の `Simple Human` をクリックします。編集可能なメタリグが追加されますが、まだメッシュではありません。このリリースでは、29本のボーンで構成されています。

英語原本の画像説明（画像省略）：A2：Simple Human を追加する

*1 — Simple Human プリセット。*

#### A3. メタリグを確認する {#a3-inspect-the-metarig}

1. ポインターをビューポートに移動します。
2. `Numpad 1` を押して、Front Orthographic にします。
3. スケルトン全体が見えていることを確認します。
4. マウスホイールで、スケルトンが収まる表示に調整します。

新しいメタリグは、Pose Mode で始まる場合があります。

英語原本の画像説明（画像省略）：A3：メタリグを確認する

*1 — 正面ビュー。2 — Simple Human のスケルトン。*

#### A4. Object Mode に戻る {#a4-return-to-object-mode}

レストポーズを変更したり、マネキンを生成したりする前に：

1. ビューポートのモードメニューで <strong>Object Mode</strong> を選びます。
2. `SimpleHumanArmature` を選択したままにします。

英語原本の画像説明（画像省略）：A4：Object Mode に戻る

*1 — モードメニュー。2 — Object Mode。*

#### A5. Tポーズにする {#a5-use-a-t-pose}

Quick Rig で <strong>T-Pose</strong> をクリックします。腕が水平に伸びます。独自の体型を使う場合は、プレビューを生成する前に、Edit Mode でメタリグをフィットさせてください。この練習では、左右の関節を対称に保ちます。

英語原本の画像説明（画像省略）：A5：Tポーズにする

*1 — T-Pose コマンド。*

#### A6. マネキンを生成する {#a6-generate-the-mannequin}

1. <strong>Mannequin → Options</strong> を展開します。
2. `Mode: Universal` に設定します。
3. `Body Type: Neutral` に設定します。
4. <strong>Medium</strong> を選びます。
5. `Radius Scale: 1.00` に設定します。
6. Advanced では、部位ごとのスケールを1.00のままにします。
7. `Joined (non-manifold)` を選びます。
8. <strong>Flat colour</strong> を選びます。
9. <strong>Joint Smoothing</strong> を有効にします。
10. Unified Volume は無効のままにします。
11. <strong>Add Mannequin</strong> をクリックします。

省略した英語原本の画像は、生成されたカプセル形状のメッシュを示しています。Add は現在のオプションを使い、Regenerate は保存済みのマネキン設定を再利用します。

英語原本の画像説明（画像省略）：A6：マネキンを生成する

*1 — Add Mannequin。2 — Universal と体型の設定。3 — Joined 出力とスムージング。*

#### A7. ボーンのポーズを試す {#a7-try-a-bone-pose}

正面ビューでは、キャラクターの左側が、画面の右側に見えます。

1. アーマチュアを選択します。
2. <strong>Pose Mode</strong> に切り替えます。
3. 左前腕のボーンをクリックします。
4. Rotate ツールで、ボーンを少し回転させます。

付属するマネキンが追従します。これは、メタリグにウェイトを付けたプレビューです。パートCで使うアニメーター向けコントロールは、まだありません。

英語原本の画像説明（画像省略）：A7：ボーンのポーズを試す

*1 — Pose Mode。2 — 選択した前腕と、そのトランスフォームギズモ。*

#### A8. プレビューを元に戻して保存する {#a8-restore-and-save-the-preview}

1. ポインターをビューポートに置き、すべてのポーズボーンを選択します。
2. <strong>F3</strong> を押します。
3. `Clear Pose Transforms` を検索します。
4. <strong>All</strong> を選びます。
5. マネキンがTポーズに戻ったことを確認します。
6. <strong>File → Save As</strong> を開きます。
7. `SimpleHuman_Mannequin.blend` という名前で保存します。

このチェックポイントを残してから、先へ進んでください。

英語原本の画像説明（画像省略）：A8：プレビューを元に戻して保存する

*1 — Clear Pose Transforms の検索。2 — All は、選択したポーズボーンをリセットします。*

### パートB：リグのないマネキンを Auto-Rig に通す {#part-b-rigless-mannequin-through-auto-rig}

#### B1. マネキンのメッシュを選ぶ {#b1-select-the-mannequin-mesh}

パートAのニュートラルなチェックポイントから続けます。このパートでは、ウィザードを実行する前に、マネキンのリグを意図的に取り外します。

1. <strong>Object Mode</strong> に切り替えます。
2. Outliner で `SimpleHumanArmature_Mannequin` を選びます。

パートAの状態を残すため、別のファイル名で保存してください。

英語原本の画像説明（画像省略）：B1：マネキンのメッシュを選ぶ

*1 — アーマチュアではなく、メッシュを選択します。*

#### B2. プレビューをメッシュに焼き込む {#b2-bake-the-preview-into-a-mesh}

マネキンを、元に戻したTポーズのままにします。マネキンだけを選択しておきます。

1. <strong>F3</strong> を押します。
2. `Convert Mesh` を検索します。
3. `Convert Mesh` を実行します。

見えているニュートラルな形状を保ち、Armature モディファイアーを取り除きます。

英語原本の画像説明（画像省略）：B2：プレビューをメッシュに焼き込む

*1 — Convert Mesh コマンド。*

#### B3. 親子関係を解除する {#b3-clear-the-parent}

1. <strong>Alt+P</strong> を押します。
2. `Clear and Keep Transformation` を選びます。

メッシュの位置を変えずに、元のメタリグとの親子関係を解除します。

英語原本の画像説明（画像省略）：B3：親子関係を解除する

*1 — Clear and Keep Transformation。*

#### B4. 元のウェイトを削除する {#b4-remove-the-old-weights}

この操作は、使い捨ての練習用メッシュに対して行うものです。既存のグループは元のメタリグ用です。ウィザードが、新しいグループを作成します。

1. <strong>Object Data Properties → Vertex Groups</strong> を開きます。
2. 一覧のドロップダウンメニューで `Delete All Groups` を選びます。

英語原本の画像説明（画像省略）：B4：元のウェイトを削除する

*1 — Vertex Groups メニュー。2 — Delete All Groups。*

#### B5. リグを外したチェックポイントを確認する {#b5-verify-the-rigless-checkpoint}

1. Outliner の目のアイコンを使い、元の `SimpleHumanArmature` を非表示にします。
2. マネキンが引き続き見えていることを確認します。
3. Modifiers パネルに Armature モディファイアーがないことを確認します。
4. Vertex Groups の一覧が空であることを確認します。

これが、リグを持たないマネキンの入力データです。BoneCraft 9.1.2 は、アーマチュアからマネキンを生成します。そのプレビューを切り離すことで、リグのない練習用メッシュを用意します。

英語原本の画像説明（画像省略）：B5：リグを外したチェックポイントを確認する

*1 — 元のメタリグを非表示にします。2 — 空のモディファイアースタック。*

#### B6. ビューポートの Rig Builder タブを有効にする {#b6-enable-the-viewport-rig-builder-tab}

検証時の9.1.2ホストでは、Scene Properties から開始した Place Marker が、ビューポートのクリックを受け付けませんでした。マーカーの配置には、ビューポートのタブを使ってください。

1. <strong>Edit → Preferences → Add-ons → BoneCraft → Tabs</strong> を開きます。
2. <strong>Rig Builder</strong> を有効にします。
3. <strong>Left</strong> を選びます。
4. Preferences を閉じます。
5. ポインターをビューポートに移動します。
6. 左のツールシェルフが隠れている場合は、<strong>T</strong> を押します。

英語原本の画像説明（画像省略）：B6：ビューポートの Rig Builder タブを有効にする

*1 — Rig Builder を有効にします。2 — 左のツールシェルフへの配置。*

#### B7. Auto-Rig を開始する {#b7-start-auto-rig}

リグのないマネキンを選択し、<strong>Start Auto-Rig</strong> をクリックします。省略した英語原本の画像は、同じ機能を持つ Scene Properties のボタンを示しています。前の手順で有効にしたビューポートの Rig Builder タブでも、上部に同じコマンドがあります。

英語原本の画像説明（画像省略）：B7：Auto-Rig を開始する

*1 — Start Auto-Rig。*

#### B8. 入力メッシュを選ぶ {#b8-choose-the-input-mesh}

ウィジェットや、別のプレビューオブジェクトを選ばないでください。

1. `Select Mesh` で、マネキンを選びます。
2. メッシュの選択確認を確かめます。
3. <strong>Next</strong> をクリックします。

英語原本の画像説明（画像省略）：B8：入力メッシュを選ぶ

*1 — 入力するマネキン。2 — Next。*

#### B9. 両方式を使うボディリグを選ぶ {#b9-choose-a-body-rig-with-both-methods}

このカプセル形状のマネキンには、顔のトポロジーがありません。そのため、Body + Face は不要です。

1. <strong>Body Only</strong> を選びます。
2. `Kinematics: IK + FK` を選びます。
3. <strong>Generate Control Shapes</strong> は有効のままにします。
4. <strong>Next</strong> をクリックします。

英語原本の画像説明（画像省略）：B9：両方式を使うボディリグを選ぶ

*1 — Body Only。2 — IK + FK。3 — Next。*

#### B10. 最初のボディマーカーを検出する {#b10-detect-initial-body-markers}

検出結果は、調整の出発点です。確認せずに、推定された配置を受け入れないでください。

1. この左右対称のマネキンでは、<strong>Mirror Symmetry</strong> を有効のままにします。
2. Body Markers の Smart Detection で、<strong>Detect Markers</strong> をクリックします。

英語原本の画像説明（画像省略）：B10：最初のボディマーカーを検出する

*1 — Detect Markers。2 — Mirror Symmetry。*

#### B11. 検出された位置を確認する {#b11-review-the-detected-positions}

部位ごとに分かれたこのプレビューでは、信頼度の低い推定がいくつか発生します。生成する前に：

1. 頭頂、首の付け根、骨盤、手首、足首の位置を、見えているメッシュと照合します。
2. 主な目印と、任意の精密な目印を確認します。
3. 必要に応じて、目印を修正します。

信頼度のラベルは、最初の検出結果を表します。行の先頭の緑色のチェックは、現在の配置が確定済みであることを示します。

英語原本の画像説明（画像省略）：B11：検出された位置を確認する

*1 — 検出信頼度の概要。2 — ボディマーカーの行。*

#### B12. 手首をメッシュ上に配置する {#b12-place-a-wrist-on-the-mesh}

正面ビューでは、キャラクターの左手首は、画面の右側にあります。

1. マーカーがすでに確定済みの場合は、その行をリセットして配置ボタンを表示します。
2. ビューポートの <strong>Rig Builder</strong> タブで、Wrist Left の <strong>Place Marker</strong> スポイトをクリックします。
3. ビューポートで、手首の表面をクリックします。

英語原本の画像説明（画像省略）：B12：手首をメッシュ上に配置する

*1 — Wrist Left の配置コントロール。2 — 手首の表面をクリックします。*

#### B13. ミラー配置した手首と足首を確認する {#b13-check-the-mirrored-wrist-and-ankles}

1. 両方の手首の行に緑色のチェックがあり、X座標が互いに正負を反転した値になっていることを確認します。
2. `Ankle Left` を、つま先ではなく足首の関節に、同じ方法で配置します。

対称配置により Ankle Right が設定されます。メッシュと照らして対称性を確認してください。大きさの違うキャラクターに、作例の座標をそのままコピーしないでください。

英語原本の画像説明（画像省略）：B13：ミラー配置した手首と足首を確認する

*1 — 確定した左右の手首。2 — メッシュ上のミラー配置した手首。*

#### B14. 肩と肘を調整する {#b14-refine-shoulders-and-elbows}

1. Precision Markers までスクロールします。
2. `Shoulder Left` をリセットします。
3. `Shoulder Left` を、上腕の回転中心に配置します。
4. `Elbow Left` をリセットします。
5. `Elbow Left` を、肘の隙間に配置します。
6. ミラー配置された反対側も確認して確定します。
7. 手首は、前腕の手側の端に配置したままにします。

これらの点が、腕のチェーンを決めます。肩や肘が誤ったカプセル上に推定されていたら、修正してください。

英語原本の画像説明（画像省略）：B14：肩と肘を調整する

*1 — 肩と肘のマーカー行。2 — 肩。3 — 肘。*

#### B15. 股関節と膝を調整する {#b15-refine-hips-and-knees}

1. `Hip Left` を、太ももの上端に配置します。
2. `Knee Left` を、太ももとすねの間の隙間に配置します。
3. 対称配置で設定された反対側を確認します。
4. 骨盤は、左右の股関節の間の中心線上に置きます。

英語原本の画像説明（画像省略）：B15：股関節と膝を調整する

*1 — 股関節と膝の行。2 — 股関節の表面。3 — 膝の隙間。*

#### B16. 横から奥行きとつま先を確認する {#b16-check-depth-and-toes-from-the-side}

1. ポインターをビューポートに置き、`Numpad 3` を押します。
2. 正面からだけでなく、Right Orthographic でも目印を確認します。
3. `Toe Left` を、足の前の方に配置します。
4. ミラー配置された反対側を確認します。

正面では正しく見えるマーカーでも、体の前方や後方にずれすぎている場合があります。

英語原本の画像説明（画像省略）：B16：横から奥行きとつま先を確認する

*1 — Right Orthographic。2 — つま先のマーカー行。3 — 足の表面。*

#### B17. かかとを配置する {#b17-place-the-heels}

1. かかとの推定位置が誤っている場合は、そのかかとをリセットします。
2. 側面ビューで、`Heel Left` を足の後ろ側に配置します。
3. Heel Right を確認します。

これらのマーカーは任意です。検証したリリースでは、両方をゼロのままにすると、近接に関する警告が出ました。足に配置すると、その警告は消えました。

英語原本の画像説明（画像省略）：B17：かかとを配置する

*1 — 確定した左右のかかと。2 — かかとの位置。*

#### B18. 確定して先へ進む {#b18-confirm-and-continue}

1. 頭頂、首の付け根、骨盤、および左右一対のすべての目印を確認します。
2. <strong>Confirm All Placed</strong> をクリックします。
3. <strong>Next</strong> をクリックします。

名前の横にある緑色のチェックは、確定状態を示します。9.1.2では、最初の信頼度を表す REVIEW/ADJUST のラベルが、そのまま表示される場合があります。

英語原本の画像説明（画像省略）：B18：確定して先へ進む

*1 — Confirm All Placed。2 — Next。*

#### B19. このメッシュでは指を省略する {#b19-skip-fingers-for-this-mesh}

このマネキンには手のカプセルがありますが、指の形状はありません。

1. `0 — No Fingers` を選びます。
2. <strong>Next</strong> をクリックします。

実際の手のメッシュを使う場合は、代わりに：

1. 適切な指の本数を選びます。
2. 指のマーカーを配置します。

英語原本の画像説明（画像省略）：B19：このメッシュでは指を省略する

*1 — No Fingers。2 — Next。*

#### B20. 確認して生成する {#b20-review-and-generate}

先へ進む前に、<strong>All checks passed</strong> であることを確認してください。これらの設定は、この単純な練習用マネキンに対するものです。あらゆる書き出しに共通の必須条件ではありません。

1. <strong>IK + FK</strong> を選びます。
2. コントロールシェイプを有効にします。
3. `Spine Segments: 3` に設定します。
4. `Neck Segments: 1` に設定します。
5. `No Fingers` を選びます。
6. <strong>Game Ready</strong> を選びます。
7. Twist Bones を無効にします。
8. Skirt Bones を無効にします。
9. Preserve Volume を無効にします。
10. Joint Correctives を無効にします。
11. <strong>Generate Rig</strong> をクリックします。

英語原本の画像説明（画像省略）：B20：確認して生成する

*1 — マーカーの確認。2 — 生成設定。3 — Generate Rig。*

#### B21. アニメーター用コントロールを作る {#b21-build-the-animator-controls}

生成後に、<strong>Build Control Rig</strong> をクリックします。Generate Rig は、ボディリグとウェイトを用意します。Build Control Rig は、以下で使うコントロール層を追加します。完了パネルに汎用的なマネキン作成の案内が表示されても、入力メッシュはすでに存在しています。Quick Mannequin をもう一度クリックしないでください。

英語原本の画像説明（画像省略）：B21：アニメーター用コントロールを作る

*1 — Build Control Rig。*

#### B22. ウィザードを終了する {#b22-finish-the-wizard}

1. コントロールリグの完了メッセージを待ちます。
2. <strong>Close Wizard</strong> をクリックします。
3. 元の Simple Human メタリグは、非表示のままにします。

新しいアーマチュアが Outliner に表示されます。新しいリグで、実際にメッシュが変形する必要があります。ボーンが見えるだけでは、変形が機能している証拠にはなりません。

英語原本の画像説明（画像省略）：B22：ウィザードを終了する

*1 — 作成ボタンは無効になっています。2 — Close Wizard。*

### パートC：ウェイトを確認して IK/FK を使う {#part-c-test-weights-and-use-ikfk}

検証したリリースでは、生成されたアーマチュアのオブジェクト名は次のとおりです。Outliner とウェイトツールで、この名前を使ってください。

```text
BoneForge_Rig
```

`FK (Forward Kinematics)` は、階層をたどって回転を伝えます。上腕の回転が前腕に伝わり、続いて手に伝わります。大きく振る動きや、自由に動く手足に向いています。`IK (Inverse Kinematics)` は、末端から動きを決めます。手首や足首のターゲットを動かすと、ソルバーがそこへ届くようにチェーンを曲げます。接地した足や、面に触れ続ける必要がある手に向いています。

| 目的 | 使うコントロール | 確認する点 |
|---|---|---|
| 腕を振る | 肩と肘の FK コントロール | 子のコントロールが親に追従すること |
| 手を配置する | 手首の IK ターゲット | 肩と肘がターゲットに向かって解かれること |
| 足を接地させる | その脚の足首 IK ターゲット | 到達可能な位置のターゲットを置いたまま、体を動かすこと |
| 肘や膝の曲がる向きを決める | IK ポールコントロール | ポールは曲がる向きを決めるもので、手首や足首のターゲットではないこと |
| 方式を切り替える | 各手足の IK/FK ボタン | アニメーションのキーを打つ前に、スナップ後のポーズを確認すること |

以下の練習では、片腕を両方のモードで比較します。各手足に、それぞれ独立した切り替えがあります。`Bake IK / Bake FK` は、アニメーションを変換するツールです。単一のポーズを切り替えるだけでは、アニメーションのベイクやキー設定の代わりにはなりません。その他の操作項目は、[Control Layer](05-rig-tools.md#control-layer-ikfk)を参照してください。

#### C1. Control Layer を開く {#c1-open-the-control-layer}

1. <strong>生成されたアーマチュア</strong>を選択します。
2. <strong>Pose Mode</strong> を選びます。
3. <strong>BoneCraft → Review → Control Layer</strong> を開きます。
4. <strong>arm-L → FK</strong> を選びます。

腕と脚には、それぞれ独立した IK/FK 切り替えがあります。左右は、キャラクターから見た向きです。正面ビューでは、arm-L は画面の右側に見えます。

英語原本の画像説明（画像省略）：C1：Control Layer を開く

*1 — Pose Mode。2 — Control Layer と arm-L の切り替え。*

#### C2. アニメーター用コントロールを表示する {#c2-show-the-animator-controls}

1. アーマチュアの <strong>Object Data Properties → Bone Collections</strong> を開きます。
2. `Controls` の Solo の星を選びます。
3. <strong>FK</strong> の Solo の星を選びます。
4. メッシュに隠れてコントロールが見えない場合は、Viewport Display の <strong>In Front</strong> を有効にします。
5. 後でターゲットを使うときは、<strong>IK</strong> も含めます。

Solo の選択により、それらのコントロールシェイプだけを表示します。この標準コレクション一覧は、このホストで BoneCraft の Collections パネルを描画できない場合にも使えます。

英語原本の画像説明（画像省略）：C2：アニメーター用コントロールを表示する

*1 — Controls と FK の Solo の星。2 — In Front。*

#### C3. 前腕の FK コントロールを選ぶ {#c3-select-the-forearm-fk-control}

1. 正面ビューで、キャラクターの左肘にある円形のコントロールをクリックします。
2. ビューポートの選択名が <strong>forearm.fk-L</strong> であることを確認します。

前腕の FK コントロールは、肘を中心に回転します。肩のコントロールを選ぶと、代わりに上腕と、その子のボーンが回転します。

英語原本の画像説明（画像省略）：C3：前腕の FK コントロールを選ぶ

*1 — 選択した forearm.fk-L コントロール。2 — arm-L は FK が有効です。*

#### C4. 回転させて変形を確認する {#c4-rotate-and-inspect-the-deformation}

この正面ビューの作例では、グローバル <strong>Y</strong> 軸を中心に、約 `−45°` 回転させることが目標です。次のいずれかの方法を使います。

- Rotate ツールで、選択した FK コントロールを回転させます。
- 作例の Bforartists キーマップを使う場合は、次の手順に従います。

1. <strong>Ctrl+E</strong> を押します。
2. <strong>Y</strong> を押します。
3. <strong>-45</strong> と入力します。
4. <strong>Enter</strong> を押します。

Blender の標準の回転ショートカットは <strong>R</strong> です。省略した英語原本の画像は、初期状態のウェイトの問題を意図的に示しています。前腕と一緒に、上腕のカプセルも傾いています。これを完成したリグとして受け入れないでください。

英語原本の画像説明（画像省略）：C4：回転させて変形を確認する

*1 — FK のテスト中に起きる、誤った上腕の動き。*

#### C5. マネキンのウェイトを再計算する {#c5-recalculate-the-mannequin-weights}

上のポーズテストで問題が出た場合は、次の手順に従います。

1. <strong>Object Mode</strong> に切り替えます。
2. メッシュを選択します。
3. <strong>BoneCraft → Skin → Weight Tools → Automatic Bone Weight Recalculation</strong> を開きます。
4. Mesh to Reweight にマネキンを設定します。
5. Existing Armature に、<strong>生成されたアーマチュア</strong>を設定します。
6. <strong>Body</strong> を選びます。
7. `Body Method: Bone Heat` を選びます。
8. `New Weight Strength: 1.00` に設定します。
9. `Smooth Passes: 0` に設定します。
10. `Max Bones per Vertex: 0` に設定します。
11. `Minimum Weight: 0.001` に設定します。
12. <strong>Keep Weight Backup</strong> は有効のままにします。
13. <strong>Automatic Bone Weight Recalculation</strong> を実行します。

検証したリリースでは、この操作で部位ごとに分かれたプレビューを修正できました。

英語原本の画像説明（画像省略）：C5：マネキンのウェイトを再計算する

*1 — メッシュとアーマチュア。2 — Bone Heat。3 — 置き換え設定とバックアップ。4 — 再計算。*

#### C6. 修正後の FK の曲がり方を確認する {#c6-verify-the-repaired-fk-bend}

1. 生成されたアーマチュアをもう一度選びます。
2. <strong>Pose Mode</strong> に戻ります。

今度は、上腕が肩から肘まで水平なままになり、前腕が肘から持ち上がるはずです。非表示の `WEIGHTS_BACKUP_…` オブジェクトに、元のウェイトが保存されています。自分のキャラクターをアニメーションさせる前に、他の手足もテストしてください。スケルトンを生成しただけでは、スキニングが正しい証拠にはなりません。

英語原本の画像説明（画像省略）：C6：修正後の FK の曲がり方を確認する

*1 — 上腕がその位置にとどまります。2 — 前腕が肘から曲がります。*

#### C7. 同じ腕を IK に切り替える {#c7-switch-the-same-arm-to-ik}

<strong>arm-L → IK</strong> をクリックします。切り替え時には、ターゲットが現在のポーズへスナップするため、腕は上がったままになるはずです。ターゲットが見えない場合は、表示する Solo コレクションに <strong>IK</strong> を加えます。切り替えは、チェーンを動かすコントロールを変更します。新しいアニメーションを記録する操作ではありません。

英語原本の画像説明（画像省略）：C7：同じ腕を IK に切り替える

*1 — arm-L の IK 切り替え。2 — 切り替え時にもポーズが保持されます。*

#### C8. 手首の IK ターゲットを選ぶ {#c8-select-the-wrist-ik-target}

1. 手首のコントロールをクリックします。
2. 選択名が <strong>forearm.ik-L</strong> であることを確認します。

名前に forearm とありますが、これは腕のチェーンの末端ターゲットです。手を配置するには、このターゲットを動かします。ソルバーは、ターゲットに届くよう、肩と肘の角度を変えます。

英語原本の画像説明（画像省略）：C8：手首の IK ターゲットを選ぶ

*1 — 選択した手首のターゲット。2 — 選択名。*

#### C9. ターゲットを動かして比較する {#c9-move-the-target-and-compare}

ターゲットは、腕の届く範囲内に置いてください。グローバル <strong>X</strong> 軸に沿って、手首のターゲットを少し内側へ動かすことが目標です。この作例では、`−0.15 m` 動かすと、曲がり方の違いがはっきり分かります。次のいずれかの方法を使います。

- Move ツールの X の矢印をドラッグします。
- 作例のキーマップを使う場合は、次の手順に従います。

1. <strong>Ctrl+W</strong> を押します。
2. <strong>X</strong> を押します。
3. `-0.15` と入力します。
4. <strong>Enter</strong> を押します。

Blender の標準の移動ショートカットは <strong>G</strong> です。腕全体を FK の作例と比較してください。末端が先導し、腕の両方のセグメントが追従します。

英語原本の画像説明（画像省略）：C9：ターゲットを動かして比較する

*1 — 手首の末端。2 — チェーンの反応。3 — X方向への移動の作例。*

#### C10. 元の方式に切り替えて作例を保存する {#c10-switch-back-and-save-the-example}

1. もう一度 <strong>arm-L → FK</strong> をクリックします。

FK コントロールが、現在の IK ポーズにスナップします。

2. メッシュの位置や形が急に飛ばないことを確認します。
3. <strong>File → Save As</strong> を開きます。
4. `Mannequin_AutoRig.blend` を保存します。

省略した英語原本の画像は、FK が有効な、保存済みの作例を示しています。ニュートラルな練習用コピーを作るには：

1. 四肢すべてを FK にします。
2. 表示されているすべてのポーズコントロールを選びます。
3. <strong>F3</strong> を押します。
4. パートAと同様に、`Clear Pose Transforms` を検索します。
5. <strong>All</strong> を選びます。
6. ニュートラルなコピーを、別の名前で保存します。

英語原本の画像説明（画像省略）：C10：元の方式に切り替えて作例を保存する

*1 — 再び FK が有効です。2 — ポーズが保持されます。3 — 保存したファイル名。*

<strong>完了時の確認：</strong> 元のメタリグのプレビューが保存されています。切り離したマネキンには、新しいボディリグとコントロールがあります。プレビューのウェイトは修正済みです。FK の回転と IK ターゲットの移動を比較できました。保存したリグは、学習用の作例として残してください。制作に使う場合は、プレビューを適切なキャラクターの形状に置き換えます。

---

### アニメーションのリターゲット {#animation-retargeting}

スケルトン間でアニメーションを移す方法は、[Rig Tools：Retarget](05-rig-tools.md#retarget)で説明しています。

クリップの操作項目は、[Retarget の画像に関する説明](05-rig-tools.md#retarget)を参照してください。

---

## Bone Merge {#bone-merge}

<strong>できること：</strong> すべてのウェイトを保持したまま、二つのアーマチュアを一つにまとめます。たとえば、体のリグと、衣服や髪のリグを統合します。

[ガイド11](03-guides-b.md#guide-11-merge-two-rigs-together)で、手順を順番に説明しています。

<strong>三つの段階：</strong>

- Scope — 二つのアーマチュアを選び、違いを確認します。
- Rename — 名前の衝突を解消し、新しいボーンを特定します。
- Merge — プレビューの後に、最終的な統合を実行します。

<strong>主な操作項目：</strong>

- <strong>Base</strong> は、残すアーマチュアです。もう一方のアーマチュアをここへ統合し、統合元は非表示になります。
- <strong>Analyze</strong> は、両方のスケルトンを比較します。<strong>Acknowledge Scope — Proceed to Rename</strong> で、段階2へ進みます。
- <strong>Normalize Both Armatures</strong> は、両方のリグの標準ボーンを、一つの命名規則にそろえて改名します。Mixamo Prefixed、Mixamo Stripped、またはカスタムの規則を使えます。
- <strong>Auto-Propose Renames</strong> は、統合するリグ固有のボーンに対する名前を提案します。
- <strong>Apply Rename</strong> は、一つの項目を改名します。Undo も一段階です。<strong>Apply Batch Pattern</strong> は、パターンを使って複数の名前を変更します。`{bone}`、`{side}`、`{index}` を使えます。
- <strong>Mark as Unique</strong> は、そのボーンを統合せず、新しいボーンとして残します。
- <strong>Verify Rename — Proceed to Merge</strong> は、段階3を開きます。
- <strong>Run Merge Preview</strong> は、何も変更せずに、統合した場合の処理内容を報告します。
- <strong>Merge Armatures</strong> は、両方のアーマチュアをバックアップしてから統合します。

<strong>場所：</strong> BoneCraft → Setup Rigging → Bone Merge

英語原本の画像説明（画像省略）：Bone Merge は Stage 1: Scope から始まります。前の段階の確認が完了するまで、後の段階はロックされたままです。

*標準のパネルポップオーバー、BoneCraft 9.2.18。Bone Merge は Stage 1: Scope から始まります。前の段階の確認が完了するまで、後の段階はロックされたままです。*

次へ：[Mechanisms](07-mechanisms.md)

