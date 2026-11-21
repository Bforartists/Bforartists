# クイック修正と用語集 {#quick-fixes-and-glossary}

[← 目次](index.md)

## クイック修正インデックス {#quick-fix-index}

問題に合った説明を、この一覧から探してください。

| 問題 | 参照先 |
|---|---|
| アップロードに失敗し、ボーンが認識されない | [ガイド4](02-guides-a.md#guide-4-fix-your-avatars-bone-names) + [VRChat Naming Extras](08-vrchat.md#vrchat-naming-extras) |
| アバターがTポーズのまま、または動きに追従しない | [ガイド5](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system) + [Set Up Humanoid Bones](08-vrchat.md#set-up-humanoid-bones) |
| メッシュが不自然に変形する、または肌が伸びる | [Weight Transfer](05-rig-tools.md#weight-transfer) + [Weight Mirror](05-rig-tools.md#weight-mirror)、または [Automatic Bone Weight Recalculation](05-rig-tools.md#automatic-bone-weight-recalculation) で再計算します。 |
| 体の左右でウェイトが異なる | [Weight Mirror](05-rig-tools.md#weight-mirror) |
| 髪が頭を突き抜ける | [ガイド6、手順5](02-guides-a.md#step-5--add-colliders-recommended) — コライダーを追加します。 |
| 髪の物理が動かない | [ガイド6](02-guides-a.md#guide-6-add-hair-physics) — チェーン検出と PhysBone プリセットを確認します。 |
| 衣装が体を突き抜ける | [ガイド7](02-guides-a.md#guide-7-attach-clothing-that-moves-with-your-body)：<ol><li>ポーズを付けたメッシュを確認します。</li><li>貫通があれば、フィットやウェイトを調整します。</li></ol> **Detect Collisions** が確認するのは、ボーン名だけです。 |
| リップシンクが動かない | [ガイド8](03-guides-b.md#guide-8-set-up-lip-sync) + [VRChat Viseme Mapping](08-vrchat.md#vrchat-viseme-mapping) |
| アバターのパフォーマンスが Very Poor | [ガイド9](03-guides-b.md#guide-9-improve-your-avatars-performance) + [Check Performance](08-vrchat.md#check-performance) |
| VRM の読み込みに失敗する | [ガイド2、手順1](02-guides-a.md#step-1--install-the-vrm-add-on) — VRM アドオンをインストールします。 |
| MMD の読み込みに失敗する | [ガイド3、手順1](02-guides-a.md#step-1--install-mmd_tools) — mmd_tools をインストールします。 |
| MMD はインストール済みだが、ブリッジが無効 | **Open Add-on Preferences** から mmd_tools を有効にします。[ガイド3](02-guides-a.md#step-1--install-mmd_tools)のインストールメッセージを確認します。 |
| アトラスの選択が更新後に変わる | **Refresh Analysis** は選択肢を再構築します。<ol><li>ソースを確認します。</li><li>Bake Checked Sources を選択します。</li></ol> [Material Atlas Combiner](09-cats.md#material-atlas-combiner)を参照してください。 |
| Select All を使ってもテクスチャが未チェックになる | 欠落したテクスチャは、除外されたままです。一括選択が変更するのは、アクティブグループ内のその一覧だけです — [ソースの選択](09-cats.md#analyze-and-choose-sources)。 |
| アトラスがソースの変更を報告する | <ol><li>解析を更新します。</li><li>ソースを再確認します。</li></ol> 事前確認は、バックアップを作成する前に、解析後に変更されたソースを拒否します。 |
| アトラスに Revert がない | **Preserve Backup Duplicate** が無効だったか、Accept でバックアップが削除されています。保存済みのファイルチェックポイントを使います。 |
| Metallic または ORM アトラスのベイクが拒否される | **Metallic** と **Pack ORM Channels** を無効のままにします。これらのパスは、9.2.18では引き続き使用できません。 |
| アトラスのテクスチャがエンジン内で乱れる | UV0 を確認します。**Keep Source UV Maps** を使うと、`atlas_uv` が UV1 に残る場合があります — [UV 設定](09-cats.md#advanced-options)。 |
| ポーズモードや編集モードで書き出しに失敗する | 現在のメインの Unity または Unreal ボタンを使います。モードと選択を復元します。**Export (Profile)** には、オブジェクトモードを使います。 |
| 書き出し時の命名が競合を報告する | 対象名またはヒューマノイドの対応付けを修正します — [書き出し時のボーン命名](08-vrchat.md#export-bone-naming)。 |
| 命名プリセットを使うと All Actions が拒否される | **Active Action**、**No Animation**、**Keep Original Names** のいずれかを選択します — [検証付きプロファイル書き出し](08-vrchat.md#validated-profile-export)。 |
| 古いメカニズム形態に現在のバージョンが必要 | 9.2.18は、古い形態を再保存せずに読み込み、適用します — [形態](07-mechanisms.md#forms)。 |
| Rig Validator がエラーを表示する | [Rig Validator](05-rig-tools.md#rig-validator)：<ol><li>検証を実行します。</li><li>メッセージに従います。</li></ol> |
| ボーンが消えた、または見えない | [Bone Collections](05-rig-tools.md#bone-collections) → **Show All Collections**。 |
| BoneCraft のパネルが見つからない | BoneCraft と Rig Builder は左のツールシェルフ（**T**）、CATS は右のサイドバー（**N**）を使います。[各機能の場所](01-start.md#where-things-are)を参照してください。 |
| Mechanisms の完全な実例を見たい | [チュートリアル：Crescent Rose](12-crescent-rose.md) — 準備の8手順と Mechanisms の30手順、文章による説明、保持された英語原本の画像説明、`examples/crescent-rose/` にある完成ファイル。 |
| タブが違う側にある | Preferences → Add-ons → BoneCraft → Tabs → Left または Right。 |
| Properties → Scene に BoneCraft のセクションがない | Preferences → Add-ons → BoneCraft → Tabs → Scene Properties → Show。青色は有効を示します。Tools のツールパッケージも確認してください。 |
| Properties → Scene で BoneCraft を隠したい | Preferences → Tabs で Scene Properties → Show を無効にします。ビューポートのタブと Armature データタブは変わりません。 |
| オプションを選ぶ前にツールが実行される | 9.1では、次の操作を行う前に、ビューポートの Adjust Last Operation パネルで、実行直後にオプションを調整します。 |
| Place Rig Markers でマーカーが置けない | <ol><li>Auto-Rig Wizard を開始します。</li><li>マーカーの手順まで進みます。</li><li>オブジェクトモードに切り替えます。</li><li>ウィザードで選択したメッシュをクリックします。</li></ol> [Rig Builder](06-rig-builder.md#auto-rig-wizard)を参照してください。 |
| Build Mechanism で使用するパーツが分からない | <ol><li>先に Add Parts from Selection を使います。</li><li>メカニズムのリグか、そのパーツの1つを選択します。</li><li>ツールヘッダーで種類を選択します。</li><li>最初のパーツをクリックします。</li></ol> [Mechanisms](07-mechanisms.md#joints-and-links-one-example-each)を参照してください。 |
| ボーンがあるのに、ヒューマノイドの必要ボーンがないとして書き出しが拒否される | 必要なボーンが実際になければ、先にリグに追加する必要があります。必要なボーンがある場合：<ol><li>Auto-Map All を実行します。</li><li>VRM / VRoid の lint の下にある Fix Humanoid Map を実行します。</li></ol> [ガイド5](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system)を参照してください。 |
| 書き出した FBX に巨大な補助形状やチューブが出る | 制御用やカスタムシェイプのメッシュが不要なら、**Helper Meshes** を無効のままにします。 |
| Unity や Unreal でマテリアルが灰色になる | <ol><li>Embed Textures を有効にして書き出します。</li><li>Unity のマテリアル読み込み／抽出オプション、または Unreal の FBX マテリアル読み込みを使います。</li></ol> |
| ウェイトがすべて違うボーンに付いている | ウィザードの Generate Rig を再実行するか、[Weight Transfer](05-rig-tools.md#weight-transfer)、または CATS タブの **Smart Automatic Weights** を使います。 |
| 2つのリグを1つにしたい | [ガイド11：2つのリグを統合する](03-guides-b.md#guide-11-merge-two-rigs-together)。 |
| 補正シェイプが有効にならない | [Corrective Shape Keys](05-rig-tools.md#corrective-shape-keys)で、ボーンの軸と角度を確認します。 |
| 別のリグでアニメーションが不自然になる | [Retarget](05-rig-tools.md#retarget) — ボーンの対応付けを確認します。 |
| CATS のツールが「Run Fix Model first」と警告する | <ol><li>クリーンアップのオプションを確認します。</li><li>アバターに必要かどうかを判断します。</li></ol> この警告は、ツールをロックしません。[CATS パイプライン](04-cats-pipeline.md)を参照してください。 |
| 話すと口が裂ける、または割れる | 元の口のキー、メッシュのトポロジー、モディファイアーを確認します — [CATS：Visemes](09-cats.md#visemes)。 |
| VRChat で目が下を向いたままになる | <ol><li>左右のボーンの割り当て、向き、コンストレイントを確認します。</li><li>書き出したアバターを確認します。</li></ol> [CATS：Eye Tracking](09-cats.md#eye-tracking)を参照してください。 |
| シェイプキーを有効にするとメッシュが大きく崩れる | <ol><li>そのキーだけでテストします。</li><li>トポロジー、元のキーの値、モディファイアーを確認します。</li></ol> BoneCraft が記録するのはキーの混合状態であり、ボーンによる変形ではありません。[CATS：Pose & Shape Keys](09-cats.md#pose--shape-keys)を参照してください。 |
| VRChat でアバターが違う大きさで出現する | メッシュとアーマチュアのトランスフォーム、書き出し／読み込みのスケール設定を確認します。復元が必要なら、元に戻す操作か保存済みのチェックポイントを使います。[Apply All Transforms](09-cats.md#apply-all-transforms)を参照してください。 |
| ボーン名が日本語／中国語／韓国語 | [CATS：Translate Bone Names](09-cats.md#translate-bone-names)。 |
| リップシンクも口のシェイプキーもない | [CATS：Visemes](09-cats.md#visemes)：先に基本の口形を作ります。CATS は、A、O、CH の3つのソース割り当てから15個のビジームを生成します。 |
| メカニズムに「changed by hand」と表示される | [Mechanisms](07-mechanisms.md) — **Keep mine** または **Restore** を使います。 |

## 用語集 {#glossary}

**Adjust Last Operation：** 直前の操作のオプションを変更する、ビューポートのパネル。BoneCraft 9.1 の多くのツールは、先に実行し、ここにオプションを表示します。次の操作を行う前に調整してください。

**アーマチュア（Armature）：** Bforartists でのスケルトンの呼び方。ポーズやアニメーションを付けられるボーンの集合です。

**ブレンドシェイプ（Blend shape）：** シェイプキーを参照してください。

**ボーン（Bone）：** スケルトンの1区間。ボーンは階層（親 → 子）を作り、子ボーンは親に追従します。

**ボーンコレクション（Bone collection）：** 名前の付いたボーングループ。全体をまとめて表示または非表示にできます。

**Bone Names：** 書き出し時の命名方法。Keep Original Names は名前を保持します。Unity-Preset と Unreal-Preset は、書き出し用コピー内の認識されたボーンの名前を変更します。

**Bake Checked Sources：** 解析を自動で再構築せずに、確認済みのグループとソースの選択をベイクするアトラス操作。

**CATS：** 案内付きのパイプライン（クリーンアップ、ビジーム、アイトラッキング、トランスフォーム）で、VRChat 用のモデルを準備するツール群。CATS タブにあります。

**CATS パイプライン（CATS pipeline）：** CATS の6フェーズの順序：Fix Model → Material Atlas → Visemes → Eye Tracking → Pose to Shape → Apply Transforms。依存する前のフェーズが未完了なら、ツールは警告します。

**補正シェイプキー（Corrective shape key）：** 極端なポーズのメッシュを補正するため、ボーンがある角度に達したときに有効になるシェイプキー。

**デフォームボーン（Deform bone）：** メッシュを動かすボーン。制御専用で、メッシュを変形しないボーンもあります。

**アイトラッキング（Eye tracking）：** 目のボーン（`LeftEye`、`RightEye`）と、VRChat が目を動かすために使う回転コンストレイントを設定する CATS ツール。

**FBT（Full Body Tracking、フルボディトラッキング）：** Vive Tracker などの追加機器で、腰や足を含む全身を追跡する VRChat の機能。Fix FBT は、その機能用にルートボーンを調整します。

**FBX：** プログラム間で3Dモデル、スケルトン、アニメーションを受け渡すファイル形式。VRChat の標準形式です。

**Fix Model：** 重複頂点、独立した形状、法線などのデータに対する、選択式の CATS クリーンアップ操作。

1. オプションを確認します。

2. アバターに必要な操作だけを実行します。

**FK（Forward Kinematics、フォワードキネマティクス）：** 肩、ひじ、手首のように、チェーンのボーンを順に回してポーズを付ける方法。大きな体のポーズに向いています。

**IK（Inverse Kinematics、インバースキネマティクス）：** 手や足のようなチェーンの末端を配置してポーズを付ける方法。中間のボーンが追従します。手足を正確に配置するのに適しています。

**ヒューマノイド（Humanoid）：** ボーンを標準の体のスロットに対応付け、すべてのアバターで同じ動作制御を使えるようにする VRChat のアバターシステム。

**メカニズム（Mechanism）：** 通常のボーンとコンストレイントで構成する小道具や機械のリグ。ジョイント（Hinge、Slide、Telescope）やリンク（Piston、Gear Link、Follow）があります。[Mechanisms](07-mechanisms.md)を参照してください。

**メッシュ（Mesh）：** アバターの見える体を形作る3Dの表面。

**MMD（MikuMikuDance）：** 日本やアニメのコミュニティでよく使われる、無料の3Dアニメーションソフト。モデルは `.pmx`、アニメーションは `.vmd` を使います。

**モーフターゲット（Morph target）：** シェイプキーを参照してください。

**Operation Ledger：** 実行した CATS の全操作を、時刻と結果とともに示す一覧。

**PhysBone：** ボーンを揺らしたり、弾ませたり、衝突させたりする VRChat コンポーネント。髪、しっぽ、ぶら下がるアクセサリーに使います。

**Pipeline Status：** CATS の6フェーズを、完了時のチェックマークとともに示す一覧。

**PMX：** MikuMikuDance の主な3Dモデル形式。

**ポーズモード（Pose Mode）：** ボーンにポーズやアニメーションを付けるモード。

1. アーマチュアを選択します。

2. Ctrl+Tab を押します。

ビューポート左上のモード一覧から Pose Mode を選ぶ方法もあります。

**リグ／リギング（Rig / rigging）：** 3Dモデル内にスケルトンを作り、メッシュを結び付けて、ポーズやアニメーションを付けられるようにすること。

**シェイプキー（Shape key）：** 変形した状態のメッシュを保存したもの。さまざまな強さで混合でき、表情、リップシンク、体型変化を動かします。

**SDK（Software Development Kit、ソフトウェア開発キット）：** VRChat では、アバターをアップロードするための VRChat Creator Companion と、その Unity ツールを指します。

**Spline IK：** カーブに沿って動くボーンのチェーン。しっぽ、触手、長い髪、背骨に使います。

**Tポーズ（T-pose）：** まっすぐ立ち、両腕を横に広げた基準ポーズ。

**ツールシェルフ（Tool Shelf）：** 3Dビューポートの左パネル（**T**）。BoneCraft と Rig Builder は、既定でこのパネルを使います。

**頂点（Vertex）：** 3D空間内の1点。多数の頂点を辺と面で結んで、メッシュを構成します。

**頂点グループ（Vertex group）：** ボーンが動かす頂点を定める、名前付きの頂点集合。

**ビジーム（Viseme）：** 発声音に対応する口形。VRChat は、リップシンクに15個のビジームを使います。

**ウェイト／ウェイトペイント（Weight / weight painting）：** 各ボーンが各頂点を動かす強さを示す、0.0から1.0の値。ウェイトペイントは、これを視覚的に調整する方法です。

**ウィザード（Wizard）：** Rig Builder の Auto-Rig Wizard。メッシュ上にマーカーを置き、それを基にリグを作ります。

**ゼロウェイトボーン（Zero-weight bone）：** 頂点を1つも動かさないボーン。アバターの外見を変えずに、パフォーマンスを下げます。Fix Model とパフォーマンス最適化が、このボーンを削除します。

次へ：[新機能](11-whats-new.md)
