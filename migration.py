from modules.logging import *
import modules.listusers as listusers
import modules.capture as capture
import argparse
import logging

# --------------------------------------------------------------------------------

def main(listuserspattern: str, process_capture: bool, upn_file: str, users: str, process_delete: bool, process_rebuild: bool, process_workitems: bool, aad: bool, azd: bool, debug: bool):

    if debug:
        logging.basicConfig(filename=LOG_FILENAME,
                            filemode='w', level=logging.DEBUG)
    else:
        logging.basicConfig(filename=LOG_FILENAME,
                            filemode='w', level=logging.INFO)

    process_aad = aad
    process_azd = azd
    # when both not set, assume both to be processed
    if not process_aad and not process_azd:
        process_aad = True
        process_azd = True

    if listuserspattern:
        listusers.process(listuserspattern)
    elif process_capture:
        capture.process(upn_file, users, process_aad, process_azd)
    # elif delete:
    #     main_delete(process_aad, process_azd)
    # elif rebuild:
    #     main_rebuild(process_aad, process_azd)
    # elif workitems:
    #     main_work_items(upn_file, users)
    else:
        printWarning('nothing to do')


# --------------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Universal user UPN migration tool capture-delete-rebuild')
    parser.add_argument("-l", "--list", required=False, dest="listuserspattern",
                        help="list users for a given pattern in AAD to be migrated")
    parser.add_argument("-c", "--capture", required=False, action='store_true',
                        dest="capture", help="capture current AAD and AzD roles and authorizations for a given set of users")
    parser.add_argument("-f", "--file", required=False, dest="file",
                        help="path to text file containing a lie for each UPN to migrate")
    parser.add_argument("-u", "--users", required=False, dest="users",
                        help="semicolon and comma separated list of UPN from/to pairs to process e.g. 'old-userid@domain.com,new-userid@domain.com;user@old-domain.com,user@new-domain.com'")
    parser.add_argument("-d", "--delete", required=False, action='store_true',
                        dest="delete", help="delete captured users from AAD and AzD")
    parser.add_argument("-r", "--rebuild", required=False, action='store_true',
                        dest="rebuild", help="rebuild roles and authorizations for captured users")
    parser.add_argument("-w", "--work-items", required=False, action='store_true',
                        dest="workitems", help="set new UPN for work items")
    parser.add_argument("--aad", required=False, action='store_true',
                        dest="aad", help="only process UPN on AAD")
    parser.add_argument("--azd", required=False, action='store_true',
                        dest="azd", help="only process UPN on Azure DevOps")
    parser.add_argument("--debug", required=False, action='store_true',
                        dest="debug", help="log on DEBUG level (default:INFO)")
    args = parser.parse_args()

    main(args.listuserspattern, args.capture, args.file, args.users,
         args.delete, args.rebuild, args.workitems, args.aad, args.azd, args.debug)
