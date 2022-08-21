from sleekxmpp import ClientXMPP
from sleekxmpp.xmlstream.stanzabase import ET
from sleekxmpp.exceptions import IqTimeout, IqError
from sleekxmpp.plugins.xep_0004.stanza.form import Form

SERVER = '@alumchat.fun'
PORT = 5222

class Client(ClientXMPP):
    def __init__(self, jid, password, Name=None, Email=None, registering=False):
        ClientXMPP.__init__(self, jid, password)
        self.password = password
        self.Name = Name
        self.Email = Email
        self.registering = registering # True if client was created for registration, False if client was created for login
        self.contacts = []
        self.connected = False
        self.add_event_handler('session_start', self.on_session_start)
        self.add_event_handler("register", self.on_register)
        self.add_event_handler("presence_subscribe", self.on_presence_subscribe)
        self.add_event_handler("presence_unsubscribe", self.on_presence_unsubscribe)
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
        self.update_roster(firts_time=True)
        self.connected = True

    def on_message(self, msg):
        print(msg)

    # Get the roster (contacts list) and updates the contacts list
    def update_roster(self, firts_time=False):
        try:
            roster = self.get_roster()
            contacts_roster = []
            for jid in roster['roster']['items'].keys():
                contact = jid
                for k, v in roster['roster']['items'][jid].items():
                    print(k, v)
                contacts_roster.append(contact)
            if firts_time:
                self.contacts = contacts_roster
            else:
                self.update_contacts(contacts_roster)
        except IqError as e:
            print(e.iq)
        except IqTimeout:
            print('Tiempo de espera agotado')

    # Send message and updates the chat history of the contact
    def send_message_to_user(self, jid, message):
        self.send_message(mto=jid+SERVER, mbody=message, mtype='chat')
        # TODO: tal vez guardar el historial de mensajes

    # Show notification when someone added you as a contact
    def on_presence_subscribe(self, presence):
        username = presence['from'].bare
        print(f'\n{username} quiere agregarte a tu lista de contactos')

    # Show notification when someone removed you from the contact list
    def on_presence_unsubscribe(self, presence):
        username = presence['from'].bare
        print(f'\n{username} te ha eliminado de su lista de contactos')

    # TODO: cuando un router se desconecta, actualizar la tabla
    def on_changed_status(self, presence):
        username = presence['from'].bare
        print(self.client_roster.presence[username]['status'])
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

    # Add a new contact to the contact list if it doesn't exist
    def add_contact(self, jid, subscription_meessage):
        can_add_contact = True
        for contact in self.contacts:
            if contact == jid:
                print('Este contacto ya existe')
                can_add_contact = False
                continue
        if can_add_contact:
            self.send_presence(
                pto=jid + SERVER, pstatus=subscription_meessage, ptype="subscribe")

    # Get the roster (contacts list) and search for contacts that match the jid
    def get_contact_by_jid(self, jid):
        self.update_roster()
        groups = self.client_roster.groups()
        contacts = []
        for group in groups:
            for user in groups[group]:
                contact = jid
                # if user string icludes jid
                if user.find(jid) != -1:
                    user_roster = self.client_roster[user]
                    #contact.set_info('Name', user_roster['name'])
                    #contact.set_info('Subscription', user_roster['subscription'])
                    connected_roster = self.client_roster.presence(user)
                    # Presence info set (show, status)
                    if connected_roster.items():
                        for _, state in connected_roster.items():
                            for k, v in state.items():
                                print(k, v)
                    contacts.append(contact)
        print("\nContactos:")
        for contact in contacts:
            print(contact)
        return contacts

    # show all the users in the server or show users that match the jid
    def get_contacts(self, jid='*'):
        iq = self.get_search_iq(jid)
        users = []
        try:
            search_result = iq.send()
            search_result = ET.fromstring(str(search_result))
            for query in search_result:
                for x in query:
                    for item in x:
                        values = {}
                        for field in list(item):
                            for value in list(field):
                                values[field.attrib['var']] = value.text
                        if values != {}:
                            #users.append(Contact(
                            #    jid=values['jid'], Email=values['Email'], Username=values['Username'], Name=values['Name']))
                            users.append(values["jid"])
        except IqError as e:
            print(e.iq)
        except IqTimeout:
            print('Tiempo de espera agotado')
        print("\nUsuarios en el servidor:")
        for user in users:
            print(user)
        return users

    # Creates an Iq with the specific attributes
    def create_iq(self, **kwargs):
        iq = self.Iq()
        iq.set_from(self.boundjid.full)
        for k, v in kwargs.items():
            iq[k] = v
        return iq

    # Custom Iq for search users
    def get_search_iq(self, search_value='*'):
        iq = self.create_iq(type="set", id="search_result",
                            to="search." + self.boundjid.domain)
        form = Form()
        form.set_type("submit")
        form.add_field(
            var='FORM_TYPE',
            type='hidden',
            value='jabber:iq:search'
        )
        form.add_field(
            var='Username',
            type='boolean',
            value=1
        )
        form.add_field(
            var='search',
            type='text-single',
            value=search_value
        )
        query = ET.Element('{jabber:iq:search}query')
        query.append(form.xml)
        iq.append(query)
        return iq

    # Receive a new list of contacts and update the self.contacts list, adding new contacts and updating existing ones.
    def update_contacts(self, contacts):
        for contact in self.contacts:
            for new_contact in contacts:
                if contact == new_contact:
                    # TODO: Update router info
                    break
                else:
                    self.contacts.append(new_contact)

    # Register a new user in the server
    def on_register(self, event):
        if self.registering:
            print("Registrando nodo")
            iq = self.Iq()
            iq['type'] = 'set'
            iq['register']['username'] = self.boundjid.user
            iq['register']['password'] = self.password
            iq['register']['name'] = self.Name
            iq['register']['email'] = self.Email
            try:
                iq.send(now=True)
            except IqError as e:
                print(e.iq)
            except IqTimeout:
                print('Tiempo de espera agotado')

    # Remove a contact from your contact list
    def delete_contact(self, jid):
        self.del_roster_item(jid+SERVER)
        for contact in self.contacts:
            if contact == jid:
                self.contacts.remove(contact)
                break