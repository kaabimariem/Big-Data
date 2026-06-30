FROM eclipse-temurin:8-jdk-jammy

ENV HADOOP_VERSION=3.3.6
ENV HADOOP_HOME=/opt/hadoop
ENV HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
ENV JAVA_HOME=/opt/java/openjdk

RUN apt-get update && apt-get install -y openssh-server procps && \
    rm -rf /var/lib/apt/lists/* && \
    ssh-keygen -t rsa -P "" -f /root/.ssh/id_rsa && \
    cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys && \
    chmod 600 /root/.ssh/authorized_keys && \
    mkdir -p /var/run/sshd

# Copy pre-downloaded Hadoop tarball (avoids network issues during build)
COPY hadoop-${HADOOP_VERSION}.tar.gz /tmp/hadoop.tar.gz
RUN tar -xz -C /opt -f /tmp/hadoop.tar.gz && \
    mv /opt/hadoop-${HADOOP_VERSION} $HADOOP_HOME && \
    rm /tmp/hadoop.tar.gz

COPY config/core-site.xml $HADOOP_CONF_DIR/
COPY config/hdfs-site.xml $HADOOP_CONF_DIR/
COPY config/mapred-site.xml $HADOOP_CONF_DIR/
COPY config/yarn-site.xml $HADOOP_CONF_DIR/
COPY config/workers $HADOOP_CONF_DIR/
COPY start-hadoop.sh /start-hadoop.sh
RUN chmod +x /start-hadoop.sh

# Inject JAVA_HOME into hadoop-env.sh so Hadoop daemons find the JDK
RUN echo "export JAVA_HOME=/opt/java/openjdk" >> $HADOOP_CONF_DIR/hadoop-env.sh

EXPOSE 9870 8088 9000 9864

CMD ["/start-hadoop.sh"]
