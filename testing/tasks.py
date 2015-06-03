#!/usr/bin/env python

import sys
import time
import json
import logging
import boto.ec2
import nodeid_tool
import ConfigParser
import concurrent.futures as futures
from os.path import expanduser
from progressbar import ProgressBar, Percentage, Bar, Timer, ETA
from contextlib import contextmanager
from fabric.state import output
from fabric.api import settings, lcd, task, local, abort, shell_env, env

logger = logging.getLogger(__name__)

class FabricException(Exception):
    pass
env.abort_exception = FabricException
# env.warn_only = True

# Load .boto config file
user_home = expanduser("~")
config = ConfigParser.ConfigParser()
config.read([str(user_home + "/.boto")])

# Get the credentials
AWS_ACCESS_KEY = config.get('Credentials', 'aws_access_key_id')
AWS_SECRET_KEY = config.get('Credentials', 'aws_secret_access_key')

# Warn if no credentials
if AWS_ACCESS_KEY is None or AWS_SECRET_KEY is None:
    logger.info("No AWS credentials set. Please set them in ~/.boto")
    raise SystemExit

implementations = ["cpp", "go", "python"]

widgets = ['Progress: ', Percentage(), '   ', Timer(), ' ', Bar(marker='#', left='[', right=']'), ' ', ETA()]
completed = 0

def set_logging(debug=False):
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
            datefmt="%H:%M:%S")
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            datefmt="%H:%M:%S")

        # Set Fabric' output level, defaults:
        # {'status': True, 'stdout': True, 'warnings': True, 'running': True,
        #  'user': True, 'stderr': True, 'aborts': True, 'debug': False}
        if not debug:
            output['aborts'] = False
            output['warnings'] = False
            output['running'] = False
            output['status'] = False

    eslogger = logging.getLogger('elasticsearch')
    eslogger.setLevel(logging.WARNING)
    urllogger = logging.getLogger('urllib3')
    urllogger.setLevel(logging.WARNING)

def append_log(line):
    with open("debug.log", "a") as logfile:
        logfile.write("%s\n" % line)

@contextmanager
def rollback(nodenames):
    try:
        yield
    except SystemExit:
        teardown(nodenames)
        abort("Bad failure...")

def machine_env(nodename):
    env_ = {}
    env_export = machine("env %s" % nodename)
    exports = env_export.splitlines()
    for export in exports:
        export = export[7:]  # remove "export "...
        if export.startswith("DOCKER_TLS_VERIFY"):
            logger.debug(export)
            tls = export.split("=")[-1]
        if export.startswith("DOCKER_CERT_PATH"):
            logger.debug(export)
            cert_path = export.split("=")[-1][1:-1]  # remove quotes
        if export.startswith("DOCKER_HOST"):
            logger.debug(export)
            host = export.split("=")[-1]
    if not tls or not cert_path or not host:
        logger.debug(exports)
        return False
    env_['tls'] = tls
    env_['cert_path'] = cert_path
    env_['host'] = host
    return env_

def create(vpc, region, zone, nodename, ami=None, securitygroup="docker-machine", capture=True, progress=None):
    """
    Launch an AWS instance
    """
    try:
        out = local(("docker-machine create "
                     "--driver amazonec2 "
                     "--amazonec2-access-key %s "
                     "--amazonec2-secret-key %s "
                     "--amazonec2-vpc-id %s "
                     "--amazonec2-region %s "
                     "--amazonec2-zone %s "
                     "--amazonec2-instance-type %s "
                     "--amazonec2-root-size 8 "
                     "--amazonec2-security-group %s "
                     "%s"
                     "%s" % (AWS_ACCESS_KEY,
                             AWS_SECRET_KEY,
                             vpc,
                             region,
                             zone,
                             "t2.medium",  # TODO evaluate final instance types / permanent ElasticSearch
                             securitygroup,
                             ("--amazonec2-ami %s " % ami) if ami else "",
                             nodename)),
                    capture=capture)
        if "Error" in out:
            append_log('Error creating %s, removing... The error was: %r' % (nodename, out))
            out = machine('rm -f %s' % nodename)
            append_log("Removed: %s" % out)
        else:
            append_log("Launched %s: %s" % (nodename, out))
            if progress:
                global completed
                completed += 9
                progress.update(completed)
    except FabricException as e:
        append_log('Exception creating %s, removing... The error was: %r' % (nodename, e))
        out = machine('rm -f %s' % nodename)
        append_log("Removed: %s" % out)

def docker(cmd, capture=True):
    """
    Run Docker command
    """
    try:
        out = local("docker %s" % cmd, capture=capture)
        return out
    except FabricException as e:
        append_log("Exception running docker: %r" % e)

def machine(cmd, capture=True, progress=None):
    """
    Run Machine command
    """
    try:
        out = local("docker-machine %s" % cmd, capture=capture)
        if progress:
            global completed
            completed += 1
            progress.update(completed)
        return out
    except FabricException as e:
        append_log("Exception running docker-machine: %r" % e)

def machine_list():
    """
    List machines
    """
    return machine("ls", capture=True)

def active(nodename):
    machine("active %s" % nodename)

def pull(image):
    docker("pull %s" % image)

def build(folder, tag):
    docker("build -t %s %s" % (tag, folder))

def run(name, image, options, command, capture=True):
    out = docker("run --name %s %s %s %s" % (name, options, image, command), capture=capture)
    append_log("Started: %s" % out)

def stop(nodename, rm=True, capture=True):
    out = docker("stop --time=30 %s" % nodename, capture=capture)
    append_log("Stopped: %s" % out)
    if rm:
        out = docker("rm %s" % nodename, capture=capture)
        append_log("Removed: %s" % out)

def exec_(container, command):
    docker("exec -it %s %s", container, command)

def run_on(nodename, image, options="", command="", name=None, progress=None):
    if name is None:
        name = nodename
    env_ = machine_env(nodename)
    if not env_:
        abort("Error getting machine environment")
    with shell_env(DOCKER_TLS_VERIFY=env_['tls'], DOCKER_CERT_PATH=env_['cert_path'], DOCKER_HOST=env_['host']):
        out = docker("run --name %s %s %s %s" % (name, options, image, command))
        append_log("Started on %s: %s" % (nodename, out))
        if progress:
            global completed
            completed += 10
            progress.update(completed)

def stop_on(nodename, capture=True, rm=True, progress=None):
    global completed
    env_ = machine_env(nodename)
    if not env_:
        abort("Error getting machine environment")
    with shell_env(DOCKER_TLS_VERIFY=env_['tls'], DOCKER_CERT_PATH=env_['cert_path'], DOCKER_HOST=env_['host']):
        out = docker("stop --time=30 %s" % nodename, capture=capture)
        append_log("Stopped on %s: %s" % (nodename, out))
        if progress:
            completed += 5
            progress.update(completed)
    if rm:
        with shell_env(DOCKER_TLS_VERIFY=env_['tls'], DOCKER_CERT_PATH=env_['cert_path'], DOCKER_HOST=env_['host']):
            out = docker("rm -f %s" % nodename, capture=capture)
            append_log("Removed on %s: %s" % (nodename, out))
            if progress:
                completed += 5
                progress.update(completed)

def docker_on(nodename, command, capture=True):
    env_ = machine_env(nodename)
    if not env_:
        abort("Error getting machine environment")
    with shell_env(DOCKER_TLS_VERIFY=env_['tls'], DOCKER_CERT_PATH=env_['cert_path'], DOCKER_HOST=env_['host']):
        return docker(command, capture=capture)

def exec_on(nodename, container, command):
    env_ = machine_env(nodename)
    if not env_:
        abort("Error getting machine environment")
    with shell_env(DOCKER_TLS_VERIFY=env_['tls'], DOCKER_CERT_PATH=env_['cert_path'], DOCKER_HOST=env_['host']):
        exec_(container, command)

def pull_on(nodename, image):
    env_ = machine_env(nodename)
    if not env_:
        abort("Error getting machine environment")
    with shell_env(DOCKER_TLS_VERIFY=env_['tls'], DOCKER_CERT_PATH=env_['cert_path'], DOCKER_HOST=env_['host']):
        pull(image)

def build_on(nodename, folder, tag):
    env_ = machine_env(nodename)
    if not env_:
        abort("Error getting machine environment")
    with shell_env(DOCKER_TLS_VERIFY=env_['tls'], DOCKER_CERT_PATH=env_['cert_path'], DOCKER_HOST=env_['host']):
        build(folder, tag)

def compose_on(nodename, command):
    env_ = machine_env(nodename)
    if not env_:
        abort("Error getting machine environment")
    with shell_env(DOCKER_TLS_VERIFY=env_['tls'], DOCKER_CERT_PATH=env_['cert_path'], DOCKER_HOST=env_['host']):
        local("docker-compose %s" % command)

def ssh_on(nodename, command):
    out = machine("ssh %s -- %s" % (nodename, command))
    return out

def scp_to(nodename, src, dest):
    env_ = machine_env(nodename)
    ip = env_['host'][6:-5]
    local("scp -q -o StrictHostKeyChecking=no "
          "-i ~/.docker/machine/machines/%s/id_rsa "
          "%s ubuntu@%s:%s" % (nodename, src, ip, dest))

@task
def cleanup(containers):
    """
    Generic cleanup routine for containers and images
    """
    with settings(warn_only=True):
        for container in containers:
            docker("stop --time=30 %s" % container)
            docker("rm $(docker ps -a -q)")
            docker("rmi $(docker images -f 'dangling=true' -q)")

def rm_data(nodename, progress=None):
    out = ssh_on(nodename, "sudo rm -rf /opt/data/*")
    if progress:
        global completed
        completed += 1
        progress.update(completed)
    return out

@task
def cleanup_data(nodenames):
    """
    Remove instances
    """
    max_workers = len(nodenames)

    global completed
    completed = 0
    progress = ProgressBar(widgets=widgets, maxval=max_workers).start()

    start = time.time()
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_node = dict((executor.submit(rm_data,
                                            nodename,
                                            progress=progress), nodename)
                           for nodename in nodenames)

    for future in futures.as_completed(future_node, 30):
        nodename = future_node[future]
        if future.exception() is not None:
            append_log('%r generated an exception' % nodename)
        if future.result():
            append_log("Data cleanup: %s" % future.result())

    progress.finish()
    logger.info("Data cleanup duration: %ss" % (time.time() - start))

@task
def teardown(nodenames):
    """
    Remove instances
    """
    max_workers = len(nodenames)

    global completed
    completed = 0
    progress = ProgressBar(widgets=widgets, maxval=max_workers).start()

    start = time.time()
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_node = dict((executor.submit(machine,
                                            "rm %s" % nodename,
                                            progress=progress), nodename)
                           for nodename in nodenames)

    for future in futures.as_completed(future_node, 30):
        nodename = future_node[future]
        if future.exception() is not None:
            append_log('%r generated an exception' % nodename)
        if future.result():
            append_log("Teardown: %s" % future.result())

    progress.finish()
    logger.info("Teardown duration: %ss" % (time.time() - start))

@task
def launch_prepare_nodes(vpc, region, zone, clients=implementations):
    """
    Launch nodes to prepare AMIs using create()
    """
    max_workers = len(clients)

    global completed
    completed = 0
    progress = ProgressBar(widgets=widgets, maxval=max_workers * 10).start()

    # Launch prepare nodes
    start = time.time()
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_client = dict((executor.submit(create, vpc, region, zone, "prepare-%s" % client,
                                                 progress=progress), client)
                                for client in clients)
        progress.update(max_workers)

    for future in futures.as_completed(future_to_client, 300):
        client = future_to_client[future]
        if future.exception() is not None:
            logger.info('%s generated an exception: %r' % ("Launching prepare-%s" % client, future.exception()))

    logger.info("Launch prepare duration: %ss" % (time.time() - start))

@task
def prepare_nodes(region, zone, es, clients=implementations, images=None, dag=False):
    """
    Prepare client nodes AMIs using prepare_ami()
    """
    max_workers = len(clients)
    ami_ids = {}

    global completed
    completed = 0
    progress = ProgressBar(widgets=widgets, maxval=max_workers * 100).start()

    # Run preparation tasks, extending base client images and creating new AMIs
    start = time.time()
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_client = dict((executor.submit(prepare_ami,
                                                 region,
                                                 zone,
                                                 "prepare-%s" % client,
                                                 es,
                                                 client,
                                                 image=images[client] if images else None,
                                                 dag=dag,
                                                 progress=progress), client)
                                for client in clients)

    for future in futures.as_completed(future_to_client, 1200):
        client = future_to_client[future]
        if future.exception() is not None:
            logger.info('%s generated an exception: %r' % ("prepare-%s" % client, future.exception()))
        else:
            ami_id = future.result()
            logger.info('%r returned: %s' % ("prepare-%s" % client, ami_id))
            ami_ids[client] = ami_id

    # Save AMI IDs to file
    with open('amis.json', 'w') as f:
        json.dump(ami_ids, f)

    progress.finish()
    logger.info("Prepare duration: %ss" % (time.time() - start))

    return ami_ids

@task
def setup_es(vpc, region, zone, user, passwd):
    # TODO per-user naming
    nodename = "elasticsearch"

    global completed
    completed = 0
    progress = ProgressBar(widgets=widgets, maxval=100).start()

    with settings(warn_only=False):
        with rollback([nodename]):
            # Launch ES node
            create(vpc, region, zone, nodename, securitygroup="elasticsearch", progress=progress)

            # Generate certificate and key for logstash-forwarder
            local("openssl req -x509 -batch -nodes -newkey rsa:2048 "
                  "-keyout elk-compose/logstash/conf/logstash-forwarder.key "
                  "-out elk-compose/logstash/conf/logstash-forwarder.crt "
                  "-subj /CN=logs.ethdev.com")
            progress.update(15)

            # Copy to logstash-forwarder's Dockerfile folder
            local("cp elk-compose/logstash/conf/logstash-forwarder.crt logstash-forwarder/")
            local("cp elk-compose/logstash/conf/logstash-forwarder.key logstash-forwarder/")
            progress.update(25)

            # Install htpasswd
            local("sudo apt-get install -q -y apache2-utils")
            progress.update(35)

            # Create htpasswd
            local("htpasswd -cb elk-compose/nginx/conf/htpasswd %s %s" % (user, passwd))
            progress.update(45)

            # Build ELK stack
            with lcd('elk-compose'):
                compose_on(nodename, "build")
            progress.update(75)

            # Run ELK stack
            with lcd('elk-compose'):
                compose_on(nodename, "up -d")
            progress.update(80)

    # Get our node IP
    es = {}
    machines = machine_list().splitlines()[1:]
    for mach in machines:
        fields = mach.split()
        ip = fields[-1][6:-5]
        if mach.startswith(nodename):
            es['ip'] = ip
    if not es:
        abort("Could not find our ElasticSearch node, aborting...")
    progress.update(90)

    # Save our ES node IP
    with open('es.json', 'w') as f:
        json.dump(es, f)

    progress.update(100)
    progress.finish()

    return es['ip']

@task
def launch_nodes(vpc, region, zone, ami_ids, nodes):
    """
    Launch bootnodes and testnodes using create()
    """
    max_workers = len(nodes['cpp'] + nodes['go'] + nodes['python'])

    global completed
    completed = 0
    progress = ProgressBar(widgets=widgets, maxval=max_workers * 10).start()

    start = time.time()
    with futures.ThreadPoolExecutor(max_workers=12) as executor:
        future_node = dict((executor.submit(create, vpc, region, zone, nodename,
                                            ami=ami_ids['cpp'],
                                            progress=progress), nodename)
                           for nodename in nodes['cpp'])
        future_node.update(dict((executor.submit(create, vpc, region, zone, nodename,
                                                 ami=ami_ids['go'],
                                                 progress=progress), nodename)
                           for nodename in nodes['go']))
        future_node.update(dict((executor.submit(create, vpc, region, zone, nodename,
                                                 ami=ami_ids['python'],
                                                 progress=progress), nodename)
                           for nodename in nodes['python']))
        progress.update(max_workers)

    for future in futures.as_completed(future_node, 300):
        nodename = future_node[future]
        if future.exception() is not None:
            append_log('%s generated an exception: %r' % (nodename, future.exception()))
        if future.result() and "Exception" not in future.result():
            append_log('Launched %s: %r' % (nodename, future.result()))

    progress.finish()
    logger.info("Launch duration: %ss" % (time.time() - start))

# TODO per-user nodenames / tags
@task
def prepare_ami(region, zone, nodename, es, client, image=None, dag=False, progress=None):
    """
    Prepare client AMI
    """
    if image is None:
        image = "ethereum/client-%s" % client

    global completed
    if progress:
        completed += 5
        progress.update(completed)

    # Get our Instance ID
    inspect = json.loads(machine("inspect %s" % nodename))
    instance_id = inspect['Driver']['InstanceId']
    if progress:
        completed += 5
        progress.update(completed)

    # Pull base image
    pull_on(nodename, image)
    if progress:
        completed += 10
        progress.update(completed)

    # Create docker container w/ logstash-forwarder
    # Build logstash-forwarder directly, docker-compose doesn't seem to
    # like getting called concurrently
    # with lcd('logstash-forwarder'):
    #     compose_on(nodename, "build")
    build_on(nodename, "logstash-forwarder", "forwarder")
    if progress:
        completed += 20
        progress.update(completed)

    # Run logstash-forwarder, using run_on so we can pass --add-host
    # with lcd('logstash-forwarder'):
    #     compose_on(nodename, "up -d")  # ElasticSearch IP
    run_on(
        nodename,
        "forwarder",
        ("-d "
         "-v /var/log/syslog:/var/log/syslog "
         "--add-host logs.ethdev.com:%s "
         "--restart always" % es),
        name="forwarder")
    if progress:
        completed += 5
        progress.update(completed)

    # Generate DAG
    if client == 'cpp':
        ssh_on(nodename, "sudo mkdir /opt/dag")  # see generate_dag()
    elif client == 'go':
        ssh_on(nodename, "sudo mkdir /opt/dag")  # see generate_dag()
    if dag and client != 'python':
        generate_dag(nodename, client, image)
        # FIXME For some reason, 'docker run' exits with 0
        # but never returns, so somewhere between futures,
        # Fabric and docker, there's an unhandled timeout
        # while generating DAG caches and getting no output...
        # We poll for 'Exited' in 'docker ps -a' and run with
        # -d in generate_dag() for now...
        dag_done = False
        logging.info("Generating DAG on %s..." % nodename)
        while dag_done is False:
            time.sleep(5)
            ps = docker_on(nodename, "ps -a")
            if "Exited" in ps:
                logging.info("DAG done on %s" % nodename)
                dag_done = True
    if progress:
        completed += 20
        progress.update(completed)

    # Stop the instance
    machine("stop %s" % nodename)
    if progress:
        completed += 5
        progress.update(completed)

    # Create EC2 connection with boto
    ec2 = boto.ec2.connect_to_region(region)

    # Cleanup old AMIs
    images = ec2.get_all_images(filters={'tag:Name': "prepared-%s" % client})
    for image in images:
        image.deregister(delete_snapshot=True)
        logger.info("Deleted AMI %s" % image.id)

    # Create new AMI
    ami_id = ec2.create_image(instance_id, "prepared-%s" % client, description="Prepared %s AMI" % client)

    # Tag new AMI
    image = ec2.get_all_images(image_ids=ami_id)[0]
    image.add_tag("Name", "prepared-%s" % client)
    if progress:
        completed += 10
        progress.update(completed)

    # Wait until the image is ready
    logger.info("Waiting for AMI to be available")
    while image.state == 'pending':
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(5)
        image.update()
    if image.state == 'available':
        return ami_id
    else:
        raise ValueError("Created AMI returned non-available state", image.state)

def account_on(nodename, image, progress=None):
    """
    Run geth with 'account new' on a node
    """
    # Create password file
    ssh_on(nodename, "sudo mkdir -p /opt/data")
    ssh_on(nodename, "sudo touch /opt/data/password")

    # Create account
    options = ("--volume /opt/data:/opt/data "
               "--entrypoint geth")
    command = ("--datadir /opt/data "
               "--password /opt/data/password "
               "account new")
    run_on(nodename, image, options, command)
    append_log("Created account on %s" % nodename)

    global completed
    if progress:
        completed += 5
        progress.update(completed)

    # Cleanup container
    docker_on(nodename, "rm %s" % nodename)
    if progress:
        completed += 5
        progress.update(completed)

@task
def create_accounts(nodenames, image):
    """
    Create geth accounts
    """
    max_workers = len(nodenames)

    global completed
    completed = 0
    progress = ProgressBar(widgets=widgets, maxval=max_workers * 10).start()

    start = time.time()
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_node = dict((executor.submit(account_on,
                                            nodename,
                                            image,
                                            progress=progress), nodename)
                           for nodename in nodenames)

    for future in futures.as_completed(future_node, 90):
        nodename = future_node[future]
        if future.exception() is not None:
            append_log('%r generated an exception: %s' % (nodename, future.exception()))

    progress.finish()
    logger.info("Create accounts duration: %ss" % (time.time() - start))

def generate_dag(nodename, client, image):
    """
    Generate DAG on node
    """

    # Set options (volume and entrypoint)
    # C++ and Go save the DAG cache in the ~/.ethash folder,
    # so we have to mount those as volumes,
    # after creating the host folder and file.
    if client == 'cpp':
        options = ('-d '  # using -d, see note in prepare_ami()
                   '--volume /opt/dag:/root/.ethash '
                   '--entrypoint eth')
        command = "--create-dag 0"
    elif client == 'go':
        options = ('-d '
                   '--volume /opt/dag:/root/.ethash '
                   '--entrypoint geth')
        command = "makedag 0 /root/.ethash"
    elif client == 'python':
        options = ('-d '
                   '--volume /opt/data:/opt/data '
                   '--entrypoint pyethapp')
        command = 'makedag'  # TODO
    else:
        raise ValueError("No implementation: %s" % client)

    run_on(nodename, image, options, command)

@task
def import_key(nodename, privkey, image):
    ssh_on(nodename, "'echo %s | sudo tee /opt/data/key'" % privkey)

    options = ('-d '
               '--volume /opt/data:/opt/data '
               '--entrypoint geth')
    command = ("--datadir /opt/data "
               "--password /opt/data/password "
               "account import /opt/data/key")

    run_on(nodename, image, options, command)
    stop_on(nodename)

@task
def run_bootnodes(nodes, images):
    options = dict()
    commands = dict()
    for impl in nodes:
        for nodename in nodes[impl]:
            env_ = machine_env(nodename)
            ip = env_['host'][6:-5]

            # Set options (daemonize, ports and entrypoint)
            if impl == 'cpp':
                options[nodename] = ('-d -p 30303:30303 -p 30303:30303/udp '
                                     '--entrypoint eth')
                commands[nodename] = ('--verbosity 9 '
                                      '--client-name %s '
                                      '--mining off '
                                      '--mode full '
                                      '--peers 25 '
                                      '--upnp off '
                                      '--public-ip %s"' % (nodename, ip))
            elif impl == 'go':
                options[nodename] = ('-d -p 30303:30303 -p 30303:30303/udp '
                                     '--entrypoint geth')
                commands[nodename] = ("--nodekeyhex=%s "
                                      "--port=30303 "
                                      "--maxpeers=25 "
                                      "--bootnodes 'enode://%s@10.0.0.0:10000'" % (nodeid_tool.topriv(nodename),
                                                                                   nodeid_tool.topub(nodename)))
            elif impl == 'python':
                options[nodename] = ('-d -p 30303:30303 -p 30303:30303/udp '
                                     '--entrypoint pyethapp')
                commands[nodename] = ''  # TODO
            else:
                raise ValueError("No implementation: %s" % impl)

    run_containers(nodes, images, options, commands)

def run_containers(nodes, images, options, commands):
    """
    Run client nodes on machines using run_on()
    """
    if images is None:
        images = {}
        for client in implementations:
            images[client] = "ethereum/client-%s" % client

    max_workers = len(nodes['cpp'] + nodes['go'] + nodes['python'])

    global completed
    completed = 0
    progress = ProgressBar(widgets=widgets, maxval=max_workers * 10).start()

    start = time.time()
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_node = dict((executor.submit(run_on,
                                            nodename,
                                            images['cpp'],
                                            options[nodename],
                                            commands[nodename],
                                            progress=progress), nodename)
                           for nodename in nodes['cpp'])
        future_node.update(dict((executor.submit(run_on,
                                                 nodename,
                                                 images['go'],
                                                 options[nodename],
                                                 commands[nodename],
                                                 progress=progress), nodename)
                           for nodename in nodes['go']))
        future_node.update(dict((executor.submit(run_on,
                                                 nodename,
                                                 images['python'],
                                                 options[nodename],
                                                 commands[nodename],
                                                 progress=progress), nodename)
                           for nodename in nodes['python']))

    for future in futures.as_completed(future_node, 90):
        nodename = future_node[future]
        if future.exception() is not None:
            append_log("Exception starting %s: %s" % (nodename, future.exception()))
        if future.result() and "Exception" not in future.result():
            append_log("Started: %s" % future.result())

    logger.info("Run duration: %ss" % (time.time() - start))

def stop_containers(nodenames):
    """
    Stop client nodes on machines using stop_on()
    """
    max_workers = len(nodenames)

    global completed
    completed = 0
    progress = ProgressBar(widgets=widgets, maxval=max_workers * 10).start()

    start = time.time()
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_node = dict((executor.submit(stop_on,
                                            nodename,
                                            progress=progress), nodename)
                           for nodename in nodenames)

    for future in futures.as_completed(future_node, 30):
        nodename = future_node[future]
        if future.exception() is not None:
            append_log("Exception stopping %s: %s" % (nodename, future.exception()))
        if future.result() and "Exception" not in future.result():
            append_log("Stopped: %s" % future.result())

    progress.finish()
    logger.info("Stop duration: %ss" % (time.time() - start))

@task
def run_scenarios(scenarios, norun=False, testnet=False):
    """
    Run test scenarios
    """
    try:
        for scenario in scenarios:
            norun = "--norun " if norun else ""
            testnet = "--testnet " if testnet else ""
            local("py.test -vvrs %s%s%s" % (norun, testnet, scenario))
    except FabricException as e:
        append_log("Exception running scenarios: %r" % e)
