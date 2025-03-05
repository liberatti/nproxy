FROM python:3.9-slim

WORKDIR /opt/waf-bypass/

RUN apt-get update && apt-get install -y git && \
    git clone https://github.com/nemesida-waf/waf_bypass.git /opt/waf-bypass/

RUN python3 -m pip install --no-cache-dir -r /opt/waf-bypass/requirements.txt

ENTRYPOINT ["python3", "/opt/waf-bypass/main.py"]
