from azure.mgmt.subscription import SubscriptionClient
from modules.clients import *

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


def load_aad_memberships(client, aadUsers):

    aadMemberships = []

    for user in aadUsers:

        membership = {
            'upn': user.mail,
            'object_id': user.object_id,
            'display_name': user.display_name,
            'groups': []
        }

        groups = client.users.get_member_groups(
            object_id=user.object_id, security_enabled_only=False)
        for g in groups:
            group = client.groups.get(object_id=g)
            membership['groups'].append({
                'name': group.display_name,
                'object_id': group.object_id
            })

        aadMemberships.append(membership)

    return aadMemberships


def load_aad_role_assignments(client: SubscriptionClient, aadUsers):

    role_assignments = []

    subscriptions = client.subscriptions.list()

    for subscription in subscriptions:

        credentials, _ = get_aad_credentials()

        mgmt_client = get_azure_authorization_management_client(
            subscription.subscription_id)

        for user in aadUsers:

            role_assignment = {
                'upn': user.mail,
                'subscription_id': subscription.subscription_id,
                'resources': []
            }

            assignments = mgmt_client.role_assignments.list(
                filter="principalId eq '{}'".format(user.object_id))

            for assignment in assignments:
                if assignment.principal_type == 'User' and assignment.principal_id == user.object_id:

                    role_assignment['resources'].append({
                        'scope': assignment.scope,
                        'role': assignment.role_definition_id
                    })

            if len(role_assignment['resources']) > 0:
                role_assignments.append(role_assignment)

    return role_assignments

