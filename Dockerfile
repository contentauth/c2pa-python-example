FROM python:3.12 AS build

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python" ]

FROM build AS app

COPY . .
ENTRYPOINT [ "python", "app.py" ]

EXPOSE 5001

FROM build AS local

COPY . .
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
