helm upgrade --install frappe-bench -n erpnext frappe/erpnext --set persistence.worker.storageClass=csi-cephfs-sc --set mariadb.primary.persistence.storageClass=csi-cephfs-sc --set jobs.createSite.enabled=true --set jobs.createSite.siteName=erp.gezi.vip

