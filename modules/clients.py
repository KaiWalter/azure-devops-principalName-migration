from azure.common.credentials import ServicePrincipalCredentials
from azure.devops.connection import Connection
from azure.devops.credentials import BasicAuthentication
from azure.graphrbac import GraphRbacManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.subscription import SubscriptionClient
from modules.config import load_config
from msrestazure.azure_active_directory import AdalAuthentication
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD
import adal


def get_aad_credentials(resource=None):

    config = load_config()

    credentials = ServicePrincipalCredentials(
        client_id=config['aadAccount']['appId'],
        secret=config['aadAccount']['password'],
        tenant=config['aadAccount']['tenant'],
        resource=resource
    )

    return credentials, config['aadAccount']['tenant']


def get_graph_rbac_client():

    credentials, tenant = get_aad_credentials('https://graph.windows.net')

    return GraphRbacManagementClient(credentials, tenant)


def get_azure_subscription_client():

    config = load_config()

    LOGIN_ENDPOINT = AZURE_PUBLIC_CLOUD.endpoints.active_directory
    RESOURCE = AZURE_PUBLIC_CLOUD.endpoints.management

    context = adal.AuthenticationContext(
        LOGIN_ENDPOINT + '/' + config['aadAccount']['tenant'])
    credentials = AdalAuthentication(
        context.acquire_token_with_client_credentials,
        RESOURCE,
        config['aadAccount']['appId'],
        config['aadAccount']['password']
    )

    return SubscriptionClient(credentials)


def get_azure_authorization_management_client(subscription_id):

    config = load_config()

    LOGIN_ENDPOINT = AZURE_PUBLIC_CLOUD.endpoints.active_directory
    RESOURCE = AZURE_PUBLIC_CLOUD.endpoints.management

    context = adal.AuthenticationContext(
        LOGIN_ENDPOINT + '/' + config['aadAccount']['tenant'])
    credentials = AdalAuthentication(
        context.acquire_token_with_client_credentials,
        RESOURCE,
        config['aadAccount']['appId'],
        config['aadAccount']['password']
    )

    return AuthorizationManagementClient(credentials, subscription_id)


def get_azd_graph_client(account):
    personal_access_token = account['pat']

    credentials = BasicAuthentication('', personal_access_token)
    connection = Connection(base_url=account['url'], creds=credentials)

    return connection.clients_v6_0.get_graph_client()


def get_azd_entitlement_client(account):
    personal_access_token = account['pat']

    credentials = BasicAuthentication('', personal_access_token)
    connection = Connection(base_url=account['url'], creds=credentials)

    return connection.clients_v6_0.get_member_entitlement_management_client()


def get_azd_workitem_tracking_client(account):
    personal_access_token = account['pat']

    credentials = BasicAuthentication('', personal_access_token)
    connection = Connection(base_url=account['url'], creds=credentials)

    return connection.clients_v6_0.get_work_item_tracking_client()
