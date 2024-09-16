import streamlit as st
import pandas as pd
from google.cloud import storage
from google.oauth2 import service_account
import io
import datetime
from utils.inputs import REAL_ESTATE_INPUTS
from typing import Dict, Any


st.set_page_config(page_title="✍️ Inputs", page_icon="✍️")
service_account_info = {
    "type": st.secrets["connections"]["gcs"]["type"],
    "project_id": st.secrets["connections"]["gcs"]["project_id"],
    "private_key_id": st.secrets["connections"]["gcs"]["private_key_id"],
    "private_key": st.secrets["connections"]["gcs"]["private_key"].replace('\\n', '\n'),
    "client_email": st.secrets["connections"]["gcs"]["client_email"],
    "client_id": st.secrets["connections"]["gcs"]["client_id"],
    "auth_uri": st.secrets["connections"]["gcs"]["auth_uri"],
    "token_uri": st.secrets["connections"]["gcs"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["connections"]["gcs"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["connections"]["gcs"]["client_x509_cert_url"],
    "universe_domain": st.secrets["connections"]["gcs"]["universe_domain"]
}

# Create credentials and client
credentials = service_account.Credentials.from_service_account_info(service_account_info)
client = storage.Client(credentials=credentials)
bucket_name = st.secrets["connections"]["gcs"]["gcp_bucket_name"]
bucket = client.bucket(bucket_name)


def download_dataframe(filename):
    blob = bucket.blob(filename)
    content = blob.download_as_text()
    return pd.read_csv(io.StringIO(content))


def upload_dataframe(df, filename):
    csv_buffer = io.BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    blob = bucket.blob(filename)
    blob.upload_from_file(csv_buffer, content_type='text/csv')


def init_input(INPUT):
    return pd.DataFrame(
        {
            key: []
        } for key in INPUT
    )


def create_inputs():
    # Create an empty dataframe on first page load, will skip on page reloads
    if '_input_information_actif' not in st.session_state:
        input_information_actif = init_input(REAL_ESTATE_INPUTS["input_information_actif"])
        st.session_state._input_information_actif = input_information_actif

    if '_input_buying_hypothesis' not in st.session_state:
        input_buying_hypothesis = init_input(REAL_ESTATE_INPUTS["input_buying_hypothesis"])
        st.session_state._input_buying_hypothesis = input_buying_hypothesis

    if '_input_financial_hypothesis' not in st.session_state:
        input_financial_hypothesis = init_input(REAL_ESTATE_INPUTS["input_financial_hypothesis"])
        st.session_state._input_financial_hypothesis = input_financial_hypothesis

    if '_input_market_hypothesis' not in st.session_state:
        input_market_hypothesis = init_input(REAL_ESTATE_INPUTS["input_market_hypothesis"])
        st.session_state._input_market_hypothesis = input_market_hypothesis

    if '_input_annual_revenue' not in st.session_state:
        input_annual_revenue = init_input(REAL_ESTATE_INPUTS["input_annual_revenue"])
        st.session_state._input_annual_revenue = input_annual_revenue

    if '_input_recurring_charges' not in st.session_state:
        input_recurring_charges = init_input(REAL_ESTATE_INPUTS["input_recurring_charges"])
        st.session_state._input_recurring_charges = input_recurring_charges

    if '_input_operating_capex' not in st.session_state:
        input_operating_capex = init_input(REAL_ESTATE_INPUTS["input_operating_capex"])
        st.session_state._input_operating_capex = input_operating_capex

    if '_input_market_sensitivity' not in st.session_state:
        input_market_sensitivity = init_input(REAL_ESTATE_INPUTS["input_market_sensitivity"])
        st.session_state._input_market_sensitivity = input_market_sensitivity
    

def display_inputs():
    # Show referenced data
    st.markdown(
        """
            ### Données référencées
            Veillez bien à ce que les informations soient correctes avant d'uploader ce bien dans la base de données
        """
        )
    col1, col2 = st.columns(2)
    with col1:
        df = st.session_state._input_information_actif.rename(index={0: "Information actif"}).T
        st.dataframe(df)
        df = st.session_state._input_buying_hypothesis.rename(index={0: "Hypothèse Achat"}).T
        st.dataframe(df)
        df = st.session_state._input_financial_hypothesis.rename(index={0: "Financement"}).T
        st.dataframe(df)
        df = st.session_state._input_market_hypothesis.rename(index={0: "Hypothèses Marché"}).T
        st.dataframe(df)
    with col2:
        df = st.session_state._input_annual_revenue.rename(index={0: "Revenus Annuels"}).T
        st.dataframe(df)
        df = st.session_state._input_recurring_charges.rename(index={0: "Charges Récurrentes"}).T
        st.dataframe(df)
        df = st.session_state._input_operating_capex.rename(index={0: "Operating CAPEX Travaux"}).T
        st.dataframe(df)
        df = st.session_state._input_market_sensitivity.rename(index={0: "Sensibilité Marché"}).T
        st.dataframe(df)


def create_real_estate_input_forms(inputs: Dict[str, Dict[str, str]]) -> pd.DataFrame:
    user_inputs = {}

    with st.form("my_form"):
        for section, fields in inputs.items():
            st.subheader(section.replace("input_", "").replace("_", " ").title())
            for field, input_type in fields.items():
                if input_type == 'text':
                    user_inputs[field] = st.text_input(field)
                elif input_type in ['int', 'euros', 'rate', 'percentage', 'year']:
                    user_inputs[field] = st.number_input(field, value=0.0)
        submitted = st.form_submit_button("Submit")
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
        if st.button("Upload real estate data"):
            df0 = download_dataframe("02data.csv")
            df1 = st.session_state.input_financial_hypothesis
            df2 = st.session_state.input_information_actif
            
            real_estate_df = pd.concat([df1, df2], axis=1)
            real_estate_df['timestamp'] = today
            real_estate_df['real_estate_id'] = real_estate_id
            df_updated = pd.concat([df0, real_estate_df], ignore_index=True)

            upload_dataframe(df_updated, "02data.csv")
            st.markdown("Sauvegarde réussie !")

        if st.button("dl updated csv"):
            df = download_dataframe("02data.csv")
            st.dataframe(df)


def input_tabs():
    tab_informations, tab_save_real_estate = st.tabs(['Informations relatif au bien', "Sauvegarder le bien"])
    with tab_informations:
        create_real_estate_input_forms(REAL_ESTATE_INPUTS)
    with tab_save_real_estate:
        save_real_estate()


create_inputs()
display_inputs()
input_tabs()