REAL_ESTATE_INPUTS = {
    "input_information_actif" : {
        'Adresse': 'text',
        'Ville': 'text',
        'DPE': 'text',
        'Surface (m²)': 'int'
    },
  
    "input_buying_hypothesis" : {
        "Prix d'achat (FAI)": 'euros',
        "Taux frais d'acquisition": 'rate',
        "Travaux": 'euros'
    },

    "input_financial_hypothesis" : {
        "Apport": 'euros',
        "Taux d'emprunt": 'percentage',
        "Durée de crédit (année)": 'year'
    },

    "input_market_hypothesis" : {
        "Durée de détention (année)": 'year',
        "Frais de vente (taux)": 'rate',
        "Taux d'actualisation": 'percentage'
    },

    "input_annual_revenue" : {
        "Loyer mensuel": 'euros'
    },

    "input_recurring_charges" : {
        "Gestion locative": 'euros',
        "Comptabiltié": 'euros',
        "Frais de copropriété": 'euros',
        "Taxe foncière": 'euros',
        "Frais d'entretien (prct prix d'achat)": 'rate',
        "Assurance (GLI, PNO) (prct loyer)": 'rate'
    },

    "input_operating_capex" : {
        "Travaux non récurrent": 'euros',
        "Fréquence": 'year'
    },

    "input_market_sensitivity" : {
        "Market Value Growth": 'percentage',
        "Market Rent Growth": 'percentage',
        "Property Tax Growth": 'percentage',
        "Vacancy": 'percentage',
        "Loyers Impayés": 'percentage'
    }
}