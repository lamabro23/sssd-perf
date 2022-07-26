import re
from subprocess import PIPE, Popen


def run_benchmark(runs: str, params: str, sss_cache: str, out: str) -> None:
    print('Starting the hyperfine benchmarks')
    cmd = ['sudo', 'hyperfine', '--ignore-failure',
           '--runs', f'{runs}',
           '--parameter-list', 'user', f'{params}',
           '--prepare', f'{sss_cache} -E',
           '--export-json', f'{out}',
           'id {user}']

    hf = Popen(cmd, stderr=PIPE)
    _, stderr = hf.communicate()
    if re.search('Error', stderr.decode('utf-8')) is not None:
        raise IOError('Hyperfine exited with: ' + str(stderr.decode('utf-8')))
    hf.terminate()


def choose_users(providers: list, users: list) -> list[str]:
    res = []
    for p in providers:
        for u in users:
            if re.search(p, u) is not None:
                res.append(u)
    return res
