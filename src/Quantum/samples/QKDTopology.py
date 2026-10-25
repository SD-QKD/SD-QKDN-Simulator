import json
import sequence.utils.log as log

from sequence.topology.qkd_topo import QKDTopo


log_filename = "bb84_star_topo.log"
log.set_logger(__name__, log_filename)
log.logger.setLevel("INFO")


def build_star_config(distance=1e3):
    """
    Builds a star topology:
          c
          |
    a --- b --- d
    """
    return {
        "nodes": [
            {"name": "a", "type": "QKDNode"},
            {"name": "b", "type": "QKDNode"},
            {"name": "c", "type": "QKDNode"},
            {"name": "d", "type": "QKDNode"},
        ],

        # quantum links
        "qchannels": [
            {"node1": "a", "node2": "b", "distance": distance},
            {"node1": "b", "node2": "c", "distance": distance},
            {"node1": "b", "node2": "d", "distance": distance},
        ],

        # classical links (both directions)
        "cchannels": [
            {"node1": "a", "node2": "b", "distance": distance},
            {"node1": "b", "node2": "a", "distance": distance},

            {"node1": "b", "node2": "c", "distance": distance},
            {"node1": "c", "node2": "b", "distance": distance},

            {"node1": "b", "node2": "d", "distance": distance},
            {"node1": "d", "node2": "b", "distance": distance},
        ],
    }


if __name__ == "__main__":
    runtime = 2e10
    distance = 1e3

    # 1) Build config and save as JSON file
    conf_file = "star_topology.json"
    topo_config = build_star_config(distance)

    with open(conf_file, "w") as f:
        json.dump(topo_config, f, indent=2)

    print(f"Saved topology config to {conf_file}")

    # 2) Load topology from JSON file
    topo = QKDTopo(conf_file)

    # 3) Set runtime and build
    topo.tl.stop_time = runtime
    topo.build()

    # 4) Access nodes
    a = topo.nodes["a"]
    b = topo.nodes["b"]
    c = topo.nodes["c"]
    d = topo.nodes["d"]

    print("Topology nodes:", list(topo.nodes.keys()))
    print("Star hub is:", b.name)

    # Optional: verify BB84 protocols attached
    print("\n--- Protocols per node (before init) ---")
    for name in ["a", "b", "c", "d"]:
        node = topo.nodes[name]
        print(f"Node {name}: {len(node.protocols)} protocols")
        for p in node.protocols:
            print("   ", type(p).__name__, getattr(p, "name", ""))

    # 5) Run simulation
    topo.tl.init()
    print("\nEvents scheduled after init:", len(topo.tl.events))
    topo.tl.run()

    print("Simulation finished.")
