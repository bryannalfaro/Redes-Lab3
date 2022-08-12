import logging
import sys
from getpass import getpass
from argparse import ArgumentParser

import slixmpp

import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class Flooding(slixmpp.ClientXMPP):

    def __init__(self, jid, password):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0004') # Data Forms
        self.register_plugin('xep_0060') # PubSub
        self.register_plugin('xep_0199') # XMPP Ping

    async def start(self, event):

        self.send_presence()
        await self.get_roster()

    def message(self, msg):

        if msg['type'] in ('chat', 'normal'):
            msg.reply("Thanks for sending\n%(body)s" % msg).send()


if __name__ == '__main__':

    parser = ArgumentParser(description=Flooding.__doc__)

    parser.add_argument("-q", "--quiet", help="set logging to ERROR",
                        action="store_const", dest="loglevel",
                        const=logging.ERROR, default=logging.INFO)
    parser.add_argument("-d", "--debug", help="set logging to DEBUG",
                        action="store_const", dest="loglevel",
                        const=logging.DEBUG, default=logging.INFO)


    parser.add_argument("-j", "--jid", dest="jid",
                        help="JID to use")
    parser.add_argument("-p", "--password", dest="password",
                        help="password to use")

    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel,
                        format='%(levelname)-8s %(message)s')


    flag = True
    while flag:
        print("Bienvenido al programa")
        print("1. Iniciar sesion")
        print("2. Registrarse")
        print("3. Salir")
        opcion = input("Ingrese una opcion: ")

        if opcion == "1":
            user = input("Ingresa tu username: ")
            print("Ingresa tu password")
            password = getpass()

            xmpp = Flooding(args.jid, args.password)
            xmpp.connect()
            xmpp.process()
            flag = False
        elif opcion == "2":
            print("Registrandose")
            xmpp = Flooding(args.jid, args.password)
            xmpp.connect()
            xmpp.process()
            flag = False
        elif opcion == "3":
            print("Saliendo")
            flag = False