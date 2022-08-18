import logging
from multiprocessing import forkserver
import sys
from getpass import getpass
from argparse import ArgumentParser
from flooding import Flooding, RegisterChat

import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
            password = getpass("Ingresa tu password: ")

            xmpp = Flooding(user, password)
            xmpp.connect(disable_starttls=True)
            xmpp.process(forever=False)
            flag = False
        elif opcion == "2":
            print("Registrandose")
            user = input("Ingresa tu username: ")
            password = getpass("Ingresa tu password: ")
            xmpp = RegisterChat(user,password)
            xmpp.connect(disable_starttls=True)
            xmpp.process(forever=False)
            xmpp['xep_0077'].force_registration = True
            flag = False
        elif opcion == "3":
            print("Saliendo")
            flag = False