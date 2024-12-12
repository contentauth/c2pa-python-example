FROM python:3.12 AS build

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENTRYPOINT [ "python" ]


FROM build AS app

ENTRYPOINT [ "python", "app.py" ]


FROM build AS client

ENTRYPOINT [ "python", "tests/client.py", "./tests/A.jpg", "-o", "client_volume/signed-images" ]


FROM build AS local-setup

RUN apt-get update \
    && apt-get install -y \
    less \
    jq
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install
RUN python3 -m pip install --upgrade localstack
RUN pip install awscli-local[ver2]

ENTRYPOINT [ "bash", "./local-setup.sh" ]
