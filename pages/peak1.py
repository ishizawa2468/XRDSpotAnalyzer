import streamlit as st
from openpyxl.xml.functions import fromstring

from app_utils import setting_handler

setting_handler.set_common_setting(has_link_in_page=False)
setting = setting_handler.Setting()

st.title("Peak 1 の観察")

st.divider() # --------------------------------------------------------------------------------------------------------#
st.subheader("Peak 範囲を設定")

is_set_from_material = st.checkbox(label='物質・ミラー指数から範囲を決定する', value=True)
if is_set_from_material:
    # 物質
    material = st.selectbox(label='物質', options=['B2-KCl', 'MgO', 'B1-FeO', 'rB1-FeO'])
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

    st.write('`現在のPeak 1のプリセット`')
    # TODO: JSONに書いておく
    st.divider()

from_col, to_col = st.columns(2)
with from_col:
    from_tth = st.number_input(
        label='From 2θ (deg)',
        min_value = 0.0,
        value = 10.0, # FIXME
        step = 0.05
    )
    from_azi = st.number_input(
        label='From Azimuth (deg)',
        value = -60, # FIXME
        step = 1
    )
with to_col:
    to_tth = st.number_input( # 終わりの2θ。from_tthより大きい必要がある
        label='To 2θ (deg)',
        min_value = from_tth + 0.05, # NOTE: 0.01 は適当
        value = 11.0, # FIXME
        step = 0.05
    )
    to_azi = st.number_input(
        label='To Azimuth (deg)',
        min_value = from_azi + 1, # NOTE: 0.01 は適当
        value = 60, # FIXME
        step = 1
    )
