import pandas as pd
from geodistance import Geodistance
import sys

def compute_km(row):
    return Geodistance().distance(row['lat_from'], row['lon_from'], row['lat_to'], row['lon_to'])


def add_costs_per_km(row):
    return row['km'] * 0.65

class Preprocessor: 
    def __init__(self, data_path, bp_path):
        self.data = self.init_data(data_path)
        self.data['year'] = self.data['Hinreisedatum'].dt.year
        self.data['id'] = self.data.index
        self.compute_km()
        self.compute_co2()
        self.add_cw()
        self.add_costs_per_km()
        self.add_work_time_gained()
        self.data = self.data.rename(columns={
            'Geschäftspartner' : 'business_id'
        })[['business_id', 'year', 'lat_from', 'lon_from', 'lat_to', 'lon_to', 'km', 'co2_train', 'co2_car', 'cw', 'costs_per_km_car', 'costs_per_km_train', 'work_time_gained']]
        self.aggregate().to_csv('data/export_co2_km_aggregated.csv', index=False)

    def init_data(self, path):
        data = pd.read_parquet(path).dropna(subset=['Hinreisedatum', 'Geschäftspartner'])
        data['Geschäftspartner'] = data['Geschäftspartner'].astype(int)
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
                'e_wgs84_x': 'lon_from',
                'n_wgs84_x': 'lat_from',
                'e_wgs84_y': 'lon_to',
                'n_wgs84_y': 'lat_to',
            }
        )
    
    def compute_km(self, ):
        self.data['km'] = self.data.apply(compute_km, axis=1)
    
    def compute_co2(self):
        self.data['co2_train'] = 0.02*self.data['km']
        self.data['co2_car'] = 0.18*self.data['km']

    def add_cw(self):
        self.data['cw'] = self.data['Hinreisedatum'].dt.isocalendar().week
    
    def add_costs_per_km(self):
        self.data['costs_per_km_car'] = self.data['km'] * 0.65
        self.data['costs_per_km_train'] = self.data['km'] * 0.15
    
    def add_work_time_gained(self):
        self.data['work_time_gained'] = self.data['km'] / 100 - 0.5

    def aggregate(self):
        return self.data.groupby(['cw', 'business_id', 'year']).sum()
    
if __name__ == "__main__":
    data_path = './data/anonymized_sap_data.parquet'
    bp_path = './data/BP.csv'

    singleton = Preprocessor(data_path, bp_path)