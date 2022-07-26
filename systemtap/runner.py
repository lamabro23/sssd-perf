import argparse
from pathlib import Path
import pwd
import re
import shutil
from subprocess import DEVNULL, PIPE, Popen, STDOUT, run
from time import sleep


# TODO change the return value to a list if the content
# won't be needed in other ways
def check_ldap_config(parser: argparse.ArgumentParser, arg: str):
    if not Path(arg).exists():
        parser.error(f'The file {arg} does not exist!')
    else:
        return open(arg, 'r')


def check_parent_dir(arg: str):
    p = Path(arg).parent
    if not p.exists():
        p.mkdir()
    return arg


parser = argparse.ArgumentParser()
parser.add_argument('-p', '--providers', nargs='+', default=providers)
parser.add_argument('-r', '--requests-count', type=int, default=1)
parser.add_argument('-s', '--systemtap-script', type=str, default='sbus_tap.stp')
parser.add_argument('-v', '--verbose-stap', type=int, default=0)
parser.add_argument('-o', '--stap-output', default='csv/stap.csv',
                    type=lambda x: check_parent_dir(x))
parser.add_argument('-l', '--ldap-config', default='conf/sssd-ldap.conf',
                    type=lambda x: check_ldap_config(parser, x))

args = parser.parse_args()

# _, stderr = Popen([sss_cache, '-E'], stderr=PIPE).communicate()
# check_sudo(str(stderr))

# Prepare the environment and start the warm-up
# prepare_providers(args.providers)
# send_requests(users, 5, True)

# Start the SystemTap script in the background and start sending requests
# stap = start_sytemtap(args.systemtap_script, args.stap_output, args.verbose_stap)
# send_requests(users, args.requests_count, False)

# print('Test finished successfully!')
# stap.terminate()
# resume_providers()
# args.ldap_config.close()
