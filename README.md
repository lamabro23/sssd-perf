# This is a performance test suite for SSSD

Test suite created to measure the response time of [SSSD](https://github.com/SSSD/sssd).

## Prepare the environment

The test suite was created and tested with data providers in containers supplied by this [repository](https://github.com/SSSD/sssd-ci-containers).
To set up the environment needed to run the test suite start with the following steps:

1. Connect to FreeIPA:
    ```bash
    ipa-client-install --unattended --no-ntp --domain ipa.test --principal admin --password Secret123 --force-join
    ```
2. Connect to AD DS (samba):
    ```bash
    echo Secret123 | realm join samba.test
    ```
3. Connect to LDAP server by appending the contents of [this](https://github.com/lamabro23/sssd-perf/blob/master/systemtap/conf/sssd-ldap.conf) configuration file to */etc/sssd/sssd.conf*.
4. Restart SSSD:
    ```
    systemctl restart sssd.service
    ```

## Run the tests

The test suite contains tests made with [SystemTap](https://github.com/groleo/systemtap) and [hyperfine](https://github.com/sharkdp/hyperfine).
Both are run through the main [runner.py](https://github.com/lamabro23/sssd-perf/blob/master/runner.py) script.

The general parameters for this script are:
- `--providers` - takes in list of data provider to test with (defaul: [ipa, ldap, samba]).
- `--sssctl` - path to the *sssctl* binary (default: /usr/sbin/sssctl).
- `--sss_cache` - path to the *sss_cache* binary (default: /usr/sbin/sss_cache).
- `--sssd-conf` - path to the *sssd.conf* file (default: /etc/sssd/sssd.conf).
- `--ldap-template` - path to the template configuration of ldap domain in *sssd.conf* (default: systemtap/conf/sssd-ldap.conf).

### SystemTap
The flags for configuration of *SystemTap* tests:
- `--run-systemtap` - enable SystemTap tests (dafault: False).
- `--stap-script` - path to the probe script (default: systemtap/sbus_tap.stp).
- `--stap-output` - the name of the file for the captured data (default: systemtap/csv/stap.csv).
- `--stap-request-count` - the number of request to send to each of the data providers (default: 5).
- `--stap-verbosity` - start the probe script with higher level of verbosity (for debugging, default: False).

Example:
Start *SystemTap* tests with 500 requests to two providers: LDAP and FreeIPA:
```bash
python runner.py --run-systemtap --stap-request-count 500 --providers ldap ipa
```
### Hyperfine
The flags for configuration of *hyperfine* tests:
- `--run-hyperfine` - enable hyperfine tests (dafault: False).
- `--hf-output` - the name of the file for the captured data (default: systemtap/json/hf.json).
- `--hf-parameters` - a list of values for the command used during hyperfine's run (default: [admin@ipa.test, ...]).
- `--hf-runs` - number of runs to send do with each of the specified commands (default: 10).

Example:
Start *hyperine* tests with 100 runs of the command `id adminldap@ldap.test`:
```bash
python runner.py --run-hyperfine --hf-runs 500 --hf-parameters adminldap@ldap.test
```

## Generate the plots
...

