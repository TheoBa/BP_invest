import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.gcp_connector import download_dataframe
import numpy_financial as npf
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

def create_kpi_metrics(df, real_estate_df):
    detention_period  = real_estate_df.loc[0, 'durée_de_détention_(année)']
    actualisation_rate = real_estate_df.loc[0, 'taux_d_actualisation']
    apport = real_estate_df.loc[0, 'apport']
    st.markdown("## Key metrics after detention period")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Net Cash Flow", f"€{df['cumulative_net_cash_flow'][f'year_{detention_period}']:,.0f}")
    with col2:
        st.metric("IRR (Internal Rate of Return)", f"{100 * npf.irr(df['net_cash_flow'].to_list()):,.2f}%")
    with col3:
        st.metric("VAN (Valeur Actuelle Nette)", f"{npf.npv(actualisation_rate, df['net_cash_flow'].to_list()):,.2f}€")
    with col4:
        st.metric("EqX", f"{df['cumulative_net_cash_flow'][f'year_{detention_period}']/apport:,.2f}x")
    
    st.markdown("## Key metrics over the investment period")
    buffer, col1, col2, col3, buffer = st.columns(5)
    with col1:
        min_net_cash_flow = df.loc[df.index > 'year_0', 'net_cash_flow'].min()
        st.metric("Min of Net Cash Flow (excluding contribution)", f"€{min_net_cash_flow:,.0f}")
    with col2:
        min_cumulative_net_cash_flow = df.loc[df.index > 'year_0', 'cumulative_net_cash_flow'].min() + apport
        st.metric("Min of Cumulative Net Cash Flow", f"€{min_cumulative_net_cash_flow:,.0f}")
    with col3:
        mean_net_cash_flow = df.loc[(df.index > 'year_0')&(df.index < f'year_{detention_period}'), 'net_cash_flow'].mean()
        st.metric("Mean of Net Cash Flow", f"€{mean_net_cash_flow:,.0f}")

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
        credit_duration = st.slider("Durée de crédit (années)", 1, 30, int(real_estate_df.loc[0, 'durée_de_crédit_(année)']))

    with col2:
        credit_rate = st.slider("Taux d'emprunt (en %)", 0.0, 5.0, 100 * float(real_estate_df.loc[0, 'taux_d_emprunt'])) / 100
        actualisation_rate = st.slider("Taux d'actualisation (en %)", 0.0, 10.0, 100 * float(real_estate_df.loc[0, 'taux_d_actualisation'])) / 100
        
    
    # Update real_estate_df with new values
    real_estate_df.loc[0, 'durée_de_détention_(année)'] = detention_period
    real_estate_df.loc[0, 'taux_d_emprunt'] = credit_rate
    real_estate_df.loc[0, 'durée_de_crédit_(année)'] = credit_duration
    real_estate_df.loc[0, 'taux_d_actualisation'] = actualisation_rate
    # Rebuild yearly_cashflow_df
    rebuilt_real_estate_df = create_additional_features(real_estate_df.copy())
    yearly_cashflow_df = build_yearly_cashflow_df(rebuilt_real_estate_df)
    df = yearly_cashflow_df.T
    
    create_kpi_metrics(yearly_cashflow_df, rebuilt_real_estate_df)
    
    cash_flow_chart = create_cash_flow_chart(df.loc[['net_cash_flow', 'cumulative_net_cash_flow']].T, 30)
    st.plotly_chart(cash_flow_chart, use_container_width=True)
    
    property_value_chart = create_property_value_chart(df.loc[['valeur_vénale', 'capital_restant_dû']].T, 30)
    st.plotly_chart(property_value_chart, use_container_width=True)
    
    st.subheader("Detailed Cash Flow Table")
    st.dataframe(df.style.highlight_max(axis=0))

if __name__ == "__main__":
    main()