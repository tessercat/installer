# Installer

This repo is
a git and Python environment
to run Ansible playbooks
on localhost
that install my hobby projects
on a Debian 12 host.


## Install the installer

Clone repo and init git and Python environments as root.

    cd /opt
    apt -y update
    apt -y install git python3-venv
    git clone https://github.com/tessercat/installer.git
    chmod 0700 installer
    cd installer

    # Roles and playbooks are in git submodules.
    git submodule init
    git submodule update

    python3 -m venv venv
    . venv/bin/activate
    pip install --upgrade pip setuptools wheel pip-tools
    pip-sync reqs/prod.txt


## Run the stack playbook

See the
[`stack-deploy`](https://github.com/tessercat/stack-deploy)
repo's readme
for more information.

Copy vars from the submodule.

    cp stack-deploy/stack-vars.yml .

Read and edit the copied vars file.

Activate the venv
and run the playbook.

    ansible-playbook stack-deploy/deploy.yml \
    -i stack-deploy/hosts \
    -e @stack-vars.yml


## Run the index playbook

See the
[`index-deploy`](https://github.com/tessercat/index-deploy)
repo's readme
for more information.

Activate the venv
and run the playbook.

    ansible-playbook index-deploy/deploy.yml \
    -i stack-deploy/hosts \
    -e @stack-vars.yml


## Run the daoistic playbook

See the
[`daoistic-deploy`](https://github.com/tessercat/daoistic-deploy)
repo's readme
for more information.

Activate the venv
and run the playbook.

    ansible-playbook daoistic-deploy/deploy.yml \
    -i stack-deploy/hosts \
    -e @stack-vars.yml

Add `daoistic.service`
to the `monitored_services` stack var
and re-run the stack playbook.

## Run the dictionary playbook

See the
[`dict-deploy`](https://github.com/tessercat/dict-deploy)
repo's readme
for more information.

Copy vars from the submodule.
    
    cp dict-deploy/dict-vars.yml .

Read and edit the copied vars file.

Activate the venv
and run the playbook.

    ansible-playbook dict-deploy/deploy.yml \
    -i stack-deploy/hosts \
    -e @stack-vars.yml \
    -e @dict-vars.yml

Add `dictionary.service`
to the `monitored_services` stack var
and re-run the stack playbook.
