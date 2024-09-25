import streamlit as st

st.set_page_config(page_title="📈 Dashboard", page_icon="📈", layout="wide")

def main():
    st.title("🔢 Dashboard")
    st.markdown("""
    ## Dashboard Overview
    This dashboard is designed to provide various visualizations and insights into the real estate data.
    Several display options may be tried here, but please note that it is still a work in progress.
    We appreciate your patience as we continue to improve and add more features.
    """)

if __name__ == "__main__":
    main()