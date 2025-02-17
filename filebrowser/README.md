k8s部署的会存在在终端使用命令连接数据库超时的问题
部署完成后需要进入终端执行以下命令
```
rm /database/filebrowser.db
filebrowser config init
chown 911:911 filebrowser.db
```
之后重启容器