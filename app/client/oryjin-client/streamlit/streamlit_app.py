import streamlit as st

# Define the pages
main_page = st.Page("main_page.py", title="Main Page", icon="🎈")
page_2 = st.Page("dsp_page.py", title="DSP", icon="❄️")


# Set up navigation
pg = st.navigation([main_page, page_2])

# Run the selected page
pg.run()