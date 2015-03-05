#!/bin/bash

EC2_REGION=${1:-us-west-1} 
SCRIPTDIR=`dirname $(readlink --canonicalize $0)`

if ! grep --silent '\[Credentials\]' ~/.boto; then
   	echo "No AWS credentials set. Please fix"
	exit -1
fi

if [ $EC2_REGION != "us-west-1" ] ; then
	echo "This is not the default region, and not testet thoroughly."
	read -p "[Enter] to continue."
fi

cd $SCRIPTDIR/ansible

# the region is also stored in the inventory control file, adjust there, too
sed --in-place=.bak "s/^regions =.*/regions = $EC2_REGION/" inventory/ec2.ini

echo "Setting up in $EC2_REGION region."

# --tag selecets implementation of bootstrap node
ansible-playbook ec2-setup.yml --extra-vars=ec2_region=$EC2_REGION --inventory-file=inventory/hosts && \
ansible-playbook client-setup.yml && \
ansible-playbook client-setup-bootstrap.yml --tag go && \  
ansible-playbook elarch-setup.yml 			-
