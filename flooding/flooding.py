'''
Universidad del Valle de Guatemala
Redes
Bryann Alfaro 19372
Diego de Jesus 19422
Julio Herrera 19402
Lab3 - Algoritmos de enrutamiento
'''

import logging
import sys
from getpass import getpass
from argparse import ArgumentParser
from aioconsole import ainput
import json
import slixmpp
from slixmpp import Iq

async def menu_options():
    print("\nChoose an option:")
    print("1 - Mandar un mensaje")
    print("2 - Salir")
    option = await ainput("Option: ")
    return option


class Flooding(slixmpp.ClientXMPP):

    def __init__(self, jid, password):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0004') # Data Forms
        self.register_plugin('xep_0060') # PubSub
        self.register_plugin('xep_0199') # XMPP Ping

        self.jid = jid
        self.flag = False
        self.run = False
        self.nodes_visited = []

    async def start(self, event):

        self.send_presence()
        await self.get_roster()

        with open('names-default.txt') as f:
            self.json_data = json.load(f)

        with open('topo-default.txt') as f:
            self.topology = json.load(f)

        option_cycle = True
        while option_cycle:
            await self.get_roster()
            option = await menu_options()
            if option == '1':
                await self.flood_send()
            elif option == '2':
                option_cycle = False
                self.disconnect()
            else:
                print("Invalid option")


    #When user sends flood message
    async def flood_send(self):
        print("Ingrese el usuario al que desea enviar el mensaje (sin @alumchat.fun): ")
        user = await ainput("Usuario: ")
        user = user + "@alumchat.fun"
        print("Ingrese el mensaje que desea enviar")
        message = await ainput("Mensaje: ")
        '''Nodo fuente [texto + @]
        - Nodo destino [texto + @]
        - Saltos (nodos) recorridos [numérico]
        - Distancia [numérico]
        - Listado de nodos [texto]
        - Mensaje [texto]'''
        msg = {}
        msg['source'] = self.jid
        msg['destination'] = user
        msg['hops'] = 0
        msg['distance'] = 0
        msg['nodes'] = []
        msg['message'] = message

        try:
            print('Getting key: ',list(self.json_data['config'].keys())[list(self.json_data['config'].values()).index(self.jid)])
            node = list(self.json_data['config'].keys())[list(self.json_data['config'].values()).index(self.jid)]
            receivers_node= self.topology['config'][node]
            print('send message to nodes: ',receivers_node)
            msg['hops'] = msg['hops'] + 1
            msg['nodes'].append(node)
            msg['distance'] = msg['distance'] + 1
            msg['id'] = id(node)
            self.flag = True
            self.nodes_visited.append(node)
            for receiver in receivers_node:
                receiver = self.json_data['config'][receiver]

                self.send_message(mto=receiver, mbody=str(msg))
        except:
            print('No hay nodos')


    #When user receives message
    def message(self, msg):


        if msg['type'] in ('chat', 'normal'):
            msg_f = eval(msg['body'])
            node = list(self.json_data['config'].keys())[list(self.json_data['config'].values()).index(msg_f['source'])]

            if self.flag == False:
                self.nodes_visited.append(node)
                self.flag = True
            else:
                for node in msg_f['nodes']:
                    if node in self.nodes_visited:
                        self.run = True

            if self.run == False:

                if msg_f['destination'] == self.jid:
                    print("LLEGUE A MI DESTINO")
                    print("\nMensaje recibido de: ", msg_f['source'])
                    print("Mensaje para: ", msg_f['destination'])
                    print("Mensaje: ", msg_f['message'])
                    print("Saltos: ", msg_f['hops'])
                    print("Distancia: ", msg_f['distance'])
                    print("Nodos: ", msg_f['nodes'])
                    print("\n")
                else:
                    print("\nMensaje recibido de: ", msg_f['source'])
                    print("Mensaje para: ", msg_f['destination'])
                    print("Mensaje: ", msg_f['message'])
                    print("Saltos: ", msg_f['hops'])
                    print("Distancia: ", msg_f['distance'])
                    print("Nodos: ", msg_f['nodes'])
                    print("\n")
                    print('Getting key: ',list(self.json_data['config'].keys())[list(self.json_data['config'].values()).index(self.jid)])
                    node = list(self.json_data['config'].keys())[list(self.json_data['config'].values()).index(self.jid)]
                    try: #cuando ya no hay mas nodos a quien enviar desde un nodo
                        receivers_node= self.topology['config'][node]
                        print('send message to: ',receivers_node)
                        msg_f['hops'] = msg_f['hops'] + 1
                        msg_f['nodes'].append(node)
                        msg_f['distance'] = msg_f['distance'] + 1
                        for receiver in receivers_node:
                            receiver = self.json_data['config'][receiver]
                            self.send_message(mto=receiver, mbody=str(msg_f))
                        self.nodes_visited.append(node)
                    except:
                        print('No hay nodos')

'''
Class to manage the registration of a user
ARGS:
    jid: username to be registered
    password: password of the user
'''
class RegisterChat(slixmpp.ClientXMPP):
    def __init__(self, jid, password):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("register", self.registration_user)
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0004') # Data Forms
        self.register_plugin('xep_0066') # Out-of-band Data
        self.register_plugin('xep_0077') # In-band Registration

    '''
    Function to handle the session start
    ARGS:
        event: event that is triggered when the session starts
    '''
    async def session_start(self, event):
        self.send_presence()
        await self.get_roster()

    '''
    Function to register an user in an iq request
    ARGS:
        iq: iq request to register a user
    '''
    async def registration_user(self, iq):
        event = self.Iq()
        event['type'] = 'set'
        event['register']['username'] = self.boundjid.user
        event['register']['password'] = self.password
        try:
            await event.send()
            print("Usuario registrado con exito")
        except slixmpp.exceptions.IqError as e:
            logging.error("Could not register: %s", e.iq['error']['text'])
            self.disconnect()
        except slixmpp.exceptions.IqTimeout:
            logging.error("No response from server.")
            self.disconnect()
        finally:
            self.disconnect()
