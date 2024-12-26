data "harvester_image" "img" {
  display_name = var.img_display_name
  namespace    = "harvester-public"
}

data "harvester_ssh_key" "mysshkey" {
  name      = var.keyname
  namespace = var.namespace
}

resource "harvester_ssh_key" "lecturer_key" {
  name       = "merizo-lecturer-key"
  public_key = file("lecturer_key.pub")
  namespace  = var.namespace
}

resource "harvester_cloudinit_secret" "cloud-config" {
  name      = "cloud-config"
  namespace = var.namespace

  user_data = templatefile("cloud-init.tmpl.yml", {
    public_key_openssh   = data.harvester_ssh_key.mysshkey.public_key
    lecturer_key_openssh = harvester_ssh_key.lecturer_key.public_key
  })
}
resource "harvester_virtualmachine" "managervm" {

  count = 1

  name                 = "${var.username}-merizo-manager"
  namespace            = var.namespace
  restart_after_update = true

  description = "Manager Node"

  cpu    = 2
  memory = "4Gi"

  efi         = true
  secure_boot = false

  run_strategy    = "RerunOnFailure"
  hostname        = "${var.username}-merizo-host"
  reserved_memory = "100Mi"
  machine_type    = "q35"

  network_interface {
    name           = "nic-1"
    wait_for_lease = true
    type           = "bridge"
    network_name   = var.network_name
  }

  disk {
    name       = "rootdisk"
    type       = "disk"
    size       = "10Gi"
    bus        = "virtio"
    boot_order = 1

    image       = data.harvester_image.img.id
    auto_delete = true
  }

  cloudinit {
    user_data_secret_name = harvester_cloudinit_secret.cloud-config.name
  }
}

resource "harvester_virtualmachine" "storagevm" {

  count = 1

  name                 = "${var.username}-merizo-storage"
  namespace            = var.namespace
  restart_after_update = true

  description = "Storage node"

  cpu    = 4
  memory = "8Gi"

  efi         = true
  secure_boot = false

  run_strategy    = "RerunOnFailure"
  hostname        = "${var.username}-merizo-storage"
  reserved_memory = "100Mi"
  machine_type    = "q35"

  network_interface {
    name           = "nic-1"
    wait_for_lease = true
    type           = "bridge"
    network_name   = var.network_name
  }

  disk {
    name       = "rootdisk"
    type       = "disk"
    size       = "10Gi"
    bus        = "virtio"
    boot_order = 1

    image       = data.harvester_image.img.id
    auto_delete = true
  }
  disk {
    name       = "datadisk"
    type       = "disk"
    size       = "200Gi"
    bus        = "virtio"
    boot_order = 2

    auto_delete = true
  }

  cloudinit {
    user_data_secret_name = harvester_cloudinit_secret.cloud-config.name
  }
}

resource "harvester_virtualmachine" "workervm" {

  count = var.worker_count

  name                 = "${var.username}-merizo-worker-${format("%02d", count.index + 1)}"
  namespace            = var.namespace
  restart_after_update = true

  description = "Worker Node"

  cpu    = 4
  memory = "32Gi"

  efi         = true
  secure_boot = false

  run_strategy    = "RerunOnFailure"
  hostname        = "${var.username}-merizo-worker-${format("%02d", count.index + 1)}"
  reserved_memory = "100Mi"
  machine_type    = "q35"

  network_interface {
    name           = "nic-1"
    wait_for_lease = true
    type           = "bridge"
    network_name   = var.network_name
  }

  disk {
    name       = "rootdisk"
    type       = "disk"
    size       = "25Gi"
    bus        = "virtio"
    boot_order = 1

    image       = data.harvester_image.img.id
    auto_delete = true
  }

  cloudinit {
    user_data_secret_name = harvester_cloudinit_secret.cloud-config.name
  }
}
