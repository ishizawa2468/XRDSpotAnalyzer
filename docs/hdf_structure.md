# HDF汎用構造（tmp.hdf）

このドキュメントは、アプリ内部で扱う一時HDFファイル（`tmp.hdf`）の構造をまとめたものです。
入出力の関係や NeXus (.nxs) からの取り込み経路は、[`docs/nxs_structure.md`](nxs_structure.md) にも記載しています。

## 入出力フロー（.nxs → tmp.hdf）

1. NeXus (`.nxs`) から `/entry/instrument/detector/data` と `count_time` を読み込む。
2. 読み込んだフレーム数・露光時間から `frame_num`・`fps` を算出する。
3. `tmp.hdf` に各種配列・積分データを書き込む。

※詳細な NeXus 側のパスは [`docs/nxs_structure.md`](nxs_structure.md) を参照してください。

## ルート構成

HDFファイル内の基点は `entry/` です。

```
entry/
├─ params/
├─ arr/
├─ pattern
├─ cake
└─ peak/
   └─ {peak_num}/
```

## params/ 以下

`entry/params/` 配下に解析条件が保存されます。

- `entry/params/frame_num`
  - フレーム数。
- `entry/params/fps`
  - `.nxs` から読み取った露光時間（`count_time`）から算出したFPS。
- `entry/params/npt_tth`
  - 2θ方向の分割数。
- `entry/params/npt_azi`
  - 方位角方向の分割数。

## arr/ 以下

`entry/arr/` 配下に各種軸配列を保存します。

- `entry/arr/frame`
  - `0..frame_num-1` のフレーム配列。
- `entry/arr/tth`
  - 2θ配列（積分の軸）。
- `entry/arr/azi`
  - 方位角配列（積分の軸）。

## pattern / cake

- `entry/pattern`
  - 形状: `(frame_num, npt_tth)`
  - 各フレームの1Dパターン強度。
- `entry/cake`
  - 形状: `(frame_num, npt_azi, npt_tth)`
  - 各フレームの2D積分（caked）データ。

## peak/ 以下

ピーク範囲に限定した再積算データを保存します。

- `entry/peak/{peak_num}/tth`
  - 形状: `(frame_num, npt_tth_diff)`
  - 2θ方向に平均化した1Dパターン。
- `entry/peak/{peak_num}/azi`
  - 形状: `(frame_num, npt_azi_diff)`
  - 方位角方向に平均化した1Dパターン。

## 図との対応（diagram.svg）

`docs/diagram.svg` では `peaks/` という表記がありますが、実際のHDFパスは `entry/peak/`（単数）です。
図は構成の概念図であり、正確なパスは本ドキュメントの `peak/` を参照してください。
この違いは NeXus 仕様ドキュメント（[`docs/nxs_structure.md`](nxs_structure.md)）にも明記しています。
