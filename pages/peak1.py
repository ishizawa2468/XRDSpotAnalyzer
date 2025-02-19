import gc
import os

import streamlit as st
from matplotlib import pyplot as plt
from openpyxl.xml.functions import fromstring

from app_utils import setting_handler
from app_utils.Writer import XRDWriter, PeakWriter
from app_utils.peak_handler import Peak
from modules.HDF5 import HDF5Reader

setting_handler.set_common_setting(has_link_in_page=False)
setting = setting_handler.Setting()

# 何本目かを変数にしておく
peak_num = 1
st.title(f"Peak {peak_num} の観察")

st.divider() # --------------------------------------------------------------------------------------------------------#
st.subheader("Peak 範囲を設定")

# 物質から決定する場合
is_set_from_material = st.checkbox(label='物質・ミラー指数から範囲を決定する', value=False)
if is_set_from_material:
    # 物質
    material = st.selectbox(label='物質', options=['B2-KCl', 'MgO', 'B1-FeO', 'rB1-FeO']) # FIXME: クラスにまとめておく
    # ミラー指数
    miller_col1, miller_col2, miller_col3 = st.columns(3)
    with miller_col1:
        miller_h = st.number_input(label='h', value=1, step=1)
    with miller_col2:
        miller_k = st.number_input(label='k', value=1, step=1)
    with miller_col3:
        miller_l = st.number_input(label='l', value=1, step=1)
    # 圧力範囲
    pressure_col1, pressure_col2 = st.columns(2)
    with pressure_col1:
        from_pressure = st.number_input(label='From P (GPa)  ※ 負でOK', value=-100, step=1)
    with pressure_col2:
        to_pressure = st.number_input(label='To P (GPa)', value=200, step=1)

    st.write('`現在のPeak 1の物質プリセット`')
    # TODO: JSONに書いておく peak_numごとに保存
    st.divider()

# ここで範囲のデフォルト値を入れておく
boundaries = {}
if is_set_from_material:
    boundaries['from_tth'] = 10.0
    boundaries['to_tth'] = 11.0
    boundaries['from_azi'] = -60.0
    boundaries['to_azi'] = 60.0
else:
    boundaries['from_tth'] = 9.0
    boundaries['to_tth'] = 10.0
    boundaries['from_azi'] = -60.0
    boundaries['to_azi'] = 60.0


# tmp.hdfを参照しておく
cake_hdf = HDF5Reader(setting.setting_json['tmp_hdf_path'])
# 配列データの取得
frame_arr = cake_hdf.find_by(query='arr/frame')
tth_arr = cake_hdf.find_by(query='arr/tth')
azi_arr = cake_hdf.find_by(query='arr/azi')

peak = Peak().set_from_json(
    peak_num, tth_arr, azi_arr
)

# 入力欄
from_col, to_col = st.columns(2)
with from_col:
    from_tth = st.number_input(
        label='From 2θ (deg)',
        min_value = tth_arr.min(),
        max_value = tth_arr.max(),
        value = peak.from_tth,
        step = 0.05
    )
    from_azi = st.number_input(
        label='From Azimuth (deg)',
        min_value = azi_arr.min(),
        max_value = azi_arr.max(),
        value = peak.from_azi,
        step = 1.0
    )
    from_frame = st.number_input(
        label='From Frame',
        min_value = frame_arr.min(),
        max_value = frame_arr.max()-1,
        value = peak.from_frame,
        step = 1
    )
with to_col:
    to_tth = st.number_input( # 終わりの2θ。from_tthより大きい必要がある
        label='To 2θ (deg)',
        min_value = from_tth + 0.05, # NOTE: 0.01 は適当
        max_value = tth_arr.max(),
        value = peak.to_tth,
        step = 0.05
    )
    to_azi = st.number_input(
        label='To Azimuth (deg)',
        min_value = from_azi + 1, # NOTE: 0.01 は適当
        max_value = azi_arr.max(),
        value = peak.to_azi,
        step = 1.0
    )
    to_frame = st.number_input(
        label='To Frame',
        min_value = from_frame+1,
        max_value = frame_arr.max()-1,
        value = peak.to_frame,
        step = 1
    )

peak = Peak().set_boundaries(
    tth_arr, from_tth, to_tth,
    azi_arr, from_azi, to_azi,
    from_frame, to_frame
)
if st.button('更新'):
    peak.save_to_json(peak_num=peak_num)

st.divider() # --------------------------------------------------------------------------------------------------------#
st.subheader("Peak 範囲の表示")
# patternデータの表示
pattern = cake_hdf.find_by(query='pattern')
# パターンの必要な領域を切り取る
selected_pattern = pattern[from_frame:to_frame, peak.from_tth_idx:peak.to_tth_idx]
st.write(selected_pattern.shape)
fig, ax = plt.subplots(figsize=(10, 5))
im = ax.imshow(selected_pattern.T, cmap='jet', aspect='auto', origin='lower',
               extent=[from_frame, to_frame, from_tth, to_tth])
plt.colorbar(im, ax=ax, label='Intensity (a.u.)')
ax.set_xlabel('Time (frame)')
ax.set_ylabel('2θ (deg)')
st.pyplot(fig)
del fig

if st.button('この範囲で再積算する'):
    # ↑で設定された2θの範囲で、全frameのcake dataから再度積算を行う。
    hdf_writer = PeakWriter(file_path=setting.setting_json['tmp_hdf_path'])
    hdf_writer.write_re_integrate_peak_data(
        peak=peak,
        peak_num=peak_num,
        frame_num=len(frame_arr)
    )

gc.collect()

st.divider() # --------------------------------------------------------------------------------------------------------#
st.subheader("再積算結果")
#
to_tth_query = os.path.join('peak', f'{peak_num}', 'tth')
tth_pattern = cake_hdf.find_by(query=to_tth_query)[from_frame:to_frame]
st.write(tth_pattern.shape)
# 描画
fig, ax = plt.subplots(figsize=(10, 5))
im = ax.imshow(tth_pattern.T, cmap='jet', aspect='auto', origin='lower')
plt.colorbar(im, ax=ax, label='Intensity (a.u.)')
ax.set_xlabel('Time (frame)')
ax.set_ylabel('2θ (deg)')
st.pyplot(fig)
del fig

#
to_azi_query = os.path.join('peak', f'{peak_num}', 'azi')
azi_pattern = cake_hdf.find_by(query=to_azi_query)[from_frame:to_frame]
# 描画
fig, ax = plt.subplots()
im = ax.imshow(azi_pattern.T, cmap='jet', aspect='auto', origin='lower')
plt.colorbar(im, ax=ax, label='Intensity (a.u.)')
ax.set_xlabel('Time (frame)')
ax.set_ylabel('2θ (deg)')
st.pyplot(fig)
del fig
