import streamlit as st
import pandas as pd
import numpy as np

from utils.computations import PMT, compute_remaining_capital_after_y_years
from utils.gcp_connector import download_dataframe
import plotly.graph_objects as go

st.set_page_config(page_title="📈 Checks", page_icon="📈", layout="wide")


def create_additional_features(database_inputs: pd.DataFrame):
    real_estate_df = (
        database_inputs
        .copy()
        .assign(
            # section "input_buying_hypothesis"
            frais_d_acquisition = lambda x: x["frais_d_acquisition_(prct_prix_d_achat)"] * x["prix_d_achat"],
            prix_acquisition = lambda x: x["prix_d_achat"] + x["frais_d_acquisition"] + x["travaux"],
            # section "input_financial_hypothesis"
            ltv = lambda x: (x["prix_acquisition"] - x["apport"]) / x["prix_acquisition"],
            montant_emprunté = lambda x: x["ltv"] * x["prix_acquisition"],
            mensualité = lambda x: PMT(C=x["montant_emprunté"], n=x["durée_de_crédit_(année)"]*12, t=x["taux_d_emprunt"]),
            # section "input_market_hypothesis"
            capital_restant_dû = lambda x: - compute_remaining_capital_after_y_years(C=x["prix_acquisition"], M=x["mensualité"], t=x["taux_d_emprunt"], y=x["durée_de_détention_(année)"]),
            valeur_de_sortie = lambda x: x["valeur_vénale"] * (1+ x["market_value_growth"]) ** x["durée_de_détention_(année)"],
            frais_de_vente = lambda x: - x["frais_de_vente_(taux)"] * x["valeur_de_sortie"],
            valeur_nette_de_sortie = lambda x: x["valeur_de_sortie"] + x["frais_de_vente"] + x["capital_restant_dû"],
            # section "input_annual_revenue"
            remboursements = lambda x: - x["mensualité"] * 12,
            # section "input_recurring_charges"
            frais_d_entretien = lambda x: x["frais_d_entretien_(prct_prix_d_achat)"] * x["prix_d_achat"],
            assurance_gli_pno = lambda x: x["assurance_(gli,_pno)_(prct_loyer)"] * x['loyer_mensuel'] * 12,
            # section "input_operating_capex"
            total_charges_récurrantes = lambda x: x["remboursements"] + x["gestion_locative"] + x["comptabilité"] + x["frais_de_copropriété"] + x["taxe_foncière"] + x["frais_d_entretien"] + x["assurance_gli_pno"]
        )
        .rename(columns=lambda x: x.lower().replace(" ", "_").replace("'", "_"))
    )
    return real_estate_df


def build_yearly_cashflow_df(real_estate_df: pd.DataFrame, time_horizon: int = 30) -> pd.DataFrame:
    """
    This function builds a yearly cashflow dataframe from a real estate dataframe.
    It is used to check the financial feasibility of the investment.
    It is a yearly cashflow, with a row for each year of the time horizon and the following columns (sliced in different sections):
    Index:
    - year: from 0 to time_horizon
    
    Income:
    - rent: rent of previous year * (1 + real_estate_df.loc[0, "market_rent_growth"]), 0 in year 0 and real_estate_df.loc[0, "rent"] in year 1
    - vacancy: rent of the year * real_estate_df.loc[0, "vacancy"]
    - unpaied_rent: rent of the year * real_estate_df.loc[0, "unpaied_rent"]
    - gross_effective_revenues: sum of rent, vacancy and unpaied_rent
    
    Recurring charges: (algebric values so always negative)
    - gestion_locative: gestion_locative of previous year * (1 + real_estate_df.loc[0, "property_tax_growth"]), 0 in year 0 and real_estate_df.loc[0, "gestion_locative"] in year 1
    - comptabilité: comptabilité of previous year * (1 + real_estate_df.loc[0, "property_tax_growth"]), 0 in year 0 and real_estate_df.loc[0, "comptabilité"] in year 1
    - frais_de_copropriété: frais_de_copropriété of previous year * (1 + real_estate_df.loc[0, "property_tax_growth"]), 0 in year 0 and real_estate_df.loc[0, "frais_de_copropriété"] in year 1
    - taxe_foncière: taxe_foncière of previous year * (1 + real_estate_df.loc[0, "property_tax_growth"]), 0 in year 0 and real_estate_df.loc[0, "taxe_foncière"] in year 1
    - frais_d_entretien: frais_d_entretien of previous year * (1 + real_estate_df.loc[0, "property_tax_growth"]), 0 in year 0 and real_estate_df.loc[0, "frais_d_entretien"] in year 1
    - assurance_gli_pno: assurance_gli_pno of previous year * (1 + real_estate_df.loc[0, "property_tax_growth"]), 0 in year 0 and real_estate_df.loc[0, "assurance_gli_pno"] in year 1
    - total_charges_récurrantes: sum of gestion_locative, comptabilité, frais_de_copropriété, taxe_foncière, frais_d_entretien, assurance_gli_pno
    
    Net Operating Income:
    - net_operating_income: algebric sum of gross_effective_revenues and total_charges_récurrantes
    
    Non Recurring charges: (algebric values so always negative)
    - apport: real_estate_df.loc[0, "apport"] only in year 0 then 0
    - travaux_non_récurrents: real_estate_df.loc[0, "travaux_non_récurrents"] every "fréquence" years, 0 otherwise
    - total_non_recurring_charges: sum of apport and travaux_non_récurrents
    
    Debt:
    - remboursements: 0 in year 0 and real_estate_df.loc[0, "remboursements"] every other year
    - cash_flow_after_debt: algebric sum of net_operating_income, total_non_recurring_charges and remboursements
    - cumulative_cash_flow_after_debt: cumulative sum of cash_flow_after_debt through the years

    Selling hypothesis:
    - valeur_vénale: previous year's valeur_vénale * (1 + real_estate_df["market_value_growth"]), initialized with real_estate_df.loc[0, "valeur_vénale"]
    - valeur_vénale_à_la_vente: valeur_vénale only in the selling year, 0 otherwise
    - frais_de_vente: valeur_vénale_à_la_vente * real_estate_df["frais_de_vente_(taux)"]
    - capital_restant_dû: - compute_remaining_capital_after_y_years(C=real_estate_df["prix_acquisition"], M=real_estate_df["mensualité"], t=real_estate_df["taux_d_emprunt"], y=year)
    - capital_residuel_à_la_vente: capital_restant_dû only in the selling year, 0 otherwise
    - valeur_nette_de_sortie: algebric sum of valeur_vénale_à_la_vente, frais_de_vente and capital_restant_dû_à_la_vente only in the selling year, 0 otherwise

    Net Cash Flow:
    - net_cash_flow: algebric sum of cash_flow_after_debt and valeur_nette_de_sortie
    - cumulative_net_cash_flow: cumulative sum of net_cash_flow through the years
    """
    # Initialize the DataFrame with years and apply transformations using operator chaining
    yearly_cashflow_df = (
        pd.DataFrame({'year': range(time_horizon + 1)})
        # Income
        .assign(
            rent=lambda df: np.where(df['year'] == 0, 0, real_estate_df.loc[0, 'loyer_mensuel'] * 12 * (1 + real_estate_df.loc[0, 'market_rent_growth']) ** (df['year'] - 1)),
            vacancy=lambda df: -df['rent'] * real_estate_df.loc[0, 'vacancy'],
            unpaied_rent=lambda df: -df['rent'] * real_estate_df.loc[0, 'loyers_impayés'],
            gross_effective_revenues=lambda df: df['rent'] + df['vacancy'] + df['unpaied_rent']
        )
        # Recurring charges
        .assign(**{
            charge: lambda df, charge=charge: np.where(df['year'] == 0, 0, -real_estate_df.loc[0, charge] * (1 + real_estate_df.loc[0, 'property_tax_growth']) ** (df['year'] - 1))
            for charge in ['gestion_locative', 'comptabilité', 'frais_de_copropriété', 'taxe_foncière', 'frais_d_entretien', 'assurance_gli_pno']
        })
        .assign(
            total_charges_récurrantes=lambda df: df[['gestion_locative', 'comptabilité', 'frais_de_copropriété', 'taxe_foncière', 'frais_d_entretien', 'assurance_gli_pno']].sum(axis=1),
            net_operating_income=lambda df: df['gross_effective_revenues'] + df['total_charges_récurrantes']
        )
        # Non Recurring charges
        .assign(
            apport=lambda df: np.where(df['year'] == 0, -real_estate_df.loc[0, 'apport'], 0),
            travaux_non_récurrents=lambda df: np.where(df['year'] % real_estate_df.loc[0, 'fréquence'] == 2, -real_estate_df.loc[0, 'travaux_non_récurrent'], 0),
            total_non_recurring_charges=lambda df: df['apport'] + df['travaux_non_récurrents']
        )
        # Debt
        .assign(
            remboursements=lambda df: np.where(df['year'] == 0, 0, real_estate_df.loc[0, 'remboursements']),
            cash_flow_after_debt=lambda df: df['net_operating_income'] + df['total_non_recurring_charges'] + df['remboursements'],
            cumulative_cash_flow_after_debt=lambda df: df['cash_flow_after_debt'].cumsum()
        )
        # Selling hypothesis
        .assign(
            valeur_vénale=lambda df: real_estate_df.loc[0, 'valeur_vénale'] * (1 + real_estate_df.loc[0, 'market_value_growth']) ** df['year'],
            valeur_vénale_à_la_vente=lambda df: np.where(df['year'] == real_estate_df.loc[0, 'durée_de_détention_(année)'], df['valeur_vénale'], 0),
            frais_de_vente=lambda df: -df['valeur_vénale_à_la_vente'] * real_estate_df.loc[0, 'frais_de_vente_(taux)'],
            capital_restant_dû=lambda df: df.apply(lambda row: -compute_remaining_capital_after_y_years(
                C=real_estate_df.loc[0, 'prix_acquisition'],
                M=real_estate_df.loc[0, 'mensualité'],
                t=real_estate_df.loc[0, 'taux_d_emprunt'],
                y=row['year']
            ), axis=1),
            capital_residuel_à_la_vente=lambda df: np.where(df['year'] == real_estate_df.loc[0, 'durée_de_détention_(année)'], df['capital_restant_dû'], 0),
            valeur_nette_de_sortie=lambda df: np.where(
                df['year'] == real_estate_df.loc[0, 'durée_de_détention_(année)'],
                df['valeur_vénale_à_la_vente'] + df['frais_de_vente'] + df['capital_residuel_à_la_vente'],
                0
            )
        )
        # Net Cash Flow
        .assign(
            net_cash_flow=lambda df: df['cash_flow_after_debt'] + df['valeur_nette_de_sortie'],
            cumulative_net_cash_flow=lambda df: df['net_cash_flow'].cumsum()
        )
        # Map the 'year' column to 'year_{i}' format and set it as the index
        .assign(year=lambda df: df['year'].apply(lambda i: f'year_{i}'))
        .set_index('year')
    )
    
    return yearly_cashflow_df


def display_checks(real_estate_df: pd.DataFrame):
    yearly_cashflow_df = build_yearly_cashflow_df(real_estate_df)
    def color_negative_red(val):
        color = 'red' if val < 0 else 'black'
        return f'color: {color}'

    def highlight_rows(s):
        is_highlight = s.name in ["gross_effective_revenues", "total_charges_récurrantes", "net_operating_income", "total_non_recurring_charges", "cash_flow_after_debt", "valeur_nette_de_sortie", "net_cash_flow"]
        return ['font-weight: bold; background-color: #e6f2ff' if is_highlight else '' for _ in s]

    styled_df = yearly_cashflow_df.T.astype(int).style.map(color_negative_red).apply(highlight_rows, axis=1)
    
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

real_estate_df = query_real_estate_df()
real_estate_df = create_additional_features(real_estate_df.copy())
#st.dataframe(real_estate_df)
display_checks(real_estate_df)