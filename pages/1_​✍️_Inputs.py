import streamlit as st
import pandas as pd
from google.cloud import storage
from google.oauth2 import service_account
import io
import datetime


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


def create_inputs():
    # Create an empty dataframe on first page load, will skip on page reloads
    if 'input_information_actif' not in st.session_state:
        input_information_actif = pd.DataFrame({
            'Adresse': [],
            'Ville': [],
            'Année de construction': [],
            'Surface (m²)': [],
            "Prix d'achat (FAI)": [],
            "Taux frais d'acquisition": [],
            "Date d'acquisition": [],
            "Revenus locatif mensuels": [],
            "Taxe foncière annuelle": [],
            "Charge copro annuelle": [],
            "Petit entretien et travaux (/m²)": [],
            "Taxe ordures (/m²)": []
            })
        st.session_state.input_information_actif = input_information_actif
    if 'input_financial_hypothesis' not in st.session_state:
        input_financial_hypothesis = pd.DataFrame({
            "LTV": [],
            "Durée d'emprunt": [],
            "Amortissement": [],
            "Management fee": [],
            "Indexation des dépenses": [],
            "Frais d'agence à la revente": [],
            "Valeur vénale (/m²)": [],
            "Durée de détention (en années)": [],
            "Prélèvement BIC": []
            })
        st.session_state.input_financial_hypothesis = input_financial_hypothesis
    
    # Show referenced data
    st.markdown(
        """
            ### Données référencées
            Veillez bien à ce que les informations soient correctes avant d'uploader ce bien dans la base de données
        """
        )
    col1, col2 = st.columns(2)
    with col1:
        df = st.session_state.input_information_actif.rename(index={0: "Information actif"}).T
        st.dataframe(df)
    with col2:
        df = st.session_state.input_financial_hypothesis.rename(index={0: "Hypothèses financières"}).T
        st.dataframe(df)


def query_information_actif():
    with st.form("information_actif_form"):
        address = st.text_input("Adresse")
        city = st.text_input("Ville")
        year = st.number_input("Année de construction")
        surface = st.number_input("Surface (m²)")
        price = st.number_input("Prix d'achat (FAI)")
        fees = st.number_input("Taux frais d'acquisition")
        acquisition_date = st.date_input("Date d'acquisition")
        rent = st.number_input("Revenus locatif mensuels")
        tax = st.number_input("Taxe foncière annuelle")
        charges = st.number_input("Charge copro annuelle")
        maintenance = st.number_input("Petit entretien et travaux annuels (/m²)")
        garbage = st.number_input("Taxe ordures annuelle (/m²)")
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state.input_information_actif = pd.DataFrame({
            'Adresse': [address],
            'Ville': [city],
            'Année de construction': [year],
            'Surface (m²)': [surface],
            "Prix d'achat (FAI)": [price],
            "Taux frais d'acquisition": [fees],
            "Date d'acquisition": [acquisition_date],
            "Revenus locatif mensuels": [rent],
            "Taxe foncière annuelle": [tax],
            "Charge copro annuelle": [charges],
            "Petit entretien et travaux (/m²)": [maintenance],
            "Taxe ordures (/m²)": [garbage],
            })


def query_hypothesis():
    with st.form("hypothesis_form"):
        ltv = st.number_input("LTV")
        applications_fees = st.number_input("Frais de dossier")
        loan = st.number_input("Durée d'emprunt")
        amortissement = st.number_input("Amortissement")
        interest_rate = st.number_input("Taux d'intérêt (TAEG)")
        fee = st.number_input("Management fee")
        spend = st.number_input("Indexation des dépenses")
        resell = st.number_input("Frais d'agence à la revente")
        venal = st.number_input("Valeur vénale (/m²)")
        detention = st.number_input("Durée de détention (en années)")
        bic = st.number_input("Prélèvement BIC")

        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state.input_financial_hypothesis = pd.DataFrame({
            "LTV": [ltv],
            "applications_fees": [applications_fees],
            "Durée d'emprunt": [loan],
            "Amortissement": [amortissement],
            "Taux d'intérêt (TAEG)": [interest_rate],
            "Management fee": [fee],
            "Indexation des dépenses": [spend],
            "Frais d'agence à la revente": [resell],
            "Valeur vénale (/m²)": [venal],
            "Durée de détention (en années)": [detention],
            "Prélèvement BIC": [bic]
            })
    return


def input_tabs():
    tab_informations, tab_hypothesis, tab_save_real_estate = st.tabs(['Informations relatif au bien','Hypothèses financières', "Sauvegarder le bien"])
    with tab_informations:
        query_information_actif()
    with tab_hypothesis:
        query_hypothesis()
    with tab_save_real_estate:
        st.markdown("Si le check ci-dessus est satisfaisant, vous pouvez uploader les info du bien dans le cloud ☁️")
        real_estate_id = st.text_input("Id du bien (id à partir duquel on y fera référence)")
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


create_inputs()
input_tabs()