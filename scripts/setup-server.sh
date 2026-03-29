#!/bin/bash
# Chạy trên EC2 sau khi SSH vào lần đầu
set -e

echo "======================================"
echo "  SkinAid EC2 Server Setup"
echo "======================================"

# 1. Update system
echo "[1/6] Updating system..."
sudo apt update && sudo apt upgrade -y

# 2. Cài Docker
echo "[2/6] Installing Docker..."
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 3. Quyền Docker cho user ubuntu
echo "[3/6] Configuring Docker..."
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
sudo systemctl start docker

# 4. Cài tiện ích
echo "[4/6] Installing utilities..."
sudo apt install -y git curl unzip make

# 5. Tạo swap 1GB (quan trọng — t3.micro chỉ có 1GB RAM)
echo "[5/6] Creating swap space..."
if [ ! -f /swapfile ]; then
  sudo fallocate -l 1G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  echo "Swap 1GB created"
else
  echo "Swap already exists, skipping"
fi

# 6. Clone repo
echo "[6/6] Cloning repository..."
echo "Nhập GitHub repo URL (vd: https://github.com/username/skinaid.git):"
read REPO_URL
cd ~
git clone "$REPO_URL" skinaid
mkdir -p ~/skinaid/backend/uploads

echo ""
echo "======================================"
echo "  Setup hoàn tất!"
echo "  Server IP: $(curl -s http://checkip.amazonaws.com)"
echo "======================================"
echo ""
echo "Bước tiếp theo:"
echo "  cd ~/skinaid"
echo "  cp .env.prod.example .env.prod"
echo "  nano .env.prod    ← điền giá trị thật vào đây"
