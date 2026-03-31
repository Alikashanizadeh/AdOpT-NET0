import adopt_net0 as adopt
import json
from pathlib import Path
import os
import pandas as pd
import numpy as np

# Create folder for results
results_data_path = Path("./userData")
results_data_path.mkdir(parents=True, exist_ok=True)
# Create input data path and optimization templates
input_data_path = Path("./caseStudies/network")
input_data_path.mkdir(parents=True, exist_ok=True)
adopt.create_optimization_templates(input_data_path)

# Load json template
with open(input_data_path / "Topology.json", "r") as json_file:
    topology = json.load(json_file)
# Nodes
topology["nodes"] = ["city", "rural"]
# Carriers:
topology["carriers"] = ["electricity", "heat", "gas", "hydrogen"]
# Investment periods:
topology["investment_periods"] = ["period1"]
# Save json template
with open(input_data_path / "Topology.json", "w") as json_file:
    json.dump(topology, json_file, indent=4)

# Load json template
with open(input_data_path / "ConfigModel.json", "r") as json_file:
    configuration = json.load(json_file)
# Set time aggregation settings:
configuration["optimization"]["typicaldays"]["N"]["value"] = 30
configuration["optimization"]["typicaldays"]["method"]["value"] = 1
# Set MILP gap
configuration["solveroptions"]["mipgap"]["value"] = 0.02
# Save json template
with open(input_data_path / "ConfigModel.json", "w") as json_file:
    json.dump(configuration, json_file, indent=4)

adopt.create_input_data_folder_template(input_data_path)

# Define node locations (here two exemplary location in the Netherlands)
node_location = pd.read_csv(input_data_path / "NodeLocations.csv", sep=';', index_col=0, header=0)
node_lon = {'city': 5.1214, 'rural': 5.24}
node_lat = {'city': 52.0907, 'rural': 51.9561}
node_alt = {'city': 5, 'rural': 10}
for node in ['city', 'rural']:
    node_location.at[node, 'lon'] = node_lon[node]
    node_location.at[node, 'lat'] = node_lat[node]
    node_location.at[node, 'alt'] = node_alt[node]

node_location = node_location.reset_index()
node_location.to_csv(input_data_path / "NodeLocations.csv", sep=';', index=False)

adopt.show_available_technologies()

# Add required technologies for node 'city'
with open(input_data_path / "period1" / "node_data" / "city" / "Technologies.json", "r") as json_file:
    technologies = json.load(json_file)
technologies["new"] = ["HeatPump_AirSourced", "Storage_Battery", "Photovoltaic"]
technologies["existing"] = {"Boiler_Small_NG": 1000}

with open(input_data_path / "period1" / "node_data" / "city" / "Technologies.json", "w") as json_file:
    json.dump(technologies, json_file, indent=4)

# Add required technologies for node 'rural'
with open(input_data_path / "period1" / "node_data" / "rural" / "Technologies.json", "r") as json_file:
    technologies = json.load(json_file)
technologies["new"] = ["HeatPump_AirSourced", "Storage_Battery", "Photovoltaic", "WindTurbine_Onshore_4000"]
technologies["existing"] = {"Boiler_Small_NG": 350, "GasTurbine_simple": 1000}

with open(input_data_path / "period1" / "node_data" / "rural" / "Technologies.json", "w") as json_file:
    json.dump(technologies, json_file, indent=4)

# Copy over technology files
adopt.copy_technology_data(input_data_path)

for node in ["city", "rural"]:
    with open(input_data_path / "period1" / "node_data" / node / "technology_data" / "Boiler_Small_NG.json",
              "r") as json_file:
        tec_data = json.load(json_file)
        tec_data["size_max"] = 2000

    with open(input_data_path / "period1" / "node_data" / node / "technology_data" / "Boiler_Small_NG.json",
              "w") as json_file:
        json.dump(tec_data, json_file, indent=4)

    with open(input_data_path / "period1" / "node_data" / node / "technology_data" / "HeatPump_AirSourced.json",
              "r") as json_file:
        tec_data = json.load(json_file)
        tec_data["size_max"] = 3000
    with open(input_data_path / "period1" / "node_data" / node / "technology_data" / "HeatPump_AirSourced.json",
              "w") as json_file:
        json.dump(tec_data, json_file, indent=4)


# Add networks
with open(input_data_path / "period1" / "Networks.json", "r") as json_file:
    networks = json.load(json_file)
networks["new"] = ["electricityOnshore"]
networks["existing"] = ["electricityOnshore"]

with open(input_data_path / "period1" / "Networks.json", "w") as json_file:
    json.dump(networks, json_file, indent=4)


# Make a new folder for the existing network
os.makedirs(input_data_path / "period1" / "network_topology" / "existing" / "electricityOnshore", exist_ok=True)

print("Existing network")
# Use the templates, fill and save them to the respective directory
# Connection
connection = pd.read_csv(input_data_path / "period1" / "network_topology" / "existing" / "connection.csv", sep=";", index_col=0)
connection.loc["city", "rural"] = 1
connection.loc["rural", "city"] = 1
connection.to_csv(input_data_path / "period1" / "network_topology" / "existing" / "electricityOnshore" / "connection.csv", sep=";")
print("Connection:", connection)

# Delete the template
os.remove(input_data_path / "period1" / "network_topology" / "existing" / "connection.csv")

# Distance
distance = pd.read_csv(input_data_path / "period1" / "network_topology" / "existing" / "distance.csv", sep=";", index_col=0)
distance.loc["city", "rural"] = 50
distance.loc["rural", "city"] = 50
distance.to_csv(input_data_path / "period1" / "network_topology" / "existing" / "electricityOnshore" / "distance.csv", sep=";")
print("Distance:", distance)

# Delete the template
os.remove(input_data_path / "period1" / "network_topology" / "existing" / "distance.csv")

# Size
size = pd.read_csv(input_data_path / "period1" / "network_topology" / "existing" / "size.csv", sep=";", index_col=0)
size.loc["city", "rural"] = 1000
size.loc["rural", "city"] = 1000
size.to_csv(input_data_path / "period1" / "network_topology" / "existing" / "electricityOnshore" / "size.csv", sep=";")
print("Size:", size)

# Delete the template
os.remove(input_data_path / "period1" / "network_topology" / "existing" / "size.csv")

print("New network")
# Make a new folder for the new network
os.makedirs(input_data_path / "period1" / "network_topology" / "new" / "electricityOnshore", exist_ok=True)


# max size arc
arc_size = pd.read_csv(input_data_path / "period1" / "network_topology" / "new" / "size_max_arcs.csv", sep=";", index_col=0)
arc_size.loc["city", "rural"] = 3000
arc_size.loc["rural", "city"] = 3000
arc_size.to_csv(input_data_path / "period1" / "network_topology" / "new" / "electricityOnshore" / "size_max_arcs.csv", sep=";")
print("Max size per arc:", arc_size)

# Use the templates, fill and save them to the respective directory
# Connection
connection = pd.read_csv(input_data_path / "period1" / "network_topology" / "new" / "connection.csv", sep=";", index_col=0)
connection.loc["city", "rural"] = 1
connection.loc["rural", "city"] = 1
connection.to_csv(input_data_path / "period1" / "network_topology" / "new" / "electricityOnshore" / "connection.csv", sep=";")
print("Connection:", connection)

# Delete the template
os.remove(input_data_path / "period1" / "network_topology" / "new" / "connection.csv")

# Distance
distance = pd.read_csv(input_data_path / "period1" / "network_topology" / "new" / "distance.csv", sep=";", index_col=0)
distance.loc["city", "rural"] = 50
distance.loc["rural", "city"] = 50
distance.to_csv(input_data_path / "period1" / "network_topology" / "new" / "electricityOnshore" / "distance.csv", sep=";")
print("Distance:", distance)

# Delete the template
os.remove(input_data_path / "period1" / "network_topology" / "new" / "distance.csv")

# Delete the max_size_arc template
os.remove(input_data_path / "period1" / "network_topology" / "new" / "size_max_arcs.csv")

adopt.copy_network_data(input_data_path)

with open(input_data_path / "period1" / "network_data"/ "electricityOnshore.json", "r") as json_file:
    network_data = json.load(json_file)

network_data["Economics"]["gamma2"] = 40000
network_data["Economics"]["gamma4"] = 300

with open(input_data_path / "period1" / "network_data"/ "electricityOnshore.json", "w") as json_file:
    json.dump(network_data, json_file, indent=4)

# Read hourly data from Excel (Examplary demand profiles are provided with the package)
rural_hourly_data = adopt.load_network_rural_data()
city_hourly_data = adopt.load_network_city_data()

# Save the hourly data to the carrier's file in the case study folder
# electricity demand and price
hourly_data = {
    'city': city_hourly_data,
    'rural': rural_hourly_data
}

el_demand = {}
heat_demand = {}

for node in ['city', 'rural']:
    el_demand[node] = hourly_data[node].iloc[:, 1]
    heat_demand[node] = hourly_data[node].iloc[:, 0]
    adopt.fill_carrier_data(input_data_path, value_or_data=el_demand[node], columns=['Demand'], carriers=['electricity'], nodes=[node])
    adopt.fill_carrier_data(input_data_path, value_or_data=heat_demand[node], columns=['Demand'], carriers=['heat'], nodes=[node])

    # Set import limits/cost
    adopt.fill_carrier_data(input_data_path, value_or_data=4000, columns=['Import limit'], carriers=['gas'], nodes=[node])
    adopt.fill_carrier_data(input_data_path, value_or_data=2000, columns=['Import limit'], carriers=['electricity'], nodes=[node])
    adopt.fill_carrier_data(input_data_path, value_or_data=0.25, columns=['Import emission factor'], carriers=['electricity'], nodes=[node])
    adopt.fill_carrier_data(input_data_path, value_or_data=40, columns=['Import price'], carriers=['gas'], nodes=[node])
    adopt.fill_carrier_data(input_data_path, value_or_data=120, columns=['Import price'], carriers=['electricity'], nodes=[node])

# Define climate data
adopt.load_climate_data_from_api(input_data_path)

m = adopt.ModelHub()
m.read_data(input_data_path)
m.quick_solve()