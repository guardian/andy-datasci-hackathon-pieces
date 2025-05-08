FROM python:3.13

COPY requirements.txt /tmp
RUN cat /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
RUN useradd agent
RUN mkdir -p /home/agent && chown agent /home/agent
RUN mkdir -p /usr/local/lib/python3.13/site-packages/hackathon && touch /usr/local/lib/python3.13/site-packages/hackathon/__init__.py
COPY hackathon/indexing.py /usr/local/lib/python3.13/site-packages/hackathon/indexing.py
COPY split_data.py /usr/local/bin/split_data.py
COPY import_data.py /usr/local/bin/import_data.py
USER agent