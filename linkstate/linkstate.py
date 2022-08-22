'''
Universidad del Valle de Guatemala
Redes
Bryann Alfaro 19372
Diego de Jesus 19422
Julio Herrera 19402
Lab3 - Algoritmos de enrutamiento
'''


#https://networkx.github.io/documentation/latest/_downloads/networkx_reference.pdf
#https://www.pythonista.io/cursos/py101/escritura-y-lectura-de-archivos
#https://www.geeksforgeeks.org/connectivity-in-a-directed-graph/
from importlib.resources import path
import logging
import sys
from getpass import getpass
from argparse import ArgumentParser
from aioconsole import ainput
import json
import slixmpp
from slixmpp import Iq
import networkx as nx

async def menu_options():
    print("\nChoose an option:")
    print("1 - Mandar un mensaje")
    print("2 - Salir")
    option = await ainput("Option: ")
    return option


class Linkstate(slixmpp.ClientXMPP):

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

        with open('users.txt') as f:
            self.json_data = json.load(f)
        #print(self.json_data['config'])
        self.grafo = nx.Graph() #Se crea un grafo dirigido
        archivo=open("test.txt", "r")
        for i in archivo:
            particion= i.split(" ")
            primerNodo = particion[0]
            segundoNodo = particion[1]
            pesoArista = float(particion [2])

            #add_edge(dato1, dato2, weight)
            self.grafo.add_edge(primerNodo,segundoNodo,weight=pesoArista)

        archivo.close()



        option_cycle = True
        while option_cycle:
            await self.get_roster()
            option = await menu_options()
            if option == '1':
                await self.link_send()
            elif option == '2':
                option_cycle = False
                self.disconnect()
            else:
                print("Invalid option")


    #When user sends link message
    async def link_send(self):
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
        route_table = {}
        try:
            sender_graph = list(self.json_data['config'].keys())[list(self.json_data['config'].values()).index(self.jid)]
            for i in self.grafo.nodes():
                if sender_graph == i:
                    route_table[sender_graph] = {}
                    for j in self.grafo.nodes():
                        path_node = []
                        if sender_graph != j: #No soy el nodo origen
                            path_node  = nx.dijkstra_path(self.grafo, i, j)
                            route_table[sender_graph].update({j:nx.path_weight(self.grafo, path_node,weight='weight')})



            print('route table', route_table)

            sender_graph = list(self.json_data['config'].keys())[list(self.json_data['config'].values()).index(self.jid)]
            receiver_graph =  list(self.json_data['config'].keys())[list(self.json_data['config'].values()).index(user)]
            path = nx.dijkstra_path(self.grafo, sender_graph, receiver_graph)
            print("Ruta ", path)

            for i in range(len(path)):
                if self.jid == self.json_data['config'][path[i]]:
                    msg['nodes'].append(path[i])
                    node = path[i+1]
            msg['hops'] = msg['hops'] + 1

            msg['distance'] = msg['distance'] + self.grafo.get_edge_data(sender_graph, node)['weight']
            receiver = self.json_data['config'][node]

            self.send_message(mto=receiver, mbody=str(msg))
        except:
            print('No hay nodos')


    #When user receives message
    def message(self, msg):


        if msg['type'] in ('chat', 'normal'):

            try:
                msg_f = eval(msg['body'])


                if self.jid != msg_f['destination']:

                    print("El mensaje no es para este usuario")
                    print("Fuente: ", msg_f['source'])
                    print("Destino: ", msg_f['destination'])
                    print("Saltos: ", msg_f['hops'])
                    print("Distancia: ", msg_f['distance'])
                    print("Nodos: ", msg_f['nodes'])
                    print("Mensaje: ", msg_f['message'])
                    route_table = {}
                    sender_graph = list(self.json_data['config'].keys())[list(self.json_data['config'].values()).index(self.jid)]
                    for i in self.grafo.nodes():
                        if sender_graph == i:

                            route_table[sender_graph] = {}
                            for j in self.grafo.nodes():
                                path_node = []

                                if sender_graph != j: #No soy el nodo origen
                                    path_node  = nx.dijkstra_path(self.grafo, i, j)

                                    route_table[sender_graph].update({j:nx.path_weight(self.grafo, path_node,weight='weight')})



                    print('route table', route_table)


                    sender_graph = list(self.json_data['config'].keys())[list(self.json_data['config'].values()).index(self.jid)]
                    receiver_graph =  list(self.json_data['config'].keys())[list(self.json_data['config'].values()).index(msg_f['destination'])]
                    path = nx.dijkstra_path(self.grafo, sender_graph, receiver_graph)
                    print("Ruta ", path)

                    for i in range(len(path)):
                        if self.jid == self.json_data['config'][path[i]]:
                            msg_f['nodes'].append(path[i])
                            node = path[i+1]
                    print("Nodo destino: ", node)
                    msg_f['hops'] = msg_f['hops'] + 1

                    msg_f['distance'] = msg_f['distance'] + self.grafo.get_edge_data(sender_graph, node)['weight']
                    receiver = self.json_data['config'][node]

                    self.send_message(mto=receiver, mbody=str(msg_f))
                else:

                    print("El mensaje es para este usuario")
                    print("Fuente: ", msg_f['source'])
                    print("Destino: ", msg_f['destination'])
                    print("Saltos: ", msg_f['hops'])
                    print("Distancia: ", msg_f['distance'])
                    print("Nodos: ", msg_f['nodes'])
                    print("Mensaje: ", msg_f['message'])
                    route_table = {}
                    sender_graph = list(self.json_data['config'].keys())[list(self.json_data['config'].values()).index(self.jid)]
                    for i in self.grafo.nodes():
                        if sender_graph == i:

                            route_table[sender_graph] = {}
                            for j in self.grafo.nodes():
                                path_node = []
                                if sender_graph != j: #No soy el nodo origen
                                    path_node  = nx.dijkstra_path(self.grafo, i, j)

                                    route_table[sender_graph].update({j:nx.path_weight(self.grafo, path_node,weight='weight')})



                    print('route table', route_table)
            except:
                print("Error")



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
