REAL_ESTATE_INPUTS = {
    "input_information_actif" : {
        'adresse': ['text', "6 Boulevard Pasteur"],
        'ville': ['text', "Dreux"],
        'dpe': ['text', "E"],
        'surface_(m²)': ['int', 55.77]
    },
  
    "input_buying_hypothesis" : {
        "valeur_vénale": ['euros', 109466],
        "prix_d_achat": ['euros', 93000],
        "frais_d_acquisition_(prct_prix_d_achat)": ['rate', 8],
        "travaux": ['euros', 0]
    },

    "input_financial_hypothesis" : {
        "apport": ['euros', 9300],
        "taux_d_emprunt": ['percentage', 2.72],
        "durée_de_crédit_(année)": ['year', 25]
    },

    "input_market_hypothesis" : {
        "durée_de_détention_(année)": ['year', 15],
        "frais_de_vente_(taux)": ['rate', 3.5],
        "taux_d_actualisation": ['percentage', 5]
    },

    "input_operating_capex" : {
        "travaux_non_récurrent": ['euros', 2000],
        "fréquence": ['year', 3]
    },

    "input_annual_revenue" : {
        "loyer_mensuel": ['euros', 721]
    },

    "input_market_sensitivity" : {
        "market_value_growth": ['percentage', 1],
        "market_rent_growth": ['percentage', 2],
        "property_tax_growth": ['percentage', 1],
        "vacancy": ['percentage', 2],
        "loyers_impayés": ['percentage', 0]
    },

    "input_recurring_charges" : {
        "gestion_locative": ['euros', 0],
        "comptabilité": ['euros', 0],
        "frais_de_copropriété": ['euros', 1400],
        "taxe_foncière": ['euros', 700],
        "frais_d_entretien_(prct_prix_d_achat)": ['rate', 1],
        "assurance_(gli,_pno)_(prct_loyer)": ['rate', 5]
    }
}