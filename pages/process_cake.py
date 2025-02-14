import streamlit as st
from matplotlib import pyplot as plt

from modules.XRD import XRD
from app_utils import setting_handler

setting_handler.set_common_setting(has_link_in_page=False)
setting = setting_handler.Setting()

st.title("")

st.divider() # --------------------------------------------------------------------------------------------------------#

st.write(setting.setting_json)

xrd = XRD(
    xrd_path=setting.setting_json['xrd_path'],
    poni_path=setting.setting_json['poni_path'],
    npt_tth=setting.setting_json['npt_tth'],
    npt_azi=setting.setting_json['npt_azi'],
)

fig, ax = plt.subplots()
ax.imshow(xrd.get_caked_data(100))
st.pyplot(fig)