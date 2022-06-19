import argparse
import os
import pwd
import re
import shutil
from subprocess import DEVNULL, PIPE, Popen, STDOUT, run
from time import sleep

# TODO add check for currently used domains (sssctl domain-list)
# TODO OR create containers within the script

closed_providers = []
sssctl = '/usr/sbin/sssctl'
sss_cache = '/usr/sbin/sss_cache'
sssd_conf = '/etc/sssd/sssd.conf'
providers = ['ipa', 'samba', 'ldap']

users = {'ipa': ['admin@ipa.test'],
         'samba': ['administrator@samba.test'],
         'ldap': ['adminldap@ldap.test']}

ipa_cmd = {'join': 'ipa-client-install --unattended --no-ntp --domain ipa.test' +
                   ' --principal admin --password Secret123 --force-join',
           'leave': 'ipa-client-install --uninstall'}

samba_cmd = {'join': 'realm join samba.test',
             'leave': 'realm leave',
             'list': 'realm list --name-only'}

sssctl_cmd = [sssctl, 'domain-list']


def get_current_domains() -> list[str]:
    p = Popen(sssctl_cmd, stdout=PIPE, universal_newlines=True)
    stdout, _ = p.communicate()
    return stdout.split()


def str_write(s: str) -> None:
    with open('/home/duradnik/Tmp/output.txt', 'a') as f:
        try:
            f.write(s)
        except Exception:
            print('!!! Couldn\'t write the file !!!')


def list_write(lst: list) -> None:
    with open('/home/duradnik/Tmp/output.txt', 'w') as f:
        try:
            for i in lst:
                f.write(i)
        except Exception:
            print('!!! Couldn\'t write the file !!!')


def remove_from_domains_list(line: str) -> str:
    opts = [', ldap.test', ', ldap.test, ', 'ldap.test, ']
    for o in opts:
        if o in line:
            return line.replace(o, '')
    return line


def prepare_ldap() -> None:
    print('About to leave ldap domain')
    conf_backup = sssd_conf + '.perf_bkp'
    shutil.copy2(sssd_conf, conf_backup)
    with open(conf_backup, 'rt') as og, open(sssd_conf, 'w') as new:
        ldap_lines = args.ldap_config.readlines()
        for line in og.readlines():
            if re.search('domains =.*ldap.test.*', line) is not None:
                new.write(remove_from_domains_list(line))
            elif line not in ldap_lines:
                new.write(line)
    run(['/bin/systemctl', 'restart', 'sssd.service'], stdout=DEVNULL)
    closed_providers.append('ldap')
    sleep(5)


def prepare_providers(providers: list) -> None:
    curr_joined = get_current_domains()

    if 'ipa' not in providers and 'ipa.test' in curr_joined:
        print('About to leave ipa domain')
        closed_providers.append('ipa')

        Popen(ipa_cmd['leave'].split(), stdin=PIPE, stdout=DEVNULL,
              stderr=STDOUT).communicate(input=b'no')
        sleep(5)

    if 'samba' not in providers and 'samba.test' in curr_joined:
        print('About to leave samba realm')
        closed_providers.append('samba')

        Popen(samba_cmd['leave'].split(), stdout=DEVNULL).communicate()

    if 'ldap' not in providers and 'ldap.test' in curr_joined:
        prepare_ldap()


def resume_providers() -> None:
    run([sss_cache, '-E'])
    print('About to resume any previously closed providers')
    if 'ipa' in closed_providers:
        run(ipa_cmd['join'].split(), stdout=DEVNULL, stderr=STDOUT)
    if 'samba' in closed_providers:
        Popen(samba_cmd['join'].split(), stdin=PIPE,
              stdout=DEVNULL).communicate(input=b'Secret123')
    if 'ldap' in closed_providers:
        args.ldap_config.seek(0)
        ldap_lines = args.ldap_config.readlines()
        with open(sssd_conf, 'r') as f:
            tmp_lines = f.readlines()
        with open(sssd_conf, 'w') as f:
            for line in tmp_lines:
                if re.match('domains =', line) is not None:
                    line = line.replace('\n', ', ldap.test\n')
                f.write(line)
        with open(sssd_conf, 'a') as f:
            for line in ldap_lines:
                f.write(line)
        run(['/bin/systemctl', 'restart', 'sssd.service'], stdout=DEVNULL)


def start_sytemtap() -> Popen:
    print(f'Starting the systemtap script: {args.systemtap_script}')
    stap_cmd = ['stap', '-w', '-g', f'{args.systemtap_script}', '-o', f'{args.stap_output}']
    print(' '.join(stap_cmd))
    stap_process = Popen(stap_cmd, stdout=DEVNULL, stderr=STDOUT)
    sleep(5)
    return stap_process


if not os.path.isfile(sss_cache) or not os.path.isfile(sssctl):
    print('Please install the sssd_tools package')
    exit(1)


# TODO change the return value to a list if the content
# won't be needed in other ways
def check_ldap_config(parser: argparse.ArgumentParser, arg: str):
    if not os.path.isfile(arg):
        parser.error(f'The file {arg} does not exist!')
    else:
        return open(arg, 'r')


parser = argparse.ArgumentParser()
parser.add_argument('-p', '--providers', nargs='+', default=providers)
parser.add_argument('-r', '--requests-count', type=int, default=1)
parser.add_argument('-s', '--systemtap-script', type=str, default='sbus_tap.stp')
parser.add_argument('-o', '--stap-output', type=str, default='csv/stap.csv')
parser.add_argument('-l', '--ldap-config', default='conf/sssd-ldap.conf',
                    type=lambda x: check_ldap_config(parser, x))

args = parser.parse_args()


prepare_providers(args.providers)

stap = start_sytemtap()

for provider, usernames in users.items():
    if provider in args.providers:
        print(f'Run for {provider} has started')
        for user in usernames:
            print(f'Fetching {user}')
            for i in range(args.requests_count):
                run([sss_cache, '-E'])
                try:
                    pwd.getpwnam(user)
                except KeyError as e:
                    print('Error:', e)


print('Test finished successfully!')
stap.terminate()
resume_providers()
args.ldap_config.close()
