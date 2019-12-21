from azure.common.credentials import ServicePrincipalCredentials
from azure.devops.connection import Connection
from azure.devops.credentials import BasicAuthentication
from azure.graphrbac import GraphRbacManagementClient
from modules.config import load_config

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

def get_azd_graph_client(account):
    personal_access_token = account['pat']

    credentials = BasicAuthentication('', personal_access_token)
    connection = Connection(base_url=account['url'], creds=credentials)

    return connection.clients_v6_0.get_graph_client()

