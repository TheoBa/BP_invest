import streamlit as st
import pandas as pd

from utils.computations import PMT

st.set_page_config(page_title="📈 Checks", page_icon="📈")


def create_additional_features(database_inputs: pd.DataFrame):
    df = (
        database_inputs
        .assign(
            # section == "input_buying_hypothesis"
            Frais_d_acquisition = lambda x: x["Frais d'acquisition (prct prix d'achat)"] * x["Prix d'achat"],
            Prix_acquisition = lambda x: x["Prix d'achat"] + x["Frais d'acquisition"] + x["Travaux"],
            # section == "input_financial_hypothesis"
            LTV = lambda x: (x["Prix Acquisition"] - x["Apport"]) / x["Prix Acquisition"],
            Montant_emprunté = lambda x: x["LTV"] * x["Prix Acquisition"],
            Mensualité = lambda x: PMT(C=x["Montant Emprunté"], n=x["Durée de crédit (année)"]*12, t=x["Taux d'emprunt"]),
            # section == "input_market_hypothesis"
            # TODO
            # section == "input_annual_revenue"
            Remboursements = lambda x: - x["Mensualité"] * 12,
            # section == "input_recurring_charges"
            Frais_d_entretien = lambda x: x["Frais d'entretien (prct prix d'achat)"] * x["Prix d'achat"],
            Assurance_GLI_PNO = lambda x: x["Assurance (GLI, PNO) (prct loyer)"] * x["TOTAL Revenus"],
            # section == "input_operating_capex"
            TOTAL_Charges_Récurrantes = lambda x: x["Remboursements"] + x["Gestion locative"] + x["Comptabiltié"] + x["Frais de copropriété"] + x["Taxe foncière"] + x["Frais d'entretien"] + x["Assurance (GLI, PNO)"]
        )
    )
    return df

