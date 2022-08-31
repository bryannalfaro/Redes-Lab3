import json

class Node():
    def __init__(self, username, password, name, email, neighbors=[], weight=0, hop=None):
        self.username = username
        self.password = password
        self.name = name
        self.email = email
        self.weight = weight
        self.hop = hop
        self.neighbors = neighbors # no son nodos
        self.table = []
        for neighbor in self.neighbors:
            node = Node(f'{username[:-1]}{neighbor["id"]}',
                        password,
                        f'{username[:-1]}{neighbor["id"]}',
                        f'{username[:-1]}{neighbor["id"]}@{email.split("@")[1]}',
                        weight=neighbor["weight"],
                        hop=f'{username[:-1]}{neighbor["id"]}')
            self.table.append(node)

    def get_table(self):
        table_str = []
        for neighbor in self.table:
            table_str.append(json.loads(str(neighbor)))
        return str(table_str)

    def print_table(self):
        print()
        for neighbor in self.table:
            print(f'{neighbor.username} - Peso acumulado: {neighbor.weight} - Salto Para llegar a él: {neighbor.hop}')

    def update_table_bellman_ford(self, table, hop):
        for neighbor in table:
            if neighbor["username"].lower() == self.username.lower():
                continue
            new_node = Node(neighbor["username"],
                            neighbor["password"],
                            neighbor["name"],
                            neighbor["email"],
                            weight=int(neighbor["weight"]) + self.get_node_by_username(hop).weight,
                            hop=hop)
            if new_node.username not in [n.username for n in self.table]:
                self.table.append(new_node)
            else:
                for node in self.table:
                    if node.username == new_node.username:
                        hop_node = self.get_node_by_username(hop)
                        new_weight = hop_node.weight + new_node.weight
                        if new_weight < node.weight:
                            node.weight = new_weight
                            node.hop = hop
        return self.table

    def get_node_by_username(self, username):
        for node in self.table:
            if node.username.lower() == username.lower():
                return node
        return None

    def __str__(self):
        return json.dumps({
            "username": self.username,
            "password": self.password,
            "name": self.name,
            "email": self.email,
            "weight": self.weight,
            "hop": self.hop,
            "neighbors": self.neighbors,
            "table": self.table
        })
