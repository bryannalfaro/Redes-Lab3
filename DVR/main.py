from multiprocessing.connection import wait
from time import sleep
from dvr_client import Client

SERVER = '@alumchat.fun'

is_authenticated = False

# Definiendo nodo
node = {
    "username": "group5_dvr_%",
    "password": "123",
    "name": "group5_dvr_%",
    "email": "group5_dvr_%@alumchat.fun"
}

node_id = input("Ingrese el identificador del nodo (ej. A, B, C, etc): ")
node["username"] = node["username"].replace('%', node_id)
node["name"] = node["name"].replace('%', node_id)
node["email"] = node["email"].replace('%', node_id)

# Logueando / registrando
node_client = Client(node["username"] + SERVER, node["password"], node["name"], node["email"])
if node_client.login():
    pass
else:
    print("No se pudo conectar")

retrys = 0
while not node_client.connected and retrys < 5:
    sleep(3)
    if not node_client.connected:
        print("Reintentando conectar...")
        if node_client.registering:
            node_client.login()
        retrys += 1

print("Nodo conectado")