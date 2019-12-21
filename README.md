# Migrate principalNames for user accounts in Azure DevOps

This script helps migrating user accounts in Azure DevOps - and if required in the connected Azure Active Directory - from principal name format to another.

## use cases

The script can be used for these cases:

- migrate from one principal name format to another e.g. `old-userid@domain.com` to  `new-userid@domain.com`
- migrate when last- and/or firstname had changed e.g. `firstname.old-lastname@domain.com` to  `firstname.new-lastname@domain.com`

## Preparations

### install dependencies

- install Python 3.7+
- if you care - create and activate a Python virtual environment
- install dependencies : ```pip install -r .\requirements.txt```

### configure Azure and Azure DevOps accounts

For Azure an registered app is required with these _application permissions_:
Microsoft Graph -> Directory.ReadWrite.All + User.Invite.All + User.ReadWrite.All

For each Azure DevOps account to be processed a `PAT` with _Full access has to be created.

With that information create a configuration file `.profile/accounts.json` and set `tentant`, `password` and `appId` in `aadAccount` section.  In section `azdAccounts` add a `url` and `pat` for each Azure DevOps account:

```json
{
    "aadAccount": {
        "tenant": "***tenant***",
        "password": "***password***",
        "appId": "***appid***"
    },
    "azdAccounts": {
        "***accountkey1***": {
            "url": "https://dev.azure.com/***account1***",
            "pat": "***full access - personal access token***"
        },
        "***accountkey2***": {
            "url": "https://dev.azure.com/***account2***",
            "pat": "***full access - personal access token***"
        }
    }
}
```

| value | origin |
| ---- | ---- |
| `***tenant***` | Tenant Id (GUID format) of the Azure Active Directory to which the Azure DevOps accounts are linked to |
| `***password***` | Client secret / password for the AAD registered app |
| `***appid***` | Client Id / App Id for the AAD registered app |
| `***accountkeyn***` | A free short key identifying your Azure DevOps accounts in the migration process |
| `***accountn***` | Account URL suffix |
| `***full access - personal access token***` | Full access _PAT_ to the particular account |
