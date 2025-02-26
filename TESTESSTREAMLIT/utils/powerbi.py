import streamlit as st
from utils.database import SessionLocal
from azure.identity import ClientSecretCredential

# Função para autenticação no Azure
@st.cache_resource
def get_power_bi_token(client_id, client_secret, tenant_id):
    credential = ClientSecretCredential(tenant_id, client_id, client_secret)
    token = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
    return token.token