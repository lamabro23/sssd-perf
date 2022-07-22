import re
import shutil
from subprocess import DEVNULL, PIPE, Popen, STDOUT, run
from time import sleep

ipa_cmd = {'join': 'ipa-client-install --unattended --no-ntp'
                   ' --domain ipa.test --principal admin'
                   ' --password Secret123 --force-join',
           'leave': 'ipa-client-install --uninstall'}

samba_cmd = {'join': 'realm join samba.test',
             'leave': 'realm leave',
             'list': 'realm list --name-only'}


def prepare_providers(providers: list, sssctl: str,
                      sssd_conf: str, ldap_template: str) -> list[str]:
    closed_providers = []
    curr_joined = get_current_domains(sssctl)

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
        print('About to leave ldap domain')
        backup_conf = sssd_conf + '.perf_bkp'
        shutil.copy2(sssd_conf, backup_conf)
        with open(backup_conf, 'rt') as backup_conf, \
             open(ldap_template, 'r') as ldap_conf, \
             open(sssd_conf, 'w') as mod_conf:
            ldap_lines = ldap_conf.readlines()
            for line in backup_conf.readlines():
                if re.search('domains =.*ldap.test.*', line) is not None:
                    mod_conf.write(remove_from_domains_list(line))
                elif line not in ldap_lines:
                    mod_conf.write(line)
        run('/bin/systemctl restart sssd.service'.split(), stdout=DEVNULL)
        closed_providers.append('ldap')

    return closed_providers


def get_current_domains(sssctl: str) -> list[str]:
    p = Popen(sssctl, stdout=PIPE, universal_newlines=True)
    stdout, _ = p.communicate()
    return stdout.split()


def remove_from_domains_list(line: str) -> str:
    opts = [', ldap.test', ', ldap.test, ', 'ldap.test, ']
    for o in opts:
        if o in line:
            return line.replace(o, '')
    return line
