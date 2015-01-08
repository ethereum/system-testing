#!/usr/bin/env python

import sys
import os

# Augment PYTHONPATH to find Python modules relative to this file path
# This is so that we can find the modules when running from a local checkout
# installed as editable with `pip install -e ...` or `python setup.py develop`
local_module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'lib')
)
sys.path.append(local_module_path)

import ansible.playbook
import ansible.utils.template
from ansible import errors
from ansible import callbacks
from ansible import utils
from ansible.color import ANSIBLE_COLOR, stringc
from ansible.callbacks import display


def colorize(lead, num, color):
    """ Print 'lead' = 'num' in 'color' """
    if num != 0 and ANSIBLE_COLOR and color is not None:
        return "%s%s%-15s" % (stringc(lead, color), stringc("=", color), stringc(str(num), color))
    else:
        return "%s=%-4s" % (lead, str(num))


def hostcolor(host, stats, color=True):
    if ANSIBLE_COLOR and color:
        if stats['failures'] != 0 or stats['unreachable'] != 0:
            return "%-37s" % stringc(host, 'red')
        elif stats['changed'] != 0:
            return "%-37s" % stringc(host, 'yellow')
        else:
            return "%-37s" % stringc(host, 'green')
    return "%-26s" % host


def run_playbook(playbook):
    ''' run ansible-playbook operations '''

    only_tags = []
    skip_tags = []
    extra_vars = {}
    sshpass = None
    sudopass = None
    su_pass = None
    vault_pass = None

    inventory = ansible.inventory.Inventory(host_list='/etc/ansible/hosts',
                                            vault_password=vault_pass)

    if len(inventory.list_hosts()) == 0:
        raise errors.AnsibleError("provided hosts list is empty")

        stats = callbacks.AggregateStats()
        playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
        runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)

        pb = ansible.playbook.PlayBook(
            playbook=playbook,
            module_path=None,
            inventory=inventory,
            forks=None,
            remote_user=None,
            remote_pass=sshpass,
            callbacks=playbook_cb,
            runner_callbacks=runner_cb,
            stats=stats,
            timeout=None,
            transport=None,
            sudo=None,
            sudo_user=None,
            sudo_pass=sudopass,
            extra_vars=extra_vars,
            private_key_file=None,
            only_tags=only_tags,
            skip_tags=skip_tags,
            check=None,
            diff=None,
            su=None,
            su_pass=su_pass,
            su_user=None,
            vault_password=vault_pass,
            force_handlers=None
        )

        failed_hosts = []
        unreachable_hosts = []

        try:

            pb.run()

            hosts = sorted(pb.stats.processed.keys())
            display(callbacks.banner("PLAY RECAP"))
            playbook_cb.on_stats(pb.stats)

            for h in hosts:
                t = pb.stats.summarize(h)
                if t['failures'] > 0:
                    failed_hosts.append(h)
                if t['unreachable'] > 0:
                    unreachable_hosts.append(h)

            retries = failed_hosts + unreachable_hosts

            if len(retries) > 0:
                filename = pb.generate_retry_inventory(retries)
                if filename:
                    display("           to retry, use: --limit @%s\n" % filename)

            for h in hosts:
                t = pb.stats.summarize(h)

                display("%s : %s %s %s %s" % (
                    hostcolor(h, t),
                    colorize('ok', t['ok'], 'green'),
                    colorize('changed', t['changed'], 'yellow'),
                    colorize('unreachable', t['unreachable'], 'red'),
                    colorize('failed', t['failures'], 'red')),
                    screen_only=True
                )

                display("%s : %s %s %s %s" % (
                    hostcolor(h, t, False),
                    colorize('ok', t['ok'], None),
                    colorize('changed', t['changed'], None),
                    colorize('unreachable', t['unreachable'], None),
                    colorize('failed', t['failures'], None)),
                    log_only=True
                )

            print ""
            if len(failed_hosts) > 0:
                return 2
            if len(unreachable_hosts) > 0:
                return 3

        except errors.AnsibleError, e:
            display("ERROR: %s" % e, color='red')
            return 1

    return 0


def run(playbook_fn):
    display(" ", log_only=True)
    display(" ".join(sys.argv), log_only=True)
    display(" ", log_only=True)
    try:
        return run_playbook(playbook_fn)
    except errors.AnsibleError, e:
        display("ERROR: %s" % e, color='red', stderr=True)
        sys.exit(1)
    except KeyboardInterrupt, ke:
        display("ERROR: interrupted", color='red', stderr=True)
        sys.exit(1)


if __name__ == "__main__":
    run(sys.argv[1])
