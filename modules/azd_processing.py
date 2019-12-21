def load_azd_users(client, migrationUPNs=None):

    azdUsers = []
    users = client.list_users()

    while True:

        for user in users.graph_users:
            if user.origin == 'aad':
                if migrationUPNs:
                    if user.principal_name.lower() in migrationUPNs:
                        azdUsers.append(user)
                else:
                    azdUsers.append(user)

        if users.continuation_token:
            users = client.list_users(
                continuation_token=users.continuation_token)
        else:
            break

    return azdUsers
