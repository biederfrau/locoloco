import pandas as pd
from geodistance import Geodistance
import sys

def compute_km(row):
    return Geodistance().distance(row['lat_von'], row['lon_von'], row['lat_nach'], row['lon_nach'])

class Preprocessor: 
    def __init__(self, data_path, bp_path):
        self.data = self.init_data(data_path)
        self.data['year'] = self.data['Hinreisedatum'].dt.year
        self.data['id'] = self.data.index

    def init_data(self, path):
        data = pd.read_parquet(path).dropna(subset='Hinreisedatum')
        bp = pd.read_csv(bp_path)

        return data.merge(
            bp[['offizielle_bezeichnung', 'e_wgs84','n_wgs84']],
            left_on='Reise von',
            right_on='offizielle_bezeichnung'
        ).merge(
            bp[['offizielle_bezeichnung', 'e_wgs84','n_wgs84']],
            left_on='Reise nach',
            right_on='offizielle_bezeichnung'
        ).rename(
            columns={
                'e_wgs84_x': 'lon_von',
                'n_wgs84_x': 'lat_von',
                'e_wgs84_y': 'lon_nach',
                'n_wgs84_y': 'lat_nach',
            }
        )
    
    def compute_km(self, ):
        self.data['km'] = self.data.apply(compute_km, axis=1)
    
    def compute_co2(self):
        self.data['co2_bahn'] = 0.02*self.data['km']
        self.data['co2_auto'] = 0.18*self.data['km']

    

if __name__ == "__main__":
    data_path = './data/anonymized_sap_data.parquet'
    bp_path = './data/BP.csv'

    singleton = Preprocessor(data_path, bp_path)
    Preprocessor.compute_km(singleton)
    Preprocessor.compute_co2(singleton)

    singleton.data.rename(columns={
        'Geschäftspartner' : 'business_id'
    })[['business_id', 'year', 'lat_von', 'lon_von', 'lat_nach', 'lon_nach', 'km', 'co2_bahn', 'co2_auto']] \
        .to_csv('data/export_co2_km.csv', index=False)