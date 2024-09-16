import streamlit as st
import pandas as pd
from typing import Dict, Any

from utils.computations import PMT

st.set_page_config(page_title="📈 Checks", page_icon="📈")


def create_additional_features(section: str, user_inputs: Dict[str, Any]):
    if section == "input_buying_hypothesis":
        user_inputs["Frais d'acquisition"] = user_inputs["Frais d'acquisition (prct prix d'achat)"] * user_inputs["Prix d'achat"]
        user_inputs["Prix Acquisition"] = user_inputs["Prix d'achat"] + user_inputs["Frais d'acquisition"] + user_inputs["Travaux"]
    elif section == "input_financial_hypothesis":
        user_inputs["LTV"] = (user_inputs["Prix Acquisition"] - user_inputs["Apport"]) / user_inputs["Prix Acquisition"]
        user_inputs["Montant Emprunté"] = user_inputs["LTV"] * user_inputs["Prix Acquisition"]
        user_inputs["Mensualité"] = PMT(C=user_inputs["Montant Emprunté"], n=user_inputs["Durée de crédit (année)"]*12, t=user_inputs["Taux d'emprunt"])
    elif section == "input_market_hypothesis":
        pass
    elif section == "input_annual_revenue":
        user_inputs["TOTAL Revenus"] = user_inputs["Loyer mensuel"] * 12
    elif section == "input_recurring_charges":
        pass
    elif section == "input_operating_capex":
        pass
    elif section == "input_market_sensitivity":
        pass
    return user_inputs