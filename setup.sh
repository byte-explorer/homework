#!/bin/bash

apt-get update
apt-get install -y ca-certificates curl gnupg qemu qemu-user-static qemu-user binfmt-support git python3 python3-pip
# Add Docker's official GPG key:
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg -y --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update

apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

python3 -m pip install virtualenv
python3 -m virtualenv venv
source venv/bin/activate

pip install -r requirements.txt
