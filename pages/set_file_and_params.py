import streamlit as st
import os

from app_utils import setting_handler

setting_handler.set_common_setting(has_link_in_page=False)
setting = setting_handler.Setting()

# FIXME: メソッドはutilに移す
def display_selectbox_recursivly(path: str, depth: int, max_depth: int, cols, keyword):
    if not os.path.exists(path):
        st.error("ファイル・フォルダが存在しません")
    if depth > max_depth:
        return path
    if os.path.isdir(path):
        with cols[depth]:
            folder = st.selectbox(
                label=f'Layer {depth+1}',
                options=sorted(exclude_extra_files(os.listdir(path))), # 隠しファイルを除いてソートした選択肢を提示
                key=f'{keyword}_{depth}'
            )
        if folder is None:
            st.warning('空のフォルダです。')
            st.stop()
        folder_path = os.path.join(path, folder)
        return display_selectbox_recursivly(folder_path, depth + 1, max_depth, cols, keyword)
    else:
        return path

def exclude_extra_files(files: list):
    ref_files = files.copy()
    for file in ref_files:
        if file.startswith('.'):
            files.remove(file)
    return files


st.title("ファイル・パラメータ設定")


st.divider() # --------------------------------------------------------------------------------------------------------#
st.subheader("XRDデータを設定")
xrd_base_path = st.text_input(
    label="読み込み先",
    value=setting.setting_json["xrd_base_path"],
    key='xrd_base_input'
)
if st.button('読み込み先を更新', key='update_xrd_base_path'):
    setting.update_setting(key='xrd_base_path', value=xrd_base_path)
    setting = setting_handler.Setting()
st.markdown('')
st.markdown("##### XRDデータファイルを選択")
max_depth = 4
xrd_cols = st.columns(max_depth)
xrd_path = display_selectbox_recursivly(xrd_base_path, 0, max_depth, xrd_cols, 'xrd_file')
st.write(f"*Update to?* : `{xrd_path}`")
if st.button('更新', key='update_xrd_path', type='primary'):
    setting.update_setting(key='xrd_path', value=xrd_path)
    setting = setting_handler.Setting()
st.write(f"*Selected file*: `{setting.setting_json['xrd_path']}`")


st.divider() # --------------------------------------------------------------------------------------------------------#
st.subheader("校正データ(`.poni`)を設定")
poni_base_path = st.text_input(
    label="読み込み先",
    value=setting.setting_json["poni_base_path"],
    key='poni_base_input'
)
if st.button('読み込み先を更新', key='update_poni_base_path'):
    setting.update_setting(key='poni_base_path', value=poni_base_path)
    setting = setting_handler.Setting()
st.markdown('')
st.markdown("##### 校正ファイルを選択")
max_depth = 2
poni_cols = st.columns(max_depth)
poni_path = display_selectbox_recursivly(poni_base_path, 0, max_depth, poni_cols, 'poni_file')
st.write(f"*Update to?* : `{poni_path}`")
if st.button('更新', key='update_poni_path', type='primary'):
    setting.update_setting(key='poni_path', value=poni_path)
    setting = setting_handler.Setting()
st.write(f"*Selected file*: `{setting.setting_json['poni_path']}`")


st.divider() # --------------------------------------------------------------------------------------------------------#
st.subheader("分割パラメータを設定")
tth_col, azi_col = st.columns(2)
with tth_col:
    npt_tth = st.number_input(
        label='2θ方向の分割数',
        value=setting.setting_json["npt_tth"],
        min_value=1_000,
        step=1_000
    )
with azi_col:
    npt_azi = st.number_input(
        label='方位角方向の分割数',
        value=setting.setting_json["npt_azi"],
        min_value=1_000,
        step=1_000
    )
if st.button('更新', key='update_number_of_ponits', type='primary'):
    setting.update_setting(key='npt_tth', value=npt_tth)
    setting.update_setting(key='npt_azi', value=npt_azi)
    setting = setting_handler.Setting()
