# KubraGen Builder: Kube State Metrics

[![PyPI version](https://img.shields.io/pypi/v/kg_kubestatemetrics.svg)](https://pypi.python.org/pypi/kg_kubestatemetrics/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/kg_kubestatemetrics.svg)](https://pypi.python.org/pypi/kg_kubestatemetrics/)

kg_kubestatemetrics is a builder for [KubraGen](https://github.com/RangelReale/kubragen) that deploys 
a [Kube State Metrics](https://github.com/kubernetes/kube-state-metrics/) service in Kubernetes.

[KubraGen](https://github.com/RangelReale/kubragen) is a Kubernetes YAML generator library that makes it possible to generate
configurations using the full power of the Python programming language.

* Website: https://github.com/RangelReale/kg_kubestatemetrics
* Repository: https://github.com/RangelReale/kg_kubestatemetrics.git
* Documentation: https://kg_kubestatemetrics.readthedocs.org/
* PyPI: https://pypi.python.org/pypi/kg_kubestatemetrics

## Example

```python
from kubragen import KubraGen
from kubragen.consts import PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE
from kubragen.object import Object
from kubragen.option import OptionRoot
from kubragen.options import Options
from kubragen.output import OutputProject, OD_FileTemplate, OutputFile_ShellScript, OutputFile_Kubernetes, \
    OutputDriver_Print
from kubragen.provider import Provider

from kg_kubestatemetrics import KubeStateMetricsBuilder, KubeStateMetricsOptions

kg = KubraGen(provider=Provider(PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE), options=Options({
    'namespaces': {
        'mon': 'app-monitoring',
    },
}))

out = OutputProject(kg)

shell_script = OutputFile_ShellScript('create_gke.sh')
out.append(shell_script)

shell_script.append('set -e')

#
# OUTPUTFILE: app-namespace.yaml
#
file = OutputFile_Kubernetes('app-namespace.yaml')

file.append([
    Object({
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {
            'name': 'app-monitoring',
        },
    }, name='ns-monitoring', source='app', instance='app')
])

out.append(file)
shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

shell_script.append(f'kubectl config set-context --current --namespace=app-monitoring')

#
# SETUP: kube-state-metrics
#
ksm_config = KubeStateMetricsBuilder(kubragen=kg, options=KubeStateMetricsOptions({
    'namespace': OptionRoot('namespaces.mon'),
    'basename': 'myksm',
    'config': {
    },
    'kubernetes': {
        'resources': {
            'deployment': {
                'requests': {
                    'cpu': '150m',
                    'memory': '300Mi'
                },
                'limits': {
                    'cpu': '300m',
                    'memory': '450Mi'
                },
            },
        },
    }
}))

ksm_config.ensure_build_names(ksm_config.BUILD_ACCESSCONTROL, ksm_config.BUILD_SERVICE)

#
# OUTPUTFILE: kubestatemetrics-config.yaml
#
file = OutputFile_Kubernetes('kubestatemetrics-config.yaml')
out.append(file)

file.append(ksm_config.build(ksm_config.BUILD_ACCESSCONTROL))

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# OUTPUTFILE: kubestatemetrics.yaml
#
file = OutputFile_Kubernetes('kubestatemetrics.yaml')
out.append(file)

file.append(ksm_config.build(ksm_config.BUILD_SERVICE))

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# Write files
#
out.output(OutputDriver_Print())
# out.output(OutputDriver_Directory('/tmp/build-gke'))
```

Output:

```text
****** BEGIN FILE: 001-app-namespace.yaml ********
apiVersion: v1
kind: Namespace
metadata:
  name: app-monitoring

****** END FILE: 001-app-namespace.yaml ********
****** BEGIN FILE: 002-kubestatemetrics-config.yaml ********
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myksm
  namespace: app-monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: myksm
<...more...>
****** END FILE: 002-kubestatemetrics-config.yaml ********
****** BEGIN FILE: 003-kubestatemetrics.yaml ********
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myksm
  namespace: app-monitoring
  labels:
    app: myksm
spec:
  selector:
    matchLabels:
      app: myksm
<...more...>
****** END FILE: 003-kubestatemetrics.yaml ********
****** BEGIN FILE: create_gke.sh ********
#!/bin/bash

set -e
kubectl apply -f 001-app-namespace.yaml
kubectl config set-context --current --namespace=app-monitoring
kubectl apply -f 002-kubestatemetrics-config.yaml
kubectl apply -f 003-kubestatemetrics.yaml

****** END FILE: create_gke.sh ********
```

### Credits

based on

[kubernetes/kube-state-metrics](https://github.com/kubernetes/kube-state-metrics/tree/master/examples/standard)

## Author

Rangel Reale (rangelreale@gmail.com)
