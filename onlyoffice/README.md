helm repo add onlyoffice https://download.onlyoffice.com/charts/stable
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
# rabbitmq安装之后降级4.0.9
helm install rabbitmq bitnami/rabbitmq \
  --set persistence.storageClass=hitosea-rbd-sc \
  --set metrics.enabled=false \
  -n dootask-saas-share

helm install redis bitnami/redis \
  --set architecture=standalone \
  --set master.persistence.storageClass=hitosea-rbd-sc \
  --set metrics.enabled=false \
  -n dootask-saas-share

在mariadb创建,参考根目录的mariadb
数据库onlyoffice
用户onlyoffice

helm upgrade --install documentserver -f value.yaml onlyoffice/docs