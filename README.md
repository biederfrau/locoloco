# Smart CO<sub>2</sub> Dashboard for Sustainable Business Travel

SBB’s B2B team serves 12,000 corporate clients in Switzerland (totaling around 1.25 million potential travelers), making those companies a powerful channel for driving greener mobility. 

Currently, much of SBB’s existing B2B travel data remains underutilized. The goal is to transform these data streams into an intuitive, action-oriented dashboard that helps corporate clients make more sustainable travel decisions. 

This dashboard aims to encourage a modal shift and reduce overall CO₂ emissions by offering actionable insights and behavior-focused features, ultimately guiding both corporate clients and SBB itself toward more sustainable mobility strategies.


## Background

<p>
  <img alt="Loco Loco Logo" src="img/logo.png" height="400"/>
  <img alt="Hack4Rail Logo" src="img/hack4rail-logo.jpg" height="400"/>
</p>



This project has been initiated during the [Hack4Rail 2025](https://hack4rail.event.sbb.ch/en/), a joint hackathon organised by the railway companies SBB, ÖBB, and DB in partnership with the OpenRail Association.

## Install

Either use the requirements.txt with pip or the pyproject.toml with uv for environment setup. 
Run preprocessor.py to generate the aggregated results.
To play around with the data use the firstlook.ipynb.
To Map unknown Betriebspunkte (e.g., bus stops to train betriebspunkte) use the data_manipulations.ipynb.

## Technical Details

### Preprocessing
The data was provided by SBB in an anonymized fashion and includes business travel data from all B2B customers from SBB from the last few months. Data was anonymized beforehand so that no conclusions on who the customer is can be drawn.
Preprocessing steps include: 
* Mapping of Reise von and Reise nach to Coordinates of Betriebspunkte based on Betriebspunkte on [didok]([https://atlas.app.sbb.ch/service-point-directory](https://data.sbb.ch/explore/dataset/dienststellen-gemass-opentransportdataswiss/export/?flg=fr-ch))
  *  If the Betriebspunkt is not known to SBB (mainly bus stops), the closest Betriebspunkt is trying to be found
    *  Remove the substring after the comma and find a train station with the corresponding name
    *  If a train station was found, the coordinates from this station are used
    *  If there are multiple train station with the same string (Zürich Altstetten, Zürich HB...) the shortest string is used.
    *  If no train station was found no mapping was added and journeys starting or ending there were excluded
* Computation of distance for the individual trips
  *  Based on the euclidian distance between the start and end point
* Computation of cost of travel per mode of travel
  *  Assumption that the distance is the same for both car and train travels
  *  Costs per km for car: CHF 0.65
  *  Costs per km for train: CHF 0.15
  *  Source: [Spar und Rechenbeispiel SBB](https://business.sbb.ch/de/beratung/ihre-vorteile/effizienzsteigerung.html#:~:text=Ein%20Autokilometer%20kostet%20Sie%20etwa,Klasse%20rund%2050%20Rappen)
* Computation of CO<sub>2</sub> emission per mode of travel
  *  CO<sub>2</sub> emission per km travelled by car: 0.18
  *  CO<sub>2</sub> emission per km travelled by train: 0.02
  *  Source: [Swiss Journal of Economics and Statistics](https://sjes.springeropen.com/articles/10.1186/s41937-019-0037-3)
* Since it might be possible to work on the train but not in the car, a potential of work time gained was computed
  *  Assuming an average speed of 100km/h for a train [Source](https://www.blick.ch/wirtschaft/verein-fordert-turbozuege-sbb-sind-die-lahmste-bahn-europas-id17223440.html)
  *  Deduction of 30mins for changing of connection and setup
* Data was grouped by business and calendarweek

## Further steps
* The plotting of a map with the travelled journeys was implemented but not embedded in the dashboard
  *  Run the script map_integration.py to see the overlay of travels per business customer
  *  Scaling via color and thickness of the line indicating the frequency of the specific journey
  *  Thick orange line = frequent journeys, thin yellow line = only few journeys found

## License

The content of this repository is licensed under the [Apache 2.0 license](LICENSE).
