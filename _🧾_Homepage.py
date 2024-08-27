import streamlit as st


st.set_page_config(
    page_title='Homepage', 
    page_icon='💸', 
    layout="wide", 
    initial_sidebar_state="collapsed"
    )

def welcome_page():
    st.markdown(
    """
    # BP-caussa
    BP-caussa est un projet de comparaison de rentabilité d'immobilier 
    \n
    **👈 Navigue au travers des pages dans la sidebar** pour devenir riche
    \n
    ## Want to learn more?
    #### **✍️ Inputs**
    Ajouter des inputs relatifs à un bien immo
    #### **📈 Checks**
    Checker les KPIs relatifs au différents biens référencés
    #### **📊 Comparaison**
    Comparer différents biens entre eux
    """
    )




if __name__=="__main__":
    welcome_page()
