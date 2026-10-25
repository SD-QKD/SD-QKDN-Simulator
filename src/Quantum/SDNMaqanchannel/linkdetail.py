class Linkdetails():
    def __init__(self,sortedlink):
        self.sorted_link_info=sortedlink
    def get_path_nodes(self, link_ids):
        path_nodes = []
        for link_id in link_ids:
            for link in self.sorted_link_info:
                if link[0] == link_id:
                    source_node = link[1]
                    destination_node = link[2]
                    path_nodes.extend([source_node, destination_node])
                    break
        return path_nodes
