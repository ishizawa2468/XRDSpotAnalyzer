"""
nxsとponiを読み込んで，積算・cakingされたデータを返す
"""
import os
import numpy as np

import h5py
import pyFAI
import pyopencl as cl
from modules.HDF5 import HDF5Reader


class XRD:
    def __init__(self,
                 xrd_path=None, poni_path=None, mask_path=None,
                 npt_tth=1_000, npt_azi=1_000):
        # ファイル別に処理
        if xrd_path.endswith('.hdf'):
            self.hdf = HDF5Reader(xrd_path)
            # TODO: 少なくともframe数は必要。.nxs と同じ用に self.frame_num を設定
            raise NotImplementedError('実装中')
        elif xrd_path.endswith('.nxs'):
            self.nxs_path = xrd_path
            self.nxs = HDF5Reader(xrd_path)
            self.data_path_to_detector = "/entry/instrument/detector"  # hdfとしてのデータまでのpath
            self._read_params_from_nxs()
        else:
            raise NotImplementedError('.nxs, .hdfのみが実装されています。')
        # 共通処理
        self.gpu_available = self._check_opencl_support() # OpenCL が利用可能か確認。GPUを使えるか
        self.xrd_path = xrd_path # 保存しておく。他のメソッドで拡張子判断するときに使う
        self._create_integrator(poni_path) # AzimuthalIntegratorを作成する
        self.npt_tth = npt_tth
        self.npt_azi = npt_azi
        # maskの設定(なくても良い)
        if mask_path is not None:
            self.set_mask(mask_path=mask_path)

    """ 拡張子別に実装 """
    def _read_frame_data(self, frame):
        if self.xrd_path.endswith('.nxs'):
            # 複数の露光データがあるとき、最初のframeを飛ばす。使い物にならないときがある&重要でないことが多いため。
            if frame == 0 and self.frame_num > 1:
                frame = 1
            with h5py.File(self.xrd_path, 'r') as f:
                frame_data = f[os.path.join(self.data_path_to_detector, 'data')][frame, :, :]
        elif self.xrd_path.endswith('.hdf'):
            raise NotImplementedError('実装してください')
        return frame_data

    """ .nxs専用 """
    def _read_params_from_nxs(self):
        with h5py.File(self.nxs_path, 'r') as f:
            self.frame_num = f[os.path.join(self.data_path_to_detector, 'data')].shape[0]
            self.exposure_ms = f.get(os.path.join(self.data_path_to_detector, 'count_time'))[0]
        self.fps = 1_000.0 / self.exposure_ms


    """ 共通 """
    def _create_integrator(self, poni_path):
        self.ai = pyFAI.load(poni_path)

    """ 共通 """
    def set_poni(self, *, poni_path=None):
        if poni_path.endswith('.poni'):
            self.poni_path = poni_path
            print(f" > Set poni: {self.poni_path}")
            self.ai.load(self.poni_path)
        else:
            raise ValueError("poni_pathが無効です")

    """ 共通 """
    def set_mask(self, *, mask_path=None):
        if mask_path.endswith('.npy'):
            print(f" > Set mask: {mask_path}")
            self.ai.mask = np.load(mask_path)
        else:
            raise Exception(f'Mask path {mask_path} not .npy')

    """ 共通 """
    def get_tth(self):
        try:
            frame_data = self._read_frame_data(0) # 0frame目のデータを読み込む
            tth, I = self.ai.integrate1d(frame_data, npt=self.npt_tth, unit="2th_deg")
            return tth
        except Exception as e:
            raise RuntimeError(f"Frame 0 の 1D 積分中にエラーが発生しました: {str(e)}")

    """ 共通 """
    def get_azi(self):
        try:
            frame_data = self._read_frame_data(0) # 0frame目のデータを読み込む
            I, tth, azi = self.ai.integrate2d(frame_data,
                                              npt_rad=self.npt_tth,  # NOTE これはintegrate_1dと揃える
                                              npt_azim=self.npt_azi,
                                              unit="2th_deg")
            return azi
        except Exception as e:
            raise RuntimeError(f"Frame 0 の 2D 積分中にエラーが発生しました: {str(e)}")

    """ 共通 """
    def get_1d_pattern_data(self, frame=None):
        """
        指定したフレームのデータを1次元に積分するメソッド

        Parameters:
        frame (int): 積分するフレームのインデックス
        npt_rad (int): 回折角方向の分割数

        Returns:
            : 強度
        """
        try:
            frame_data = self._read_frame_data(frame)
            tth, I = self.ai.integrate1d(frame_data, npt=self.npt_tth, unit="2th_deg")
            return I # tthは別でメソッドを作っている
        except Exception as e:
            raise RuntimeError(f"Frame {frame} の 1D 積分中にエラーが発生しました: {str(e)}")

    """ 共通 """
    def get_caked_data(self, frame):
        """
        指定したフレームのデータを2次元に積分し、cakingを行うメソッド

        Parameters:
        frame (int): 積分するフレームのインデックス
        npt_rad (int): 回折角方向の分割数（デフォルトはself.npt_rad）
        npt_azim (int): 方位角方向の分割数（デフォルトはself.npt_azim）

        Returns:
            : 強度
        """
        try:
            frame_data = self._read_frame_data(frame)
            # 2D積分を行いcakedデータを取得する
            I, tth, azi = self.ai.integrate2d(frame_data,
                                              npt_rad=self.npt_tth,  # NOTE これはintegrate_1dと揃える
                                              npt_azim=self.npt_azi,
                                              unit="2th_deg",
                                              # method='ocl' if self.gpu_available else 'cython', # コメントアウトして
                                              )
            return I
        except Exception as e:
            raise RuntimeError(f"Frame {frame} の 2D 積分中にエラーが発生しました: {str(e)}")

    def _check_opencl_support(self):
        """ OpenCL (GPU) が利用可能かチェック """
        try:
            platforms = cl.get_platforms()
            if platforms:
                print("OpenCL (GPU) 利用可能: ", [platform.name for platform in platforms])
                return True
        except Exception:
            print("OpenCL (GPU) が見つかりません。CPU (cython) を使用します。")
            return False
