import streamlit as st
import pandas as pd
import io
from google.cloud import storage
from google.oauth2 import service_account


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