# Migrate principalNames for user accounts in Azure DevOps

This script helps migrating user accounts in Azure DevOps - and if required in the connected Azure Active Directory - from principal name format to another.

## use cases

The script can be used for these cases:

- migrate from one principal name format to another e.g. `old-userid@domain.com` to  `new-userid@domain.com`
- migrate when last- and/or firstname had changed e.g. `firstname.old-lastname@domain.com` to  `firstname.new-lastname@domain.com`

# Preparations

## install dependencies

- install Python 3.7+
- if you care - create and activate a Python virtual environment
- install dependencies : ```pip install -r .\requirements.txt```


