
kubectl create secret -n kube-system generic csi-access-key \
   --from-literal=id='LTA**TRED' \
   --from-literal=secret='**********'
git clone https://github.com/kubernetes-sigs/alibaba-cloud-csi-driver.gits
helm upgrade --install alibaba-cloud-csi-driver ./chart --values chart/values-nonecs.yaml --namespace kube-system