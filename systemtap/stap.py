import pwd
import re
from subprocess import DEVNULL, PIPE, Popen, STDOUT, run
from time import sleep

users = {'ipa': ['admin@ipa.test', 'wrong@ipa.test'],
         'samba': ['administrator@samba.test'],
         'ldap': ['adminldap@ldap.test']}


def send_requests(providers: list, sss_cache: str,
                  req_cnt: int, warm_up: bool) -> None:
    if warm_up:
        print("Starting SSSD warm-up")

    for provider, usernames in users.items():
        if provider in providers:
            if not warm_up:
                print(f'Run for {provider} has started')
            for user in usernames:
                if not warm_up:
                    print(f'  Fetching {user}')
                for _ in range(req_cnt):
                    run([sss_cache, '-E'])
                    try:
                        pwd.getpwnam(user)
                    except KeyError as e:
                        if re.search('wrong@.*\\.test', str(e)) is not None:
                            pass
                        else:
                            print('Error:', e)

    if warm_up:
        print('Warm-up finished')


def start_sytemtap(script: str, out: str, verbose: bool) -> Popen:
    print(f'Starting systemtap with the command:')
    stap_cmd = ['stap', '-w', '-g', f'{script}',
                '-o', f'{out}', f'{int(verbose)}']
    print(' ', ' '.join(stap_cmd))
    stap_process = Popen(stap_cmd, stdout=DEVNULL, stderr=STDOUT)
    sleep(5)
    return stap_process


def check_markers() -> None:
    probe_list = ['sss_dp_send', 'sss_dp_done',
                  'dp_req_send', 'dp_req_done',
                  'nss_getby_name_send', 'nss_getby_done']
    for probe in probe_list:
        stap_process = Popen(['stap', '-L', f'process("/usr/libexec/sssd/sssd_*").mark("{probe}")'],
                             stdout=PIPE)
        out, _ = stap_process.communicate()
        if out.decode('utf-8') == '':
            raise IOError(f'The probe \'{probe}\' is missing from the SSSD binary!')
