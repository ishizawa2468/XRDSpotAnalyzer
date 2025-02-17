"""
XRDに関するデータを一時的な.hdfに書き込むクラス

Cakeデータ・Patternデータをはじめ、角度配列、frame配列など使いそうなデータを片っ端から保存する
"""
import os

import h5py
import numpy as np
from tqdm import tqdm

from modules import XRD
from modules.HDF5 import HDF5Writer


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
            # 既存データが存在すれば削除する
            if to_cake_data in f_append:
                del f_append[to_cake_data]

            # cakeデータの保存領域を作っておく
            cake_dataset = f_append.create_dataset(
                to_cake_data,
                shape=(self.xrd.frame_num, self.xrd.npt_azi, self.xrd.npt_tth),
                dtype=np.float32
            )
            # 書き込み
            # TODO streamlitでの進捗バー表示、threading処理
            for frame in tqdm(range(self.xrd.frame_num)):
                cake = self.xrd.get_caked_data(frame)
                cake_dataset[frame, :] = cake