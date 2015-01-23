if ! ansible-playbook -i inventory/hosts ec2-setup.yml; then echo 'aborting'; exit 1; fi
sleep 120;
echo 'sleeping a minute to give nodes time to boot';
sleep 60;
if ! ansible-playbook client-setup.yml; then echo 'aborting'; exit 1; fi
if ! ansible-playbook client-setup-bootstrap.yml; then echo 'aborting'; exit 1; fi
if ! ansible-playbook elarch-setup.yml; then echo 'aborting'; exit 1; fi
