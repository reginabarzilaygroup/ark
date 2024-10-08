FROM mitjclinic/sybil:latest

RUN apt-get update && apt-get install -y --no-install-recommends orthanc \
&& rm -rf /var/lib/apt/lists/*

EXPOSE 5000 8000 4242 8042

ENV NAME=ark
ENV ARK_SAVE_SCORES="true"
ENV LOG_LEVEL="INFO"
ENV ARK_THREADS=4

ENTRYPOINT ./orthanc/start_ark_orthanc.sh sybil
