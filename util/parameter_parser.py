
import argparse


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
    parser.add_argument('--stap-output', type=str,
                        default='systemtap/csv/stap.csv')
    parser.add_argument('--stap-verbosity', action='store_true')
    parser.add_argument('--stap-request-count', type=int, default=5)

    # Hyperfine parameters
    parser.add_argument('--run-hyperfine', action='store_true')
    parser.add_argument('--hf-output', type=str,
                        default='hyperfine/json/hf.json')
    parser.add_argument('--hf-runs', type=int, default=10)
    parser.add_argument('--hf-parameters', nargs='+',
                        default=['admin@ipa.test', 'administrator@samba.test',
                                 'adminldap@ldap.test', 'wrong@ipa.test',
                                 'wrong@samba.test', 'wrong@ldap.test'])

    return parser.parse_args()
