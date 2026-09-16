# pyxel-aozora-reader

Pyxel + 日本語TTFで青空文庫テキストをタイプ表示するノベルゲーム風リーダー。

## リポジトリ構成

```
pyxel-aozora-reader/
├── aozora_reader.py           # メインスクリプト（このリポジトリのルートに配置）
├── aozora_416.txt             # 読み込む青空文庫テキスト（要用意・下記参照）
├── PixelMplus12-Regular.ttf   # 日本語ピクセルフォント（要用意・下記参照）
└── README.md
```

すべて **リポジトリ直下（フラット）** に置くのがポイント。
Pyxel Web Launcher はスクリプトと同じ場所にあるファイルしか `open()` できないため、
サブフォルダに分けると `FILE_PATH` / `FONT_PATH` の指定と Launcher の URL 階層の両方を
揃えて変更する必要がある。迷ったらフラット構成が一番シンプル。

## 用意するファイル

このリポジトリには `aozora_reader.py` と `README.md` しか含まれていない。
以下の2つは自分で入手して直下に置くこと。

1. **PixelMplus12-Regular.ttf**
   [PixelMplus](https://github.com/itouhiro/PixelMplus) の配布ページから取得。
   ライセンスに従って同梱・再配布可否を確認すること。

2. **aozora_416.txt**
   青空文庫からダウンロードした作品テキスト（UTF-8）。
   ファイル名を変える場合は `aozora_reader.py` 内の `FILE_PATH` も合わせて変更する。

## GitHubへの配置手順

```bash
git init
git add aozora_reader.py README.md PixelMplus12-Regular.ttf aozora_416.txt
git commit -m "add pyxel aozora reader"
git remote add origin https://github.com/<ユーザー名>/pyxel-aozora-reader.git
git push -u origin main
```

## Pyxel Web Launcher での実行

リポジトリ直下に `aozora_reader.py` を置いた場合のURLは以下の形式:

```
https://kitao.github.io/pyxel/wasm/launcher/?run=<ユーザー名>.pyxel-aozora-reader.aozora_reader
```

例えば GitHub ユーザー名が `Neko-Kuroi` なら:

```
https://kitao.github.io/pyxel/wasm/launcher/?run=Neko-Kuroi.pyxel-aozora-reader.aozora_reader
```

サブディレクトリ（例: `src/`）に置いた場合は
`?run=<ユーザー名>.<リポジトリ名>.src.aozora_reader` のように階層をドットで追加する。

## 操作

- ENTER / クリック: 文字送りをスキップ / 次ページへ
- SPACE 長押し: 文字送りを高速化
- ↑: 前ページに戻る
- Q / ESC: 終了