output "worker_vm_ips" {
  value = harvester_virtualmachine.workervm[*].network_interface[0].ip_address
}

output "worker_vm_ids" {
  value = harvester_virtualmachine.workervm.*.id
}
output "storage_vm_ips" {
  value = harvester_virtualmachine.storagevm[*].network_interface[0].ip_address
}

output "storage_vm_ids" {
  value = harvester_virtualmachine.storagevm.*.id
}
output "manager_vm_ips" {
  value = harvester_virtualmachine.managervm[*].network_interface[0].ip_address
}

output "manager_vm_ids" {
  value = harvester_virtualmachine.managervm.*.id
}
output "grafana_hostname"{
  value = local.monitoring_host_tags.condenser_ingress_grafana_hostname
}