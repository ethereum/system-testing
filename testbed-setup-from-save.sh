#!/bin/bash
set -e

EC2_REGION=${1:-us-west-1} 
SCRIPTDIR=`dirname $(readlink --canonicalize $0)`

if ! grep --silent '\[Credentials\]' ~/.boto; then
   	echo "No AWS credentials set. Please fix"
	exit -1
fi


cd $SCRIPTDIR/ansible

# the region is also stored in the inventory control file, adjust there, too
sed --in-place=.bak "s/^regions =.*/regions = $EC2_REGION/" inventory/ec2.ini

echo "Setting up in $EC2_REGION region from previously saved state."
echo "This will only work if instance configuration was previously saved for this region!"
read -p "[Enter] to continue if region is right."

ansible-playbook ec2-setup-from-save.yml --extra-vars=ec2_region=$EC2_REGION --inventory-file=inventory/hosts
./inventory/ec2.py --refresh-cache 
ansible-playbook client-prepare.yml
ansible-playbook client-start-bootstrap.yml
ansible-playbook elarch-start.yml

# still needs to create dag, so it's not as fast as it could be
