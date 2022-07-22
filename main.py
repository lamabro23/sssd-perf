import manage_providers
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--providers', nargs='+', default=['ipa', 'samba', 'ldap'])
parser.add_argument('--sssctl', type=str, default='/usr/sbin/sssctl')
parser.add_argument('--sss_cache', type=str, default='/usr/sbin/sss_cache')
parser.add_argument('--sssd-conf', type=str, default='/etc/sssd/sssd.conf')
parser.add_argument('--ldap-template', type=str, default='conf/sssd-ldap.conf')
args = parser.parse_args()

closed_providers = manage_providers\
                        .prepare_providers(providers=args.providers,
                                           sssctl=args.sssctl,
                                           sssd_conf=args.sssd_conf,
                                           ldap_template=args.ldap_template)
