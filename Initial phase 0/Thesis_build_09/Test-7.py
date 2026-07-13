import adopt_net0 as adopt
import json
from pathlib import Path
import os
import shutil
import pandas as pd


# 0. PATHS
results_data_path = Path("./userData")
results_data_path.mkdir(parents=True, exist_ok=True)

input_data_path = Path("./caseStudies/lohc_thesis_basic")

# always rebuild fresh
if input_data_path.exists():
    shutil.rmtree(input_data_path)

input_data_path.mkdir(parents=True, exist_ok=True)


# 1. CREATE BASIC ADOPT-NET0 CASE STRUCTURE
adopt.create_optimization_templates(input_data_path)

with open(input_data_path / "Topology.json", "r") as f:
    topology = json.load(f)

topology["nodes"] = [
    "import_hydrogen_node",
    "hydrogenation_node",
    "dehydrogenation_node",
    "demand_node"
]

topology["carriers"] = [
    "hydrogen",
    "lohc_loaded",
    "electricity",
    "lohc_unloaded",
    "heat"
]

topology["investment_periods"] = ["period1"]

# one full year = 8760 hourly steps
topology["start_date"] = "2022-01-01 00:00"
topology["end_date"] = "2022-01-31 23:00"
topology["resolution"] = "1h"
topology["investment_period_length"] = 1

with open(input_data_path / "Topology.json", "w") as f:
    json.dump(topology, f, indent=4)


# 2. MODEL CONFIGURATION
with open(input_data_path / "ConfigModel.json", "r") as f:
    config = json.load(f)

config["solveroptions"]["mipgap"]["value"] = 0.02

with open(input_data_path / "ConfigModel.json", "w") as f:
    json.dump(config, f, indent=4)


# 3. CREATE INPUT DATA FOLDER STRUCTURE
adopt.create_input_data_folder_template(input_data_path)


# 4. NODE LOCATIONS
node_location = pd.read_csv(
    input_data_path / "NodeLocations.csv",
    sep=";",
    index_col=0,
    header=0
)

node_lon = {
    "import_hydrogen_node": 5.00,
    "hydrogenation_node": 5.10,
    "dehydrogenation_node": 5.20,
    "demand_node": 5.30,
}
node_lat = {
    "import_hydrogen_node": 52.00,
    "hydrogenation_node": 52.00,
    "dehydrogenation_node": 52.00,
    "demand_node": 52.00,
}
node_alt = {
    "import_hydrogen_node": 0,
    "hydrogenation_node": 0,
    "dehydrogenation_node": 0,
    "demand_node": 0,
}

for node in topology["nodes"]:
    node_location.at[node, "lon"] = node_lon[node]
    node_location.at[node, "lat"] = node_lat[node]
    node_location.at[node, "alt"] = node_alt[node]

node_location = node_location.reset_index()
node_location.to_csv(input_data_path / "NodeLocations.csv", sep=";", index=False)


# 5. ASSIGN TECHNOLOGIES TO NODES
def set_node_technologies(node, new_techs=None, existing_techs=None):
    tech_file = input_data_path / "period1" / "node_data" / node / "Technologies.json"
    with open(tech_file, "r") as f:
        technologies = json.load(f)

    technologies["new"] = new_techs or []
    technologies["existing"] = existing_techs or {}

    with open(tech_file, "w") as f:
        json.dump(technologies, f, indent=4)


set_node_technologies("import_hydrogen_node", new_techs=[])

set_node_technologies(
    "hydrogenation_node",
    new_techs=["Hydrogenation_LOHC"]
)

set_node_technologies(
    "dehydrogenation_node",
    new_techs=["Dehydrogenation_LOHC"]
)

set_node_technologies("demand_node", new_techs=[])


# 6. COPY TECHNOLOGY DATA FROM MODEL DATABASE
adopt.copy_technology_data(input_data_path)


# 7. DEFINE NETWORKS
with open(input_data_path / "period1" / "Networks.json", "r") as f:
    networks = json.load(f)

networks["new"] = [
    "hydrogenTruck",
    "lohcTransport",
    "unloaded_lohcTransport"
]
networks["existing"] = []

with open(input_data_path / "period1" / "Networks.json", "w") as f:
    json.dump(networks, f, indent=4)


# 8. CREATE NETWORK TOPOLOGY FOLDERS
for network_name in networks["new"]:
    os.makedirs(
        input_data_path / "period1" / "network_topology" / "new" / network_name,
        exist_ok=True
    )


def write_network_topology(network_name, arcs, distances, size_max_value=10):
    base_new = input_data_path / "period1" / "network_topology" / "new"

    arc_size = pd.read_csv(base_new / "size_max_arcs.csv", sep=";", index_col=0)
    connection = pd.read_csv(base_new / "connection.csv", sep=";", index_col=0)
    distance = pd.read_csv(base_new / "distance.csv", sep=";", index_col=0)

    for i, j in arcs:
        connection.loc[i, j] = 1
        distance.loc[i, j] = distances[(i, j)]
        arc_size.loc[i, j] = size_max_value

    connection.to_csv(base_new / network_name / "connection.csv", sep=";")
    distance.to_csv(base_new / network_name / "distance.csv", sep=";")
    arc_size.to_csv(base_new / network_name / "size_max_arcs.csv", sep=";")


write_network_topology(
    "hydrogenTruck",
    arcs=[
        ("import_hydrogen_node", "hydrogenation_node"),
        ("dehydrogenation_node", "demand_node")
    ],
    distances={
        ("import_hydrogen_node", "hydrogenation_node"): 25,
        ("dehydrogenation_node", "demand_node"): 25
    },
    size_max_value=1000
)

write_network_topology(
    "lohcTransport",
    arcs=[("hydrogenation_node", "dehydrogenation_node")],
    distances={("hydrogenation_node", "dehydrogenation_node"): 25},
    size_max_value=1000
)

write_network_topology(
    "unloaded_lohcTransport",
    arcs=[("dehydrogenation_node", "hydrogenation_node")],
    distances={("dehydrogenation_node", "hydrogenation_node"): 25},
    size_max_value=1000
)

os.remove(input_data_path / "period1" / "network_topology" / "new" / "connection.csv")
os.remove(input_data_path / "period1" / "network_topology" / "new" / "distance.csv")
os.remove(input_data_path / "period1" / "network_topology" / "new" / "size_max_arcs.csv")


# 9. COPY NETWORK DATA FROM MODEL DATABASE
adopt.copy_network_data(input_data_path)


# 10. INPUT CARRIER DATA
hours = 24 * 31

# hydrogen import at import node

# adopt.fill_carrier_data(
#     input_data_path,
#     value_or_data=5.0,   # MW
#     columns=["Import limit"],
#     carriers=["hydrogen"],
#     nodes=["import_hydrogen_node"]
# )

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=80.0,   # EUR/MWh
    columns=["Import price"],
    carriers=["hydrogen"],
    nodes=["import_hydrogen_node"]
)

# heat import at dehydrogenation node

# adopt.fill_carrier_data(
#     input_data_path,
#     value_or_data=1.5,   # MW
#     columns=["Import limit"],
#     carriers=["heat"],
#     nodes=["dehydrogenation_node"]
# )

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=25.0,   # EUR/MWh
    columns=["Import price"],
    carriers=["heat"],
    nodes=["dehydrogenation_node"]
)

# hydrogen demand at demand node: ~1 ktpa ≈ 3.8 MW
adopt.fill_carrier_data(
    input_data_path,
    value_or_data= 0.1,
    columns=["Demand"],
    carriers=["hydrogen"],
    nodes=["demand_node"]
)

# temporary initialization of unloaded LOHC
# adopt.fill_carrier_data(
#     input_data_path,
#     value_or_data=5.0,   # MW-equivalent
#     columns=["Import limit"],
#     carriers=["lohc_unloaded"],
#     nodes=["hydrogenation_node"]
# )

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=0.0,
    columns=["Import price"],
    carriers=["lohc_unloaded"],
    nodes=["hydrogenation_node"]
)

# electricity input at all nodes
# adopt.fill_carrier_data(
#     input_data_path,
#     value_or_data=5.0,   # MW
#     columns=["Import limit"],
#     carriers=["electricity"],
#     nodes=["import_hydrogen_node", "hydrogenation_node", "dehydrogenation_node", "demand_node"]
# )

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=100.0,   # EUR/MWh
    columns=["Import price"],
    carriers=["electricity"],
    nodes=["import_hydrogen_node", "hydrogenation_node", "dehydrogenation_node", "demand_node"]
)


# 11. SOLVE
m = adopt.ModelHub()
m.read_data(input_data_path)
m.quick_solve()