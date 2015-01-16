# if inventory/ec2.py > /dev/null ;
#     then
#         echo 'cluster is already up';
#         exit 1
#     fi
if ! ansible-playbook -i inventory/hosts launch-ec2.yml; then echo 'aborting'; exit 1; fi
if ! ansible-playbook setup.yml; then echo 'aborting'; exit 1; fi
if ! ansible-playbook boot.yml; then echo 'aborting'; exit 1; fi
if ! ansible-playbook elarch.yml; then echo 'aborting'; exit 1; fi
