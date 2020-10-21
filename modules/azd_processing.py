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


def load_azd_entitlements(client, azdUsers):

    azdEntitlements = []

    for user in azdUsers:

        user_entitlements = client.search_user_entitlements(filter=f"name eq '{user.principal_name}'")

        for member in user_entitlements.members:

            if user.principal_name == member.user.principal_name:
                azdEntitlements.append({
                    'upn': user.principal_name,
                    'id': member.id,
                    'extensions': member.extensions,
                    'account_license_type': member.access_level.account_license_type,
                    'msdn_license_type': member.access_level.msdn_license_type
                })
                break

    return azdEntitlements


def load_azd_memberships(client, azdUsers):

    azdMemberships = []

    for user in azdUsers:

        membership = {
            'upn': user.principal_name,
            'object_id': user.origin_id,
            'descriptor': user.descriptor,
            'groups': []
        }

        groups = client.list_memberships(
            subject_descriptor=user.descriptor, direction='Up')

        for g in groups:
            group = client.get_group(group_descriptor=g.container_descriptor)
            membership['groups'].append({
                'name': group.principal_name,
                'descriptor': group.descriptor
            })

        azdMemberships.append(membership)

    return azdMemberships


def load_azd_avatars(client, azdUsers):

    azdAvatars = []

    for user in azdUsers:

        avatar_entry = {
            'upn': user.principal_name,
            'descriptor': user.descriptor,
            'avatar': {}
        }

        try:
            payload = client.get_avatar(
                subject_descriptor=user.descriptor)

            if payload:
                if not payload.is_auto_generated:
                    avatar_entry['avatar'] = {
                        "size": payload.size, "value": payload.value}

            azdAvatars.append(avatar_entry)

        except:
            pass

    return azdAvatars

