if ! ansible-playbook -i inventory/hosts launch-ec2.yml; then echo 'aborting'; exit 1; fi
sleep 120;
echo 'sleeping a minute to give nodes time to boot';
sleep 60;
if ! ansible-playbook setup.yml; then echo 'aborting'; exit 1; fi
if ! ansible-playbook boot.yml; then echo 'aborting'; exit 1; fi
if ! ansible-playbook elarch.yml; then echo 'aborting'; exit 1; fi
