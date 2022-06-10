import argparse
import os
import pwd
from subprocess import DEVNULL, PIPE, Popen, STDOUT, run
from time import sleep

closed_providers = []
sssctl = '/usr/sbin/sssctl'
sss_cache = '/usr/sbin/sss_cache'
providers = ['ipa', 'samba', 'ldap']

users = {'ipa': ['admin@ipa.test'],
         'samba': ['administrator@samba.test'],
         'ldap': []}

ipa_cmd = {'join': 'ipa-client-install --unattended --no-ntp --domain ipa.test' +
                   ' --principal admin --password Secret123 --force-join',
           'leave': 'ipa-client-install --uninstall'}

samba_cmd = {'join': 'realm join samba.test',
             'leave': 'realm leave',
             'list': 'realm list --name-only'}


def get_current_domains() -> list[str]:
    p = Popen(samba_cmd['list'].split(), stdout=PIPE, universal_newlines=True)
    stdout, _ = p.communicate()
    return stdout.split()


def prepare_providers(providers: list) -> None:
    if len(curr_joined := get_current_domains()) <= 1:
        return

    if 'ipa' not in providers and 'ipa.test' in curr_joined:
        print('About to leave ipa domain')
        closed_providers.append('ipa')

        Popen(ipa_cmd['leave'].split(), stdin=PIPE, stdout=DEVNULL,
              stderr=STDOUT).communicate(input=b'no')
    if 'samba' not in providers and 'samba.test' in curr_joined:
        print('About to leave samba realm')
        closed_providers.append('samba')

        Popen(samba_cmd['leave'].split(), stdout=DEVNULL).communicate()
# TODO add ldap
#     if 'ldap' not in providers and 'ldap.test' in curr_joined:
#         print('About to leave ldap domain')


def resume_providers():
    run([sss_cache, '-E'])
    if 'ipa' in closed_providers:
        Popen(ipa_cmd['join'].split(), stdout=DEVNULL, stderr=STDOUT).communicate()
    if 'samba' in closed_providers:
        Popen(samba_cmd['join'].split(), stdin=PIPE,
              stdout=DEVNULL).communicate(input=b'Secret123')
        print('Joining...')
# TODO add ldap
#     if 'ldap' in closed_providers:
#         print('About to join ldap domain again')


def start_sytemtap() -> Popen:
    print(f'Starting the systemtap script: {args.systemtap_script}')
    print(' '.join(['stap', '-w', '-g', f'{args.systemtap_script}',
                    '-o', f'{args.stap_output}']))
    stap_process = Popen(['stap', '-w', '-g', f'{args.systemtap_script}',
                          '-o', f'{args.stap_output}'], stdout=DEVNULL, stderr=STDOUT)
    sleep(5)
    return stap_process


if not os.path.isfile(sss_cache) or not os.path.isfile(sssctl):
    print('Please install the sssd_tools package')
    exit(1)

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--providers', nargs='+', default=providers)
parser.add_argument('-r', '--requests-count', type=int, default=1)
parser.add_argument('-s', '--systemtap-script', type=str, default='sbus_tap.stp')
parser.add_argument('-o', '--stap-output', type=str, default='stap.txt')

args = parser.parse_args()

prepare_providers(args.providers)
stap = start_sytemtap()

for provider, usernames in users.items():
    if provider in args.providers:
        print(f'Run for {provider} has started')
        for user in usernames:
            for i in range(args.requests_count):
                run([sss_cache, '-E'])
                if pwd.getpwnam(user) is None:
                    print('Fetch failed!')
                    exit(1)

print('Test finished successfully!')
resume_providers()
stap.terminate()
