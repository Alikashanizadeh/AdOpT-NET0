import adopt_net0 as adopt
import json
from pathlib import Path
import os
import shutil
import pandas as pd


# 0. PATHS

results_data_path = Path("./userData/Scenario Horizon Aanvoer-Fully  heat waste")
results_data_path.mkdir(parents=True, exist_ok=True)

input_data_path = Path("./caseStudies/lohc_thesis")

# always rebuild fresh
if input_data_path.exists():
    shutil.rmtree(input_data_path)

input_data_path.mkdir(parents=True, exist_ok=True)



# 1. CREATE BASIC ADOPT-NET0 CASE STRUCTURE

adopt.create_optimization_templates(input_data_path)

with open(input_data_path / "Topology.json", "r") as f:
    topology = json.load(f)

topology["nodes"] = [
    "import_terminal",
    "hydrogen_hub",
    "cluster",
    "industry_1",
    "industry_2",
    "industry_3"
]

topology["carriers"] = [
    "hydrogen",
    "lohc_loaded",
    "lohc_unloaded",
    "electricity",
    "heat"
]

topology["investment_periods"] = ["period1"]

# timestep
topology["start_date"] = "2022-01-01 00:00"
topology["end_date"] = "2022-01-02 00:00"
topology["resolution"] = "1h"
topology["investment_period_length"] = 1

with open(input_data_path / "Topology.json", "w") as f:
    json.dump(topology, f, indent=4)


# 2. MODEL CONFIGURATION

with open(input_data_path / "ConfigModel.json", "r") as f:
    config = json.load(f)

config["reporting"]["save_path"]["value"] = str(results_data_path)

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
    "import_terminal": 5.00,
    "hydrogen_hub":   5.10,
    "cluster":        5.20,
    "industry_1":     5.30,
    "industry_2":     5.30,
    "industry_3":     5.40,
}

node_lat = {
    "import_terminal": 52.00,
    "hydrogen_hub":    52.00,
    "cluster":         52.00,
    "industry_1":      52.05,
    "industry_2":      51.95,
    "industry_3":      52.05,
}

node_alt = {
    "import_terminal": 0,
    "hydrogen_hub": 0,
    "cluster": 0,
    "industry_1": 0,
    "industry_2": 0,
    "industry_3": 0,
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


set_node_technologies("import_terminal",
                      new_techs=[]
                      )

set_node_technologies("hydrogen_hub",
                      new_techs=["Dehydrogenation_LOHC"]
                      )

set_node_technologies("cluster",
                      new_techs=["Dehydrogenation_LOHC"]
                      )

set_node_technologies("industry_1",
                      new_techs=["Dehydrogenation_LOHC"],
                      )

set_node_technologies("industry_2",
                      new_techs=["Dehydrogenation_LOHC"]
                      )

# 6. COPY TECHNOLOGY DATA FROM MODEL DATABASE

adopt.copy_technology_data(input_data_path)


# 7. DEFINE NETWORKS

with open(input_data_path / "period1" / "Networks.json", "r") as f:
    networks = json.load(f)

networks["new"] = [
    "hydrogenPipelineOnshore_highP",
    "hydrogenPipelineOnshore_lowP",
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


def write_network_topology(network_name, arcs, distances, size_max_value=1000):
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

#8' Defining the network possibility distances
distances = {
    ("import_terminal", "hydrogen_hub"): 25,
    ("hydrogen_hub", "import_terminal"): 25,

    ("hydrogen_hub", "cluster"): 60,
    ("cluster", "hydrogen_hub"): 60,

    ("cluster", "industry_1"): 45,
    ("industry_1", "cluster"): 45,

    ("industry_2", "cluster"): 25,
    ("cluster", "industry_2"): 25,

    ("cluster", "industry_3"): 55,

    ("industry_1", "industry_3"): 10,



}

# hydrogen pipeline high
write_network_topology(
    "hydrogenPipelineOnshore_highP",
    arcs=[
        ("hydrogen_hub", "cluster"),
    ],
    distances={
        ("hydrogen_hub", "cluster"): distances[("hydrogen_hub", "cluster")],
    },
    size_max_value=30000
)

#hydrogen pipeline low

write_network_topology(
    "hydrogenPipelineOnshore_lowP",
    arcs=[
        ("cluster", "industry_1"),
        ("cluster", "industry_2"),
        ("industry_1", "industry_3"),
        ("cluster", "industry_3"),
    ],
    distances={
        ("cluster", "industry_1"): distances[("cluster", "industry_1")],
        ("cluster", "industry_2"): distances[("cluster", "industry_2")],
        ("industry_1", "industry_3"): distances[("industry_1", "industry_3")],
        ("cluster", "industry_3"): distances[("cluster", "industry_3")],
    },
    size_max_value=7500
)

# loaded LOHC
write_network_topology(
    "lohcTransport",
    arcs=[
        ("import_terminal", "hydrogen_hub"),
        ("hydrogen_hub", "cluster"),
        ("cluster", "industry_1"),
        ("cluster", "industry_2"),
    ],
    distances={
        ("import_terminal", "hydrogen_hub"): distances[("import_terminal", "hydrogen_hub")],
        ("hydrogen_hub", "cluster"): distances[("hydrogen_hub", "cluster")],
        ("cluster", "industry_1"): distances[("cluster", "industry_1")],
        ("cluster", "industry_2"): distances[("cluster", "industry_2")],
    },
    size_max_value=200000
)

# unloaded LOHC return
write_network_topology(
    "unloaded_lohcTransport",
    arcs=[
        ("hydrogen_hub", "import_terminal"),
        ("cluster", "hydrogen_hub"),
        ("industry_1", "cluster"),
        ("industry_2", "cluster"),
    ],
    distances={
        ("hydrogen_hub", "import_terminal"): distances[("hydrogen_hub", "import_terminal")],
        ("cluster", "hydrogen_hub"): distances[("cluster", "hydrogen_hub")],
        ("industry_1", "cluster"): distances[("industry_1", "cluster")],
        ("industry_2", "cluster"): distances[("industry_2", "cluster")],
    },
    size_max_value=200000
)

os.remove(input_data_path / "period1" / "network_topology" / "new" / "connection.csv")
os.remove(input_data_path / "period1" / "network_topology" / "new" / "distance.csv")
os.remove(input_data_path / "period1" / "network_topology" / "new" / "size_max_arcs.csv")

# 9. COPY NETWORK DATA FROM MODEL DATABASE

adopt.copy_network_data(input_data_path)

#10-Import limits and price

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=200000,
    columns=["Import limit"],
    carriers=["lohc_loaded"],
    nodes=["import_terminal"]
)

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=0,
    columns=["Import price"],
    carriers=["lohc_loaded"],
    nodes=["import_terminal"]
)



# hydrogen import at dehydrogenation node

# adopt.fill_carrier_data(
#     input_data_path,
#     value_or_data=10000,
#     columns=["Import limit"],
#     carriers=["hydrogen"],
#     nodes=["hydrogen_hub", "cluster", "industry_1", "industry_2"]
# )
# adopt.fill_carrier_data(
#     input_data_path,
#     value_or_data=0,
#     columns=["Import price"],
#     carriers=["hydrogen"],
#     nodes=["hydrogen_hub", "cluster", "industry_1", "industry_2"]
# )

#new heat

heat_data = {
    "hydrogen_hub": {"limit": 50000, "price": 0},
    "cluster": {"limit": 50000, "price": 0},
    "industry_1": {"limit": 50000, "price": 0},
    "industry_2": {"limit": 50000, "price": 0},
}

for node, data in heat_data.items():
    adopt.fill_carrier_data(
        input_data_path,
        value_or_data=data["limit"],
        columns=["Import limit"],
        carriers=["heat"],
        nodes=[node]
    )

    adopt.fill_carrier_data(
        input_data_path,
        value_or_data=data["price"],
        columns=["Import price"],
        carriers=["heat"],
        nodes=[node]
    )


#exporting unloade_lohc

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=200000,
    columns=["Export limit"],
    carriers=["lohc_unloaded"],
    nodes=["import_terminal"]
)


adopt.fill_carrier_data(
    input_data_path,
    value_or_data=0,
    columns=["Export price"],
    carriers=["lohc_unloaded"],
    nodes=["import_terminal"]
)


# electricity input at all nodes
adopt.fill_carrier_data(
    input_data_path,
    value_or_data=150000,
    columns=["Import limit"],
    carriers=["electricity"],
    nodes=topology["nodes"]
)

# variable electricity import price from AdOpT-NET0 household case-study data
household_hourly_data = adopt.load_household_data()

# In the household case study, column 2 is the hourly day-ahead electricity price
el_price = household_hourly_data.iloc[:, 2]

# Match the electricity price length to your model horizon
n_steps = len(pd.date_range(
    start=topology["start_date"],
    end=topology["end_date"],
    freq=topology["resolution"],
    inclusive="left"
))

el_price = el_price.iloc[:n_steps+1].reset_index(drop=True)

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=el_price,
    columns=["Import price"],
    carriers=["electricity"],
    nodes=topology["nodes"]
)



# hydrogen demand at demand node
adopt.fill_carrier_data(
    input_data_path,
    value_or_data=1698.6,
    columns=["Demand"],
    carriers=["hydrogen"],
    nodes=["industry_1"]
)

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=3745.4,
    columns=["Demand"],
    carriers=["hydrogen"],
    nodes=["industry_2"]
)

adopt.fill_carrier_data(
    input_data_path,
    value_or_data=1569.2,
    columns=["Demand"],
    carriers=["hydrogen"],
    nodes=["industry_3"]
)

# 11. SOLVE

m = adopt.ModelHub()
m.read_data(input_data_path)
m.quick_solve()