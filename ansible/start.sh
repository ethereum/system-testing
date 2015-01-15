if inventory/ec2.py > /dev/null ;
    then
        echo 'cluster is already up';
        exit 1
    fi
ansible-playbook -i inventory/hosts launch-ec2.yml
ansible-playbook setup.yml
ansible-playbook boot.yml
ansible-playbook elarch.yml
