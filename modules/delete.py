from modules.aad_processing import *
from modules.azd_processing import *
from modules.capture import read_capture
from modules.clients import get_azd_graph_client, get_graph_rbac_client, get_azure_subscription_client
from modules.config import load_config
from modules.logging import *

def process(aad: bool, azd: bool):

    capture = read_capture()

    if not capture:
        printWarning('nothing to process')
        return

    config = load_config()

    # 1. delete Azure DevOps

    if azd:

        for u in capture['records']:
            if 'azd' in u:
                for azd_account in u['azd']:
                    azd_account_config = config['azdAccounts'][azd_account]
                    azd_entitlement_client = get_azd_entitlement_client(
                        azd_account_config)
                    azd_entitlement_client.config.enable_http_logger = True
                    azd_graph_client = get_azd_graph_client(azd_account_config)
                    azd_graph_client.config.enable_http_logger = True
                    user_check = None
                    entitlement_check = None
                    user_account = u['azd'][azd_account]
                    if user_account and azd_account_config:
                        try:
                            user_check = azd_graph_client.get_user(
                                user_descriptor=user_account['azd_descriptor'])
                            entitlement_check = azd_entitlement_client.get_user_entitlement(
                                user_id=user_account['azd_id'])
                        except:
                            pass
                    if entitlement_check:
                        printInfo('deleting entitlement {} from AzD {}'.format(
                            user_account['azd_UPN'], azd_account))
                        azd_entitlement_client.delete_user_entitlement(
                            user_id=user_account['azd_id'])
                    if user_check:
                        printInfo('deleting {} from AzD {}'.format(
                            user_account['azd_UPN'], azd_account))
                        azd_graph_client.delete_user(
                            user_descriptor=user_account['azd_descriptor'])

    # 2. delete in Azure Active Directory

    if aad:
        az_graph_rbac_client = get_graph_rbac_client()

        for u in capture['records']:
            if 'aad_object_id' in u:
                try:
                    user_check = az_graph_rbac_client.users.get(
                        upn_or_object_id=u['aad_object_id'])
                except:
                    user_check = None
                if user_check:
                    printInfo('deleting {} from AAD'.format(u['aad_UPN']))
                    resp = az_graph_rbac_client.users.delete(
                        upn_or_object_id=u['aad_object_id'], raw=True)
                    printInfo(resp)
