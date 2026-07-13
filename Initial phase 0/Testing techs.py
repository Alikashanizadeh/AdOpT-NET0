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

#Adapting Topology
import json

with open(input_data_path / "Topology.json", "r") as f:
    topology = json.load(f)

topology["nodes"] = ["source", "demand"]
topology["carriers"] = ["hydrogen", "lohc_loaded", "lohc_unloaded", "heat"]
topology["investment_periods"] = ["period1"]

with open(input_data_path / "Topology.json", "w") as f:
    json.dump(topology, f, indent=4)

# Load ConfigModel.json

with open(input_data_path / "ConfigModel.json", "r") as json_file:
    configuration = json.load(json_file)

# Use a lighter setup for first debugging
configuration["optimization"]["typicaldays"]["N"]["value"] = 10
configuration["optimization"]["typicaldays"]["method"]["value"] = 1

# Set MILP gap
configuration["solveroptions"]["mipgap"]["value"] = 0.02

# Save ConfigModel.json
with open(input_data_path / "ConfigModel.json", "w") as json_file:
    json.dump(configuration, json_file, indent=4)

adopt.create_input_data_folder_template(input_data_path)

# Define node locations
node_location = pd.read_csv(input_data_path / "NodeLocations.csv", sep=';', index_col=0, header=0)

node_lon = {'source': 5.1214, 'demand': 5.2400}
node_lat = {'source': 52.0907, 'demand': 51.9561}
node_alt = {'source': 5, 'demand': 10}

for node in ['source', 'demand']:
    node_location.at[node, 'lon'] = node_lon[node]
    node_location.at[node, 'lat'] = node_lat[node]
    node_location.at[node, 'alt'] = node_alt[node]

node_location = node_location.reset_index()
node_location.to_csv(input_data_path / "NodeLocations.csv", sep=';', index=False)

# Add required technologies for node 'source'
with open(input_data_path / "period1" / "node_data" / "source" / "Technologies.json", "r") as json_file:
    technologies = json.load(json_file)

technologies["new"] = ["Hydrogenation_LOHC"]
technologies["existing"] = {}

with open(input_data_path / "period1" / "node_data" / "source" / "Technologies.json", "w") as json_file:
    json.dump(technologies, json_file, indent=4)

# Add required technologies for node 'demand'
with open(input_data_path / "period1" / "node_data" / "demand" / "Technologies.json", "r") as json_file:
    technologies = json.load(json_file)

technologies["new"] = ["Dehydrogenation_LOHC"]
technologies["existing"] = {}

with open(input_data_path / "period1" / "node_data" / "demand" / "Technologies.json", "w") as json_file:
    json.dump(technologies, json_file, indent=4)

# Add networks
with open(input_data_path / "period1" / "Networks.json", "r") as json_file:
    networks = json.load(json_file)

networks["new"] = ["lohcTransport"]
networks["existing"] = []

with open(input_data_path / "period1" / "Networks.json", "w") as json_file:
    json.dump(networks, json_file, indent=4)

# Make a new folder for the new LOHC transport network
os.makedirs(input_data_path / "period1" / "network_topology" / "new" / "lohcTransport", exist_ok=True)

# Max size per arc
arc_size = pd.read_csv(
    input_data_path / "period1" / "network_topology" / "new" / "size_max_arcs.csv",
    sep=";", index_col=0
)

arc_size.loc["source", "demand"] = 3000
arc_size.loc["demand", "source"] = 3000

arc_size.to_csv(
    input_data_path / "period1" / "network_topology" / "new" / "lohcTransport" / "size_max_arcs.csv",
    sep=";"
)

# Distance matrix
distance = pd.read_csv(
    input_data_path / "period1" / "network_topology" / "new" / "distance.csv",
    sep=";", index_col=0
)

distance.loc["source", "demand"] = 50
distance.loc["demand", "source"] = 50

distance.to_csv(
    input_data_path / "period1" / "network_topology" / "new" / "lohcTransport" / "distance.csv",
    sep=";"
)

# Delete original templates in the new folder
os.remove(input_data_path / "period1" / "network_topology" / "new" / "connection.csv")
os.remove(input_data_path / "period1" / "network_topology" / "new" / "distance.csv")
os.remove(input_data_path / "period1" / "network_topology" / "new" / "size_max_arcs.csv")


adopt.copy_network_data(input_data_path)

with open(input_data_path / "period1" / "network_data" / "lohcTransport.json", "r") as json_file:
    network_data = json.load(json_file)

network_data["Economics"]["gamma2"] = 40000
network_data["Economics"]["gamma4"] = 300

with open(input_data_path / "period1" / "network_data" / "lohcTransport.json", "w") as json_file:
    json.dump(network_data, json_file, indent=4)


# Define a simple hourly profile for one year
hours = 8760
hydrogen_demand = pd.Series([100.0] * hours)
heat_supply_limit = pd.Series([1000.0] * hours)
hydrogen_import_limit = pd.Series([1000.0] * hours)

# Hydrogen demand at demand node
adopt.fill_carrier_data(
    input_data_path,
    value_or_data=hydrogen_demand,
    columns=['Demand'],
    carriers=['hydrogen'],
    nodes=['demand']
)

# No hydrogen demand at source
adopt.fill_carrier_data(
    input_data_path,
    value_or_data=0,
    columns=['Demand'],
    carriers=['hydrogen'],
    nodes=['source']
)

# Hydrogen import at source
adopt.fill_carrier_data(
    input_data_path,
    value_or_data=1000,
    columns=['Import limit'],
    carriers=['hydrogen'],
    nodes=['source']
)

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=80,
    columns=['Import price'],
    carriers=['hydrogen'],
    nodes=['source']
)

# No hydrogen import at demand, so the model must use transport/conversion
adopt.fill_carrier_data(
    input_data_path,
    value_or_data=0,
    columns=['Import limit'],
    carriers=['hydrogen'],
    nodes=['demand']
)

# Heat import at demand for dehydrogenation
adopt.fill_carrier_data(
    input_data_path,
    value_or_data=1000,
    columns=['Import limit'],
    carriers=['heat'],
    nodes=['demand']
)

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=20,
    columns=['Import price'],
    carriers=['heat'],
    nodes=['demand']
)

for node in ['source', 'demand']:
    for carrier in ['lohc_loaded', 'lohc_unloaded', 'heat']:
        adopt.fill_carrier_data(
            input_data_path,
            value_or_data=0,
            columns=['Demand'],
            carriers=[carrier],
            nodes=[node]
        )


for node in ['source', 'demand']:
    for carrier in ['lohc_loaded', 'lohc_unloaded']:
        adopt.fill_carrier_data(
            input_data_path,
            value_or_data=0,
            columns=['Import limit'],
            carriers=[carrier],
            nodes=[node]
        )

# Solve
m = adopt.ModelHub()
m.read_data(input_data_path)
m.quick_solve()

