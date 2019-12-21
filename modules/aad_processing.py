def load_aad_users(client, migrationUPNs=None):

    aadUsers = []

    if migrationUPNs:

        for upn in migrationUPNs:
            users = client.users.list(filter="mail eq '{}'".format(upn))
            if users:
                for user in users:
                    if user.mail.lower() == upn.lower():
                        aadUsers.append(user)

    else:

        aadUsers = client.users.list()

    return aadUsers

