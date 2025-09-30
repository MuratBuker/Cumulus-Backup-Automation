# Introduction

This repository contains Ansible playbooks and related files for automating backup and configuration management tasks on Cumulus Linux network devices. The playbooks are designed to streamline operations such as backing up configurations, restoring configurations, and managing device settings.

## Prerequisites

- Ansible installed on your control machine.
- Access to Cumulus Linux devices with appropriate permissions.
- SSH access to the devices.
- Basic understanding of Ansible and YAML syntax.
- Python installed on the control machine (for Ansible).

## Setup

1. Clone the repository to your local machine:
2. Navigate to the repository directory:
    cd Cumulus-Backup-Automation
3. Install any required Ansible collections or roles (if applicable).
4. Update the inventory file (inventory.ini) with your Cumulus Linux device details.
5. Update the playbooks with any specific configurations or tasks as needed.

## Running the Playbook

- To run a specific playbook, use the following command:

~~~bash
ansible-playbook -i inventory.ini playbook_name.yml
~~~

- Monitor the output for any errors or confirmations of successful execution.

## Playbook Variables

You can change below variables in the playbook as per your requirements.

~~~yaml
  vars:
    dest_path: "/root/{{ datacenter }}"
    folder: "{{ dest_path }}/{{ inventory_hostname }}/{{ hostvars['localhost']['backup_date'] }}"
    filename: "{{ folder }}/backup_{{ hostvars['localhost']['backup_date'] }}_{{ hostvars['localhost']['backup_time'] }}.tgz"
    latest_file: "{{ dest_path }}/{{ inventory_hostname }}/latest/latest.tgz"
~~~

- `dest_path`: The base directory where backups will be stored.
- `folder`: The specific folder for the current backup, organized by hostname and date.
- `filename`: The full path and name of the backup file.
- `latest_file`: The path to the latest backup file for easy access.
- `datacenter`: A variable that should be defined in your inventory or playbook to specify the data center name.
- `backup_date` and `backup_time`: Variables that should be defined in your playbook or inventory to timestamp the backups.
- `inventory_hostname`: A built-in Ansible variable that represents the current host being managed.

### Contributing

- Feel free to fork the repository and submit pull requests for improvements or additional features.
- Please ensure that your code adheres to the existing style and includes appropriate documentation.
- Report any issues or bugs via the repository's issue tracker.
