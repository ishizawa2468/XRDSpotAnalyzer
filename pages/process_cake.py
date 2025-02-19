import gc
import os

import streamlit as st
from matplotlib import pyplot as plt

from app_utils.Writer import XRDWriter
from modules.HDF5 import HDF5Reader
from modules.XRD import XRD
from app_utils import setting_handler

setting_handler.set_common_setting(has_link_in_page=False)
setting = setting_handler.Setting()

st.title("積算処理")

st.divider() # --------------------------------------------------------------------------------------------------------#
st.subheader('積算するファイルを確認')
st.markdown(
    f"""
    *XRD data path*:
    
        {setting.setting_json["xrd_path"]}
    
    *PONI data path*:
    
        {setting.setting_json["poni_path"]}
    
    *Number of Points (分割数)*:
    
        2θ: {setting.setting_json["npt_tth"]} / Azimuth: {setting.setting_json["npt_azi"]}
    """
)

# 選択されたデータを取り出す・処理するためにオブジェクト化
xrd = XRD(
    xrd_path=setting.setting_json['xrd_path'],
    poni_path=setting.setting_json['poni_path'],
    npt_tth=setting.setting_json['npt_tth'],
    npt_azi=setting.setting_json['npt_azi'],
)

st.divider() # --------------------------------------------------------------------------------------------------------#
st.subheader('積算・Caking処理')

st.write('')
if st.toggle("中間データの保存先を変更する"):
    tmp_hdf_path = st.text_input(
        label='tmp hdf',
        value=setting.setting_json['tmp_hdf_path'],
    )
    if st.button(label='更新'):
        setting.update_setting(key='tmp_hdf_path', value=tmp_hdf_path)
        setting = setting_handler.Setting()

st.markdown(
    f"""
    *Temporary saved to (一時保存先)*:

        {setting.setting_json["tmp_hdf_path"]}
    """
)
# 処理
if st.button(label='Start process', type='primary'):
    # 書き込みクラスをオブジェクト化
    writer = XRDWriter(filepath=setting.setting_json['tmp_hdf_path'], xrd=xrd)
    # 書き込み
    writer.write_params()
    writer.write_arrays()
    writer.write_pattern_data()
    writer.write_cake_data()

gc.collect() # メモリを掃除

st.divider() # --------------------------------------------------------------------------------------------------------#
st.subheader('積算データの確認')

if not os.path.exists(setting.setting_json['tmp_hdf_path']):
    st.error(f'ファイルが見つかりません: {setting.setting_json['tmp_hdf_path']}')
    st.stop()

# ここからはtmp.hdfを参照しながらデータを描画する
cake_hdf = HDF5Reader(setting.setting_json['tmp_hdf_path'])

# 配列データの取得
frame_arr = cake_hdf.find_by(query='arr/frame')
tth_arr = cake_hdf.find_by(query='arr/tth')
azi_arr = cake_hdf.find_by(query='arr/azi')

# patternデータの表示
pattern = cake_hdf.find_by(query='pattern')
fig, ax = plt.subplots()
im = ax.imshow(pattern, cmap='jet', aspect='auto', origin='lower',
               extent=[tth_arr.min(), tth_arr.max(), frame_arr.min(), frame_arr.max()])
plt.colorbar(im, ax=ax, label='Intensity (a.u.)')
ax.set_xlabel('2θ (deg)')
ax.set_ylabel('Time (frame)')
st.pyplot(fig)
del fig

# cakeデータの表示
# 大量のデータに対しては fetcher (HDF内の特定のデータパスにあるデータを取る専用のオブジェクト)を作成しておく
cake_fetcher = cake_hdf.create_fetcher(query='cake')
frame = st.slider(
    label='frame',
    min_value=0,
    max_value=500
)
fig, ax = plt.subplots()
im = ax.imshow(
    cake_fetcher.fetch_by_frame(frame=frame),
    cmap='jet', aspect='auto', origin='lower',
    extent=[tth_arr.min(), tth_arr.max(), azi_arr.min(), azi_arr.max()]
)
plt.colorbar(im, ax=ax, label='Intensity (a.u.)')
ax.set_xlabel('2θ (deg)')
ax.set_ylabel('Azimuth (deg)')
ax.set_title(f'Frame = {frame}')
st.pyplot(fig)
del fig





