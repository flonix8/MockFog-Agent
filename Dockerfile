# Build with "docker build . -t agent"
# run with "docker run -it -p 5000:5000  agent -hostname localhost -iface eth0 -port 5000" 
FROM python:3.6

WORKDIR /usr/src/agent

COPY requirements.txt ./
EXPOSE 5000
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN apt update && apt install -y iptables

ENTRYPOINT [ "python", "fog_agent.py" ]
