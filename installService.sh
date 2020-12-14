echo "Stop service"
sudo systemctl stop switch_device_router.service
echo "Install virtual python environment"
python3.8 -m venv venv
source venv/bin/activate
echo "Install python requirements"
pip install -r ./requirements.txt
echo "Copy service"
sudo cp switch_device_router.service /etc/systemd/system/
echo "Enable service"
sudo systemctl enable switch_device_router.service
echo "Start service"
sudo systemctl start switch_device_router.service
echo "Status of service"
sudo systemctl status switch_device_router.service