# Migrate principalNames for user accounts in Azure DevOps

The script in this repository helps migrating user accounts in Azure DevOps and - if required - invited user accounts in the connected Azure Active Directory from one principal name to another.

Although it can be used for these cases ...

- migrate from one domain to another e.g. `userid@old-domain.com` to  `userid@new-domain.com`
- migrate from one principal name to another e.g. `old-userid@domain.com` to  `new-userid@domain.com`
- migrate when last- and/or firstname had changed e.g. `firstname.old-lastname@domain.com` to  `firstname.new-lastname@domain.com`
- copy Azure Active Directory, Azure Resource Manager and/or Azure DevOps authorizationsfrom one user account to another e.g. `userid@domain.com` to  `some-other-userid@domain.com`

... it was originally created for the case when principal names for __invited__ accounts in an Azure Active Directory with connected Azure DevOps accounts change e.g. from `userid@domain.com` to  `firstname.lastname@domain.com`.

## abbreviations used

| term | |
| ---- | ---- |
| AAD | Azure Active Directory |
| ARM | Azure Resource Manager |
| AzD | Azure DevOps |
| UPN | User Principal Name |

## processing flow

The script `migration.py` has this main processes:

- **capture** AAD (Azure Active Directory) user account group assignments and ARM (Azure Resource Manager) role assignments; **capture** AzD (Azure DevOps) entitlements and group assignments
- **delete** accounts previously captured from AAD and AzD
- **rebuild** accounts previously captured in AAD and AzD - inviting the AAD account, re-assigning group memberships, re-assigning ARM role assignments, re-creating in AzD, re-assigning group memberships and entitlements in AzD
- transfer **work items** from one principal to another

## Preparations

### install dependencies

> if you care - create and activate a Python virtual environment before

- install Python 3.7+
- install dependencies : ```pip install -r .\requirements.txt```

### configure Azure and Azure DevOps accounts

> DISCLAIMER! The success of capture and rebuild hugely depends on the authorizations given to these accounts. Check the captured information thoroughly. I had cases where I had to assign IAM / Subscription Owner to the registered app.

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

## Usage

### listing users

List AAD users with their reference to the configured Azure DevOps accounts into a file `userlist.txt`.

This option expects a RegEx pattern to identify the user account in the AAD.

```sh
.\migration.py -l "^ab.*@domain.com$"
```

### capture user account information

Users to be captured (analyzed) for a migration can be either specified in a text file - as a migrate from UPN to UPN pair - with a line for each user ...

```text
userid@domain.com,firstname.lastname@domain.com
userid2@domain.com,firstname2.lastname2@domain.com
```

```bash
.\migration.py -c -f .\upnsbatch1.txt
```

... or directly as an argument

```bash
.\migration.py -c -u "userid@domain.com,firstname.lastname@domain.com"
```

Results of the capture can be verified in ```migration.json```.

### delete old user

Delete capture (old) user accounts:

```bash
.\migration.py -d
```

Delete only in Azure DevOps:

```bash
.\migration.py -d --azd
```

### rebuild with new user

Rebuild user accounts from captured information:

```bash
.\migration.py -r
```

### transfer work items

Transfer work items from captured information:

```bash
.\migration.py -w
```

Transfer work items directly (full diplayname is expected):

```bash
.\migration.py -w -u "John Doe <john.doe@old-domain.com>,John Doe <john.doe@new-domain.com>"
```

### general parameters

| parameter | purpose |
| ---- | ---- |
| `--aad` | only process Azure Active Directory (capture, delete, rebuild) |
| `--azd` | only process Azure DevOps (capture, delete, rebuild) |
| `--debug` | switch logging to DEBUG mode so that SDK logs API calls |
