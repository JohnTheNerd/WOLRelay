FROM python:3

RUN apt-get update && \
  apt-get upgrade --yes && \
  apt-get install --yes tcpdump && \
  apt-get clean

ADD ./requirements.txt /usr/src/WOLRelay/
RUN pip3 install -r /usr/src/WOLRelay/requirements.txt
ADD . /usr/src/WOLRelay
CMD ["python3", "/usr/src/WOLRelay/main.py"]