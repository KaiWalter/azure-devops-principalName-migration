from modules.aad_processing import *
from modules.azd_processing import *
from modules.clients import get_azd_graph_client, get_graph_rbac_client, get_azure_subscription_client
from modules.config import load_config
from modules.logging import *
import json
import logging

CAPTURE_FILENAME = 'migration.json'
PAIR_SAMPLE = 'userid@domain.com,firstname.lastname@domain.com'


def process(upn_file: str, users: str, aad: bool, azd: bool):

    migrationSourceUPNs, migrationTargetUPNs = extract_migration_upns(
        upn_file, users)

    if len(migrationSourceUPNs) == 0 or len(migrationTargetUPNs) == 0:
        printException('no UPN pairs found to process')

    # capture AAD account information
    aad_capture = capture_aad(migrationSourceUPNs)

    # capture Azd account information
    azd_capture = capture_azd(
        load_config(), migrationSourceUPNs, migrationTargetUPNs)

    # prepare and write capture file
    capture = {'records': []}

    for i in range(0, len(migrationSourceUPNs)):

        logging.info(
            'capturing {} -> {}'.format(migrationSourceUPNs[i], migrationTargetUPNs[i]))

        sourceUPN = migrationSourceUPNs[i]

        aadMemberships_extract = aad_capture[sourceUPN]['aadMemberships']
        aadRoleAssignments_extract = aad_capture[sourceUPN]['aadRoleAssignments']

        record = {
            'sourceUPN': migrationSourceUPNs[i],
            'targetUPN': migrationTargetUPNs[i],
            'aad_UPN': aadMemberships_extract[0]['upn'] if len(aadMemberships_extract) > 0 else "",
            'aad_object_id': aadMemberships_extract[0]['object_id'] if len(aadMemberships_extract) > 0 else "",
            'aad_display_name': aadMemberships_extract[0]['display_name'] if len(aadMemberships_extract) > 0 else "",
            'aad_member_ships': aadMemberships_extract[0]['groups'] if len(aadMemberships_extract) > 0 else "",
            'aad_role_assignments': [{'subscription_id': x['subscription_id'], 'resources':x['resources']} for x in aadRoleAssignments_extract],
            'azd': azd_capture[sourceUPN]
        }

        capture['records'].append(record)

    with open(CAPTURE_FILENAME, 'w') as f:
        json.dump(capture, f)


def read_capture():

    with open(CAPTURE_FILENAME, 'r') as f:
        capture = json.load(f)

    if capture:
        return capture
    else:
        return


def extract_migration_upns(upn_file: str, users: str):

    migrationSourceUPNs = []
    migrationTargetUPNs = []

    migration_list = []

    if users:
        migration_list = [u.lower() for u in users.split(';')]
    elif upn_file:
        text_file = open(upn_file, "r")
        lines = text_file.readlines()
        migration_list = [u.lower().replace('\n', '') for u in lines if u]
        text_file.close()

    for i in range(0, len(migration_list)):
        pair = migration_list[i].split(',')
        if len(pair) != 2:
            printException(
                'specify UPNs in source+target pairs e.g. {}'.format(PAIR_SAMPLE))
        else:
            migrationSourceUPNs.append(pair[0])
            migrationTargetUPNs.append(pair[1])

    return (migrationSourceUPNs, migrationTargetUPNs)


def capture_aad(migrationSourceUPNs):

    aad_capture = {}

    az_graph_rbac_client = get_graph_rbac_client()
    az_subscription_client = get_azure_subscription_client()

    print('capture AAD account information')
    aadUsers = load_aad_users(az_graph_rbac_client,
                            migrationUPNs=migrationSourceUPNs)

    aadMemberships = load_aad_memberships(az_graph_rbac_client, aadUsers)
    aadRoleAssignments = load_aad_role_assignments(
        az_subscription_client, aadUsers)

    for i in range(0, len(migrationSourceUPNs)):

        sourceUPN = migrationSourceUPNs[i]

        aadMemberships_extract = [
            x for x in aadMemberships if x['upn'].lower() == sourceUPN]
        aadRoleAssignments_extract = [
            x for x in aadRoleAssignments if x['upn'].lower() == sourceUPN]

        aad_capture[sourceUPN] = {
            'aadMemberships': aadMemberships_extract,
            'aadRoleAssignments': aadRoleAssignments_extract
        }

    return aad_capture


def capture_azd_instance(account, migrationSourceUPNs):

    azd_graph_client = get_azd_graph_client(account)
    azd_entitlement_client = get_azd_entitlement_client(account)

    azdUsers = load_azd_users(
        azd_graph_client, migrationUPNs=migrationSourceUPNs)
    azdEntitlements = load_azd_entitlements(azd_entitlement_client, azdUsers)

    azdMemberships = load_azd_memberships(azd_graph_client, azdUsers)
    azdAvatars = load_azd_avatars(azd_graph_client, azdUsers)

    return azdUsers, azdEntitlements, azdMemberships, azdAvatars


def capture_azd(config, migrationSourceUPNs, migrationTargetUPNs):

    azd_capture = {}

    for azd_account in config['azdAccounts']:
        print(f'capture AzD account information : {azd_account}')
        azdUsers, azdEntitlements, azdMemberships, azdAvatars = capture_azd_instance(
            config['azdAccounts'][azd_account], migrationSourceUPNs)

        for i in range(0, len(migrationSourceUPNs)):

            sourceUPN = migrationSourceUPNs[i]
            targetUPN = migrationTargetUPNs[i]

            azdUsers_extract = [
                x for x in azdUsers if x.principal_name.lower() == sourceUPN]
            azdEntitlements_extract = [
                x for x in azdEntitlements if x['upn'].lower() == sourceUPN]
            azdMemberships_extract = [
                x for x in azdMemberships if x['upn'].lower() == sourceUPN]
            azdAvatars_extract = [
                x for x in azdAvatars if x['upn'].lower() == sourceUPN]

            record = {}

            if len(azdEntitlements_extract) > 0:
                record['azd_id'] = azdEntitlements_extract[0]['id']
                record['azd_extensions'] = [{'id': x.id, 'name': x.name, 'source': x.source,
                                             'assignment_source': x.assignment_source} for x in azdEntitlements_extract[0]['extensions']],
                record['azd_account_license_type'] = azdEntitlements_extract[0]['account_license_type']
                record['azd_msdn_license_type'] = azdEntitlements_extract[0]['msdn_license_type']

            if len(azdMemberships_extract) > 0:
                record['azd_UPN'] = azdMemberships_extract[0]['upn']
                record['azd_descriptor'] = azdMemberships_extract[0]['descriptor']
                record['azd_member_ships'] = azdMemberships_extract[0]['groups']

            if len(azdAvatars_extract) > 0:
                if len(azdAvatars_extract[0]["avatar"]) > 0:
                    record['azd_avatar'] = azdAvatars_extract[0]["avatar"]

            if len(azdUsers_extract) > 0:
                record['azd_from_workitem_user'] = f'{azdUsers_extract[0].display_name} <{azdUsers_extract[0].principal_name}>'
                record['azd_to_workitem_user'] = f'{azdUsers_extract[0].display_name} <{targetUPN}>'

            if record:
                if not sourceUPN in azd_capture:
                    azd_capture[sourceUPN] = {}
                azd_capture[sourceUPN][azd_account] = record

    return azd_capture
