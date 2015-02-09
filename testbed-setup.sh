#!/bin/bash

EC2_REGION=${1:-us-west-1} 
SCRIPTDIR=`dirname $(readlink --canonicalize $0)`
cd $SCRIPTDIR/ansible

if ! grep --silent '\[local\]' "/etc/ansible/hosts"; then
   	echo "Needs an entry like"
   	echo "[local]"
	echo "localhost ansible_connection=local"
	echo "in /etc/ansible/hosts"
	echo "to function properly. Please fix"
	exit -1
fi

if ! grep --silent '\[Credentials\]' ~/.boto; then
   	echo "No AWS credentials set. Please fix"
	exit -1
fi

if [ $EC2_REGION != "us-west-1" ] ; then
	echo "Make sure you have adjusted ec2.ini for your region! Otherwise will fail"
	read -p "[Enter] to continue."
fi

echo "Setting up in $EC2_REGION region."

ansible-playbook ec2-setup.yml	 			--extra-vars=ec2_region=$EC2_REGION && \
ansible-playbook client-setup.yml 			--extra-vars=ec2_region=$EC2_REGION && \
ansible-playbook client-setup-bootstrap.yml --extra-vars=ec2_region=$EC2_REGION && \
ansible-playbook elarch-setup.yml 			--extra-vars=ec2_region=$EC2_REGION 
