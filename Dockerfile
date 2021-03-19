FROM python:3 as base
RUN apt update
RUN apt-get -y install build-essential
RUN apt-get -y install \
    curl \
    git \
    vim \
    nano \
    sudo \
    ffmpeg
RUN mkdir cam
WORKDIR /cam

# install requirements
COPY . .
RUN pip3 install --upgrade -r requirements.txt

# Entry point
CMD ["src/main.py"]
ENTRYPOINT ["python3"]