#!/bin/bash
set -e

# Allow Hadoop daemons to run as root inside Docker
export HDFS_NAMENODE_USER=root
export HDFS_DATANODE_USER=root
export HDFS_SECONDARYNAMENODE_USER=root
export YARN_RESOURCEMANAGER_USER=root
export YARN_NODEMANAGER_USER=root

service ssh start

NODE_TYPE="${NODE_TYPE:-master}"

# Clean ALL stale PID files (Hadoop may write to /tmp or /tmp/hadoop)
rm -rf /tmp/hadoop-root-*.pid /tmp/hadoop/hadoop-root-*.pid 2>/dev/null || true

if [ "$NODE_TYPE" = "master" ]; then
    echo "=== Starting Hadoop Master ==="

    # Format NameNode only if not already done
    if [ ! -f "/hadoop/dfs/name/current/VERSION" ]; then
        echo "Formatting NameNode..."
        hdfs namenode -format -force -nonInteractive
    fi

    echo "Starting HDFS NameNode..."
    hdfs --daemon start namenode
    echo "Starting HDFS Secondary NameNode..."
    hdfs --daemon start secondarynamenode
    echo "Starting YARN ResourceManager..."
    yarn --daemon start resourcemanager

    echo ""
    echo "=== Hadoop Master ready ==="
    echo "  NameNode UI : http://localhost:9870"
    echo "  YARN UI     : http://localhost:8088"

    tail -f /opt/hadoop/logs/*.log 2>/dev/null || tail -f /dev/null

else
    echo "=== Starting Hadoop Worker: $(hostname) ==="

    # Wait for master to be reachable
    echo "Waiting for hadoop-master:9000..."
    for i in $(seq 1 20); do
        if hdfs dfs -ls / >/dev/null 2>&1; then
            echo "Master is up!"
            break
        fi
        echo "  attempt $i/20 - sleeping 3s..."
        sleep 3
    done

    echo "Starting HDFS DataNode..."
    hdfs --daemon start datanode
    echo "Starting YARN NodeManager..."
    yarn --daemon start nodemanager

    echo "=== Worker $(hostname) ready ==="
    tail -f /opt/hadoop/logs/*.log 2>/dev/null || tail -f /dev/null
fi
