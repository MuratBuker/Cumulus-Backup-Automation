#! /bin/bash
ansible-playbook /root/ansible/NVIDIA/nvidia-backup-playbook.yaml -i /root/ansible/NVIDIA/inventory.ini
cd /root/equinix/
git add -A
git commit -m "Equinix Push"
git push
cd /root/kkb/
git add -A
git commit -m "KKB Push"
git push
cd /root/turksat/
git add -A
git commit -m "Turksat Push"
git push
cd /root/onprem/
git add -A
git commit -m " OnPrem Push"
git push
