# OIM Extranet Kubernetes Kustomize overlay configuration

Declarative management of Kubernetes objects using Kustomize.

# How to use

Within an overlay directory, create a `.env` file to contain required secret
values in the format KEY=value (i.e. `overlays/uat/.env`). Example:

    DATABASE_URL=value
    SECRET_KEY=value
    EMAIL_HOST=smtp.email.host

See the main project `README` for all required values.

To mount Azure File shares as persistent volumes, create a `.env.azurefile`
file in the overlay directory containing the storage account and key to use:


    azurestorageaccountname=storage_account_name
    azurestorageaccountkey=storage_account_access_key

Run `kubectl` with the `-k` flag to generate resources for a given overlay.
For example, to manage the UAT overlay:

```bash
# Use a dry run for error-checking:
kubectl apply -k overlays/uat --dry-run=client
# See the object manifests by setting the output to YAML:
kubectl apply -k overlays/uat --dry-run=client -o yaml
# Apply the overlay to a cluster:
kubectl apply -k overlays/uat
```

# References:

* https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/
* https://github.com/kubernetes-sigs/kustomize
* https://github.com/kubernetes-sigs/kustomize/tree/master/examples
