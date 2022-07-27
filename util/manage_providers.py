import re
import shutil
from subprocess import DEVNULL, PIPE, Popen, STDOUT, run
from time import sleep

import ldap

ipa_cmd = {'join': 'sudo ipa-client-install --unattended --no-ntp'
                   ' --domain ipa.test --principal admin'
                   ' --password Secret123 --force-join',
           'leave': 'sudo ipa-client-install --uninstall'}

samba_cmd = {'join': 'sudo realm join samba.test',
             'leave': 'sudo realm leave'}

ldap_user = {'objectclass': b'posixAccount',
             'homeDirectory': b'/home/adminldap',
             'uidNumber': b'1000',
             'gidNumber': b'1000',
             'cn': b'Admin LDAP'}


def ldap_user_check() -> None:
    binddn = 'cn=Directory Manager'
    pwd = 'Secret123'
    basedn = 'dc=ldap,dc=test'
    scope = ldap.SCOPE_SUBTREE
    search = '(&(objectClass=posixAccount)(uidNumber=*)(|(cn=Admin LDAP)))'

    conn = ldap.initialize('ldap://master.ldap.test')
    conn.simple_bind_s(binddn, pwd)

    if len(conn.search_s(base=basedn, scope=scope, filterstr=search)) == 0:
        dn = 'uid=adminldap,dc=ldap,dc=test'
        conn.add_s(dn, [(k, v) for k, v in ldap_user.items()])


def prepare_providers(providers: list, sssctl: str,
                      sssd_conf: str, ldap_template: str) -> list[str]:
    closed_providers = []
    curr_joined = get_current_domains(sssctl)

    if 'ldap.test' in curr_joined:
        ldap_user_check()

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
        run(['sudo', '/bin/systemctl', 'restart', 'sssd.service'], stdout=DEVNULL)
        closed_providers.append('ldap')

    return closed_providers


def get_current_domains(sssctl: str) -> list[str]:
    p = Popen(['sudo', sssctl, 'domain-list'], stdout=PIPE, universal_newlines=True)
    stdout, _ = p.communicate()
    return stdout.split()


def remove_from_domains_list(line: str) -> str:
    opts = [', ldap.test', ', ldap.test, ', 'ldap.test, ']
    for o in opts:
        if o in line:
            return line.replace(o, '')
    return line


def resume_providers(providers: list, sss_cache: str,
                     ldap_template: str, sssd_conf: str) -> None:
    run(['sudo', sss_cache, '-E'])
    print('About to resume any previously closed providers')
    if 'ipa' in providers:
        run(ipa_cmd['join'].split(), stdout=DEVNULL, stderr=STDOUT)
    if 'samba' in providers:
        Popen(samba_cmd['join'].split(), stdin=PIPE,
              stdout=DEVNULL).communicate(input=b'Secret123')
    if 'ldap' in providers:
        with open(ldap_template) as ldap:
            # ldap.seek(0)
            ldap_lines = ldap.readlines()
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
        run(['sudo', '/bin/systemctl', 'restart', 'sssd.service'], stdout=DEVNULL)
