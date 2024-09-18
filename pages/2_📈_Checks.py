import streamlit as st
import pandas as pd
import numpy as np

from utils.computations import PMT, compute_remaining_capital_after_y_years
from utils.gcp_connector import download_dataframe

st.set_page_config(page_title="📈 Checks", page_icon="📈")


def create_additional_features(database_inputs: pd.DataFrame):
    real_estate_df = (
        database_inputs
        .copy()
        .assign(
            # section "input_buying_hypothesis"
            Frais_d_acquisition = lambda x: x["Frais d'acquisition (prct prix d'achat)"] * x["Prix d'achat"],
            Prix_acquisition = lambda x: x["Prix d'achat"] + x["Frais_d_acquisition"] + x["Travaux"],
            # section "input_financial_hypothesis"
            LTV = lambda x: (x["Prix_acquisition"] - x["Apport"]) / x["Prix_acquisition"],
            Montant_emprunté = lambda x: x["LTV"] * x["Prix_acquisition"],
            Mensualité = lambda x: PMT(C=x["Montant_emprunté"], n=x["Durée de crédit (année)"]*12, t=x["Taux d'emprunt"]),
            # section "input_market_hypothesis"
            capital_restant_dû = lambda x: - compute_remaining_capital_after_y_years(C=x["Prix_acquisition"], M=x["Mensualité"], t=x["Taux d'emprunt"], y=x["Durée de crédit (année)"]),
            valeur_de_sortie = lambda x: x["Valeur vénale"] * (1+ x["Market Value Growth"]) ** x["Durée de détention (année)"],
            frais_de_vente = lambda x: - x["Frais de vente (taux)"] * x["valeur_de_sortie"],
            valeur_nette_de_sortie = lambda x: x["valeur_de_sortie"] + x["frais_de_vente"] + x["capital_restant_dû"],
            # section "input_annual_revenue"
            Remboursements = lambda x: - x["Mensualité"] * 12,
            # section "input_recurring_charges"
            Frais_d_entretien = lambda x: x["Frais d'entretien (prct prix d'achat)"] * x["Prix d'achat"],
            Assurance_GLI_PNO = lambda x: x["Assurance (GLI, PNO) (prct loyer)"] * x['Loyer mensuel'] * 12,
            # section "input_operating_capex"
            TOTAL_Charges_Récurrantes = lambda x: x["Remboursements"] + x["Gestion locative"] + x["Comptabilité"] + x["Frais de copropriété"] + x["Taxe foncière"] + x["Frais_d_entretien"] + x["Assurance_GLI_PNO"]
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
    - rent: rent of previous year * (1 + real_estate_df.loc[0, "market_rent_growth"]), initialized with real_estate_df.loc[0, "rent"]
    - vacancy: rent of the year * real_estate_df.loc[0, "vacancy"]
    - unpaied_rent: rent of the year * real_estate_df.loc[0, "unpaied_rent"]
    - gross_effective_revenues: sum of rent, vacancy and unpaied_rent
    
    Recurring charges: (algebric values so always negative)
    - gestion_locative: real_estate_df.loc[0, "gestion_locative"] of the year * real_estate_df.loc[0, "property_tax_growth"]
    - comptabilité: real_estate_df.loc[0, "comptabilité"] of the year * real_estate_df.loc[0, "property_tax_growth"]
    - frais_de_copropriété: real_estate_df.loc[0, "frais_de_copropriété"] of the year * real_estate_df.loc[0, "property_tax_growth"]
    - taxe_foncière: real_estate_df.loc[0, "taxe_foncière"] of the year * real_estate_df.loc[0, "property_tax_growth"]
    - frais_d_entretien: real_estate_df.loc[0, "frais_d_entretien"] of the year * real_estate_df.loc[0, "property_tax_growth"]
    - assurance_gli_pno: real_estate_df.loc[0, "assurance_gli_pno"] of the year * real_estate_df.loc[0, "property_tax_growth"]
    - total_charges_récurrantes: sum of gestion_locative, comptabilité, frais_de_copropriété, taxe_foncière, frais_d_entretien, assurance_gli_pno
    
    Net Operating Income:
    - net_operating_income: algebric sum of gross_effective_revenues and total_charges_récurrantes
    
    Non Recurring charges: (algebric values so always negative)
    - apport: real_estate_df.loc[0, "apport"] only in the first year then 0
    - travaux_non_récurrents: real_estate_df.loc[0, "travaux_non_récurrents"] every "fréquence" years, 0 otherwise
    - total_non_recurring_charges: sum of apport and travaux_non_récurrents
    
    Debt:
    - remboursements: real_estate_df.loc[0, "remboursements"] every year
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
    # Initialize the DataFrame with years
    yearly_cashflow_df = pd.DataFrame({'year': range(time_horizon + 1)})
    
    # Income
    yearly_cashflow_df['rent'] = real_estate_df.loc[0, 'loyer_mensuel'] * 12 * (1 + real_estate_df.loc[0, 'market_rent_growth']) ** yearly_cashflow_df['year']
    yearly_cashflow_df['vacancy'] = -yearly_cashflow_df['rent'] * real_estate_df.loc[0, 'vacancy']
    yearly_cashflow_df['unpaied_rent'] = -yearly_cashflow_df['rent'] * real_estate_df.loc[0, 'loyers_impayés']
    yearly_cashflow_df['gross_effective_revenues'] = yearly_cashflow_df['rent'] + yearly_cashflow_df['vacancy'] + yearly_cashflow_df['unpaied_rent']
    
    # Recurring charges
    recurring_charges = ['gestion_locative', 'comptabilité', 'frais_de_copropriété', 'taxe_foncière', 'frais_d_entretien', 'assurance_gli_pno']
    for charge in recurring_charges:
        yearly_cashflow_df[charge] = -real_estate_df.loc[0, charge] * (1 + real_estate_df.loc[0, 'property_tax_growth']) ** yearly_cashflow_df['year']
    
    yearly_cashflow_df['total_charges_récurrantes'] = yearly_cashflow_df[recurring_charges].sum(axis=1)
    
    # Net Operating Income
    yearly_cashflow_df['net_operating_income'] = yearly_cashflow_df['gross_effective_revenues'] + yearly_cashflow_df['total_charges_récurrantes']
    
    # Non Recurring charges
    yearly_cashflow_df['apport'] = 0
    yearly_cashflow_df.loc[0, 'apport'] = -real_estate_df.loc[0, 'apport']
    
    frequency = real_estate_df.loc[0, 'fréquence']
    yearly_cashflow_df['travaux_non_récurrents'] = np.where(yearly_cashflow_df['year'] % frequency == 0, -real_estate_df.loc[0, 'travaux_non_récurrent'], 0)
    
    yearly_cashflow_df['total_non_recurring_charges'] = yearly_cashflow_df['apport'] + yearly_cashflow_df['travaux_non_récurrents']
    
    # Debt
    yearly_cashflow_df['remboursements'] = real_estate_df.loc[0, 'remboursements']
    yearly_cashflow_df['cash_flow_after_debt'] = yearly_cashflow_df['net_operating_income'] + yearly_cashflow_df['total_non_recurring_charges'] + yearly_cashflow_df['remboursements']
    yearly_cashflow_df['cumulative_cash_flow_after_debt'] = yearly_cashflow_df['cash_flow_after_debt'].cumsum()
    
    # Selling hypothesis
    yearly_cashflow_df['valeur_vénale'] = real_estate_df.loc[0, 'valeur_vénale'] * (1 + real_estate_df.loc[0, 'market_value_growth']) ** yearly_cashflow_df['year']
    
    selling_year = real_estate_df.loc[0, 'durée_de_détention_(année)']
    yearly_cashflow_df['valeur_vénale_à_la_vente'] = np.where(yearly_cashflow_df['year'] == selling_year, yearly_cashflow_df['valeur_vénale'], 0)
    yearly_cashflow_df['frais_de_vente'] = -yearly_cashflow_df['valeur_vénale_à_la_vente'] * real_estate_df.loc[0, 'frais_de_vente_(taux)']
    
    yearly_cashflow_df['capital_restant_dû'] = yearly_cashflow_df.apply(lambda row: -compute_remaining_capital_after_y_years(
        C=real_estate_df.loc[0, 'prix_acquisition'],
        M=real_estate_df.loc[0, 'mensualité'],
        t=real_estate_df.loc[0, 'taux_d_emprunt'],
        y=row['year']
    ), axis=1)
    
    yearly_cashflow_df['capital_residuel_à_la_vente'] = np.where(yearly_cashflow_df['year'] == selling_year, yearly_cashflow_df['capital_restant_dû'], 0)
    yearly_cashflow_df['valeur_nette_de_sortie'] = np.where(
        yearly_cashflow_df['year'] == selling_year,
        yearly_cashflow_df['valeur_vénale_à_la_vente'] + yearly_cashflow_df['frais_de_vente'] + yearly_cashflow_df['capital_residuel_à_la_vente'],
        0
    )
    
    # Net Cash Flow
    yearly_cashflow_df['net_cash_flow'] = yearly_cashflow_df['cash_flow_after_debt'] + yearly_cashflow_df['valeur_nette_de_sortie']
    yearly_cashflow_df['cumulative_net_cash_flow'] = yearly_cashflow_df['net_cash_flow'].cumsum()
    
    return yearly_cashflow_df


def display_checks(real_estate_df: pd.DataFrame):
    yearly_cashflow_df = build_yearly_cashflow_df(real_estate_df)
    st.title("📈 Checks")
    st.markdown("""
    This page is used to check the financial feasibility of the investment.
    It is a yearly cashflow, with a row for each year of the time horizon and the following columns (sliced in different sections):
    """)
    st.dataframe(yearly_cashflow_df)

st.dataframe(st.session_state['real_estate_df'])
real_estate_df = create_additional_features(st.session_state['real_estate_df'].copy())
st.dataframe(real_estate_df)
display_checks(real_estate_df)