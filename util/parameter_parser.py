import argparse
from pathlib import Path


def parse_argumets():
    parser = argparse.ArgumentParser()

    # SSSD parameters
    parser.add_argument('--providers', nargs='+',
                        default=['ipa', 'samba', 'ldap'])
    parser.add_argument('--sssctl', type=str, default='/usr/sbin/sssctl')
    parser.add_argument('--sss_cache', type=str, default='/usr/sbin/sss_cache')
    parser.add_argument('--sssd-conf', type=str, default='/etc/sssd/sssd.conf')
    parser.add_argument('--ldap-template', type=str,
                        default='systemtap/conf/sssd-ldap.conf')

    # SystemTap parameters
    parser.add_argument('--run-systemtap', action='store_true')
    parser.add_argument('--stap-script', type=str,
                        default='systemtap/sbus_tap.stp')
    parser.add_argument('--stap-output', type=stap_output,
                        default='systemtap/csv/stap.csv')
    parser.add_argument('--stap-request-count', type=int, default=5)
    parser.add_argument('--stap-verbosity', action='store_true')

    # Hyperfine parameters
    parser.add_argument('--run-hyperfine', action='store_true')
    parser.add_argument('--hf-output', type=hf_output,
                        default='hyperfine/json/hf.json')
    parser.add_argument('--hf-runs', type=int, default=10)
    parser.add_argument('--hf-parameters', nargs='+',
                        default=['admin@ipa.test', 'administrator@samba.test',
                                 'adminldap@ldap.test', 'wrong@ipa.test',
                                 'wrong@samba.test', 'wrong@ldap.test'])

    return parser.parse_args()


def check_parent_dir(name: str) -> None:
    parent_dir = Path(name).parent
    if not parent_dir.exists():
        parent_dir.mkdir(parents=True, exist_ok=True)


def stap_output(name: str) -> str:
    check_parent_dir(name)
    if Path(name).suffix != '.csv':
        raise ValueError('The output for SystemTap has to be a CSV file!')
    return name


def hf_output(name: str) -> str:
    check_parent_dir(name)
    if Path(name).suffix != '.json':
        raise ValueError('The output for SystemTap has to be a JSON file!')
    return name
