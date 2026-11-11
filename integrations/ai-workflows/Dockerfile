FROM docker.io/library/python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1 LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false HOME=/tmp/home
COPY requirements.lock /opt/requirements.lock
COPY wheelhouse/ /opt/wheelhouse/
RUN python -m pip install --no-index --find-links=/opt/wheelhouse --require-hashes --no-deps -r /opt/requirements.lock && rm -r /opt/wheelhouse
COPY smoke.py /opt/smoke.py
USER 10001:10001
WORKDIR /work
ENTRYPOINT ["python"]
