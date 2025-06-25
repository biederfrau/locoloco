import os.path
import matplotlib
import matplotlib.pyplot as plt
import pandas
import geopandas
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
import pyarrow as pa
import cartopy.io.img_tiles as cimgt
from shapely.geometry import Point
import pyproj
import cartopy.crs as ccrs
import folium
from pyproj import Geod
import branca.colormap as cm


def write_parquet(df, pq_file):
    table = pa.Table.from_pandas(df)
    pq.write_table(table, pq_file)


def get_energie_equiv(km, artikel):  # Energie MJ-equiv./pkm
    if artikel == "Tickets Inland":
        nrj = km * 0.5
    elif artikel == "GA":
        nrj = km * 0.5
    elif artikel == "Tickets Ausland":
        nrj = km * 0.75
    elif artikel == "Ausschluss":
        nrj = km * 0.5
    elif artikel == "Erstattung":
        nrj = km * 0.5
    elif artikel == "Tickets Verkehrsverbund":
        nrj = km * 0.73
    elif pandas.isnull(artikel):
        nrj = km * 0.5
    else:
        nrj = None
    return nrj


def get_co2_equiv(km, artikel):   # CO2-equiv. kg/pkm
    if artikel == "Tickets Inland":
        co2 = km * 7.02 / 1000
    elif artikel == "GA":
        co2 = km * 7.02 / 1000
    elif artikel == "Tickets Ausland":
        co2 = km * 40.82 / 1000
    elif artikel == "Ausschluss":
        co2 = km * 7.02 / 1000
    elif artikel == "Erstattung":
        co2 = km * 7.02 / 1000
    elif artikel == "Tickets Verkehrsverbund":
        co2 = km * 8.04 / 1000
    elif pandas.isnull(artikel):
        co2 = km * 7.02 / 1000
    else:
        co2 = None
    return co2


def get_kilometer(betrag, klasse, ermassigung):
    klasse = int(klasse)
    if betrag < 0:
        km = betrag / 0.3
    elif klasse == 0 and pandas.isnull(ermassigung):
        km = 0
    elif klasse == 0 and ermassigung == "KEINE":
        km = 0
    elif klasse == 2 and ermassigung == "GA1KL":
        km = betrag / 0.2
    elif klasse == 1 and ermassigung == "GA1KL":
        km = betrag / 0.36
    elif klasse == 1 and ermassigung == "GA2KL":
        km = betrag / 0.36
    elif klasse == 0 and ermassigung == "HTA123":
        km = 0
    elif klasse == 1 and ermassigung == "HTA123":
        km = betrag / 0.36
    elif klasse == 2 and ermassigung == "HTA123":
        km = betrag / 0.2
    elif klasse == 1 and ermassigung == "KEINE":
        km = betrag / 0.287
    elif klasse == 1 and pandas.isnull(ermassigung):
         km = betrag / 0.287
    elif klasse == 2 and pandas.isnull(ermassigung):
        km = betrag / 0.239
    elif klasse == 2 and ermassigung == "KEINE":
        km = betrag / 0.239
    else:
        km = betrag
    return km


# ÖV = Öffentlicher Verkehr
# MIV = Motorisierter Individualverkehr
def get_co2_saved(km, co2_equiv):  # Einsparung CO2-equiv. kg/pkm ÖV vs. MIV
    return km * 118.64 / 1000 - co2_equiv


def get_energie_saved(km, nrj_equiv):  # Einsparung Energie MJ-equiv./pkm ÖV vs. MIV
    return km * 2.73 - nrj_equiv


def get_artikel(df_artikel, produktbezeichnung):
    mask = df_artikel.loc[:, "Artikelname"] == produktbezeichnung
    if mask.sum() == 1:
        artikel = df_artikel.loc[mask, "RUMBA-Artikel"].values[0]
    else:
        artikel = 'Tickets Verkehrsverbund'  # worst case
    return artikel


def main():
    data_dir = Path("..", "Data")

    pq_file = Path(data_dir, "dienststellen-gemass-opentransportdataswiss.parquet")

    df_geo = geopandas.read_parquet(pq_file, columns=["designationofficial", "geopos"])

    pq_file = Path(data_dir, "data_with_co2.parquet")

    if os.path.isfile(pq_file):
        df = pandas.read_parquet(pq_file)
    else:
        # file1 = Path(data_dir, "Anonymised SAP B2B Data.xlsx")
        file1 = Path(data_dir, "anonymized_sap_data.parquet")
        print(file1)

        # df = pandas.read_excel(file1, engine='openpyxl')
        dtypes = {"Reiseklasse": str,
                  "Geschäftspartner": str,
                  "Vertragskonto": str,
                  "NOVA Produktnummer": str,
                  "NOVA Service ID": str}
        df = pandas.read_parquet(file1).astype(dtypes)
        df = df.dropna()   # for ex. there are 159 lines without "Vertragskonto"
        df.loc[:, "Käufer"] = df.apply(lambda o: o["Vorname des Käufers"] + ' ' + o["Nachname des Käufers"], axis=1)
        df.loc[:, "Reisenden"] = df.apply(lambda o: o["Vorname des Reisenden"] + ' ' + o["Nachname des Reisenden"], axis=1)
        cols2drop = ["Geschäftsfall ID", "NOVA Produktnummer", "Vorname des Käufers", "Nachname des Käufers",
                     "Vorname des Reisenden", "Nachname des Reisenden",
                     "Personalnummer", "WebShop Benutzer Name"]
        df.drop(columns=cols2drop, inplace=True)
        # Geschäftspartner, Vertragskonto: 1:1 Beziehung
        # Reduktion: 1 Käufer may have various values. for ex. KEINE, HTA123, GA2KL
        # Käufer, Personalnummer: 1:1 Beziehung
        # Vertragskonto, Käufer: 1:n Beziehung

        print("============================")

        file2 = Path(data_dir, "Basic Emissions Report.xlsx")
        df_artikel = pandas.read_excel(file2, engine='openpyxl', sheet_name="Artikel Prüfung")
        print(df_artikel.head())

        print("km")
        df.loc[:, "km"] = df.apply(lambda o: get_kilometer(o['Betrag'], o['Reiseklasse'], o['Reduktion']), axis=1)
        print("artikel")
        df.loc[:, "artikel"] = df.loc[:, "NOVA Produktbezeichnung"].apply(lambda x: get_artikel(df_artikel, x))
        print("co2_equiv")
        df.loc[:, "co2_equiv"] = df.apply(lambda o: get_co2_equiv(o["km"], o["artikel"]), axis=1)
        print("co2_saved")
        df.loc[:, "co2_saved"] = df.apply(lambda o: get_co2_saved(o["km"], o["co2_equiv"]), axis=1)

        df.loc[:, "yyyy-mm"] = df.loc[:, "Hinreisedatum"].apply(lambda v: v.strftime('%Y-%m'))
        df.loc[:, "yyyy-kw"] = df.loc[:, "Hinreisedatum"].apply(lambda v: v.strftime('%Y - CW%V'))

        write_parquet(df, pq_file)
    # print(df.head())

    print('Vertragskonto: sum km')
    print(df.groupby(['Vertragskonto'])['km'].sum().sort_values(ascending=False).head())
    print('Vertragskonto: sum co2-equiv')
    print(df.groupby(['Vertragskonto'])['co2_equiv'].sum().sort_values(ascending=False).head())

    #

    # -----------------------------------------------------------------------------------------------------------
    # Here and below, consider only 1 company

    vertragskonto = "9209577.0"
    # vertragskonto = "8469347.0"
    # vertragskonto = "6275091.0"
    # vertragskonto = "6947275.0"

    mask_vertrag = df.loc[:, 'Vertragskonto'] == vertragskonto

    print(df.loc[mask_vertrag, :])

    print("datum:", df.loc[mask_vertrag, "Hinreisedatum"].min().date(), df.loc[mask_vertrag, "Hinreisedatum"].max().date())

    co2_saved_ = df.loc[mask_vertrag, :].groupby(["yyyy-kw"])["co2_saved"].sum()
    #
    plt.figure(figsize=(15, 6))
    plt.title(vertragskonto[:-2])
    plt.plot(co2_saved_.index, np.cumsum(co2_saved_.values), 'g-s', lw=2)
    plt.ylabel('cumulated saved CO2-equiv. kg/pkm (Train vs. Auto)')
    plt.xticks(rotation=40)

    # plt.show()

    co2_saved_employees = df.loc[mask_vertrag, :].groupby(["Reisenden"])["co2_saved"].sum()
    print(co2_saved_employees)
    plt.figure(figsize=(15, 6))
    plt.title(vertragskonto[:-2])
    plt.hist(co2_saved_employees.values, bins=20, rwidth=0.8)
    plt.xlabel('cumulated saved CO2-equiv. kg/pkm (Train vs. Auto)')
    plt.ylabel('number of employees')
    xmax = max(co2_saved_employees.values)*1.1
    plt.xlim([0, xmax])

    plt.show()

    df.loc[:, 'von'] = df.apply(lambda o: sort_ort(o["Reise von"], o["Reise nach"], order='first'), axis=1)
    df.loc[:, 'nach'] = df.apply(lambda o: sort_ort(o["Reise von"], o["Reise nach"], order='second'), axis=1)

    lines = []
    geod = Geod("+ellps=WGS84")
    # c = 0
    counts = []

    roads = df.loc[mask_vertrag, :].groupby(['von', 'nach']).size().sort_values(ascending=True)

    for road in roads.index:
        ort_von = road[0]
        ort_nach = road[1]
        count = roads[road]
        print(ort_von, '--->', ort_nach, ':', count)

        mask_von = df_geo.loc[:, "designationofficial"] == ort_von
        mask_nach = df_geo.loc[:, "designationofficial"] == ort_nach

        point_von = df_geo.loc[mask_von, "geopos"].values[0] if mask_von.sum() == 1 else None
        point_nach = df_geo.loc[mask_nach, "geopos"].values[0] if mask_nach.sum() == 1 else None
        if point_von and point_nach:
            counts.append(count)
            lines.append([count, geod.npts(lon1=point_von.y, lat1=point_von.x, lon2=point_nach.y, lat2=point_nach.x, npts=20)])

        #    c += 1
        #if c == 100:
        #    break

    lines = sorted(lines, key=lambda x: x[0])  # should not be needed

    # count_max = max(counts)
    count_min = max(10, int(np.percentile(counts, 5)))
    count_max = int(np.percentile(counts, 99.8))
    max_counts = max(counts)
    print(count_min, count_max, max_counts)

    plt.figure(figsize=(15, 6))
    plt.title("Trevel line frequency")
    plt.hist(counts, bins=np.arange(0, 10*int(max_counts/10)+10, 10), rwidth=0.8)
    plt.xlabel('number of travel lines')
    plt.ylabel('Frequency')
    plt.show()

    colormap = cm.LinearColormap(
        colors=['#FFF2AA', '#FF9C00'],  #' '#FFC004'],
        vmin=count_min, vmax=count_max  # adjust range to your data
    )
    weight_min, weight_max = 0.5, 6
    m = folium.Map(location=[45.5236, -122.6750], zoom_start=13)
    for count, points in lines:
        f = count if count_min < count < count_max else count_min if count < count_min else count_max
        color = colormap(f)
        weight = (weight_max-weight_min)*((count-count_min)/(count_max-count_min))+weight_min if count_min < count < count_max else weight_min if count < count_min else weight_max
        # print(color, weight)
        line = folium.PolyLine(locations=points, color=color, weight=weight, opacity=0.6)
        line.add_to(m)

    folium.LayerControl().add_to(m)

    # Set the zoom to the maximum possible
    m.fit_bounds(m.get_bounds())
    filename_html = "test.html"
    m.save(filename_html)

    # -----------------------------------------------------------------------------------------------------------


def sort_ort(a, b, order='first'):
    l = sorted([a, b])
    return l[0] if order == 'first' else l[1]


if __name__ == "__main__":
    # Pandas will try to autodetect the size of your terminal window if you set
    pandas.options.display.width = 0

    main()

