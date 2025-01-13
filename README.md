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

## Monitoring
https://grafana-ucabojm.comp0235.condenser.arc.ucl.ac.uk/d/e173fa5c-9e1f-4c97-97ae-4e88dc76d324/merizosearch-cluster-dashboard?orgId=1&from=1736559000000&to=1736645399000 

## Access results
https://ucabojm-cons.comp0235.condenser.arc.ucl.ac.uk/browser/merizosearch-results
