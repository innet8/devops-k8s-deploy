# 设置备份pvc
./velero install     --provider gcp     --plugins velero/velero-plugin-for-gcp:v1.11.0     --bucket dootask_saas_backup     --secret-file ./credentials-velero --use-node-agent --uploader-type restic
./velero backup create test-$(date +%s)   --include-namespaces official-website   --default-volumes-to-fs-backup
## credentials-velero
```
{
  "type": "service_account",
  "project_id": "dootask-4c1cc",
  "private_key_id": "8e7693f6c814e41e16400cb2b2d67a246de58631",
  "private_key": "-----BEGIN PRIVATE KEY-----\n\n-----END PRIVATE KEY-----\n",
  "client_email": "saas-backup@dootask-4c1cc.iam.gserviceaccount.com",
  "client_id": "\",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/saas-backup%40dootask-4c1cc.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
```