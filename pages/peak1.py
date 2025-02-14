import streamlit as st

from app_utils import setting_handler

setting_handler.set_common_setting(has_link_in_page=False)
setting = setting_handler.Setting()

st.title("")

st.divider() # --------------------------------------------------------------------------------------------------------#
