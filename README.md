# devops-k8s-deploy
111


for file in jjjshop-saas/deploy/*; do  
if [[ "$file" == "jjjshop-saas/deploy/init-job.yaml" || "$file" == "jjjshop-saas/deploy/web-deployment.yaml" ]]; then 
    envsubst < $file| kubectl -n jjjshop-test apply -f - ;
else
    kubectl -n jjjshop-test apply -f $file
fi
done