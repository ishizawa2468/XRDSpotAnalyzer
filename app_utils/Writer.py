"""
XRDに関するデータを一時的なtmp.hdfに書き込むクラス

Cakeデータ・Patternデータをはじめ、角度配列、frame配列など使いそうなデータを片っ端から保存する
"""
import os
from concurrent.futures import ThreadPoolExecutor

import h5py
import numpy as np
from matplotlib import pyplot as plt
from tqdm import tqdm
import streamlit as st

from app_utils.peak_handler import Peak
from modules import XRD
from modules.HDF5 import HDF5Writer, HDF5Reader


class XRDWriter(HDF5Writer):
    BASE_PATH = 'entry/'

    def __init__(self, filepath: str, xrd: XRD):
        super().__init__(filepath) # .hdfファイルを紐づけ or 新規作成
        self.xrd = xrd

    def write_params(self):
        params_path = os.path.join(self.BASE_PATH, 'params') # パラメータ書き込み先の起点。これの先にぶら下げる

        # frame数
        to_frame_num = os.path.join(params_path, 'frame_num')
        self.write(data_path=to_frame_num, data=self.xrd.frame_num, overwrite=True)
        # fps (現在.nxsのみ)
        if self.xrd.xrd_path.endswith('.nxs'):
            to_fps = os.path.join(params_path, 'fps')
            self.write(data_path=to_fps, data=self.xrd.fps, overwrite=True)
        if self.xrd.xrd_path.endswith('.hdf'): # .hdfには実装されていないはずなので、間違って流用しないように消す
            self.delete(data_path=to_fps)

        # 分割数
        to_npt_tth = os.path.join(params_path, 'npt_tth')
        self.write(data_path=to_npt_tth, data=self.xrd.npt_tth, overwrite=True)
        to_npt_azi = os.path.join(params_path, 'npt_azi')
        self.write(data_path=to_npt_azi, data=self.xrd.npt_azi, overwrite=True)

    def write_arrays(self):
        arr_path = os.path.join(self.BASE_PATH, 'arr')

        # frame配列
        to_frame_arr = os.path.join(arr_path, 'frame')
        frame_arr = np.arange(self.xrd.frame_num)
        self.write(data_path=to_frame_arr, data=frame_arr, overwrite=True)
        # 2θ配列
        to_tth_arr = os.path.join(arr_path, 'tth')
        self.write(data_path=to_tth_arr, data=self.xrd.get_tth(), overwrite=True)
        # 方位角配列
        to_azi_arr = os.path.join(arr_path, 'azi')
        self.write(data_path=to_azi_arr, data=self.xrd.get_azi(), overwrite=True)


    # 全frameに対する処理なのでメソッドを分けている。
    #   HDF5Writer の write メソッドは書き込むデータ全てをメモリ上に載せることを前提にしているため
    # NOTE: 1,000frameくらいの1次元データなら、最近のPCならいちいち書き込まなくてもメモリに保持できる。そっちのほうが速い
    def write_pattern_data(self):
        to_pattern_data = os.path.join(self.BASE_PATH, 'pattern')
        with h5py.File(self.file_path, 'a') as f_append:
            # 既存データが存在すれば削除する
            if to_pattern_data in f_append:
                del f_append[to_pattern_data]
            # patternデータの保存領域を作っておく
            pattern_dataset = f_append.create_dataset(
                to_pattern_data,
                shape=(self.xrd.frame_num, self.xrd.npt_tth),
                dtype=np.float32
            )
            # 書き込み
            # TODO streamlitでの進捗バー表示、threading処理
            for frame in tqdm(range(self.xrd.frame_num)):
                pattern = self.xrd.get_1d_pattern_data(frame)
                pattern_dataset[frame, :] = pattern


    # 全frameに対する処理なのでメソッドを分けている
    def write_cake_data(self):
        to_cake_data = os.path.join(self.BASE_PATH, 'cake')

        with h5py.File(self.file_path, 'a') as f_append:
            if to_cake_data in f_append:
                del f_append[to_cake_data]

            cake_dataset = f_append.create_dataset(
                to_cake_data,
                shape=(self.xrd.frame_num, self.xrd.npt_azi, self.xrd.npt_tth),
                dtype=np.float32,
            )

            num_workers = min(8, os.cpu_count()-2)
            frame_list = list(range(self.xrd.frame_num))

            def _write_cake_slice(cake_dataset, frame, xrd: XRD):
                """ 1フレームのデータを取得してHDF5に書き込む """
                cake = xrd.get_caked_data(frame)
                cake_dataset[frame, :, :] = cake

            for frame in tqdm(frame_list):
                _write_cake_slice(cake_dataset, frame, self.xrd)

            # with ThreadPoolExecutor(max_workers=num_workers) as executor:
            #     list(tqdm(
            #         executor.map(lambda f: _write_cake_slice(cake_dataset, f, self.xrd), frame_list),
            #         total=len(frame_list),
            #         desc="Writing Cake Data"
            #     ))

class PeakWriter(HDF5Writer):
    BASE_PATH = 'entry/'

    # 設定されたピーク範囲から再積算を行う
    def write_re_integrate_peak_data(self, peak: Peak, peak_num: int, frame_num: int):
        # hdf内のデータパスの設定
        to_peak_path = os.path.join(self.BASE_PATH, 'peak', f'{peak_num}')
        to_peak_tth_pattern_data = os.path.join(to_peak_path, 'tth')
        to_peak_azi_pattern_data = os.path.join(to_peak_path, 'azi')

        # Peakから範囲の個数を計算しておく
        npt_azi_diff = peak.to_azi_idx - peak.from_azi_idx
        npt_tth_diff = peak.to_tth_idx - peak.from_tth_idx

        # 書き込み
        with h5py.File(self.file_path, 'a') as f_append:
            # 既存データを削除する
            if to_peak_azi_pattern_data in f_append:
                del f_append[to_peak_azi_pattern_data]
            if to_peak_tth_pattern_data in f_append:
                del f_append[to_peak_tth_pattern_data]

            # データ書き込み先の作成
            tth_pattern_dataset = f_append.create_dataset(
                to_peak_tth_pattern_data,
                shape=(frame_num, npt_tth_diff),
                dtype=np.float32,
            )
            azi_pattern_dataset = f_append.create_dataset(
                to_peak_azi_pattern_data,
                shape=(frame_num, npt_azi_diff),
                dtype=np.float32,
            )

            # 並列スレッド処理の準備
            num_workers = min(8, os.cpu_count()-2)
            frame_list = list(range(frame_num))

            # cakeデータ取得の fetcherを作成する
            cake_fetcher = HDF5Reader(self.file_path).create_fetcher(query='cake')

            def process_frame(frame):
                # フレームごとにデータ取得
                cake = cake_fetcher.fetch_by_frame(frame)
                selected_cake = cake[
                                peak.from_azi_idx:peak.to_azi_idx,
                                peak.from_tth_idx:peak.to_tth_idx
                                ]
                tth_pattern = selected_cake.mean(axis=0)
                azi_pattern = selected_cake.mean(axis=1)

                # HDF5 に直接書き込む（ファイルは開いたまま）
                tth_pattern_dataset[frame] = tth_pattern
                azi_pattern_dataset[frame] = azi_pattern

            # ThreadPoolExecutor でマルチスレッド処理
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                list(tqdm(
                    executor.map(process_frame, frame_list),
                    total=len(frame_list),
                    desc="Writing Peak Data"
                ))

            # 並列処理しないバージョン
            # for frame in tqdm(frame_list, desc="Writing Peak Data"):
            #     # cake dataを取得して選択された範囲を渡す
            #     cake = cake_fetcher.fetch_by_frame(frame)
            #     selected_cake = cake[
            #                     peak.from_azi_idx:peak.to_azi_idx,
            #                     peak.from_tth_idx:peak.to_tth_idx
            #                     ]
            #
            #     # azi方向に積算して 1d tthパターンを作成して保存 (回折角度の変化を見る用)
            #     tth_pattern = selected_cake.mean(axis=0)
            #     # tth方向に積算して、1d aziパターンを作成して保存 (粒の変化を見る用)
            #     azi_pattern = selected_cake.mean(axis=1)
            #     # 書き込み
            #     tth_pattern_dataset[frame] = tth_pattern
            #     azi_pattern_dataset[frame] = azi_pattern









