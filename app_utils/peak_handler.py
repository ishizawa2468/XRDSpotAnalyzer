import json
import os
import streamlit as st
import numpy as np

""" peak_numはメンバとして持たないので注意。その都度わたしてあげる必要がある。 """
class Peak:
    path_to_json = os.path.join('app_utils', 'peaks.json')

    def __init__(self):
        pass

    def set_boundaries(
            self,
            tth_arr, from_tth, to_tth,
            azi_arr, from_azi, to_azi,
            from_frame, to_frame
        ):
        # 2θ
        self.tth_arr = tth_arr
        self.from_tth = from_tth
        self.to_tth = to_tth
        # 方位角
        self.azi_arr = azi_arr
        self.from_azi = from_azi
        self.to_azi = to_azi
        # それぞれのindexを取得しておく
        self._set_boundary_indices()
        # frame
        self.from_frame = from_frame
        self.to_frame = to_frame
        return self

    def set_from_json(
            self, peak_num,
            tth_arr, azi_arr
    ):
        self.tth_arr = tth_arr
        self.azi_arr = azi_arr
        # jsonを読んでそこから代入
        peak_settings = self._get_setting()
        self.from_tth = peak_settings[f'{peak_num}']['from_tth']
        self.to_tth = peak_settings[f'{peak_num}']['to_tth']
        self.from_azi = peak_settings[f'{peak_num}']['from_azi']
        self.to_azi = peak_settings[f'{peak_num}']['to_azi']
        self.from_frame = peak_settings[f'{peak_num}']['from_frame']
        self.to_frame = peak_settings[f'{peak_num}']['to_frame']
        return self

    def _set_boundary_indices(self):
        # 2θ
        from_tth_idx, to_tth_idx = self._return_idx(
            self.tth_arr,
            self.from_tth, self.to_tth
        )
        self.from_tth_idx = from_tth_idx
        self.to_tth_idx = to_tth_idx
        # 方位角
        from_azi_idx, to_azi_idx = self._return_idx(
            self.azi_arr,
            self.from_azi, self.to_azi
        )
        self.from_azi_idx = from_azi_idx
        self.to_azi_idx = to_azi_idx

    # 配列と値を渡したら、値に最も近いindexを返す関数
    @staticmethod
    def _return_idx(arr, *values) -> int | tuple[int, ...]:
        idxs = tuple(int((np.abs(arr - value)).argmin()) for value in values)
        # valuesが1つであればタプルではなく単独の値を返す
        return idxs[0] if len(idxs) == 1 else idxs

    def save_to_json(self, peak_num):
        # 読み出し
        peak_settings = self._get_setting()
        # 更新
        peak_settings[peak_num] = {
            'from_tth': self.from_tth,
            'to_tth': self.to_tth,
            'from_azi': self.from_azi,
            'to_azi': self.to_azi,
            'from_frame': self.from_frame,
            'to_frame': self.to_frame
        }
        # 更新したものを書き込み
        with open(self.path_to_json, 'w') as f:  # 追加したものを書き込み
            json.dump(peak_settings, f, ensure_ascii=False)

    # 設定jsonを読み込むメソッド
    def _get_setting(self) -> dict:
        try:
            with open(self.path_to_json, 'r') as f:
                setting_json = json.load(f)
        except FileNotFoundError:
            print(f'File {self.path_to_json} not found.')
        return setting_json

