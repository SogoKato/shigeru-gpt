ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}-slim-bookworm

RUN apt update && \
    apt install -y curl && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

ARG USERNAME=ryeuser
RUN useradd ${USERNAME} --create-home
USER ${USERNAME}

WORKDIR /home/${USERNAME}/app

ENV RYE_HOME /home/${USERNAME}/.rye
ENV PATH ${RYE_HOME}/shims:${PATH}

RUN curl -sSf https://rye.astral.sh/get | RYE_NO_AUTO_INSTALL=1 RYE_INSTALL_OPTION="--yes" bash

# For kaniko
# kaniko does not support RUN --mount
# https://github.com/GoogleContainerTools/kaniko/issues/1568
COPY ./pyproject.toml ./requirements*.lock ./.python-version ./README.md ./
RUN rye sync --no-dev --no-lock

RUN . .venv/bin/activate

COPY . .

ENTRYPOINT [ "rye", "run" ]
CMD ["uvicorn", "--host", "0.0.0.0", "main:app"]
