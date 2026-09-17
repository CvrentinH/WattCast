FROM spark:4.2.0-scala2.13-java21-ubuntu

USER root

RUN apt-get update -y && \
    apt-get install -y python3 python3-pip wget && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    rm -rf /var/lib/apt/lists/*

ENV SPARK_HOME=/opt/spark
ENV PATH="${SPARK_HOME}/bin:${PATH}"
ENV PYTHONPATH="${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-0.10.9.9-src.zip:${PYTHONPATH}"

RUN pip3 install --no-cache-dir pyarrow pandas requests

RUN wget -P /opt/spark/jars/ https://jdbc.postgresql.org/download/postgresql-42.7.3.jar && \
    wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.5.0/hadoop-aws-3.5.0.jar && \
    wget -P /opt/spark/jars/ https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.35.4/bundle-2.35.4.jar

USER spark