import streamlit as st
import pandas as pd
from google.cloud import storage
from google.oauth2 import service_account
import io


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
    
    # Show current data
    st.markdown(
        """
            ### Données référencées
            Veillez bien à ce que les informations soient correctes avant d'uploader ce bien dans la base de données
        """
        )
    df = st.session_state.input_information_actif.rename(index={0: "Information actif"}).T
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
        ltv = st.text_input("LTV")
        loan = st.text_input("Durée d'emprunt")
        amortissement = st.number_input("Amortissement")
        fee = st.number_input("Management fee")
        spend = st.number_input("Indexation des dépenses")
        resell = st.number_input("Frais d'agence à la revente")
        venal = st.date_input("Valeur vénale (/m²)")
        detention = st.number_input("Durée de détention")
        bic = st.number_input("Prélèvement BIC")

        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state.input_information_actif = pd.DataFrame({
            "LTV": [ltv],
            "Durée d'emprunt": [loan],
            "Amortissement": [amortissement],
            "Management fee": [fee],
            "Indexation des dépenses": [spend],
            "Frais d'agence à la revente": [resell],
            "Valeur vénale (/m²)": [venal],
            "Durée de détention": [detention],
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
        if st.button("dl csv"):
            df = download_dataframe("01data.csv")
            st.dataframe(df)
        st.markdown("Si le check ci-dessus est satisfaisant, vous pouvez uploader les info du bien dans le cloud ☁️")
        st.dataframe(st.session_state.input_information_actif)
        if st.button("Update worksheet"):
            upload_dataframe(st.session_state.input_information_actif, "02data.csv")
            st.markdown("Bien sauvegardé !")
        if st.button("dl updated csv"):
            df = download_dataframe("02data.csv")
            st.dataframe(df)


create_inputs()
input_tabs()