import adopt_net0 as adopt
import json
from pathlib import Path
import os
import pandas as pd

# -----------------------------
# 1. Create folders
# -----------------------------
results_data_path = Path("./userData_lohc")
results_data_path.mkdir(parents=True, exist_ok=True)

input_data_path = Path("./caseStudies/lohc_minimal")
input_data_path.mkdir(parents=True, exist_ok=True)

custom_tech_path = Path(r"C:\Users\kasha\Thesis\Main optimisation file\AdOpT-NET0")

# -----------------------------
# 2. Create base templates
# -----------------------------
adopt.create_optimization_templates(input_data_path)

# -----------------------------
# 3. Edit Topology.json
# -----------------------------
with open(input_data_path / "Topology.json", "r") as json_file:
    topology = json.load(json_file)

topology["nodes"] = ["source", "demand"]
topology["carriers"] = ["hydrogen", "lohc_loaded", "lohc_unloaded", "heat"]
topology["investment_periods"] = ["period1"]

with open(input_data_path / "Topology.json", "w") as json_file:
    json.dump(topology, json_file, indent=4)

# -----------------------------
# 4. Edit ConfigModel.json
# -----------------------------
with open(input_data_path / "ConfigModel.json", "r") as json_file:
    configuration = json.load(json_file)

configuration["optimization"]["typicaldays"]["N"]["value"] = 10
configuration["optimization"]["typicaldays"]["method"]["value"] = 1
configuration["solveroptions"]["mipgap"]["value"] = 0.02

with open(input_data_path / "ConfigModel.json", "w") as json_file:
    json.dump(configuration, json_file, indent=4)

# -----------------------------
# 5. Create input-data folder structure
# -----------------------------
adopt.create_input_data_folder_template(input_data_path)

# -----------------------------
# 6. Fill NodeLocations.csv
# -----------------------------
node_location = pd.read_csv(
    input_data_path / "NodeLocations.csv",
    sep=";",
    index_col=0,
    header=0
)

node_lon = {"source": 5.1214, "demand": 5.2400}
node_lat = {"source": 52.0907, "demand": 51.9561}
node_alt = {"source": 5, "demand": 10}

for node in ["source", "demand"]:
    node_location.at[node, "lon"] = node_lon[node]
    node_location.at[node, "lat"] = node_lat[node]
    node_location.at[node, "alt"] = node_alt[node]

node_location = node_location.reset_index()
node_location.to_csv(input_data_path / "NodeLocations.csv", sep=";", index=False)

# -----------------------------
# 7. Define technologies per node
# -----------------------------
with open(input_data_path / "period1" / "node_data" / "source" / "Technologies.json", "r") as json_file:
    technologies = json.load(json_file)

technologies["new"] = ["Hydrogenation_LOHC"]
technologies["existing"] = {}

with open(input_data_path / "period1" / "node_data" / "source" / "Technologies.json", "w") as json_file:
    json.dump(technologies, json_file, indent=4)

with open(input_data_path / "period1" / "node_data" / "demand" / "Technologies.json", "r") as json_file:
    technologies = json.load(json_file)

technologies["new"] = ["Dehydrogenation_LOHC"]
technologies["existing"] = {}

with open(input_data_path / "period1" / "node_data" / "demand" / "Technologies.json", "w") as json_file:
    json.dump(technologies, json_file, indent=4)

# -----------------------------
# 8. Copy custom technology data
# -----------------------------
adopt.copy_technology_data(input_data_path, tec_data_path=custom_tech_path)

# -----------------------------
# 9. Define network topology
# -----------------------------
with open(input_data_path / "period1" / "Networks.json", "r") as json_file:
    networks = json.load(json_file)

networks["new"] = ["lohcTransport"]
networks["existing"] = []

with open(input_data_path / "period1" / "Networks.json", "w") as json_file:
    json.dump(networks, json_file, indent=4)

os.makedirs(
    input_data_path / "period1" / "network_topology" / "new" / "lohcTransport",
    exist_ok=True
)

arc_size = pd.read_csv(
    input_data_path / "period1" / "network_topology" / "new" / "size_max_arcs.csv",
    sep=";",
    index_col=0
)
arc_size.loc["source", "demand"] = 3000
arc_size.loc["demand", "source"] = 3000
arc_size.to_csv(
    input_data_path / "period1" / "network_topology" / "new" / "lohcTransport" / "size_max_arcs.csv",
    sep=";"
)

connection = pd.read_csv(
    input_data_path / "period1" / "network_topology" / "new" / "connection.csv",
    sep=";",
    index_col=0
)
connection.loc["source", "demand"] = 1
connection.loc["demand", "source"] = 1
connection.to_csv(
    input_data_path / "period1" / "network_topology" / "new" / "lohcTransport" / "connection.csv",
    sep=";"
)

distance = pd.read_csv(
    input_data_path / "period1" / "network_topology" / "new" / "distance.csv",
    sep=";",
    index_col=0
)
distance.loc["source", "demand"] = 50
distance.loc["demand", "source"] = 50
distance.to_csv(
    input_data_path / "period1" / "network_topology" / "new" / "lohcTransport" / "distance.csv",
    sep=";"
)

os.remove(input_data_path / "period1" / "network_topology" / "new" / "size_max_arcs.csv")
os.remove(input_data_path / "period1" / "network_topology" / "new" / "connection.csv")
os.remove(input_data_path / "period1" / "network_topology" / "new" / "distance.csv")

# -----------------------------
# 10. Create custom network json
# -----------------------------
network_data_folder = input_data_path / "period1" / "network_data"
network_data_folder.mkdir(parents=True, exist_ok=True)

lohc_network_data = {
    "network_type": "fluid",
    "size_is_int": 0,
    "decommission": "impossible",
    "size_min": 0,
    "size_max": 3000,
    "Economics": {
        "gamma1": 0.0,
        "gamma2": 0.0,
        "gamma3": 0.0,
        "gamma4": 0.0,
        "OPEX_variable": 0.0,
        "OPEX_fixed": 0.0,
        "discount_rate": 0.08,
        "lifetime": 20,
        "decommission_cost": 0.0
    },
    "Performance": {
        "carrier": "lohc_loaded",
        "bidirectional_network": 1,
        "loss": 0.0,
        "min_transport": 0.0,
        "loss2emissions": 0.0,
        "emissionfactor": 0.0,
        "energyconsumption":[]
    },
    "Units": {
        "size": "MW",
        "transport_carrier": {
            "lohc_loaded": "MW"
        }
    }
}

with open(network_data_folder / "lohcTransport.json", "w") as json_file:
    json.dump(lohc_network_data, json_file, indent=4)

print("Created network file:", network_data_folder / "lohcTransport.json")

# -----------------------------
# 11. Define carrier data
# -----------------------------
hours = 8760
hydrogen_demand = pd.Series([100.0] * hours)

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=hydrogen_demand,
    columns=["Demand"],
    carriers=["hydrogen"],
    nodes=["demand"]
)

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=0,
    columns=["Demand"],
    carriers=["hydrogen"],
    nodes=["source"]
)

for node in ["source", "demand"]:
    adopt.fill_carrier_data(
        input_data_path,
        value_or_data=0,
        columns=["Demand"],
        carriers=["heat"],
        nodes=[node]
    )

for node in ["source", "demand"]:
    for carrier in ["lohc_loaded", "lohc_unloaded"]:
        adopt.fill_carrier_data(
            input_data_path,
            value_or_data=0,
            columns=["Demand"],
            carriers=[carrier],
            nodes=[node]
        )

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=1000,
    columns=["Import limit"],
    carriers=["hydrogen"],
    nodes=["source"]
)

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=50,
    columns=["Import price"],
    carriers=["hydrogen"],
    nodes=["source"]
)

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=0,
    columns=["Import limit"],
    carriers=["hydrogen"],
    nodes=["demand"]
)

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=1000,
    columns=["Import limit"],
    carriers=["heat"],
    nodes=["demand"]
)

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=10,
    columns=["Import price"],
    carriers=["heat"],
    nodes=["demand"]
)

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=0,
    columns=["Import limit"],
    carriers=["heat"],
    nodes=["source"]
)

for node in ["source", "demand"]:
    for carrier in ["lohc_loaded", "lohc_unloaded"]:
        adopt.fill_carrier_data(
            input_data_path,
            value_or_data=0,
            columns=["Import limit"],
            carriers=[carrier],
            nodes=[node]
        )

for node in ["source", "demand"]:
    for carrier in ["lohc_loaded", "lohc_unloaded"]:
        adopt.fill_carrier_data(
            input_data_path,
            value_or_data=0,
            columns=["Import price"],
            carriers=[carrier],
            nodes=[node]
        )

# -----------------------------
# 12. Solve model
# -----------------------------
m = adopt.ModelHub()
m.read_data(input_data_path)
m.quick_solve()