#!/usr/bin/env python3

"""Send actions to one or more devices in a Kandji instance."""

########################################################################################
# Created by Matt Wilson | support@kandji.io | Kandji, Inc.
########################################################################################
# Created - 2022-08-17
########################################################################################
# Software Information
########################################################################################
#
# This script can be used to send device actions to one or more devices in a Kandji
# tenant.
#
########################################################################################
# License Information
########################################################################################
# Copyright 2022 Kandji, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CNNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
########################################################################################

__version__ = "0.0.5"


# Standard library
import argparse
import json
import pathlib
import random
import sys
from datetime import datetime

# 3rd party imports

try:
    import requests
except ImportError as import_error:
    print(import_error)
    sys.exit(
        "Looks like you need to install the requests module. Open a Terminal and run  "
        "python3 -m pip install requests."
    )

from requests.adapters import HTTPAdapter

########################################################################################
######################### UPDATE VARIABLES BELOW #######################################
########################################################################################

SUBDOMAIN = "accuhive"  # bravewaffles, example, company_name
REGION = "us"  # us and eu - this can be found in the Kandji settings on the Access tab

# Kandji Bearer Token
TOKEN = "your_api_key_here"

########################################################################################
######################### DO NOT MODIFY BELOW THIS LINE ################################
########################################################################################

# Initialize some variables
# Kandji API base URL
if REGION == "us":
    BASE_URL = f"https://{SUBDOMAIN}.clients.{REGION}-1.kandji.io/api"
else:
    BASE_URL = f"https://{SUBDOMAIN}.clients.{REGION}.kandji.io/api"

SCRIPT_NAME = "Device details report"
TODAY = datetime.today().strftime("%Y%m%d")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json;charset=utf-8",
    "Cache-Control": "no-cache",
}

# Current working directory
HERE = pathlib.Path("__file__").parent.absolute()


def var_validation():
    """Validate variables."""
    if "accuhive" in BASE_URL:
        print(
            f'\n\tThe subdomain "{SUBDOMAIN}" in {BASE_URL} needs to be updated to '
            "your Kandji tenant subdomain..."
        )
        print("\tPlease see the example in the README for this repo.\n")
        sys.exit()

    if "api_key" in TOKEN:
        print(f'\n\tThe TOKEN should not be "{TOKEN}"...')
        print("\tPlease update this to your API Token.\n")
        sys.exit()


def program_arguments():
    """Return arguments."""
    parser = argparse.ArgumentParser(
        prog="device_actions.py",
        description="Send device actions to one or more devices in a Kandji instance.",
        allow_abbrev=False,
    )

    # add grouped arguments that cannot be called together
    group_actions = parser.add_mutually_exclusive_group()

    group_actions.add_argument(
        "--blankpush",
        action="store_true",
        help="This action sends an MDM command to initiate a blank push. "
        "A Blank Push utilizes the same service that sends MDM profiles and commands. "
        "It's meant for verifying a connection to APNs, but it sometimes helps to get "
        "pending push notifications that are stuck in the queue to complete. ",
        required=False,
    )

    group_actions.add_argument(
        "--reinstall-agent",
        action="store_true",
        help="This action with send a command to reinstall the Kandji agent on a macOS "
        "device.",
        required=False,
    )

    group_actions.add_argument(
        "--remote-desktop",
        type=str,
        metavar="[on|off]",
        help="This action with send an MDM command to set macOS remote desktop to on "
        "or off remoted desktop for macOS. If Remote Management is already disabled on "
        'a device, sending the off option will result in a "Command is not allowed for '
        'current device" message to be returned from Kandji and the command will not '
        "be sent.",
        required=False,
    )

    group_actions.add_argument(
        "--renew-mdm",
        action="store_true",
        help="This action sends an MDM command to re-install the existing root MDM "
        "profile for a given device ID. This command will not impact any existing "
        "configurations, apps, or profiles.",
        required=False,
    )

    group_actions.add_argument(
        "--restart",
        action="store_true",
        help="This action sends an MDM command to remotely restart a device.",
        required=False,
    )

    group_actions.add_argument(
        "--shutdown",
        action="store_true",
        help="This action sends an MDM command to shutdown a device.",
        required=False,
    )

    group_actions.add_argument(
        "--update-inventory",
        action="store_true",
        help="This action sends a few MDM commands to start a check-in for a device, "
        "initiating the daily MDM commands and MDM logic. MDM commands sent with this "
        "action include: AvailableOSUpdates, DeviceInformation, SecurityInfo, "
        "UserList, InstalledApplicationList, ProfileList, and CertificateList.",
        required=False,
    )

    # add grouped arguments that cannot be called together
    group_search = parser.add_mutually_exclusive_group()

    group_search.add_argument(
        "--serial-number",
        type=str,
        metavar="XX7FFXXSQ1GH",
        help="Look up a device by its serial number and send an action to it.",
        required=False,
    )

    group_search.add_argument(
        "--platform",
        type=str,
        metavar="Mac",
        help="Send an action to a specific device family in a Kandji instance. "
        "Example: Mac, iPhone, iPad.",
        required=False,
    )

    group_search.add_argument(
        "--all-devices",
        action="store_true",
        help="Send an action to all devices in a Kandji instance. If this option is "
        "used, you will see a prompt to comfirm the action and will be required to "
        "enter a code to continue.",
        required=False,
    )

    parser.version = __version__
    parser.add_argument("--version", action="version", help="Show this tool's version.")

    args = vars(parser.parse_args())
    if not any(args.values()):
        print()
        parser.error(
            "No command options given. Use the --help flag for more details.\n"
        )

    args = parser.parse_args()

    if not (
        args.blankpush
        or args.reinstall_agent
        or args.remote_desktop
        or args.renew_mdm
        or args.restart
        or args.shutdown
        or args.update_inventory
    ):
        print()
        parser.error("No action provided. Use the --help flag for more details.\n")

    return parser.parse_args()


def error_handling(resp, resp_code, err_msg):
    """Handle HTTP errors."""
    # 400
    if resp_code == requests.codes["bad_request"]:
        print(f"\n\t{err_msg}")
        print(f"\tResponse msg: {resp.text}\n")
    # 401
    elif resp_code == requests.codes["unauthorized"]:
        print("Make sure that you have the required permissions to access this data.")
        print(
            "Depending on the API platform this could mean that access has just been "
            "blocked."
        )
        sys.exit(f"\t{err_msg}")
    # 403
    elif resp_code == requests.codes["forbidden"]:
        print("The api key may be invalid or missing.")
        sys.exit(f"\t{err_msg}")
    # 404
    elif resp_code == requests.codes["not_found"]:
        print("\nWe cannot find the one that you are looking for...")
        print("Move along...")
        print(f"\tError: {err_msg}")
        print(f"\tResponse msg: {resp}")
        print(
            "\tPossible reason: If this is a device it could be because the device is "
            "not longer\n"
            "\t\t\t enrolled in Kandji. This would prevent the MDM command from being\n"
            "\t\t\t sent successfully.\n"
        )
    # 429
    elif resp_code == requests.codes["too_many_requests"]:
        print("You have reached the rate limit ...")
        print("Try again later ...")
        sys.exit(f"\t{err_msg}")
    # 500
    elif resp_code == requests.codes["internal_server_error"]:
        print("The service is having a problem...")
        sys.exit(err_msg)
    # 503
    elif resp_code == requests.codes["service_unavailable"]:
        print("Unable to reach the service. Try again later...")
    else:
        print("Something really bad must have happened...")
        print(err_msg)
        # sys.exit()


def kandji_api(method, endpoint, params=None, payload=None):
    """Make an API request and return data.

    method   - an HTTP Method (GET, POST, PATCH, DELETE).
    endpoint - the API URL endpoint to target.
    params   - optional parameters can be passed as a dict.
    payload  - optional payload is passed as a dict and used with PATCH and POST
               methods.
    Returns a JSON data object.
    """
    attom_adapter = HTTPAdapter(max_retries=3)
    session = requests.Session()
    session.mount(BASE_URL, attom_adapter)

    try:
        response = session.request(
            method,
            BASE_URL + endpoint,
            data=payload,
            headers=HEADERS,
            params=params,
            timeout=30,
        )

        # If a successful status code is returned (200 and 300 range)
        if response:
            try:
                data = response.json()
            except Exception:
                data = response.text

        # if the request is successful exeptions will not be raised
        response.raise_for_status()

    except requests.exceptions.RequestException as err:
        error_handling(resp=response, resp_code=response.status_code, err_msg=err)
        data = {"error": f"{response.status_code}", "api resp": f"{err}"}

    return data


def get_devices(params=None, ordering="serial_number"):
    """Return device inventory."""
    count = 0
    # limit - set the number of records to return per API call
    limit = 300
    # offset - set the starting point within a list of resources
    offset = 0
    # inventory
    data = []

    while True:
        # update params
        params.update(
            {"ordering": f"{ordering}", "limit": f"{limit}", "offset": f"{offset}"}
        )
        # print(params)

        # check to see if a platform was sprecified
        response = kandji_api(method="GET", endpoint="/v1/devices", params=params)

        count += len(response)
        offset += limit
        if len(response) == 0:
            break

        # breakout the response then append to the data list
        for record in response:
            data.append(record)

    if len(data) < 1:
        print("No devices found...\n")
        sys.exit()

    return data


def send_device_action(devices, action, payload=None):
    """Return device details."""
    # list to hold all device detail records
    data = []
    # Get device details for each device
    count = 0

    for device in devices:
        print(f"Attempting to send a \"{action}\" action to {device['serial_number']}")
        response = kandji_api(
            method="POST",
            endpoint=f"/v1/devices/{device['device_id']}/action/{action}",
            payload=payload,
        )

        data.append(response)
        count += 1

    return data


def main():
    """Run main logic."""
    # validate vars
    var_validation()

    # Return the arguments
    arguments = program_arguments()

    print(f"\nVersion: {__version__}")
    print(f"Base URL: {BASE_URL}\n")

    # dict placeholder for params passed to api requests
    params_dict = {}

    # evaluate options
    if arguments.serial_number:
        params_dict.update({"serial_number": f"{arguments.serial_number}"})
        print(
            "Looking for device record with the following serial number: "
            f"{arguments.serial_number}"
        )

    if arguments.platform:
        params_dict.update({"platform": f"{arguments.platform}"})

    if arguments.blankpush:
        action = "blankpush"

    if arguments.remote_desktop:
        action = "remotedesktop"

        if arguments.remote_desktop == "on":
            payload = {"EnableRemoteDesktop": True}
        else:
            payload = {"EnableRemoteDesktop": False}

        # encode the payload
        payload = json.dumps(payload)

    if arguments.reinstall_agent:
        action = "reinstallagent"

    if arguments.renew_mdm:
        action = "renewmdmprofile"

    if arguments.restart:
        action = "restart"

    if arguments.shutdown:
        action = "shutdown"

    if arguments.update_inventory:
        action = "updateinventory"

    if arguments.all_devices:
        print(
            f"The {action} command will go out to ALL devices in the Kandji instance..."
        )
        user_answer = input(
            'This is NOT reversable. Are you sure you want to do this? Type "Yes" to '
            "continue: "
        )

        if user_answer == "Yes":
            check_number = random.randint(0, 9999)
            check_string = f"{check_number:>4}"
            print(f"\n\tCode: {check_number}")
            response = input("\tPlease enter the code above: ")
            print("")

            if response != check_string:
                print("Failed code check!")
                sys.exit("Exiting...")

            print("Code verification complete.")

        else:
            sys.exit("Exiting...")

    # Get all device inventory records
    print("Getting device inventory from Kandji...")
    device_inventory = get_devices(params=params_dict)
    print(f"Total records returned: {len(device_inventory)}\n")

    # send the action to the device(s)
    try:
        send_device_action(devices=device_inventory, action=action, payload=payload)
    except Exception:
        send_device_action(devices=device_inventory, action=action)


if __name__ == "__main__":
    main()
