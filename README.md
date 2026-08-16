# Align View to Selection

Blenderの3Dビューポートを、**選択した頂点群に最もよくフィットする平面（best-fit plane）へ正対させる**ためのアドオンです。

Blender標準の法線やアクティブ要素を基準にしたビュー整列では意図した向きになりにくい、**辺ループ**や**互いに接続されていない頂点群**を扱うときに便利です。

## 特徴

- 選択した3頂点以上から best-fit plane を計算
- 辺ループに対応
- 接続されていない頂点群にも対応
- 辺・面を選択した場合も、その選択頂点を使って計算
- 複数オブジェクトのEdit Modeにも対応
- トポロジーや平均法線ではなく、選択頂点の**位置関係**から向きを決定
- 現在のビューポートのロールをできるだけ維持
- 現在のズームを維持
- Blender標準に近い滑らかなビュー遷移
- Transform Orientationを自動的に `View` に切り替えるオプション
- ショートカットをBlender標準のKeymap UIから変更可能
- ショートカット競合を検出して警告

## インストール

1. GitHub右上の **Code** をクリック
2. **Download ZIP** をクリック
3. ダウンロードしたZIPを解凍せず、そのままBlenderにインストール

Blenderでは、次のどちらかの方法でインストールできます。

- **Edit → Preferences → Extensions → Install from Disk...** からZIPを選択
- ダウンロードしたZIPを **Blenderのウィンドウ上へドラッグ＆ドロップ**

## 使い方

1. Mesh Edit Modeに入る
2. 3つ以上の頂点を選択する
3. **Align View to Selection** を実行する

デフォルトショートカット：

**Alt + Numpad 7**

コマンドは次の場所からも実行できます。

**3D Viewport → Nパネル → View → Align View to Selection**

## ショートカット設定

**Edit → Preferences → Add-ons / Extensions → Align View to Selection**

Preferences内にBlender標準のKeymap編集UIが表示されます。

キー、Ctrl / Shift / Altなどの修飾キー、イベントタイプ、ショートカットの有効・無効を、Blenderの他のショートカットと同じ操作で変更できます。

同じキーが関連する3D View / Mesh Edit Modeのコマンドと競合している場合は警告を表示します。

## Auto Transform Orientation: View

デフォルトでは **OFF** です。

有効にすると、Align View to Selectionの実行後にTransform Orientationを `View` へ切り替えます。

その後、パン・ズーム・ロールだけを行っている間は `View` を維持し、ビューの向きそのものを変更すると、実行前のTransform Orientationへ戻します。

## 仕組み

Align View to Selectionは、選択した全頂点の位置からPCAを使って best-fit plane を求めます。

大まかな処理は次の通りです。

1. 選択された頂点のワールド座標を取得
2. 点群の中心と共分散行列を計算
3. 最も分散が小さい方向を平面の法線として取得
4. 現在ユーザー側を向いている法線方向を選択
5. 現在の画面上方向をできるだけ維持しながらビューを整列
6. ズームを維持したまま滑らかに遷移

Blender標準の整列機能が主にアクティブ要素・法線・Transform Orientationなどから方向を決めるのに対し、このアドオンは、

> 選択した点群の位置関係を最もよく表す平面はどこか？

を基準にビュー方向を決めます。

そのため、少し非平面になっている辺ループや、接続されていない頂点集合でも扱えます。

## 制限

- 3頂点以上の選択が必要です
- ほぼ一直線上に並んだ頂点群では平面を一意に決められないため、処理をキャンセルします
- Mesh Edit Mode向けの機能です

## 対応バージョン

- Blender 4.2以降
- 外部Pythonライブラリ不要

## ライセンス

GPL-3.0-or-later
