import streamlit as st
import pandas as pd

from utils.gcp_connector import download_dataframe
from utils.transformations import build_yearly_cashflow_df, create_additional_features

st.set_page_config(page_title="📈 Checks", page_icon="📈", layout="wide")


def display_checks(real_estate_df: pd.DataFrame):
    yearly_cashflow_df = build_yearly_cashflow_df(real_estate_df)
    st.session_state['yearly_cashflow_df'] = yearly_cashflow_df
    def color_negative_red(val):
        color = 'red' if val < 0 else 'black'
        return f'color: {color}'

    def highlight_rows(s):
        is_highlight = s.name in ["gross_effective_revenues", "total_charges_récurrantes", "net_operating_income", "total_non_recurring_charges", "cash_flow_after_debt", "valeur_nette_de_sortie", "net_cash_flow"]
        return ['font-weight: bold; background-color: #e6f2ff' if is_highlight else '' for _ in s]

    styled_df = yearly_cashflow_df.T.round().astype(int).style.map(color_negative_red).apply(highlight_rows, axis=1)
    
    # Create a scrollable container for the dataframe
    st.markdown(
        f"""
        <div style="max-height: 500px; overflow-y: scroll;">
            {styled_df.to_html()}
        """,
        unsafe_allow_html=True
    )


def query_real_estate_df():
    real_estate_df = download_dataframe("02data.csv")
    real_estate_id = st.selectbox("Select a real estate", real_estate_df['real_estate_id'].unique())
    return real_estate_df[real_estate_df['real_estate_id'] == real_estate_id].sort_values('timestamp', ascending=False).iloc[:1].reset_index(drop=True)


st.title("📈 Checks")
st.markdown("""
This page is used to check the financial feasibility of the investment.
It is a yearly cashflow, with a row for each year of the time horizon and the following columns (sliced in different sections):
""")

# Add a refresh button
st.button("Refresh")
real_estate_df = query_real_estate_df()
real_estate_df = create_additional_features(real_estate_df.copy())
display_checks(real_estate_df)
