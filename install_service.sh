echo "Stop service"
sudo systemctl stop switch_device_router.service
if [ ! -f venv/bin/activate ]; then
  echo "Install virtual python environment"
  python3.8 -m venv venv
fi
source venv/bin/activate
echo "Install python requirements"
pip install -r ./requirements.txt
echo "Copy service"
sudo cp switch_device_router.service /etc/systemd/system/
echo "Adapt service for current user"
sudo sed -i "s@USERNAME@$USER@" /etc/systemd/system/switch_device_router.service
sudo sed -i "s@HOMEDIR@$HOME@" /etc/systemd/system/switch_device_router.service
echo "Enable service"
sudo systemctl enable switch_device_router.service
echo "Start service"
sudo systemctl start switch_device_router.service
echo "Status of service"
sudo systemctl status switch_device_router.service