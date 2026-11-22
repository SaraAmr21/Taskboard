#!/bin/bash
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y ca-certificates curl gnupg

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable --now docker
usermod -aG docker ubuntu

# --- Firewall ---
apt-get install -y ufw fail2ban
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

systemctl enable --now fail2ban


# --- Data disk ---
DATA_DEV=/dev/nvme1n1

while [ ! -b "$DATA_DEV" ]; do sleep 2; done

if ! blkid "$DATA_DEV"; then
  mkfs.ext4 "$DATA_DEV"
fi

mkdir -p /srv/taskboard-data

DATA_UUID=$(blkid -s UUID -o value "$DATA_DEV")
echo "UUID=$DATA_UUID /srv/taskboard-data ext4 defaults,nofail 0 2" >> /etc/fstab
mount -a

apt-get install -y unattended-upgrades
systemctl enable --now unattended-upgrades

touch /var/log/taskboard-bootstrap.done
