部署
helm upgrade --install frappe-bench -n erpnext frappe/erpnext --set persistence.worker.storageClass=csi-cephfs-sc --set mariadb.primary.persistence.storageClass=csi-cephfs-sc --set jobs.createSite.enabled=true --set jobs.createSite.siteName=erp.gezi.vip

更新版本
helm upgrade --install frappe-bench -n erpnext frappe/erpnext --set persistence.worker.storageClass=csi-cephfs-sc --set mariadb-sts.enabled=true --set mariadb-sts.persistence.storageClass=csi-cephfs-sc --set worker.long.autoscaling.enabled=true --set worker.default.autoscaling.enabled=true --set worker.short.autoscaling.enabled=true
需要手动配置worker的资源限制,如果使用命名空间限制,会限制数据库的资源

创建新站点
https://github.com/frappe/helm/blob/main/erpnext/README.md#create-new-site

恢复数据
~/frappe-bench$ bench --site erp-uat.hk.keli.vip --force restore /tmp/20260107_034535-ttpos-uat_s_frappe_cloud-database.sql.gz --with-private-files /tmp/20260107_034535-ttpos-uat_s_frappe_cloud-private-files.tar --with-public-files /tmp/20260107_034535-ttpos-uat_s_frappe_cloud-files.tar

bench --site erp-test.hk.keli.vip --force restore /tmp/20260107_061510-wallace-th_s_frappe_cloud-database.sql.gz --with-private-files /tmp/20260107_061510-wallace-th_s_frappe_cloud-private-files.tar --with-public-files /tmp/20260107_061510-wallace-th_s_frappe_cloud-files.tar 

bench --site erp-uat.hk.keli.vip --force restore /tmp/20260107_034535-ttpos-uat_s_frappe_cloud-database.sql.gz  --with-private-files /tmp/20260107_034535-ttpos-uat_s_frappe_cloud-private-files.tar --with-public-files /tmp/20260107_034535-ttpos-uat_s_frappe_cloud-files.tar

bench --site erp.gezi.vip --force restore /home/frappe/frappe-bench/sites/erp.gezi.vip/private/backups/20260108_154340-erp_gezi_vip-database.sql.gz  --with-private-files /home/frappe/frappe-bench/sites/erp.gezi.vip/private/backups/20260108_154340-erp_gezi_vip-private-files.tar --with-public-files /home/frappe/frappe-bench/sites/erp.gezi.vip/private/backups/20260108_154340-erp_gezi_vip-files.tar


kubectl cp 20260107_034535-ttpos-uat_s_frappe_cloud-database.sql.gz frappe-bench-erpnext-nginx-685696bbc7-6v4tr:/tmp -n erpnext
kubectl cp 20260107_034535-ttpos-uat_s_frappe_cloud-files.tar frappe-bench-erpnext-nginx-685696bbc7-6v4tr:/tmp -n erpnext
kubectl cp 20260107_034535-ttpos-uat_s_frappe_cloud-private-files.tar frappe-bench-erpnext-nginx-685696bbc7-6v4tr:/tmp -n erpnext
kubectl cp 20260107_061510-wallace-th_s_frappe_cloud-database.sql.gz frappe-bench-erpnext-nginx-685696bbc7-6v4tr:/tmp -n erpnext
kubectl cp 20260107_061510-wallace-th_s_frappe_cloud-files.tar frappe-bench-erpnext-nginx-685696bbc7-6v4tr:/tmp -n erpnext
kubectl cp 20260107_061510-wallace-th_s_frappe_cloud-private-files.tar frappe-bench-erpnext-nginx-685696bbc7-6v4tr:/tmp -n erpnext