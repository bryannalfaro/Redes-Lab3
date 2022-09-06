from sleekxmpp import ClientXMPP
from sleekxmpp.xmlstream.stanzabase import ET
from sleekxmpp.exceptions import IqTimeout, IqError
from sleekxmpp.plugins.xep_0004.stanza.form import Form
from node import Node
from ast import literal_eval
import json

SERVER = '@alumchat.fun'
PORT = 5222

class Client(ClientXMPP, Node):
    def __init__(self, node):
        ClientXMPP.__init__(self, node.username + SERVER, node.password)
        Node.__init__(self, node.username, node.password, node.name, node.email, node.neighbors, topology=node.topology, option_login=node.option_login)
        self.registering = False # True if client was created for registration, False if client was created for login
        self.contacts = [] # solo nombres de neighbors
        self.connected = False
        self.users_file = open("users.txt")
        self.users_dict = json.load(self.users_file)["config"]
        self.retrys = 0
        self.add_event_handler('session_start', self.on_session_start)
        self.add_event_handler("register", self.on_register)
        self.add_event_handler("message", self.on_message)
        self.add_event_handler("changed_status", self.on_changed_status)
        self.add_event_handler("connection_failed", self.on_connection_failed)
        self.add_event_handler("failed_auth", self.on_connection_failed)
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0004') # Data forms
        self.register_plugin('xep_0065') # SOCKS5 Bytestreams
        self.register_plugin('xep_0066') # Out-of-band Data
        self.register_plugin('xep_0071') # XHTML-IM
        self.register_plugin('xep_0077') # In-band Registration
        self['xep_0077'].force_registration = True

    def on_session_start(self, event):
        self.set_status('chat', 'available')
        self.connected = True

    # Get the roster (contacts list) and updates the contacts list
    def set_initial_contacts(self):
        if len(self.contacts) == 0:
            for neighbor in self.table:
                self.contacts.append(neighbor.username)

    def on_message(self, msg):
        # if message is error, show error message
        if msg['type'] == 'error':
            print(f"\nError en mensaje: {msg['error']['condition']}")
            return
        # pass the &apos; character to the string '
        msg_obj = msg['body'].replace("&apos;", "'")
        msg_obj = literal_eval(msg_obj)
        if self.option_login == 2:
            node_id = [id for id in self.users_dict.keys() if self.users_dict[id] == msg["from"].bare][0]
        else:
            node_id = msg['from'].bare.split('@')[0]
        if msg_obj["type"] == "message":
            sender_neighbor = self.get_node_by_username(node_id)
            # verificar si el mensaje es para mi
            node_username = [self.users_dict[username] for username in self.users_dict if self.users_dict[username] == self.users_dict[msg_obj["to"]]][0]
            if node_username.split('@')[0].lower() == self.username.lower():
                msg_obj["hops"] = int(msg_obj["hops"]) + 1
                msg_obj["distance"] = int(msg_obj["distance"]) + int(sender_neighbor.weight)
                msg_obj["nodes"] = msg_obj["nodes"] + "," + sender_neighbor.username if msg_obj["nodes"] != "" else sender_neighbor.username
                print(f"\n{msg_obj['from']} dice: {msg_obj['message']}")
                print(f"Hizo {msg_obj['hops']} saltos pasando por {msg_obj['nodes']} con una distancia de {msg_obj['distance']}")
            # verificar si ya se paso por mi nodo (si está más de dos veces)
            elif msg_obj["nodes"].lower().split(",").count(self.username.lower()) > 1:
                print("\nEste mensaje ya paso por mi nodo")
            # si no es para mi, reenviar
            else:
                self.send_message_to_user(msg_obj["to"], msg_obj, sender_neighbor=sender_neighbor)
        elif msg_obj["type"] == self.topology:
            new_table = literal_eval(msg_obj["message"])

            if self.update_table_bellman_ford(new_table, node_id):
                self.retrys = 0
            else:
                self.retrys += 1

    # send table to neigbors
    def share_table(self):
        if self.retrys < 5:
            for contact in self.contacts:
                self.send_message_to_user(contact, self.get_table(), new_message=True, ptype=self.topology)

    # Send message and updates the chat history of the contact
    def send_message_to_user(self, jid, message, new_message=False, ptype="message", sender_neighbor=None):
        hop_node = self.get_node_by_username(self.get_node_by_username(jid).hop)
        if new_message:
            packet = {
                "from": self.username,
                "to": jid,
                "type": ptype,
                "hops": 0,
                "distance": 0,
                "nodes": "",
                "message": message
            }
            message = json.dumps(packet)
        else:
            message["hops"] = int(message["hops"]) + 1
            message["distance"] = int(message["distance"]) + int(sender_neighbor.weight)
            message["nodes"] = message["nodes"] + "," + sender_neighbor.username if message["nodes"] != "" else sender_neighbor.username
            print(f"\nReenviando mensaje de {message['from']} a {jid} por medio de {hop_node.username}")
            print(f"Lleva {message['hops']} saltos pasando por {message['nodes']} con una distancia de {message['distance']}")
            message = json.dumps(message)
        if self.option_login == 2:
            node_username = [self.users_dict[username] for username in self.users_dict if self.users_dict[username] == self.users_dict[hop_node.username]][0]
        else:
            node_username = hop_node.username + SERVER
        self.send_message(mto=node_username, mbody=message, mtype='chat')

    # TODO: cuando un router se desconecta, actualizar la tabla
    def on_changed_status(self, presence):
        username = presence['from'].bare
        #print(self.client_roster.presence[username]['status'])
        print(f'\n{username} ha cambiado su estado a {self.client_roster.presence[username]["status"]}')

    # Connect to the server, used on login and register
    def login(self):
        result = self.connect((SERVER[1:], PORT), use_ssl=False, use_tls=False)
        if result:
            self.process()
            return True
        return False

    # Show error when connection failed
    def on_connection_failed(self, error):
        print('\nError de conexión: %s' % error)
        if not self.connected:
            print("Error al tratar de conectar")
            self.disconnect()
            self.registering = True
        else:
            self.connected = False
            self.disconnect()

    # Set a new presence status and message
    def set_status(self, show, status):
        self.send_presence(pshow=show, pstatus=status)

    # Register a new user in the server
    def on_register(self, event):
        if self.registering:
            print("Registrando nodo")
            iq = self.Iq()
            iq['type'] = 'set'
            iq['register']['username'] = self.boundjid.user
            iq['register']['password'] = self.password
            iq['register']['name'] = self.name
            iq['register']['email'] = self.email
            try:
                iq.send(now=True)
            except IqError as e:
                print(e.iq)
            except IqTimeout:
                print('Tiempo de espera agotado')
