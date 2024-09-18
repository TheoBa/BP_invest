import streamlit as st
import pandas as pd

from utils.computations import PMT, compute_remaining_capital_after_y_years

st.set_page_config(page_title="📈 Checks", page_icon="📈")


def create_additional_features(database_inputs: pd.DataFrame):
    real_estate_df = (
        database_inputs
        .copy()
        .assign(
            # section "input_buying_hypothesis"
            Frais_d_acquisition = lambda x: x["Frais d'acquisition (prct prix d'achat)"] * x["Prix d'achat"],
            Prix_acquisition = lambda x: x["Prix d'achat"] + x["Frais d'acquisition"] + x["Travaux"],
            # section "input_financial_hypothesis"
            LTV = lambda x: (x["Prix Acquisition"] - x["Apport"]) / x["Prix Acquisition"],
            Montant_emprunté = lambda x: x["LTV"] * x["Prix Acquisition"],
            Mensualité = lambda x: PMT(C=x["Montant Emprunté"], n=x["Durée de crédit (année)"]*12, t=x["Taux d'emprunt"]),
            # section "input_market_hypothesis"
            capital_restant_dû = lambda x: - compute_remaining_capital_after_y_years(C=x["Prix Acquisition"], M=x["Mensualité"], t=x["Taux d'emprunt"], y=x["Durée de crédit (année)"]),
            valeur_de_sortie = lambda x: x["Valeur vénale"] * (1+ x["Market Value Growth"]) ** x["Durée de détention (année)"],
            frais_de_vente = lambda x: - x["Frais de vente (taux)"] * x["valeur_de_sortie"],
            valeur_nette_de_sortie = lambda x: x["valeur_de_sortie"] + x["frais_de_vente"] + x["capital_restant_dû"],
            # section "input_annual_revenue"
            Remboursements = lambda x: - x["Mensualité"] * 12,
            # section "input_recurring_charges"
            Frais_d_entretien = lambda x: x["Frais d'entretien (prct prix d'achat)"] * x["Prix d'achat"],
            Assurance_GLI_PNO = lambda x: x["Assurance (GLI, PNO) (prct loyer)"] * x["TOTAL Revenus"],
            # section "input_operating_capex"
            TOTAL_Charges_Récurrantes = lambda x: x["Remboursements"] + x["Gestion locative"] + x["Comptabiltié"] + x["Frais de copropriété"] + x["Taxe foncière"] + x["Frais d'entretien"] + x["Assurance (GLI, PNO)"]
        )
        .rename(columns=lambda x: x.lower().replace(" ", "_").replace("'", "_"))
    )
    return real_estate_df


def build_yearly_cashflow_df(real_estate_df: pd.DataFrame, time_horizon: int = 30):
    """
    This function builds a yearly cashflow dataframe from a real estate dataframe.
    It is used to check the financial feasibility of the investment.
    It is a yearly cashflow, with a row for each year of the time horizon and the following columns (sliced in different sections):
    Index:
    - year: from 0 to time_horizon
    
    Income:
    - rent
    - vacancy
    - unpaied_rent
    - gross_effective_revenues: sum of rent, vacancy and unpaied_rent
    
    Recurring charges: (algebric values so always negative)
    - gestion_locative
    - comptabilité
    - frais_de_copropriété
    - taxe_foncière
    - frais_d_entretien
    - assurance_gli_pno
    - total_charges_récurrantes: sum of gestion_locative, comptabilité, frais_de_copropriété, taxe_foncière, frais_d_entretien, assurance_gli_pno
    
    Net Operating Income:
    - net_operating_income: algebric sum of gross_effective_revenues and total_charges_récurrantes
    
    Non Recurring charges: (algebric values so always negative)
    - apports: only in the first year then 0
    - travaux_non_récurrents: once every "fréquence" years, 0 otherwise
    - total_non_recurring_charges: sum of apports and travaux_non_récurrents
    
    Debt:
    - remboursements: sum of all interest payments for a year (see real_estate_df["Mensualité"])
    - cash_flow_after_debt: algebric sum of net_operating_income, total_non_recurring_charges and remboursements
    - cumulative_cash_flow_after_debt: cumulative sum of cash_flow_after_debt through the years

    Selling hypothesis:
    - valeur_vénale: previous year's valeur_vénale * (1 + real_estate_df["Market Value Growth"]), initialized with real_estate_df["Valeur vénale"]
    - valeur_vénale_à_la_vente: valeur_vénale only in the selling year, 0 otherwise
    - frais_de_vente: valeur_vénale_à_la_vente * real_estate_df["Frais de vente (taux)"]
    - capital_restant_dû: - compute_remaining_capital_after_y_years(C=real_estate_df["Prix Acquisition"], M=real_estate_df["Mensualité"], t=real_estate_df["Taux d'emprunt"], y=year)
    - capital_residuel_à_la_vente: capital_restant_dû only in the selling year, 0 otherwise
    - valeur_nette_de_sortie: algebric sum of valeur_vénale_à_la_vente, frais_de_vente and capital_restant_dû_à_la_vente in the selling year

    Net Cash Flow:
    - net_cash_flow: algebric sum of cash_flow_after_debt and valeur_nette_de_sortie
    - cumulative_net_cash_flow: cumulative sum of net_cash_flow through the years
    """
    yearly_cashflow_df = (
        real_estate_df
        .copy()
        .assign(
            year = lambda x: x.index
        )
    )
    return yearly_cashflow_df
