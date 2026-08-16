# Align View to Selection

**選択した頂点群を「ひとつの平面」として捉え、その平面を真正面から見るようにビューを揃える Blender アドオンです。**

Blender標準のビュー整列では扱いづらい、**辺ループ**や**接続されていない頂点群**でも使えます。

デフォルトショートカット：**Alt + Numpad 7**

---

## インストール

1. GitHub右上の **Code** をクリック
2. **Download ZIP** をクリック
3. ダウンロードしたZIPを解凍せず、そのままBlenderへインストール

インストール方法はどちらでもOKです。

- **Edit → Preferences → Extensions → Install from Disk...** からZIPを選択
- ZIPを **Blenderのウィンドウ上へドラッグ＆ドロップ**

---

## 使い方

1. Mesh Edit Modeに入る
2. 3つ以上の頂点を選択
3. **Alt + Numpad 7**

または、

**3D Viewport → Nパネル → View → Align View to Selection**

から実行できます。

### こんな選択に使えます

- 辺ループ
- 少し歪んだ / 非平面なループ
- 接続されていない複数の頂点
- 選択した辺や面
- 複数オブジェクトを同時編集している状態

---

## Blender標準との違い

Blender標準のビュー整列は、主にアクティブ要素や法線などから向きを決めます。

Align View to Selectionは、**選択した頂点の位置関係そのもの**から、

> この点群に最もよくフィットする平面はどこか？

を計算してビュー方向を決めます。

そのため、辺ループや離れた頂点集合でも、点群全体を基準にした向きへ揃えられます。

---

## 動作

実行すると、

- 選択頂点から best-fit plane を計算
- その平面に対して垂直な方向へビューを整列
- 現在のロールをできるだけ維持
- 現在のズームを維持
- Blender標準に近い滑らかなアニメーションで移動

します。

best-fit plane の計算には PCA を使っています。

---

## 設定

**Edit → Preferences → Add-ons / Extensions → Align View to Selection**

### Auto Transform Orientation: View

デフォルト：**OFF**

ONにすると、ビュー整列後に Transform Orientation を `View` へ自動で切り替えます。

パン・ズーム・ロールだけでは `View` のまま維持し、ビューの向き自体を変更すると、実行前の Transform Orientation に戻ります。

### Shortcut

PreferencesにはBlender標準のKeymap編集UIが表示されます。

デフォルト：

**Alt + Numpad 7**

Blenderの通常のショートカット設定と同じように、キーや修飾キーを変更できます。

同じキーが別の3D View / Mesh Edit Mode操作と競合している場合は警告を表示します。

> ショートカット行の右端にある `×` はアドオンのアンインストールではなく、そのショートカット項目を削除するボタンです。

---

## 制限

- 3頂点以上の選択が必要です
- ほぼ一直線上の頂点群では平面を一意に決められないため、処理をキャンセルします
- Mesh Edit Mode向けです

---

## 対応環境

- Blender 4.2以降
- 外部Pythonライブラリ不要

## License

GPL-3.0-or-later
