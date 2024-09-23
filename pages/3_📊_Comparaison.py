import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.gcp_connector import download_dataframe
from utils.computations import PMT, compute_remaining_capital_after_y_years

st.set_page_config(page_title="📊 Comparaison", page_icon="📊", layout="wide")

# Import necessary functions from Checks.py
from utils.transformations import create_additional_features, build_yearly_cashflow_df

def load_css():
    st.markdown("""
        <style>
        .stSlider > div > div > div > div {
            background-color: #0068c9;
        }
        .stMetric {
            background-color: #f0f2f6;
            border-radius: 5px;
            padding: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

def query_real_estate_df():
    real_estate_df = download_dataframe("02data.csv")
    real_estate_id = st.selectbox("Select a real estate", real_estate_df['real_estate_id'].unique())
    return real_estate_df[real_estate_df['real_estate_id'] == real_estate_id].sort_values('timestamp', ascending=False).iloc[:1].reset_index(drop=True)

def create_kpi_metrics(df, year):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Cumulative Cash Flow", f"€{df[f'year_{year}']['cumulative_net_cash_flow']:,.0f}")
    with col2:
        st.metric("Net Operating Income", f"€{df[f'year_{year}']['net_operating_income']:,.0f}")
    with col3:
        st.metric("Property Value", f"€{df[f'year_{year}']['valeur_vénale']:,.0f}")
    with col4:
        st.metric("Remaining Debt", f"€{abs(df[f'year_{year}']['capital_restant_dû']):,.0f}")

def create_cash_flow_chart(df, max_year):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(x=df.index, y=df['net_cash_flow'], name="Net Cash Flow"),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(x=df.index, y=df['cumulative_net_cash_flow'], name="Cumulative Net Cash Flow"),
        secondary_y=True,
    )
    
    fig.update_layout(
        title_text="Cash Flow Over Time",
        xaxis_title="Year",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_yaxes(title_text="Net Cash Flow", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative Net Cash Flow", secondary_y=True)
    
    return fig

def create_property_value_chart(df, max_year):
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(x=df.index, y=df['valeur_vénale'], name="Property Value"))
    fig.add_trace(go.Scatter(x=df.index, y=-df['capital_restant_dû'], name="Remaining Debt"))
    
    fig.update_layout(
        title_text="Property Value vs Remaining Debt",
        xaxis_title="Year",
        yaxis_title="Amount (€)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def main():
    load_css()
    st.title("📊 Real Estate Investment Comparison")
    
    # Select real estate
    real_estate_df = query_real_estate_df()
    
    
    col1, col2 = st.columns(2)
    
    with col1:
        detention_period = st.slider("Durée de détention (années)", 1, 30, int(real_estate_df.loc[0, 'durée_de_détention_(année)']))
    
    with col2:
        credit_duration = st.slider("Durée de crédit (années)", 1, 30, int(real_estate_df.loc[0, 'durée_de_crédit_(année)']))
    
    # Update real_estate_df with new values
    real_estate_df.loc[0, 'durée_de_détention_(année)'] = detention_period
    real_estate_df.loc[0, 'durée_de_crédit_(année)'] = credit_duration
    
    # Rebuild yearly_cashflow_df
    rebuilt_real_estate_df = create_additional_features(real_estate_df.copy())
    yearly_cashflow_df = build_yearly_cashflow_df(rebuilt_real_estate_df)
    df = yearly_cashflow_df.T
    
    create_kpi_metrics(df, detention_period)
    
    cash_flow_chart = create_cash_flow_chart(df.loc[['net_cash_flow', 'cumulative_net_cash_flow']].T, 30)
    st.plotly_chart(cash_flow_chart, use_container_width=True)
    
    property_value_chart = create_property_value_chart(df.loc[['valeur_vénale', 'capital_restant_dû']].T, 30)
    st.plotly_chart(property_value_chart, use_container_width=True)
    
    st.subheader("Detailed Cash Flow Table")
    st.dataframe(df.style.highlight_max(axis=0))

if __name__ == "__main__":
    main()