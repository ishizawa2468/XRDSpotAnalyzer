# NeXus（.nxs）構造

このドキュメントは、NeXus形式（`.nxs`）から取り込むパス構造をまとめたものです。
`tmp.hdf` 側の構造は [`docs/hdf_structure.md`](hdf_structure.md) を参照してください。

## 入出力フロー（.nxs → tmp.hdf）

1. `.nxs` の `/entry/instrument/detector/data` からフレームデータを取得する。
2. `/entry/instrument/detector/count_time` を読み取り、露光時間（ms）とする。
3. `frame_num` と `fps` を算出し、`tmp.hdf` の `entry/params` 以下へ書き込む。
4. 取得データを積分し、`tmp.hdf` の `entry/pattern`・`entry/cake` などへ保存する。

## XRD 読み取りで使用するパス

`modules/XRD.py` では、以下のパスを前提に `.nxs` を読み込みます。

- `/entry/instrument/detector/data`
  - 2D検出器データの配列。
  - 先頭次元がフレーム数（`frame_num`）に対応します。
- `/entry/instrument/detector/count_time`
  - 露光時間（ms）配列。
  - `count_time[0]` を `exposure_ms` として利用し、`fps = 1000.0 / exposure_ms` を計算します。

これらの値は `tmp.hdf` の `entry/params/frame_num`・`entry/params/fps` に反映されます。
詳細な保存先は [`docs/hdf_structure.md`](hdf_structure.md) を参照してください。

## 図との対応（diagram.svg）

`docs/diagram.svg` では `peaks/` という表記がありますが、実際のHDFパスは `entry/peak/`（単数）です。
図は構成の概念図であり、正確なパスは HDF仕様ドキュメント（[`docs/hdf_structure.md`](hdf_structure.md)）の `peak/` を参照してください。
この違いは両仕様ファイルで共通の注記として扱っています。
