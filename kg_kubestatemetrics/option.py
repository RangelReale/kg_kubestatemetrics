from typing import Mapping

from kubragen.option import OptionDef
from kubragen.options import Options


class KubeStateMetricsOptions(Options):
    """
    Options for the Kube State Metrics builder.

    .. list-table::
        :header-rows: 1

        * - option
          - description
          - allowed types
          - default value
        * - basename
          - object names prefix
          - str
          - ```kube-state-metrics```
        * - namespace
          - namespace
          - str
          - ```default```
        * - config |rarr| prometheus_annotation
          - add prometheus annotations
          - bool
          - ```False```
        * - config |rarr| node_selector
          - Kubernetes node selector
          - Mapping
          - ```{'kubernetes.io/os': 'linux'}```
        * - config |rarr| authorization |rarr| serviceaccount_create
          - whether to create a service account
          - bool
          - ```True```
        * - config |rarr| authorization |rarr| serviceaccount_use
          - service account to use if not creating
          - str
          -
        * - config |rarr| authorization |rarr| roles_create
          - whether create roles
          - bool
          - ```True```
        * - config |rarr| authorization |rarr| roles_bind
          - whether to bind roles to service account
          - bool
          - ```True```
        * - container |rarr| kube-state-metrics
          - kube-state-metrics container image
          - str
          - ```quay.io/coreos/kube-state-metrics:<version>```
        * - kubernetes |rarr| resources |rarr| deployment
          - Kubernetes Deployment resources
          - Mapping
          -
    """
    def define_options(self):
        """
        Declare the options for the Kube State Metrics builder.

        :return: The supported options
        """
        return {
            'basename': OptionDef(required=True, default_value='kube-state-metrics', allowed_types=[str]),
            'namespace': OptionDef(required=True, default_value='default', allowed_types=[str]),
            'config': {
                'prometheus_annotation': OptionDef(required=True, default_value=False, allowed_types=[bool]),
                'node_selector': OptionDef(default_value={'kubernetes.io/os': 'linux'}, allowed_types=[Mapping]),
                'authorization': {
                    'serviceaccount_create': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                    'serviceaccount_use': OptionDef(allowed_types=[str]),
                    'roles_create': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                    'roles_bind': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                },
            },
            'container': {
                'kube-state-metrics': OptionDef(required=True,
                                                default_value='quay.io/coreos/kube-state-metrics:v2.0.0-alpha.1',
                                                allowed_types=[str]),
            },
            'kubernetes': {
                'resources': {
                    'deployment': OptionDef(allowed_types=[Mapping]),
                }
            },
        }
