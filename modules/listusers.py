from modules.config import load_config
from modules.clients import get_azd_graph_client, get_graph_rbac_client
from modules.aad_processing import load_aad_users
from modules.azd_processing import load_azd_users
import re

def process(listuserspattern):

    """For a given RegEx pattern list users from AAD and indicate reference in Azure DevOps accounts."""

    pattern = re.compile(listuserspattern, re.IGNORECASE)

    print('list AAD account information')
    az_graph_rbac_client = get_graph_rbac_client()
    aadUsers = load_aad_users(az_graph_rbac_client)

    config = load_config()
    tenantId = config['aadAccount']['tenant']
    azdUsers = {}

    header = "upn,aadCreatedDateTime,aadRefreshTokensValidFromDateTime"

    for azd_account in config['azdAccounts'].keys():
        print(f'list Azd account information : {azd_account}')
        header += ",hasAzd" + azd_account.upper()

        azd_graph_client = get_azd_graph_client(
            config['azdAccounts'][azd_account])
        azdUsers[azd_account] = load_azd_users(azd_graph_client)

    dataset = {}

    for u in aadUsers:
        if u.mail:
            upn = u.mail.lower()
            if pattern.match(upn):
                dataset[upn] = {'createdDateTime': u.additional_properties['createdDateTime'],
                                'refreshTokensValidFromDateTime': u.additional_properties['refreshTokensValidFromDateTime']}
                for azd_account in config['azdAccounts'].keys():
                    dataset[upn][azd_account] = False

    for azd_account in azdUsers.keys():
        for u in azdUsers[azd_account]:
            upn = u.principal_name.lower()
            if u.domain == tenantId and pattern.match(upn):
                if upn in dataset:
                    dataset[upn][azd_account] = True

    with open('userlist.txt', 'w') as f:
        f.write(header + '\n')

        for rowkey in dataset.keys():
            row = rowkey
            for columnkey in dataset[rowkey].keys():
                row += ',' + str(dataset[rowkey][columnkey])
            f.write(row + '\n')
