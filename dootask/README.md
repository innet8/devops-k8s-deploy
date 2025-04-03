export    DB_PASSWORD = "$params.DB_PASSWORD"
export    DB_ROOT_PASSWORD = "$params.DB_ROOT_PASSWORD"
export    APP_KEY = "$params.APP_KEY"
export    APP_ID = "$params.APP_ID"
export    NS = "$params.NS"
for file in deploy/*; do  
if [[ "$file" == "deploy/config.yaml" || "$file" == "deploy/ingress.yaml" ]]; then 
    envsubst < $file| kubectl -n $NS apply -f - ;
else
    kubectl -n $NS apply -f $file
fi
done