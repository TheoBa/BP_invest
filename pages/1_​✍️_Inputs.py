import streamlit as st
import pandas as pd
import datetime
from utils.inputs import REAL_ESTATE_INPUTS
from utils.gcp_connector import download_dataframe, upload_dataframe
from typing import Dict, Any


st.set_page_config(page_title="✍️ Inputs", page_icon="✍️", layout="wide")


def init_input(INPUT):
    return pd.DataFrame(
        {
            key: []
        } for key in INPUT
    )


def initialize_inputs():
    for key, value in REAL_ESTATE_INPUTS.items():
        session_key = f'_{key}'
        if session_key not in st.session_state:
            st.session_state[session_key] = init_input(value)


def display_inputs():
    # Show referenced data
    st.markdown(
        """
            ### Données référencées
            Veillez bien à ce que les informations soient correctes avant d'uploader ce bien dans la base de données
        """
    )
    with st.expander("Inputs", expanded=False):
        
        
        def display_dataframe(session_key, display_name):
            df = st.session_state[session_key].rename(index={0: display_name}).T
            st.dataframe(df)

        col1, col2 = st.columns(2)
        
        with col1:
            display_dataframe("_input_information_actif", "Information actif")
            display_dataframe("_input_buying_hypothesis", "Hypothèse Achat")
            display_dataframe("_input_financial_hypothesis", "Financement")
            display_dataframe("_input_market_hypothesis", "Hypothèses Marché")
        
        with col2:
            display_dataframe("_input_annual_revenue", "Revenus Annuels")
            display_dataframe("_input_recurring_charges", "Charges Récurrentes")
            display_dataframe("_input_operating_capex", "Operating CAPEX Travaux")
            display_dataframe("_input_market_sensitivity", "Sensibilité Marché")


def create_real_estate_input_forms(inputs: Dict[str, Dict[str, str]]) -> pd.DataFrame:
    
    def display_input_form(section, fields):
        st.subheader(section.replace("input_", "").replace("_", " ").title())
        for field, input_properties in fields.items():
            input_type = input_properties[0]
            init_value = input_properties[1]
            if input_type == 'text':
                user_inputs[field] = st.text_input(field, value=init_value)
            elif input_type in ['percentage', 'rate']:
                user_inputs[field] = st.number_input(field, value=init_value) / 100
            elif input_type in ['int', 'euros', 'year']:
                user_inputs[field] = st.number_input(field, value=init_value)

    user_inputs = {}
    with st.expander("", expanded=True):
        buffer1, col_0, col_1, buffer2 = st.columns([1, 2, 2, 1])
        for i, (section, fields) in enumerate(inputs.items()):
            if i % 2 == 0:
                with col_0:
                    display_input_form(section, fields)
            else:
                with col_1:
                    display_input_form(section, fields)
        footer_cols = st.columns([5,1])
        with footer_cols[1]:
            submitted = st.button('Submit', type='primary', key='submit_btn')
        # Update the session state with the new DataFrame
        if submitted:
            for section, fields in inputs.items():
                st.session_state[f"_{section}"] = pd.DataFrame([user_inputs])[list(fields.keys())]

    # Create a DataFrame with a single row
    df = pd.DataFrame([user_inputs])    
    return df


def save_real_estate():
    st.markdown("Si le check ci-dessus est satisfaisant, vous pouvez uploader les info du bien dans le cloud ☁️")
    real_estate_id = st.text_input("Id du bien (Default: Adresse)", value="Default")
    today = datetime.date.today()
    footer_cols = st.columns([5,1])
    agreed = footer_cols[0].checkbox("J'ai vérifié que les données saisies sont correctes")
    with footer_cols[1]:
        upload_btn = st.button("Upload real estate data", type='primary', key='upload_btn', disabled=not agreed)
    if upload_btn:
        df0 = download_dataframe("02data.csv")
        
        real_estate_df = st.session_state['real_estate_df'].copy()
        real_estate_df['timestamp'] = today
        real_estate_df['real_estate_id'] = real_estate_id if real_estate_id != "Default" else real_estate_df.iloc[0]['adresse']
        df_updated = pd.concat([df0, real_estate_df], ignore_index=True)

        upload_dataframe(df_updated, "02data.csv")
        st.markdown("Sauvegarde réussie !")


def input_tabs():
    tab_informations, tab_save_real_estate = st.tabs(['Informations relatif au bien', "Sauvegarder le bien"])
    with tab_informations:
        df = create_real_estate_input_forms(REAL_ESTATE_INPUTS)
        st.session_state['real_estate_df'] = df
        display_inputs()
    with tab_save_real_estate:
        save_real_estate()


initialize_inputs()
input_tabs()
