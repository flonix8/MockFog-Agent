# MockFog-Agent
MockFog | Agent Software (that runs on FogNodes)

## Run development server
- Depending on your system run `sudo python3 fog_agent.py -hostname localhost -iface en0 -port 5000`
- `ifconfig` lists network interfaces on current machine

## Troubleshooting
- Required python version: 3.6
- `pip3 install -r requirements.txt`
- `pip3 install --trusted-host pypi.python.org pytest-xdist`

## Debugging
- `export FLASK_ENV=development`

## Tests
- `sudo python3 -m unittest properties/tc_config_test.py`
- `sudo python3 -m unittest properties/firewall.py`
- Network interface name is hardcoded in `__init__` methods

## Development on machine created by Nodemanager
- The server is managed by a systemd service called `mfog-agent.service`, the service source can be found in the MockFog-IaC repository

```bash
# list all services that start with fog
systemctl list-units | grep fog

# show the log of the fog agent service
journalctl -u mfog-agent.service

# restart the fog agent service
sudo systemctl restart mfog-fog_agent.service
```
- The source code is at `/opt/mfog-agent`
- eth0 is the management network, eth1 is the communication network
