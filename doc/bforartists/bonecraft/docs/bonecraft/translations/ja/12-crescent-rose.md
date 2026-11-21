# チュートリアル：Mechanisms で Crescent Rose をリグ化する {#tutorial-crescent-rose-with-mechanisms}

[← 目次](index.md)

<!-- Print layout is scoped to this illustrated chapter; the shared renderer is unchanged. -->
<style>
@media print {
  h3[id^="12-crescent-rose--"] { break-before: page; break-after: avoid; }
  h2:has(+ h3[id^="12-crescent-rose--"]) { break-before: page; break-after: avoid; }
  h2 + h3[id^="12-crescent-rose--"] { break-before: avoid; }
  section.chapter:has(#ch-12-crescent-rose) p:has(> img) { break-after: avoid; }
  section.chapter:has(#ch-12-crescent-rose) p:has(> img) + p { break-before: avoid; }
  section.chapter:has(#ch-12-crescent-rose) table { break-inside: avoid; }
  [id="12-crescent-rose--what-you-built"] { break-before: page; break-after: avoid; }
}
</style>

## 作成するもの {#what-you-will-build}

Crescent Rose は大鎌とライフルを組み合わせた武器です。このチュートリアルでは Mechanisms でモデルをリグ化します。1 つのスライダーで大鎌からライフルへ変形し、2 つ目のスライダーでライフルをコンパクトな形態に折り畳みます。

このチュートリアルでは、Gear Link を除く現在のすべてのジョイントとリンクを使います。Hinge を 8 個、Slide を 3 個、Telescope、Piston、Follow をそれぞれ 1 個作成します。Sequence を 2 個、Form を 3 個作成します。

これらの形態は、このファン制作モデルで学習するためのポーズです。Mechanisms は衝突を検出せず、物理設計を満たす実物の複製を作るものでもありません。リグを応用する際は、部品間の隙間を確認してください。

完成ファイルは `examples/crescent-rose/CrescentRose_Mechanisms.blend` です。比較のために、いつでも開くことができます。

## 始める前に {#before-you-start}

- ファイル：`examples/crescent-rose/CrescentRose_parts.blend` には、15 個の部品オブジェクトに分割したモデルが入っています。このファイルからチュートリアルを始めてください。`CrescentRose_Mechanisms.blend` は完成したリグです。
- 所要時間：FBX の準備と Mechanisms の学習には、それぞれ 1 回分の作業時間を確保してください。どちらも本格的な演習です。段階の区切りでチェックポイントを保存してください。
- 用語：先に [Mechanisms](07-mechanisms.md) の「What Mechanisms does」を読んでください。部品、ジョイント、リンク、ハンドル、Sequence、Form を定義しています。
- 言語：ここでは省略している英語原典のスクリーンショットには、Bforartists と BoneCraft の英語パネルが表示されています。BoneCraft のパネルは **Language** 設定に従います。Bforartists のそれ以外の部分は、インターフェース言語に従います。BoneCraft が Bforartists の設定言語をサポートしていない場合、そのパネルは英語のままです。このテキスト版の操作手順は、その場合も適用できます。
- 開始方法：元の FBX を使う場合は以下の P1-P8 に従い、準備済みファイルを使う場合は手順 1 に進んでください。どちらも同じ 15 個の部品を使います。
- 英語原典の過去の確認：操作手順と実際のインターフェースキャプチャは、BoneCraft `9.1.2` を Bforartists `5.2.0` の既定のキーマップで使って確認されています。このテキスト版のための新しいキャプチャやチュートリアルの再実行は行っていません。

**現在のナビゲーション：** 9.2.18 では **BoneCraft → Mechanisms** または **Properties → Scene → Mechanisms** を使います。Scene の各セクションが非表示の場合は、**Tabs → Scene Properties → Show** を有効にしてください。Parts、Joints & Links、Sequences、Controls の名前は変わっていません。ここでは省略している英語原典の古いスクリーンショットでは、これらのセクションの周辺が以前の配置になっている場合があります。

このテキスト版は、英語原典における 9.1.2 のキャプチャと再実行の範囲をそのまま引き継ぎ、画像を省略しています。9.2.18 のソースレビューは、それらを新しいチュートリアルの再実行に置き換えるものではありません。以前に保存した Form も引き続き読み込み、使用できます。開いたり適用したりしても、その値は再保存されません。[Forms](07-mechanisms.md#forms) を参照してください。

英語原典の画像では、クリック、入力、確認する対象を赤い番号で示しています。このテキスト版では画像を省略し、その説明文と操作番号のキャプションを残しています。文章の手順と操作番号の注記を順番に（1、次に 2、次に 3）進めてください。これらの番号は英語原典の注釈に対応し、原典の画像ごとに振り直されます。原典の証拠画像では、枠が確認すべき結果を、丸が使う部品やボタンを示します。

## 元の FBX を準備する（P1-P8） {#prepare-the-original-fbx-p1-p8}

`CrescentRose_parts.blend` を使う場合は、このセクションを飛ばしてください。

1. 新しいファイルで作業します。

2. 元の FBX と `CrescentRoseTextures` フォルダーを同じ場所に置きます。

これらの手順は、Bforartists 5.2.0 の既定のキーマップで再実行されています。画面上のモードメニューを使ってください。このキーマップでは、Tab で Edit Mode に入る代わりにオーバーレイの表示が切り替わる場合があります。

### P1 - FBX をインポートする {#p1---import-the-fbx}

この手順には Legacy インポーターを使います。

1. 空のシーンから始めます。

2. **File > Import > FBX (.fbx) (Legacy)** を選択します。

3. `CrescentRose.fbx` を選択します。

4. インポートの Scale は `1.00` のままにします。

5. Import FBX を選択します。

6. Numpad 3 を押して Right ビューにします。

7. Home を押して、インポートしたオブジェクト全体を表示します。

Outliner にはルートと、`Black01`、`Blades01`、`Red01` の 3 個のマテリアル別メッシュがあります。

英語原典の画像説明（画像省略）：P1：Scale 1.00 の Legacy FBX インポートオプション

*1：CrescentRose.fbx を選択します。2：Scale を 1.00 のままにします。3：Import FBX をクリックします。Legacy インポーターを使ってください。*

### P2 - 配置を保持してサイズを設定する {#p2---preserve-placement-and-set-the-size}

インポートした武器の高さは約 `0.32 m` です。準備済みファイルでは、すでに拡大されています。このサイズ変更は、インポートしたメッシュに対して一度だけ行ってください。

1. Object Mode に切り替えます。

2. 3 個のメッシュをすべて選択します。

3. **Object > Parent > Clear and Keep Transformation** を選択します。

4. 不要になったルートを作業シーンから削除します。

5. 3 個のメッシュをすべて選択したまま、**Object > Apply > Rotation & Scale** を選択します。

6. Ctrl+R を押して、この Bforartists キーマップの Scale を開始します。

7. `6.25` と入力して、3 個のメッシュをまとめて拡大します。

8. 拡大を確定します。

9. もう一度 **Object > Apply > Rotation & Scale** を選択します。

武器全体の高さは約 `1.997 m` になります。

英語原典の画像説明（画像省略）：P2：配置を保持して親子関係を解除する

*1：F3 を押し、Clear Parent Keep Transform を検索します。2：Clear and Keep Transformation を選択します。ルートを削除する前に、3 個すべてのメッシュで繰り返してください。*

英語原典の画像説明（画像省略）：P2：インポートした武器に回転とスケールを適用した状態

*1：3 個のメッシュをまとめて 6.25 倍に拡大した後、Rotation & Scale を適用します。Rotation は 0 でなければなりません。2：Scale はすべての軸で 1 でなければなりません。*

個々のオブジェクトの Dimensions フィールドは、そのマテリアルのメッシュだけを測定します。武器を測るときは、全体の最下部から最上部までの範囲を確認してください。分離する前に、3 個すべてのオブジェクトで回転がゼロ、スケールが 1 になっていなければなりません。

### P3 - マテリアルを接続する {#p3---connect-the-materials}

1. Shading ワークスペースに切り替えます。

2. Material Preview を選択します。

3 個の各マテリアルは、`CrescentRoseTextures` の画像を 4 枚使います。

| 画像 | 色空間 |
|---|---|
| `BaseColor` | **sRGB** |
| `Metallic` | `Non-Color` |
| `Roughness` | `Non-Color` |
| `Normal` | `Non-Color` |

各マテリアルについて、画像を 1 枚ずつ処理します。

1. `CrescentRoseTextures` から対応する画像を読み込みます。

2. 表に従って、その画像の色空間を設定します。

3. BaseColor、Metallic、Roughness の画像では、Image Texture の Color を Principled BSDF の対応する入力につなぎます。

各 Normal 画像には、次の別系統の接続を使います。

1. **Normal Map** ノードを挿入します。

2. Normal Map ノードは `Tangent Space` のままにします。

3. Normal 画像の Color を Normal Map の Color につなぎます。

4. Normal Map の Normal を Principled BSDF の Normal につなぎます。

既存の UV を保持してください。

英語原典の画像説明（画像省略）：P3：黒いマテリアル用に接続した 4 枚のテクスチャマップと Tangent Space の Normal Map

*1：BaseColor の Color を BSDF の Base Color につなぎます。2：BaseColor は sRGB のままにします。3：すべてのデータマップを Non-Color に設定します。4：Tangent Space を使い、Normal 画像 > Normal Map > BSDF Normal の順に接続します。*

英語原典の画像説明（画像省略）：P3：Material Preview に表示された 3 個のマテリアル

*1：刃のマテリアルを確認します。2：Material Preview で赤と黒の本体マテリアルを確認します。テクスチャ欠落を示すピンク色がないことを確認してください。*

この手順は、黒、刃、赤の各マテリアルに適用します。各画像を選択した後、色空間を確認してください。色空間の設定は画像に属します。武器は赤、黒、金属色で表示され、テクスチャ欠落を示すピンク色がない状態になります。

### P4 - つながっていない部品を分離する {#p4---separate-loose-pieces}

1. 3 個のマテリアル別メッシュをすべて選択します。

2. ビューポートのモードメニューから **Edit Mode** を選択します。

3. すべてのジオメトリを選択します。

4. **Mesh > Separate > By Loose Parts** を選択します。

5. Object Mode に戻ります。

メッシュオブジェクトは **37** 個になります。自動生成される数字の接尾辞は異なる場合があります。位置と形でオブジェクトを識別してください。

英語原典の画像説明（画像省略）：P4：Edit Mode に入り、By Loose Parts を選択する

*1：Edit Mode に切り替え、すべてのジオメトリを選択します。2：F3 を押し、Separate Loose を検索して、By Loose Parts を選択します。*

英語原典の画像説明（画像省略）：P4：分離後の 37 個の独立した部品

*1：分離後のオブジェクト総数が 37 であることを確認します。2：Outliner で、形と位置を基準に部品を選択します。接尾辞は異なる場合があります。*

### P5 - 可動グループ 15 組を結合する {#p5---join-the-15-moving-groups}

表には元のすべての独立したメッシュ部分を示しています。マテリアル名は外観を表し、完成後のオブジェクト名ではありません。

| 完成後のオブジェクト | 結合する部品 | 結合後のメッシュ頂点数 |
|---|---|---:|
| `BladeTip` | 刃先の関節にある黒いノブと金属製の先端スパイク | 252 |
| `Blade2` | 第 2 セグメントの金属板 2 枚と赤いカバー 2 枚 | 1000 |
| `Blade1` | ヘッドに最も近い第 1 セグメントの金属板 2 枚 | 512 |
| `HeadMount` | 黒い後部ブロック、上部キャップ、芯、および赤い内側プレート 2 枚と薄い上部カバー 2 枚 | 1395 |
| `PlateL` | X の負側にある赤いヘッド外側プレート 1 枚 | 676 |
| `PlateR` | X の正側にある赤いヘッド外側プレート 1 枚 | 676 |
| `RearSpike` | 金属製スパイク刃 2 枚、赤いピボットキャップ 2 個、赤い取付プレート 2 枚 | 1194 |
| `Receiver` | 黒い本体と小さなノブ、ボルトの上にある金属リング、長い赤いハウジング | 2609 |
| `Grip` | レシーバーの下にある赤いグリップブロック | 194 |
| `Magazine` | 本体下の黒いチューブ | 96 |
| `Bolt` | 赤いボルトのシリンダーと、そのノブ部分 2 個 | 362 |
| `Pole` | 金属製の下部シャフトと赤いカラー | 148 |
| `ButtSpike` | 金属製の下端スパイク | 110 |
| `StrutBase` | レシーバーとヘッドの間にある細い赤いロッド | 34 |
| `StrutRod` | そのロッドを囲む、切り欠きのある黒いスリーブ | 108 |

外側プレートを Blade1 に結合しないでください。支柱の 2 つの部品を 1 つに結合しないでください。支柱はすでに 2 個の独立した部品になっています。二等分する必要はありません。

刃先から内側へ進み、その後レシーバーとポールを処理します。各可動グループで次を行います。

1. 一緒に動く部品を選択します。

2. 両側に対になっている部品は、ビューを回り込ませて両方を選択します。

3. 結合する前に選択を確認します。

4. **Object > Join**（Ctrl+J）を選択します。

5. Outliner で、結合したオブジェクトの名前を変更します。

合計で **15 個のメッシュ、9,366 個の頂点**が必要です。手順 2 には、完成後の部品名と後で設定する親子関係を再掲しています。

英語原典の画像説明（画像省略）：P5：Outliner で名前を付けた 15 組すべての可動グループ

*1：Outliner で、結合した各グループを表の 15 個の名前に合わせて変更します。*

英語原典の画像説明（画像省略）：P5：結合前に選択した Blade1 の元のプレート 2 枚

*1：両側にある Blade1 の金属板 2 枚を選択します。2：両方のオブジェクトが選択されていることを確認してから Join を使い、結果の名前を Blade1 にします。*

英語原典の画像説明（画像省略）：P5：Object メニューの Join コマンド

*1：1 グループ分の部品だけを選択して Object を開きます。2：Join（Ctrl+J）を選択します。このメニューの切り抜きはコマンドを示しています。上記の 2 部品の選択を使ってください。*

### P6 - 原点を中央にする {#p6---centre-the-origins}

1. Object Mode に切り替えます。

2. 15 個のメッシュをすべて選択します。

3. **Object > Set Origin > Origin to Geometry** を選択します。

4. 操作の Center オプションを `Bounds Center` に設定します。

5. 回転がゼロ、スケールが 1 であることを確認します。

オブジェクトには、まだ親がありません。アーマチュアもありません。これらの原点は準備用です。手順 6 で、機構のピボットを実際の関節位置へ移動します。

英語原典の画像説明（画像省略）：P6：Object > Set Origin > Origin to Geometry

*1：Object を開きます。2：Set Origin にポインターを合わせます。3：Origin to Geometry を選択し、操作オプションで Bounds Center を設定します。*

英語原典の画像説明（画像省略）：P6：トランスフォーム適用済みで中央に置かれた Blade1 の原点

*1：オレンジ色の原点がメッシュの中央になっています。2：Rotation 0 を確認します。3：Scale 1 を確認します。機構のピボットは後で移動します。*

### P7 - テクスチャを縮小してパックする {#p7---resize-and-pack-the-textures}

使用するマップは **12 枚**で、各マテリアルにつき 4 枚です。元の JPEG を上書きしないでください。使用する各マップで次を行います。

1. Image Editor でマップを選択します。

2. **Image > Resize** を選択します。

3. 幅を **1024** に設定します。

4. 高さを **1024** に設定します。

5. サイズ変更を確定します。

6. **Image > Pack** を選択します。

パックすると、サイズ変更後のピクセルが blend ファイル内に保持されます。すべてのマップを処理した後、Material Preview を確認してください。

英語原典の画像説明（画像省略）：P7：1024 x 1024 に縮小したテクスチャを Image メニューからパックする

*1：Image > Resize を選択し、幅と高さに 1024 を入力します。2：結果が 1024 x 1024 になっていることを確認します。3：Pack を選択します。使用する 12 枚すべてのマップで繰り返してください。*

### P8 - 準備済みファイルを保存して開き直す {#p8---save-and-reopen-the-prepared-file}

1. 作業コピーを `CrescentRose_parts.blend` として保存します。

2. そのファイルを開き直します。

3. 名前を付けた 15 個のメッシュ、そのトランスフォーム、赤と黒のマテリアルを確認します。

4. 再び Right ビューを選択します。

5. Home を押します。

6. 手順 1 に進みます。

元のテクスチャディレクトリがなくても、12 枚すべてのマップを引き続き利用できる状態になっている必要があります。

英語原典の画像説明（画像省略）：P8：テクスチャを保持した武器が、開き直した準備済みファイルに表示されている

*1：File から Save As を使い、その後 Open で作業コピーを開き直します。2：名前を付けた 15 個のメッシュが残っていることを確認します。3：マテリアルを確認します。タイトルバーで、開き直したファイルを識別できます。*

## A. ファイルを開く {#a-open-the-file}

### 手順 1 — 部品ファイルを開く {#step-1--open-the-parts-file}

1. `examples/crescent-rose/CrescentRose_parts.blend` を開きます。

2. ビューポートで Material Preview シェーディングを選択します。

3. Numpad 3 を押して Right ビューにします。

4. Home を押して武器全体を表示します。

刃は左を向き、下端のスパイクは下を向いています。

英語原典の画像説明（画像省略）：手順 1：Right ビューで表示した部品ファイル

*1：Material Preview をクリックします。2：ビューに Right Orthographic と表示されるまで Numpad 3 を押し、Home を押して武器全体を表示します。*

**表示される状態：** 高さ約 2 m の赤と黒の大鎌が表示され、何も選択されていません。

### 手順 2 — 部品を確認する {#step-2--meet-the-parts}

Outliner には 15 個のオブジェクトが並びます。それぞれが一体として動く部品です。

| オブジェクト | 内容 | Rides on の設定先 |
|---|---|---|
| `Receiver` | スコープ、トリガー、照準器を備えたライフル本体 | リグ |
| `Grip` | レシーバーの下のグリップ | `Receiver` |
| `Magazine` | 円筒形のマガジン | `Receiver` |
| `Bolt` | ボルト | `Receiver` |
| `Pole` | 下部シャフトとそのカラー | `Receiver` |
| `ButtSpike` | 下端のスパイク | `Pole` |
| `HeadMount` | 刃を支えるヘッドブロック | `Receiver` |
| `Blade1` | ヘッドに最も近い、刃の第 1 セグメント | `HeadMount` |
| `Blade2` | 第 2 セグメント | `Blade1` |
| `BladeTip` | 刃先 | `Blade2` |
| `RearSpike` | ヘッド後部のスパイク | `HeadMount` |
| `PlateL`, `PlateR` | ヘッドの外側の側面プレート | `HeadMount` |
| `StrutBase` | レシーバーとヘッドの間にある細いロッド | `Receiver` |
| `StrutRod` | そのロッドを囲む、切り欠きのあるスリーブ | `HeadMount` |

英語原典の画像説明（画像省略）：手順 2：Outliner に並ぶ 15 個の部品オブジェクト

*1：刃の 3 個のセグメントを確認します。2：本体、ヘッド、ポールの名前を表と照合します。3：StrutBase と StrutRod は別々のオブジェクトのままにしてください。*

元の FBX を使う場合は、上記の P1-P8 に従ってください。付属の準備済みファイルは、これらのインターフェース操作で作成されています。リポジトリの準備スクリプトには、参考用のグループ分け表があります。

### 手順 3 — Mechanisms を見つける {#step-3--find-mechanisms}

左の Tool Shelf が非表示の場合：

1. ビューポート上にポインターを置き、T を押します。

2. Region Toggle メニューから Tools を選択します。

続いて：

1. 左の Tool Shelf で BoneCraft タブを開きます。

2. **Mechanisms** を展開します。

3. シェルフの右端をドラッグして、パネルの文字が読める幅にします。

BoneCraft の設定で Scene Properties が Show に設定されている場合は、**Properties > Scene** にも同じセクションが表示されます。ここでは省略している英語原典のスクリーンショットでは、Tool Shelf を使っています。

メッシュがアクティブでリグがない場合、上部に **Add Parts from Selection** が表示されます。使う前に、手順 4 に従ってすべての部品を選択してください。番号付きのサブセクションは、部品を追加した後に使用できるようになります。

英語原典の画像説明（画像省略）：手順 3：BoneCraft タブの Mechanisms セクション

*1：BoneCraft タブをクリックします。2：Mechanisms を展開します。3：Add Parts from Selection を見つけます。使う前にメッシュを選択してください。*

## B. 部品 {#b-parts}

### 手順 4 — Add Parts from Selection {#step-4--add-parts-from-selection}

1. ビューポート上にポインターを置き、A を押して 15 個のオブジェクトをすべて選択します。

2. **Add Parts from Selection** を選択します。

英語原典の画像説明（画像省略）：手順 4：すべての部品を選択して Add Parts from Selection を実行する

*1：ビューポートにポインターを置いて A を押し、15 個のメッシュを選択します。2：Add Parts from Selection をクリックします。*

**表示される状態：** Outliner に新しいアーマチュア「Mechanism Rig」が現れ、その下に部品が並びます。メッシュオブジェクトは選択されたままです。**1. Parts** に 15 個の部品が並びます。BoneCraft タブの先頭には、リグの折り畳み可能な Overview が表示されるようになります。

### 手順 5 — Rides on {#step-5--rides-on}

部品は、取り付け先の部品に追従します。

1. **1. Parts** で `Blade1` を選択します。

2. リストの下にある「Rides on」メニューを開きます。

3. `HeadMount` を選択します。

4. 手順 2 の表を使い、各部品で繰り返します。

`Receiver` は「the rig」のままにします。

英語原典の画像説明（画像省略）：手順 5：HeadMount に追従する Blade1

*1：Parts リストで Blade1 を選択します。2：Rides on を開き、HeadMount を選択します。親子関係の表に従って繰り返してください。*

### 手順 6 — ピボット {#step-6--pivots}

Hinge は部品のピボットを中心に回転します。刃の各セグメント、ヘッド、グリップは、中心ではなく関節位置で回転する必要があります。ピボットの左右方向の位置を保持するため、側面の平行投影ビューで作業してください。

1. リストで `Blade1` を選択します。

2. **Edit Pivot** を選択します。

3. マーカーを選択します。

4. Bforartists の Move を実行するため、Ctrl+W を押します。

5. セグメントがヘッドと接する位置をクリックします。

6. **Apply Pivot** を選択します。

7. 以下の部品でもピボットの手順を繰り返します。

| 部品 | ピボット位置 |
|---|---|
| `Blade2` | `Blade1` と接する位置 |
| `BladeTip` | `Blade2` と接する位置 |
| `HeadMount` | 支柱と接する最下点 |
| `Grip` | 上端 |
| `RearSpike` | ヘッドと接する位置 |
| `PlateL` と `PlateR` | Blade1 がヘッドと接する、丸いボルトの中心 |
| `StrutBase` | 下端 |
| `StrutRod` | 上端 |

省略した英語原典のスクリーンショットにあるマーカー位置は目安です。数ミリメートルの違いで、見た目が変わることはありません。

英語原典の画像説明（画像省略）：手順 6：部品を選択して Edit Pivot をクリックする

*1：Parts で Blade1 を選択します。2：Edit Pivot をクリックします。次の説明に従って、マーカーを移動して適用します。*

英語原典の画像説明（画像省略）：手順 6：関節位置にある Blade1 のピボットマーカーと Apply Pivot

*1：Ctrl+W でピボットマーカーを刃の関節に移動します。2：Apply Pivot をクリックして、その位置を保持します。*

## C. ヘッド {#c-the-head}

### 手順 7 — Add Joint → Hinge {#step-7--add-joint--hinge}

邪魔な物を非表示にする必要がある場合は、ガイドを開始する前に非表示にしてください。

**Add Joint → Hinge** を開きます。ガイド付き作成のヘッダーとステータスバーに、各手順の説明が表示されます。

英語原典の画像説明（画像省略）：手順 7：Add Joint メニューの Hinge

*1：Add Joint を開きます。2：Hinge をクリックします。ガイド付き作成が部品の指定を待つ状態になります。*

### 手順 8 — ヘッドをクリックする {#step-8--click-the-head}

ヘッダーには「click the part that turns」（回転する部品をクリック）と表示されます。Right ビューでは、外側プレートがヘッドを隠しています。プレートの奥にあるヘッド後部のブロックを、丸で示された位置でクリックしてください。

ヘッダーに `PlateR` と表示された場合：

1. Esc を押します。

2. **Add Joint > Hinge** をもう一度開始します。

3. ヘッドのさらに後方をクリックします。

ガイドの実行中は、通常のキーボードショートカットがガイドに取り込まれます。

英語原典の画像説明（画像省略）：手順 8：ヘッド後部のブロックをクリックする

*1：赤い外側プレートの奥にある、HeadMount の黒い後部ブロックをクリックします。ガイドに HeadMount と表示されることを確認してください。*

### 手順 9 — X、次に Enter を押す {#step-9--press-x-then-enter}

ヘッダーで軸の指定を求められます。

1. X を押します。

2. 繰り返し再生されるプレビューを確認します。

3. Enter を押して Hinge を確定します。

ヘッドは左右方向の軸を中心に回転します。

英語原典の画像説明（画像省略）：手順 9：軸を指定する段階

*1：軸の指示に従い、X、次に Enter を押します。2：確定する前に、ヘッドがピボットを中心に回転する様子を確認します。*

**表示される状態：** **2. Joints & Links** に `HeadMount Hinge` が表示され、**4. Controls** にそのスライダーが表示されます。これらのスライダーは Object Mode で使います。

ビューポートのボーンハンドルを使うには：

1. アーマチュアを選択します。

2. Pose Mode に切り替えます。

### 手順 10 — 制限 {#step-10--limits}

1. リストで `HeadMount Hinge` を選択します。

2. **Min** を 0 に設定します。

3. **Max** を 120 に設定します。

正の値で、ヘッドが下方から後方へ回転します。可動範囲の制限は 120 度のままにしてください。Rifle シーケンスでは、刃の Hinge とともに 90 度の目標値を使います。

英語原典の画像説明（画像省略）：手順 10：Min 0、Max 120

*1：HeadMount Hinge を選択します。2：Min を 0 に設定します。3：Max を 120 に設定します。数値をダブルクリックして入力し、Enter を押してください。*

### 手順 11 — テスト {#step-11--test}

行の再生ボタンをクリックします。ヘッドが 120° まで動いて戻り、ポーズが復元されます。

英語原典の画像説明（画像省略）：手順 11：Hinge 行の Test

*1：HeadMount Hinge 行の小さな再生三角形をクリックします。往復する動きを確認してください。*

## D. 刃のチェーン {#d-the-blade-chain}

### 手順 12 — Hinge をさらに 3 個作る {#step-12--three-more-hinges}

`Blade1`、`Blade2`、`BladeTip` のそれぞれで、手順 7 から 10 を繰り返します。

1. **Add Joint → Hinge** を開きます。

2. セグメントをクリックします。

3. X を押します。

4. Enter を押します。

5. **Max** を 120 に設定します。

各セグメントは、その前のセグメントに追従します。3 個の Hinge がチェーンになります。

英語原典の画像説明（画像省略）：手順 12：リストに並ぶ刃の 3 個の Hinge と、別のヘッドの Hinge

*1：刃の Hinge、Blade1、Blade2、BladeTip をそれぞれ作成して選択します。2：各 Max を 120 に設定し、軸には X を使います。*

### 手順 13 — チェーンを試す {#step-13--try-the-chain}

1. **2. Joints & Links** を折り畳んで場所を空けます。

2. **4. Controls** を展開します。

3. Object Mode で、`Blade1 Hinge`、`Blade2 Hinge`、`BladeTip Hinge` をそれぞれ 60 度に設定します。

各値を入力するには：

1. 数値フィールドをダブルクリックします。

2. Ctrl+A を押します。

3. 値を入力します。

4. Enter を押します。

後ろのセグメントが前のセグメントと一緒に動き、チェーンが丸まります。続ける前に、3 個すべての値を 0 に戻してください。

英語原典の画像説明（画像省略）：手順 13：Controls で 60 度にした刃の 3 個の Hinge

*1：刃の 3 個のスライダーそれぞれに 60 を入力します。2：チェーンが一緒に丸まることを確認します。3 個すべてのスライダーを 0 に戻してください。*

## E. プレートと支柱 {#e-plates-and-strut}

### 手順 14 — プレートの Hinge {#step-14--hinges-on-the-plates}

Right ビューでは、`PlateL` はヘッドの奥に隠れています。

1. 同じ手順で `PlateR` に Hinge を追加します。

2. その **Max** を 30 に設定します。

3. Ctrl+Numpad 3 を押して Left ビューにします。

4. `PlateL` に Hinge を追加します。

5. その **Max** を 30 に設定します。

6. Numpad 3 を押して Right ビューに戻ります。

英語原典の画像説明（画像省略）：手順 14：PlateL Hinge と PlateR Hinge

*1：PlateR と PlateL の両方に Hinge を作成します。PlateL を選ぶには反対側の側面ビューを使います。2：各 Max を 30 に設定します。*

### 手順 15 — Add Link → Follow {#step-15--add-link--follow}

1 つのハンドルで両方のプレートを動かします。ガイドを始める前に、ビューを設定してください。

1. Numpad 1 を押して Front ビューにします。

2. `Blade2` を選択します。

3. F3 > Frame Selected を使って、ヘッドを近くに表示します。

外側プレート 2 枚が左右の端に見えます。

1. **Add Link > Follow** を開きます。

2. 先行する部品として、左端の `PlateL` をクリックします。

3. 追従する部品として、右端の `PlateR` をクリックします。

4. Enter を押します。

英語原典の画像説明（画像省略）：手順 15：Follow の指定で使う両方の外側プレートが見える Front ビュー

*1：先行する部品の PlateL を先にクリックします。2：追従する部品の PlateR を次にクリックします。Enter を押してください。*

### 手順 16 — 範囲 {#step-16--ranges}

1. 新しい Follow を選択します。

2. 自動入力された **Source Range** 0…30 と **Target Range** 0…30 を確認します。

3. **Name** でリンクの名前を `PlateR Follow` に変更します。

英語原典の画像説明（画像省略）：手順 16：Source Range と Target Range

*1：リンクの名前を PlateR Follow にします。2：Source Range が 0 から 30 であることを確認します。3：Target Range が 0 から 30 であることを確認します。*

### 手順 17 — Add Link → Piston {#step-17--add-link--piston}

ヘッドを折り畳む間、支柱はレシーバーとヘッドを結ぶ方向を向く必要があります。ガイドの実行中は、ナビゲーションのショートカットがガイドに取り込まれます。ガイドを始める前に：

1. Numpad 3 を押して Right ビューにします。

2. Outliner で `StrutRod` を選択します。

3. F3 > Frame Selected を使って近くに表示します。

4. **Add Link > Piston** を開きます。

英語原典の画像説明（画像省略）：手順 17：Add Link メニューの Piston

*1：StrutRod を画面内に大きく表示してから Add Link を開きます。2：Piston を選択します。ガイドは最初にシリンダーの指定を求めます。*

### 手順 18 — シリンダーとロッド {#step-18--the-cylinder-and-the-rod}

ガイドのシリンダーとロッドという役割は、リンクの両端を指します。モデルのオブジェクト名は、元の部品を表しています。`StrutBase` はスリーブの切り欠きから露出している細い赤いロッドです。`StrutRod` は黒いスリーブです。

1. 近くに表示したビューで、シリンダー側の部品として `StrutBase` を先にクリックします。

2. ロッド側の部品として `StrutRod` を次にクリックします。

3. Enter を押して確定します。

4. リンクの名前を `Head Strut` に変更します。

5. **Stretch** は無効のままにします。

1. Controls の `HeadMount Hinge` を変更します。

2. 支柱を確認します。

3. 値をゼロに戻します。

**表示される状態：** 支柱がヘッドに追従します。両方の部品が互いの方向を向きます。

英語原典の画像説明（画像省略）：手順 18：Piston ガイドで、露出した赤いシリンダー、黒いスリーブの順に指定する

*1：露出した赤い StrutBase を先にクリックします。2：黒い StrutRod スリーブを次にクリックします。Enter を押してください。*

英語原典の画像説明（画像省略）：手順 18：Stretch をオフにした Head Strut の設定

*1：リンクの名前を Head Strut に変更します。2：Stretch のチェックは外したままにします。その後 HeadMount Hinge をテストし、0 に戻してください。*

## F. ライフル {#f-the-rifle}

### 手順 19 — グリップと後部スパイクの Hinge {#step-19--grip-and-rear-spike-hinges}

`Grip` と `RearSpike` のそれぞれで：

1. **Add Joint → Hinge** を開きます。

2. 部品をクリックします。

3. X を押します。

4. Enter を押します。

5. **Min** を 0 に設定します。

6. **Max** を 90 に設定します。

続いて：

1. リストで `RearSpike Hinge` を選択します。

2. その Axis X を -1 に設定します。

3. Y と Z は 0 のままにします。

4. Grip は X の正方向のままにします。

5. ジョイントリストに `Grip Hinge` と `RearSpike Hinge` が表示されることを確認します。

RearSpike の X 軸を反転すると、Compact で折り畳まれたヘッドに向かって折り畳まれます。これらのコントロールは、手順 25 のコンパクト形態にするためにグリップと後部スパイクを折り畳みます。

英語原典の画像説明（画像省略）：手順 19：Max 90 の Grip Hinge

*1：Grip Hinge を選択します。2：Axis X は 1、Y と Z は 0 のままにします。3：Max を 90 に設定し、Min は 0 のままにします。*

英語原典の画像説明（画像省略）：手順 19：Axis X -1、Max 90 の RearSpike Hinge

*1：RearSpike Hinge を選択します。2：Axis X を -1 に設定します。3：Max を 90 に設定し、Min は 0 のままにします。*

### 手順 20 — Magazine と Bolt の Slide {#step-20--magazine-and-bolt-slides}

`Magazine`、次に `Bolt` で：

1. **Add Joint → Slide** を開きます。

2. 部品をクリックします。

3. Z を押します。

4. Enter を押します。

5. **Max** を、Magazine では 0.04、Bolt では 0.06 に設定します。

Slide はシーンの単位を使います。0.06 は 6 cm です。

英語原典の画像説明（画像省略）：手順 20：Z 軸、Max 0.04 の Magazine Slide

*1：Add Joint > Slide の後で Magazine Slide を選択します。2：Z 軸（Z = 1、X = Y = 0）を使います。3：Max を 0.04 に設定し、Min は 0 のままにします。*

英語原典の画像説明（画像省略）：手順 20：Z 軸、Max 0.06 の Bolt Slide

*1：Add Joint > Slide の後で Bolt Slide を選択します。2：Z 軸（Z = 1、X = Y = 0）を使います。3：Max を 0.06 に設定し、Min は 0 のままにします。*

### 手順 21 — Pole Slide {#step-21--pole-slide}

1. **Add Joint → Slide** を開きます。

2. `Pole` をクリックします。

3. Z を押します。

4. Enter を押します。

5. **Max** を 0.6 に設定します。

6. **4. Controls** で `Pole Slide` を 0.6 に設定します。

7. 引き込まれたシャフトを確認します。

8. コントロールをゼロに戻します。

正の値で、ポールがレシーバーの中へ上がります。

英語原典の画像説明（画像省略）：手順 21：Z 軸、Max 0.6 の Pole Slide 設定

*1：Add Joint > Slide の後で Pole Slide を選択します。2：Z 軸（Z = 1、X = Y = 0）を使います。3：Max を 0.6 に設定し、Min は 0 のままにします。*

### 手順 22 — Pole Telescope {#step-22--pole-telescope}

1. **Add Joint → Telescope** を開きます。

2. ベースとして `Pole` をクリックします。

3. セグメントとして `ButtSpike` をクリックします。

4. Enter を押します。

5. Z を押します。

6. Enter を押します。

7. **Length** を 0.2 に設定します。

8. 個別のコントロールをテストします。

9. コントロールをゼロに戻します。

このコントロールは、Z の正方向に最大 20 cm スパイクを移動させ、このモデルのポール内に引き込みます。

英語原典の画像説明（画像省略）：手順 22：ガイドで Pole をベース、ButtSpike をセグメントとして指定する Telescope

*1：Pole をベースとしてクリックします。2：ButtSpike をそのセグメントとしてクリックします。Enter、Z、Enter の順に押してください。*

英語原典の画像説明（画像省略）：手順 22：Z 軸、Length 0.2 の Pole Telescope 設定

*1：Pole Telescope を選択します。2：軸が Z であることを確認します。3：Length に 0.2 を入力します。コントロールをテストし、ゼロに戻してください。*

## G. シーケンス {#g-sequences}

### 手順 23 — Add Sequence {#step-23--add-sequence}

1. **3. Sequences** で **Add Sequence** を選択します。

2. リスト内のシーケンス名をダブルクリックします。

3. `Scythe to Rifle` と入力します。

4. Enter を押します。

英語原典の画像説明（画像省略）：手順 23：Add Sequence

*1：Add Sequence をクリックします。2：新しい名前をダブルクリックし、Scythe to Rifle と入力します。Enter を押してください。*

### 手順 24 — 動作グループを記録する {#step-24--record-a-motion-group}

1. **Move Slider to End** を選択します。

シーケンスのスライダーが `100%` に移動します。ボタンは Record Step 1 に変わります。

1. **4. Controls** で `BladeTip Hinge` を 70 に設定します。

2. `Blade2 Hinge` を 120 に設定します。

3. Record Step 1 を選択します。

これにより、動かしたハンドルごとに 1 件ずつ、2 件の目標エントリが保存されます。両方のジョイントスライダーはゼロに戻ります。

英語原典の画像説明（画像省略）：手順 24：最初のグループのポーズを設定する前に Move Slider to End を使う

*1：Move Slider to End を 1 回クリックします。ボタンが Record Step 1 に変わります。*

英語原典の画像説明（画像省略）：手順 24：Blade2 を 120 度、BladeTip を 70 度に設定して Record Step 1 を実行する

*1：Blade2 = 120、BladeTip = 70 を入力します。2：Record Step 1 をクリックします。両方の目標が保存され、ジョイントスライダーがリセットされます。*

*残りの動作グループ。* 各記録の後も、記録待機状態は維持されます。再び待機状態にする必要はありません。以下の残りの各グループについて：

1. グループのハンドルを、表の値のポーズにします。

2. 表示されている Record Step ボタンを選択します。

| 動作グループ | ポーズを設定するハンドル | 前のグループの記録後に表示されるボタン |
|---|---|---|
| 2 | `Blade1 Hinge` 10、`PlateL Hinge` 30 | Record Step 3 |
| 3 | `HeadMount Hinge` 90 | Record Step 5 |
| 4 | `Pole Slide` 0.6 | Record Step 6 |

ボタンの番号は、保存済みの目標エントリ数に 1 を足した値です。ハンドルを 2 個記録すると、番号は 2 進みます。記録ボタンをクリックした回数ではありません。4 組の動作グループで、6 件の目標エントリが作成されます。動かすハンドルを変更した場合は、実際に表示されているボタンの番号を使ってください。

### 手順 25 — 各ステップ {#step-25--the-steps}

記録した目標ごとに、シーケンスの下にエントリが作られます。エントリには **Target**、イージング、**Start**、**End** が表示されます。Start/End フィールドは 0-1 を使います。Controls のスライダーは 0-100% で表示されます。

| 動作 | Start | End |
|---|---:|---:|
| 刃を最初に折り畳む | 0 | 0.25 |
| プレートと第 1 セグメントが続く | 0.25 | 0.5 |
| ヘッドを 3 番目に折り畳む | 0.5 | 0.8 |
| ポールを最後に動かす | 0.8 | 1 |

同じ動作グループ内のエントリでは、Start と End に同じ値を使います。`Scythe to Rifle` の各エントリで：

1. **Start** を、表にあるその動作グループの Start 値に設定します。

2. **End** を、表にあるその動作グループの End 値に設定します。

3. エントリは `Ease In Out` のままにします。

各ステップの区間より前では開始値を保持し、区間を過ぎると終了値を保持します。

各シーケンスが完成したら、キャプチャバナーの **Cancel** を選択してください。Cancel は記録を終了し、保存したエントリを保持して、そのシーケンスのスライダーをゼロに戻します。記録待機中の重なり警告は、次に記録しようとしている区間についてのものです。余分な空のグループを追加しないでください。

2 つ目のシーケンスには、手順 24 の記録方法を使います。

1. `Rifle to Compact` を追加します。

2. **Move Slider to End** を 1 回選択し、記録待機状態にします。

3. 最初のグループとして、`Grip Hinge` を 90 に設定します。

4. `RearSpike Hinge` を 90 に設定します。

5. Record Step 1 を選択します。

6. 最初のグループの各エントリで：

    1. **Start** を 0 に設定します。

    2. **End** を 0.5 に設定します。

7. 2 番目のグループとして、`Magazine Slide` を 0.04 に設定します。

8. `Bolt Slide` を 0.06 に設定します。

9. Record Step 3 を選択します。

10. 2 番目のグループの各エントリで：

    1. **Start** を 0.5 に設定します。

    2. **End** を 1 に設定します。

11. 各エントリは `Ease In Out` のままにします。

12. キャプチャバナーの **Cancel** を選択して記録を終了します。

各グループは 2 件のエントリを作成します。2 番目のグループでは、記録ボタンが Record Step 1 から Record Step 3 に変わります。

英語原典の画像説明（画像省略）：手順 25：Scythe to Rifle の全 6 件の目標と時間区間

*1：Target は記録したジョイント値です。2：Ease In Out を選択します。3：Start を入力します。4：End を入力します。示された値を使い、6 件すべてのエントリでこれらのフィールドを設定します。*

英語原典の画像説明（画像省略）：手順 25：Rifle to Compact の全 4 件の目標と時間区間

*1：Grip と RearSpike は Target 90、Start 0、End 0.5 を使います。2：Magazine と Bolt は 0.04 / 0.06、Start 0.5、End 1 を使います。Ease In Out のままにしてください。*

英語原典の画像説明（画像省略）：手順 25：キャプチャバナーの Cancel で記録を終了する

*1：シーケンスが完成したら、このキャプチャバナーの Cancel をクリックして記録を終了します。エントリは保持され、シーケンスはゼロに戻ります。*

### 手順 26 — シーケンスをテストする {#step-26--test-the-sequence}

ステップ記録ボタンの隣の **Test** は、スライダーを 0% から 100%、そして 0% へ動かします。その後、テスト前のスライダー値を復元します。

1. Scythe の状態から、`Scythe to Rifle` の **Test** を選択します。

2. 最初のシーケンスが 100% の状態で、`Rifle to Compact` の **Test** を選択します。

3. テスト後、両方のシーケンスを 0% に戻します。

英語原典の画像説明（画像省略）：手順 26：折り畳み中のシーケンスの Test ボタン

*1：記録ボタンの隣の Test をクリックします。2：折り畳まれて戻る様子を確認します。Scythe to Rifle を 100% にして Compact をテストしてください。*

**表示される状態：** 刃が丸まり、プレートが閉じ、ヘッドがレシーバーに沿って下に折り畳まれ、ポールが上に滑ります。その後、すべてが元に戻ります。

## H. フォーム {#h-forms}

### 手順 27 — Save Form {#step-27--save-form}

個々のジョイントスライダーは、すべてゼロのままにしてください。動きはシーケンスで与えます。選択中のシーケンスを終端に設定すると、再び記録待機状態になる場合があります。Form の保存で新しいステップが記録されることはありません。別の目標を追加する意図がない限り、Record Step を選択しないでください。

**4. Controls** で：

1. すべてのスライダーが 0 の状態で、**Save Form** を選択します。

2. リストの新しいエントリをダブルクリックします。

3. 名前を `Scythe` にします。

4. `Scythe to Rifle` を `100%` に設定します。

5. **Save Form** を選択します。

6. 同じ名前変更の手順で、新しいエントリの名前を `Rifle` にします。

7. `Rifle to Compact` も `100%` に設定します。

8. **Save Form** を選択します。

9. 新しいエントリの名前を `Compact` にします。

記録待機状態を解除するには：

1. フォームリストで `Scythe` を選択します。

2. **Go to Form** を選択します。

両方のシーケンスがゼロに戻ります。Rifle または Compact に移動すると、選択中のシーケンスが 100% になるため、再び記録待機状態になる場合があります。

英語原典の画像説明（画像省略）：手順 27：すべてのスライダーが 0 の状態で Save Form を使う

*1：両方のシーケンスと、すべてのジョイントが 0 の状態から始めます。2：Save Form をクリックします。3：リストの新しいエントリをダブルクリックし、Scythe と名付けます。Rifle と Compact でも繰り返してください。*

### 手順 28 — Go to Form {#step-28--go-to-form}

1. リストでフォームを選択します。

2. **Go to Form** を選択します。

**Go and Key** は、さらに現在のフレームで、すべてのコントロールにキーを挿入します。これらのキーで変形をアニメーション化します。

英語原典の画像説明（画像省略）：手順 28：Rifle を選択した状態の Go to Form

*1：保存したフォームを選択します。2：Go to Form をクリックします。Go and Key はアニメーションキーも挿入します。*

### 手順 29 — ライフル {#step-29--the-rifle}

英語原典の画像説明（画像省略）：手順 29：Rifle フォーム

*1：Rifle を選択します。2：Go to Form をクリックします。3：原典画像のポーズと照合し、シーケンスのパーセンテージを確認します。*

### 手順 30 — コンパクト形態 {#step-30--compact}

英語原典の画像説明（画像省略）：手順 30：Compact フォーム

*1：Compact を選択します。2：Go to Form をクリックします。3：原典画像のポーズと照合し、シーケンスのパーセンテージを確認します。*

1. `Scythe` に戻します。

2. ファイルを保存します。

## 作成したもの {#what-you-built}

| 記録 | ボーン | 役割 |
|---|---|---|
| 15 個の部品 | `MCH-<part>` と `DEF-<part>` | 各部品のメッシュは、その `DEF-` ボーンの子になります |
| Hinge 8 個、Slide 3 個、Telescope 1 個 | `CTRL-<part>` | ハンドル。その値が **4. Controls** のスライダーです |
| Piston 1 個 | `MCH-<part>-aim` と `MCH-<part>-target` | 支柱の 2 個の部品を、互いの方向へ向け続けます |
| Follow 1 個 | なし | `PlateR` が `PlateL` と一緒に回転します |
| Sequence 2 個 | `CTRL-SEQ-<name>` | それぞれにスライダーが 1 つあります |
| Form 3 個 | なし | 保存されたスライダー値 |

更新したサンプルは、Rig Validator で問題の報告なく検証を通過しました。Auto Run Python Scripts をオフにした状態での再読み込み確認にも、個々のすべてのコントロールと 3 個すべての Form を含めて通過しました。

## 次に試すこと {#try-next}

Follow の対応関係を編集するには：

1. `PlateR Follow` の **Curve** を有効にします。

2. Graph Editor で対応曲線の形を変更します。

別のポーズとして、刃を折り畳んでヘッドを上げた 4 つ目のフォーム `Carry` を保存してみてください。

アニメーション化してエクスポートするには：

1. **Go and Key** で、フレームを変えながらフォームのキーを設定します。

2. `DEF-` ボーンをエクスポートします（[VRChat ツール](08-vrchat.md)を参照）。

## Gear Link {#gear-link}

Crescent Rose には歯車の組がないため、このリグには Gear Link がありません。Gear Link は、片方の Hinge が回転すると、歯数比に従ってもう片方の Hinge を回転させます。例として、クランクと車輪や、回転をスライドに変換するラックがあります。[Gear Link](07-mechanisms.md#gear-link) を参照してください。

## クレジット {#credits}

Crescent Rose モデル制作：amandangm、https://sketchfab.com/3d-models/crescent-rose-dcb6bfbb3b824c01a182fa131fe35824, CC BY 4.0。このチュートリアルでは、分割、拡大、リグ化した版を使っています。Crescent Rose は Rooster Teeth Productions のデザインです。これはファン制作のチュートリアル用アセットです。

[← 目次](index.md)
