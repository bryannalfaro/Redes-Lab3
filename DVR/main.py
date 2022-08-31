from time import sleep
from node import Node
from dvr_client import Client
import json
import threading

SERVER = "@alumchat.fun"
BASENAME = "group5_dvr_%"
is_authenticated = False

# Read json
file = open("topology.json")
nodes = json.load(file)

node_id = input("Ingrese el identificador del nodo (ej. A, B, C, etc): ")
find_node = lambda id: [ i for i in nodes if i["id"] == id ]
node = find_node(node_id)[0]
name = BASENAME.replace("%", node["id"])
node = Node(name, "123", name, f'{name}{SERVER}', node["neighbors"])

# Logueando / registrando
node_client = Client(node)
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

def share_table_interval(stop):
    while True:
        if stop():
            break
        node_client.share_table()
        sleep(5)

print("Nodo conectado")
node_client.update_roster()
# share_table on interval using threading
stop_thread = False
thread = threading.Thread(target=share_table_interval, args=(lambda: stop_thread,))
thread.start()

menu = """
1. Ver tabla
2. ver vecinos
3. enviar mensaje
4. salir
"""

option = ""
while option != "4":
    print(menu)
    option = input("Ingrese una opcion: ")
    if option == "1":
        print(node_client.print_table())
    elif option == "2":
        print()
        for contact in node_client.contacts:
            print(contact)
    elif option == "3":
        to = input("Ingrese el id del nodo destinatario: ")
        msg = input("Ingrese el mensaje: ")
        node_client.send_message_to_user(f'{node_client.username[:-1]}{to}', msg, new_message=True)
    elif option == "4":
        print("Saliendo...")
        stop_thread = True
        node_client.disconnect()
        thread.join()
        print("Saliendo...")
    else:
        print("Opcion invalida")
        print("\n")
        continue
    print("\n")
    continue
