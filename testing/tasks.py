#!/usr/bin/env python

import sys
import time
import json
import logging
import boto.ec2
from fabric.api import settings, task, local, abort, shell_env
import futures
import ConfigParser
from os.path import expanduser

logger = logging.getLogger(__name__)

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

def docker(cmd, capture=False):
    """
    Run Docker command
    """
    return local("docker %s" % cmd, capture=capture)

def machine(cmd, capture=False):
    """
    Run Machine command
    """
    return local("docker-machine %s" % cmd, capture=capture)

@task
def machine_list():
    """
    List machines
    """
    return machine("ls", capture=True)

@task
def create(vpc, region, zone, nodename, ami=None):
    """
    Launch an AWS instance
    """
    machine(("create "
             "--driver amazonec2 "
             "--amazonec2-access-key %s "
             "--amazonec2-secret-key %s "
             "--amazonec2-vpc-id %s "
             "--amazonec2-region %s "
             "--amazonec2-zone %s "
             "--amazonec2-root-size 8 "
             "--amazonec2-security-group system-testing "
             "%s"
             "%s" % (
                 AWS_ACCESS_KEY,
                 AWS_SECRET_KEY,
                 vpc,
                 region,
                 zone,
                 ("--amazonec2-ami %s " % ami) if ami else "",
                 nodename)))

@task
def cleanup(containers):
    """
    Generic cleanup routine for containers and images
    """
    with settings(warn_only=True):
        for container in containers:
            docker("stop %s" % container)
            docker("rm $(docker ps -a -q)")
            docker("rmi $(docker images -f 'dangling=true' -q)")

def machine_env(nodename):
    env = {}
    env_export = machine("env %s" % nodename, capture=True)
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
    env['tls'] = tls
    env['cert_path'] = cert_path
    env['host'] = host
    return env

@task
def active(nodename):
    machine("active %s" % nodename)

@task
def pull(image):
    docker("pull %s" % image)

@task
def build(client, tag):
    docker("build -t %s %s", tag, client)

@task
def run(nodename, image, options, command):
    docker("run --name %s %s %s %s" % (nodename, options, image, command))

@task
def stop(nodename):
    docker("stop %s" % nodename)

@task
def exec_(container, command):
    docker("exec -it %s %s", container, command)

@task
def run_on(nodename, image, options="", command="", capture=False):
    env = machine_env(nodename)
    if not env:
        abort("Error getting machine environment")
    with shell_env(DOCKER_TLS_VERIFY=env['tls'], DOCKER_CERT_PATH=env['cert_path'], DOCKER_HOST=env['host']):
        run(nodename, image, options, command)

@task
def stop_on(nodename, capture=False):
    env = machine_env(nodename)
    if not env:
        abort("Error getting machine environment")
    with shell_env(DOCKER_TLS_VERIFY=env['tls'], DOCKER_CERT_PATH=env['cert_path'], DOCKER_HOST=env['host']):
        stop(nodename)

@task
def docker_on(nodename, command):
    env = machine_env(nodename)
    if not env:
        abort("Error getting machine environment")
    with shell_env(DOCKER_TLS_VERIFY=env['tls'], DOCKER_CERT_PATH=env['cert_path'], DOCKER_HOST=env['host']):
        docker(command)

@task
def exec_on(nodename, container, command):
    env = machine_env(nodename)
    if not env:
        abort("Error getting machine environment")
    with shell_env(DOCKER_TLS_VERIFY=env['tls'], DOCKER_CERT_PATH=env['cert_path'], DOCKER_HOST=env['host']):
        exec_(container, command)

@task
def pull_on(nodename, image):
    env = machine_env(nodename)
    if not env:
        abort("Error getting machine environment")
    with shell_env(DOCKER_TLS_VERIFY=env['tls'], DOCKER_CERT_PATH=env['cert_path'], DOCKER_HOST=env['host']):
        pull(image)

@task
def build_on(nodename, client, tag):
    env = machine_env(nodename)
    if not env:
        abort("Error getting machine environment")
    with shell_env(DOCKER_TLS_VERIFY=env['tls'], DOCKER_CERT_PATH=env['cert_path'], DOCKER_HOST=env['host']):
        build(tag, client)

@task
def launch_prepare_nodes(vpc, region, zone, clients=implementations):
    """
    Launch nodes to prepare AMIs using create()
    """
    max_workers = len(clients)

    # Launch prepare nodes
    start = time.time()
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_client = dict((executor.submit(create, vpc, region, zone, "prepare-%s" % client), client)
                                for client in clients)

    for future in futures.as_completed(future_to_client, 300):
        client = future_to_client[future]
        if future.exception() is not None:
            logger.info('%r generated an exception: %s' % ("Launching prepare-%s" % client, future.exception()))

    logger.info("Launch prepare duration: %ss" % (time.time() - start))

@task
def prepare_nodes(region, zone, clients=implementations, images=None):
    """
    Prepare client nodes AMIs using prepare_ami()
    """
    max_workers = len(clients)
    ami_ids = {}

    # Run preparation tasks, extending base client images and creating new AMIs
    start = time.time()
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_client = dict((executor.submit(prepare_ami,
                                                 region,
                                                 zone,
                                                 "prepare-%s" % client,
                                                 client,
                                                 image=images[client] if images else None), client)
                                for client in clients)

    for future in futures.as_completed(future_to_client, 600):
        client = future_to_client[future]
        if future.exception() is not None:
            logger.info('%r generated an exception: %s' % ("prepare-%s" % client, future.exception()))
        else:
            ami_id = future.result()
            logger.info('%r returned: %s' % ("prepare-%s" % client, ami_id))
            ami_ids[client] = ami_id

    # Save AMI IDs to file
    with open('amis.json', 'w') as f:
        json.dump(ami_ids, f)

    logger.info("Prepare duration: %ss" % (time.time() - start))

    return ami_ids

@task
def bootstrap(vpc, region, zone, ami_ids, nodes):
    """
    Launch bootnodes and client nodes using create()
    """
    max_workers = len(nodes['cpp'] + nodes['go'] + nodes['python'])

    start = time.time()
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_node = dict((executor.submit(create, vpc, region, zone, nodename, ami=ami_ids['cpp']), nodename)
                           for nodename in nodes['cpp'])
        logger.info(future_node)
        future_node.update(dict((executor.submit(create, vpc, region, zone, nodename, ami=ami_ids['go']), nodename)
                           for nodename in nodes['go']))
        logger.info(future_node)
        future_node.update(dict((executor.submit(create, vpc, region, zone, nodename, ami=ami_ids['python']), nodename)
                           for nodename in nodes['python']))
        logger.info(future_node)

    for future in futures.as_completed(future_node, 300):
        nodename = future_node[future]
        if future.exception() is not None:
            logger.info('%r generated an exception: %s' % (nodename, future.exception()))
        # else:  # No return value as we're not capturing create()'s output
        #     logger.info('%r returned: %s' % (nodename, future.result()))

    logger.info("Bootstrap duration: %ss" % (time.time() - start))

@task
def run_containers(nodes, images, options, commands):
    """
    Run client nodes on machines using run_on()
    """
    if images is None:
        images = {}
        for client in implementations:
            images[client] = "ethereum/client-%s" % client

    start = time.time()
    with futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_node = dict((executor.submit(run_on,
                                            nodename,
                                            images['cpp'],
                                            options['cpp'],
                                            commands['cpp']), nodename)
                           for nodename in nodes['cpp'])
        future_node.update(dict((executor.submit(run_on,
                                                 nodename,
                                                 images['go'],
                                                 options['go'],
                                                 commands['go']), nodename)
                           for nodename in nodes['go']))
        future_node.update(dict((executor.submit(run_on,
                                                 nodename,
                                                 images['python'],
                                                 options['python'],
                                                 commands['python']), nodename))
                           for nodename in nodes['python'])

    for future in futures.as_completed(future_node, 30):
        nodename = future_node[future]
        if future.exception() is not None:
            logger.info('%r generated an exception: %s' % (nodename, future.exception()))

    logger.info("Bootstrap duration: %ss" % (time.time() - start))

@task
def stop_containers(nodenames):
    """
    Stop client nodes on machines using stop_on()
    """
    start = time.time()
    with futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_node = dict((executor.submit(stop_on,
                                            nodename), nodename)
                           for nodename in nodenames)

    for future in futures.as_completed(future_node, 30):
        nodename = future_node[future]
        if future.exception() is not None:
            logger.info('%r generated an exception: %s' % (nodename, future.exception()))

    logger.info("Stop duration: %ss" % (time.time() - start))

@task
def teardown(nodenames):
    # TODO use futures
    for nodename in nodenames:
        machine("rm %s" % nodename)

# TODO
@task
def bootnode_run_on(nodename, image, options):
    env = machine_env(nodename)
    ip = env['host'][6:-5]
    run_on(
        nodename,
        image,
        options,
        "--verbosity 9 --client-name %s --mining off --mode full --upnp off --public-ip %s" % (
            nodename,
            ip))

# TODO
@task
def client_run_on(nodename, image, options, command):
    env = machine_env(nodename)
    ip = env['host'][6:-5]

    run_on(
        nodename,
        image,
        options,
        command.format(ip=ip))

# TODO per-user nodenames / tags
@task
def prepare_ami(region, zone, nodename, client, image=None):
    """
    Prepare client AMI
    """
    if image is None:
        image = "ethereum/client-%s" % client

    # Get our Instance ID
    inspect = json.loads(machine("inspect %s" % nodename, capture=True))
    instance_id = inspect['Driver']['InstanceId']
    # machine("ssh %s env" % nodename)

    # Pull base image
    pull_on(nodename, image)

    # TODO create new docker image w/ logstash-forwarder

    # Stop the instance
    machine("stop %s" % nodename)

    # Create EC2 connection with boto
    ec2 = boto.ec2.connect_to_region(region)

    # Cleanup old AMIs
    images = ec2.get_all_images(filters={'tag:Name': "prepared-%s" % client})
    for image in images:
        image.deregister(delete_snapshot=True)
        logger.info("Deleted AMI " + image.id)

    # Create new AMI
    ami_id = ec2.create_image(instance_id, "prepared-%s" % client, description="Prepared %s AMI" % client)

    # Tag new AMI
    image = ec2.get_all_images(image_ids=ami_id)[0]
    image.add_tag("Name", "prepared-%s" % client)

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

@task
def run_scenarios(scenarios):
    """
    Run test scenarios
    """
    for scenario in scenarios:
        local("py.test -vvrs %s" % scenario)
