#!/bin/bash -i

SETUP_FILES_DIR=$(realpath "$(dirname "$0")")
REPO_DIR=$(realpath "$(dirname "$0")/..")

# Go to the repo directory
cd "$REPO_DIR"

# Exit if main.py doesn't exist
if [ ! -f main.py ]; then
    echo "Please symlink a \`main_*.py\` file to \`main.py\` inside pi_serial_uploader."
    echo "Example: \`ln -s main_foo.py main.py\`"
    exit 1
fi

# Enable the serial port
sudo raspi-config nonint do_serial_hw 0
# Disable serial console over the serial port
sudo raspi-config nonint do_serial_cons 1

# Create a python venv and install the requirements
sudo apt update
sudo apt install -y python3-venv
python -m venv env
source env/bin/activate
pip install -r requirements.txt

# Copy the service file to the systemd services folder
cd "$SETUP_FILES_DIR"
sudo cp serial-uploader.service /etc/systemd/system/

# Reload systemd daemon to read the new service file
sudo systemctl daemon-reload

# Enable the service to run on boot
sudo systemctl enable serial-uploader.service

# Start the service
sudo systemctl restart serial-uploader.service

echo "Reboot to apply changes to enable the serial port."
