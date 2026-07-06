#! /bin/bash
ansible-playbook /root/ansible/NVIDIA/nvidia-backup-playbook.yaml -i /root/ansible/NVIDIA/inventory.ini
cd /root/dc1/
git add -A
git commit -m "DC 1 Push"
git push
cd /root/dc2/
git add -A
git commit -m "DC 2 Push"
git push
cd /root/dc3/
git add -A
git commit -m "DC 3 Push"
git push
cd /root/dc4/
git add -A
git commit -m "DC 4 Push"
git push
