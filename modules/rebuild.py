from azure.devops.v6_0.graph.models import GraphSubjectQuery, GraphUserCreationContext, GraphUserUpdateContext, Avatar
from azure.devops.v6_0.member_entitlement_management.models import AccessLevel, UserEntitlement, GraphUser, Extension
from azure.graphrbac.models import CheckGroupMembershipParameters
from azure.mgmt.authorization.models import RoleAssignmentCreateParameters
from modules.aad_processing import *
from modules.azd_processing import *
from modules.capture import read_capture
from modules.clients import get_azd_graph_client, get_graph_rbac_client, get_azure_subscription_client, get_aad_graph_token
from modules.config import load_config
from modules.logging import *
import json
import time
import uuid

AAD_USER_SEARCH_RETRY_COUNT = 10
AAD_USER_SEARCH_RETRY_WAIT = 30
AZD_GRAPH_INVITE_URL = 'https://graph.microsoft.com/v1.0/invitations'
AZD_GRAPH_OBJECT_URL = 'https://graph.windows.net/{}/directoryObjects/{}'


def process(aad: bool, azd: bool):

    capture = read_capture()

    if not capture:
        printWarning('nothing to process')
        return

    # 1. invite in Azure Active Directory
    if aad:

        graph_token = get_aad_graph_token()

        for u in capture['records']:

            # check if user needs to be invited
            user_found = False

            with get_graph_rbac_client() as az_graph_rbac_client:

                users = az_graph_rbac_client.users.list(
                    filter="mail eq '{}'".format(u['targetUPN']))

                if users:
                    for user in users:
                        if user.mail == u['targetUPN']:
                            user_found = True

            if not user_found:
                # invite user to AAD directly with Graph API (as of 2019-08 not yet available in Python SDKs)
                printInfo('inviting user {} in AAD'.format(u['targetUPN']))

                invite = {
                    "invitedUserDisplayName": u['aad_display_name'],
                    "invitedUserEmailAddress": u['targetUPN'],
                    "inviteRedirectUrl": "https://portal.azure.com",
                    "invitedUserType": "Member",
                    "sendInvitationMessage": True
                }

                postBody = json.dumps(invite)
                response = postAPI(
                    url=AZD_GRAPH_INVITE_URL, body=postBody, token=graph_token)
                printInfo(response)


        for u in capture['records']:

            # retry until Graph RBAC client picks up user invited directly over API
            printInfo(
                'setting authorizations for user {} in AAD'.format(u['targetUPN']))

            user_found = False
            retry_count = 0

            while not user_found and retry_count < AAD_USER_SEARCH_RETRY_COUNT:

                if retry_count > 0:
                    printInfo('retry {} searching user {} in AAD'.format(
                        retry_count, u['targetUPN']))
                    time.sleep(AAD_USER_SEARCH_RETRY_WAIT)

                retry_count += 1

                with get_graph_rbac_client() as az_graph_rbac_client:

                    users = az_graph_rbac_client.users.list(
                        filter="mail eq '{}'".format(u['targetUPN']))

                    if users:
                        for user in users:
                            if user.mail == u['targetUPN']:
                                user_found = True
                                user_url = AZD_GRAPH_OBJECT_URL.format(
                                    az_graph_rbac_client.config.tenant_id, user.object_id)

                                for m in u['aad_member_ships']:
                                    existing_membership = az_graph_rbac_client.groups.is_member_of(
                                        CheckGroupMembershipParameters(group_id=m['object_id'], member_id=user.object_id))
                                    if not existing_membership or not existing_membership.value:
                                        print(
                                            'adding membership for {}'.format(m['name']))
                                        az_graph_rbac_client.groups.add_member(
                                            group_object_id=m['object_id'], url=user_url)

                                credentials, _ = get_aad_credentials()

                                for ra in u['aad_role_assignments']:
                                    mgmt_client = get_azure_authorization_management_client(
                                        ra['subscription_id'])
                                    for re in ra['resources']:
                                        existing_assignments = mgmt_client.role_assignments.list_for_scope(
                                            scope=re['scope'], filter="principalId eq '{}'".format(user.object_id))
                                        is_existing_assignment = False
                                        for ea in existing_assignments:
                                            is_existing_assignment = True
                                        if not is_existing_assignment:
                                            print('adding assignment for {}'.format(
                                                re['scope']))
                                            parameters = RoleAssignmentCreateParameters(
                                                role_definition_id=re['role'], principal_id=user.object_id)
                                            mgmt_client.role_assignments.create(
                                                scope=re['scope'], role_assignment_name=str(uuid.uuid4()), parameters=parameters)

            if not user_found:
                printException(
                    'user with UPN {} not found in AAD'.format(u['targetUPN']))

    # 2. create Azure DevOps

    if azd:

        config = load_config()

        for u in capture['records']:
            if 'azd' in u:
                for azd_account in u['azd']:

                    azd_account_config = config['azdAccounts'][azd_account]
                    user_account = u['azd'][azd_account]

                    azd_entitlement_client = get_azd_entitlement_client(
                        azd_account_config)
                    azd_graph_client = get_azd_graph_client(azd_account_config)
                    azd_graph_client.config.enable_http_logger = True

                    printInfo('creating graph user {} in AzD {}'.format(
                        u['targetUPN'], azd_account))
                        
                    new_graph_user = GraphUserPrincipalNameCreationContext(
                        storage_key=u['targetUPN'], principal_name=u['targetUPN'])

                    # assemble list of groups on 
                    groups = [m['descriptor'] for m in user_account['azd_member_ships'] if azd_account+']\\' in m['name']]

                    graph_user = azd_graph_client.create_user(new_graph_user,group_descriptors=groups)
                    printInfo(graph_user)

                    if graph_user.principal_name != u['targetUPN']:
                        printException(
                            'AzD graph user created does not have matching principal name')

                    if 'azd_account_license_type' in user_account and 'azd_msdn_license_type' in user_account:
                        printInfo('creating entitlement {} in AzD {}'.format(
                            u['targetUPN'], azd_account))
                        new_access_level = AccessLevel(
                            account_license_type=user_account['azd_account_license_type'], msdn_license_type=user_account['azd_msdn_license_type'])
                        new_extensions = []
                        if 'azd_extensions' in user_account:
                            for x in user_account['azd_extensions']:
                                if x:
                                    new_extensions.append(Extension(
                                        assignment_source=x['assignment_source'], id=x['id'], name=x['name'], source=x['source']))
                        new_user_entitlement = UserEntitlement(
                            access_level=new_access_level, extensions=new_extensions, user=graph_user)
                        entitlement = azd_entitlement_client.add_user_entitlement(
                            new_user_entitlement)
                        printInfo(entitlement)

                    if 'azd_member_ships' in user_account:
                        for m in user_account['azd_member_ships']:
                            printInfo('adding membership for graph user {} to {}'.format(
                                u['targetUPN'], m['name']))
                            member_ship = azd_graph_client.add_membership(
                                subject_descriptor=graph_user.descriptor, container_descriptor=m['descriptor'])
                            printInfo(member_ship)

                    if 'azd_avatar' in u:
                        azd_graph_client.set_avatar(
                            subject_descriptor=graph_user.descriptor, avatar=user_account['azd_avatar'])


# --------------------------------------------------------------------------------
# class extension until defined in SDK

class GraphUserOriginIdCreationContext(GraphUserCreationContext):

    _attribute_map = {
        'origin_id': {'key': 'originId', 'type': 'str'}
    }

    def __init__(self, origin_id=None):
        super(GraphUserOriginIdCreationContext, self).__init__()
        self.origin_id = origin_id


class GraphUserOriginIdUpdateContext(GraphUserUpdateContext):

    _attribute_map = {
        'origin_id': {'key': 'originId', 'type': 'str'}
    }

    def __init__(self, origin_id=None):
        super(GraphUserOriginIdUpdateContext, self).__init__()
        self.origin_id = origin_id


class GraphUserPrincipalNameCreationContext(GraphUserCreationContext):

    _attribute_map = {
        'storage_key': {'key': 'storageKey', 'type': 'str'},
        'principal_name': {'key': 'principalName', 'type': 'str'}
    }

    def __init__(self, storage_key=None, principal_name=None):
        super(GraphUserPrincipalNameCreationContext, self).__init__()
        self.principal_name = principal_name

class GraphUserMailAddressCreationContext(GraphUserCreationContext):

    _attribute_map = {
        'mail_address': {'key': 'mailAddress', 'type': 'str'}
    }

    def __init__(self, mail_address=None):
        super(GraphUserMailAddressCreationContext, self).__init__()
        self.mail_address = mail_address


class GraphUserPrincipalNameUpdateContext(GraphUserUpdateContext):

    _attribute_map = {
        'principal_name': {'key': 'principalName', 'type': 'str'}
    }

    def __init__(self, principal_name=None):
        super(GraphUserPrincipalNameUpdateContext, self).__init__()
        self.principal_name = principal_name

