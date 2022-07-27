from pathlib import Path
import re
from subprocess import PIPE, Popen

from hyperfine import hf
from systemtap import stap
from util import manage_providers, parameter_parser


def check_tools(tools: list[str]) -> None:
    for t in tools:
        if not Path(t).exists():
            raise IOError(f'The {t} command missing.' +
                          ' Please install the sssd_tools package')


def check_sudo():
    _, stderr = Popen([args.sss_cache, '-E'], stderr=PIPE).communicate()
    if re.search('root', str(stderr)) is not None:
        raise OSError('This test suite needs to be with root privileges!')


args = parameter_parser.parse_argumets()
check_tools([args.sss_cache, args.sssctl])
check_sudo()

# Disconnect and track redundant providers for reconnection in the end
closed_providers = manage_providers\
                    .prepare_providers(providers=args.providers,
                                       sssctl=args.sssctl,
                                       sssd_conf=args.sssd_conf,
                                       ldap_template=args.ldap_template)

try:
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
        # Adjust the list of users to comply with the chosen providers
        users = hf.choose_users(args.providers, args.hf_parameters)
        hf.run_benchmark(args.hf_runs, ','.join(users),
                         args.sss_cache, args.hf_output)
        print('Hyperfine tests finished successfully!')

except Exception as e:
    print('An exception occured!\n', e)

finally:
    if len(closed_providers) > 0:
        manage_providers.resume_providers(closed_providers, args.sss_cache,
                                          args.ldap_template, args.sssd_conf)
