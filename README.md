# distributed_merizosearch
This project implements a distributed data analysis pipeline for running the Merizo-search tool.

## Deploy the complete application
Provision the resources:
```bash
cd infra/
terraform init
terraform apply
```
Download dependencies and datasets, and deploy the application on the "Ecoli" and "Human" subsets:
```
cd ../ansible
ansible-playbook -i hosts master-playbook.yaml --key-file <path-to-your-key>
```
## Deploy only specific parts 
You can target the individual playbooks for setup, prepare, or deploy, or simply comment out tasks that you don't want to run. 

## Provide a different dataset
The datasets can be specified as variables in the relevant tasks in  `prepare-playbook.yaml` and `deploy-playbook.yaml`.
