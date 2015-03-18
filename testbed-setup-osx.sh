#!/bin/bash
EC2_REGION=${1:-us-west-1}
SCRIPTDIR=`pwd`
echo $SCRIPTDIR

if ! grep --silent '\[Credentials\]' ~/.boto; then
   	echo "No AWS credentials set. Please fix"
	exit -1
fi

if [ $EC2_REGION != "us-west-1" ] ; then
	echo "This is not the default region, and not testet thoroughly."
	read -p "[Enter] to continue."
fi

cd $SCRIPTDIR/ansible

export EC2_REGION=us-west-1
echo "Setting up in $EC2_REGION region."

# --tag selecets implementation of bootstrap node
ansible-playbook ec2-setup.yml --extra-vars=ec2_region=$EC2_REGION --inventory-file=inventory/hosts.1 && \
ansible-playbook client-setup.yml && \
ansible-playbook client-setup-bootstrap.yml && \
ansible-playbook client-start-bootstrap.yml && \
ansible-playbook elarch-setup.yml
