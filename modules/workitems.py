from azure.devops.v6_0.work_item_tracking.models import Wiql, JsonPatchOperation
from modules.capture import extract_migration_upns, read_capture
from modules.clients import get_azd_workitem_tracking_client
from modules.config import load_config
from modules.logging import *

MAX_WORK_ITEMS_BATCH_PATH = 1000


def process(upn_file: str, users: str):

    config = load_config()

    # check if migration pair is specified
    if upn_file or users:
        azdAccounts = []  # when empty, all accounts are processed
        sourceUPNs, targetUPNs = extract_migration_upns(
            upn_file, users)
    else:
        # when not specified read from file capture
        azdAccounts = []
        sourceUPNs = []
        targetUPNs = []
        capture = read_capture()

        if not capture:
            printWarning('nothing to process')
            return

        for u in capture['records']:
            if u['azd']:
                for azd_account in u['azd']:

                    azd_account_config = config['azdAccounts'][azd_account]
                    user_account = u['azd'][azd_account]
                    if user_account['azd_from_workitem_user'] and user_account['azd_to_workitem_user']:
                        azdAccounts.append(azd_account)
                        sourceUPNs.append(
                            user_account['azd_from_workitem_user'])
                        targetUPNs.append(user_account['azd_to_workitem_user'])

    if len(sourceUPNs) == 0 or len(targetUPNs) == 0:
        printException('no UPN pairs found to process')

    for i, sourceUPN in enumerate(sourceUPNs, start=0):
        targetUPN = targetUPNs[i]

        if len(azdAccounts) == 0:
            azd_accounts_scope = list(config['azdAccounts'].keys())
        else:
            azd_accounts_scope = [azdAccounts[i]]

        for azd_account in azd_accounts_scope:

            azd_account_config = config['azdAccounts'][azd_account]
            client = get_azd_workitem_tracking_client(azd_account_config)

            print('patching work items from {} to {}'.format(sourceUPN, targetUPN))

            wiql = Wiql(
                query="""
                select *
                from WorkItems
                where [System.AssignedTo] = '{}'
                order by [System.ChangedDate] asc""".format(sourceUPN)
            )

            wiql_results = client.query_by_wiql(
                wiql, top=MAX_WORK_ITEMS_BATCH_PATH).work_items

            if wiql_results:
                work_items = (
                    client.get_work_item(int(res.id)) for res in wiql_results
                )

                for work_item in work_items:
                    if 'System.AssignedTo' in work_item.fields:
                        operations = [JsonPatchOperation(
                            op='replace', path='/fields/System.AssignedTo', value=targetUPN)]
                        printInfo(f'work item ID {work_item.id}')
                        resp = client.update_work_item(
                            document=operations, id=work_item.id)

