import streamlit as st

import app_utils.setting_handler as setting_handler

st.set_option('client.showSidebarNavigation', False) # デフォルトのサイドバー表示を一旦無効にする。自分でlabelをつけるため。
setting_handler.set_common_setting()

print('log: Homeを表示')

# 共通の表示
st.title("Welcome to XRD Spot Analyzer!")
st.markdown(
    """
    ### 【概要】
    - hoge
        - `.nxs` / `.hdf` に対応しています。
        - 
    - 以下のようにページが分かれています。←から選択してください。
        1. hoge: 
        2. huga:
    """
)
