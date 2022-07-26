import argparse
from pathlib import Path
import re
from subprocess import DEVNULL, PIPE, Popen

from hyperfine import hf
from systemtap import stap
from util import manage_providers


def check_tools(tools: list[str]) -> None:
    for t in tools:
        if not Path(t).exists():
            raise IOError(f'The {t} command missing.' +
                          ' Please install the sssd_tools package')


def check_sudo():
    _, stderr = Popen([args.sss_cache, '-E'], stderr=PIPE).communicate()
    if re.search('root', str(stderr)) is not None:
        raise OSError('This test suite needs to be with root privileges!')


parser = argparse.ArgumentParser()

# SSSD parameters
parser.add_argument('--providers', nargs='+', default=['ipa', 'samba', 'ldap'])
parser.add_argument('--sssctl', type=str, default='/usr/sbin/sssctl')
parser.add_argument('--sss_cache', type=str, default='/usr/sbin/sss_cache')
parser.add_argument('--sssd-conf', type=str, default='/etc/sssd/sssd.conf')
parser.add_argument('--ldap-template', type=str,
                    default='systemtap/conf/sssd-ldap.conf')

# SystemTap parameters
parser.add_argument('--run-systemtap', action='store_true')
parser.add_argument('--stap-script', type=str,
                    default='systemtap/sbus_tap.stp')
parser.add_argument('--stap-output', type=str,
                    default='systemtap/csv/stap.csv')
parser.add_argument('--stap-verbosity', action='store_true')
parser.add_argument('--stap-request-count', type=int, default=5)

# Hyperfine parameters
parser.add_argument('--run-hyperfine', action='store_true')
parser.add_argument('--hf-output', type=str, default='hyperfine/json/hf.json')
parser.add_argument('--hf-runs', type=int, default=10)
parser.add_argument('--hf-parameters', nargs='+', default=['admin@ipa.test', 'administrator@samba.test',
                                                           'adminldap@ldap.test', 'wrong@ipa.test',
                                                           'wrong@samba.test', 'wrong@ldap.test'])

args = parser.parse_args()


check_tools([args.sss_cache, args.sssctl])
check_sudo()

closed_providers = manage_providers\
                        .prepare_providers(providers=args.providers,
                                           sssctl=args.sssctl,
                                           sssd_conf=args.sssd_conf,
                                           ldap_template=args.ldap_template)

if args.run_systemtap:
    # Run 5 warm-up runs before starting the tests
    stap.send_requests(args.providers, args.sss_cache, 5, True)

    sp = stap.start_sytemtap(args.stap_script, args.stap_output,
                             args.stap_verbosity)

    stap.send_requests(args.providers, args.sss_cache,
                       args.stap_request_count, False)
    # Stop SystemTap
    sp.terminate()

    print('SystemTap tests finished successfully!')

if args.run_hyperfine:
    hf.run_benchmark(args.hf_runs, ','.join(args.hf_parameters),
                     args.sss_cache, args.hf_output)
    print('Hyperfine tests finished successfully!')

if len(closed_providers) > 0:
    manage_providers.resume_providers(closed_providers, args.sss_cache,
                                      args.ldap_template, args.sssd_conf)
