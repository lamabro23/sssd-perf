import re
from subprocess import DEVNULL, PIPE, Popen


def run_benchmark(runs: str, params: str, sss_cache: str, out: str):
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
