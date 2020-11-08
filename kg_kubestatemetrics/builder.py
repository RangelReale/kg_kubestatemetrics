from typing import List, Optional, Sequence, Any

from kubragen import KubraGen
from kubragen.builder import Builder
from kubragen.data import ValueData
from kubragen.exception import InvalidParamError, InvalidNameError
from kubragen.helper import QuotedStr
from kubragen.object import ObjectItem, Object
from kubragen.types import TBuild, TBuildItem
from .option import KubeStateMetricsOptions


class KubeStateMetricsBuilder(Builder):
    """
    Kube State Metrics builder.

    Based on `kubernetes/kube-state-metrics <https://github.com/kubernetes/kube-state-metrics/tree/master/examples/standard>`_.

    .. list-table::
        :header-rows: 1

        * - build
          - description
        * - BUILD_ACCESSCONTROL
          - creates service account, roles, and roles bindings
        * - BUILD_SERVICE
          - creates Deployment and Service

    .. list-table::
        :header-rows: 1

        * - build item
          - description
        * - BUILDITEM_SERVICE_ACCOUNT
          - ServiceAccount
        * - BUILDITEM_CLUSTER_ROLE
          - ClusterRole
        * - BUILDITEM_CLUSTER_ROLE_BINDING
          - ClusterRoleBinding
        * - BUILDITEM_DEPLOYMENT
          - Deployment
        * - BUILDITEM_SERVICE
          - Service

    .. list-table::
        :header-rows: 1

        * - object name
          - description
          - default value
        * - service
          - Service
          - ```<basename>```
        * - service-account
          - ServiceAccount
          - ```<basename>```
        * - cluster-role
          - ClusterRole
          - ```<basename>```
        * - cluster-role-binding
          - ClusterRoleBinding
          - ```<basename>```
        * - deployment
          - Deployment
          - ```<basename>```
        * - pod-label-all
          - label *app* to be used by selection
          - ```<basename>```
    """
    options: KubeStateMetricsOptions
    _namespace: str

    SOURCE_NAME = 'kg_kubestatemetrics'

    BUILD_ACCESSCONTROL: TBuild = 'accesscontrol'
    BUILD_SERVICE: TBuild = 'service'

    BUILDITEM_SERVICE_ACCOUNT: TBuildItem = 'service-account'
    BUILDITEM_CLUSTER_ROLE: TBuildItem = 'cluster-role'
    BUILDITEM_CLUSTER_ROLE_BINDING: TBuildItem = 'cluster-role-binding'
    BUILDITEM_DEPLOYMENT: TBuildItem = 'deployment'
    BUILDITEM_SERVICE: TBuildItem = 'service'

    def __init__(self, kubragen: KubraGen, options: Optional[KubeStateMetricsOptions] = None):
        super().__init__(kubragen)
        if options is None:
            options = KubeStateMetricsOptions()
        self.options = options

        self._namespace = self.option_get('namespace')

        if self.option_get('config.authorization.serviceaccount_create') is not False:
            serviceaccount_name = self.basename()
        else:
            serviceaccount_name = self.option_get('config.authorization.serviceaccount_use')
            if serviceaccount_name == '':
                serviceaccount_name = None

        if self.option_get('config.authorization.roles_create') is not False:
            role_name = self.basename()
        else:
            role_name = None

        if self.option_get('config.authorization.roles_bind') is not False:
            if serviceaccount_name is None:
                raise InvalidParamError('To bind roles a service account is required')
            if role_name is None:
                raise InvalidParamError('To bind roles the role must be created')
            rolebinding_name = self.basename()
        else:
            rolebinding_name = None

        self.object_names_init({
            'service': self.basename(),
            'service-account': serviceaccount_name,
            'cluster-role': role_name,
            'cluster-role-binding': rolebinding_name,
            'deployment': self.basename(),
            'pod-label-app': self.basename(),
        })

    def option_get(self, name: str):
        return self.kubragen.option_root_get(self.options, name)

    def basename(self, suffix: str = ''):
        return '{}{}'.format(self.option_get('basename'), suffix)

    def namespace(self):
        return self._namespace

    def build_names(self) -> List[TBuild]:
        return [self.BUILD_ACCESSCONTROL, self.BUILD_SERVICE]

    def build_names_required(self) -> List[TBuild]:
        ret = [self.BUILD_SERVICE]
        if self.option_get('config.authorization.serviceaccount_create') is not False or \
                self.option_get('config.authorization.roles_create') is not False:
            ret.append(self.BUILD_ACCESSCONTROL)
        return ret

    def builditem_names(self) -> List[TBuildItem]:
        return [
            self.BUILDITEM_CLUSTER_ROLE,
            self.BUILDITEM_SERVICE_ACCOUNT,
            self.BUILDITEM_CLUSTER_ROLE_BINDING,
            self.BUILDITEM_DEPLOYMENT,
            self.BUILDITEM_SERVICE,
        ]

    def internal_build(self, buildname: TBuild) -> List[ObjectItem]:
        if buildname == self.BUILD_ACCESSCONTROL:
            return self.internal_build_accesscontrol()
        elif buildname == self.BUILD_SERVICE:
            return self.internal_build_service()
        else:
            raise InvalidNameError('Invalid build name: "{}"'.format(buildname))

    def internal_build_accesscontrol(self) -> List[ObjectItem]:
        ret = []

        if self.option_get('config.authorization.serviceaccount_create') is not False:
            ret.extend([
                Object({
                    'apiVersion': 'v1',
                    'kind': 'ServiceAccount',
                    'metadata': {
                        'name': self.object_name('service-account'),
                        'namespace': self.namespace(),
                    }
                }, name=self.BUILDITEM_SERVICE_ACCOUNT, source=self.SOURCE_NAME, instance=self.basename())
            ])

        if self.option_get('config.authorization.roles_create') is not False:
            ret.extend([
                Object({
                    'apiVersion': 'rbac.authorization.k8s.io/v1',
                    'kind': 'ClusterRole',
                    'metadata': {
                        'name': self.object_name('cluster-role'),
                    },
                    'rules': [{
                        'apiGroups': [''],
                        'resources': ['configmaps',
                            'secrets',
                            'nodes',
                            'pods',
                            'services',
                            'resourcequotas',
                            'replicationcontrollers',
                            'limitranges',
                            'persistentvolumeclaims',
                            'persistentvolumes',
                            'namespaces',
                            'endpoints'],
                        'verbs': ['list', 'watch']
                    },
                    {
                        'apiGroups': ['extensions'],
                        'resources': ['daemonsets', 'deployments', 'replicasets'],
                        'verbs': ['list', 'watch']
                    },
                    {
                        'apiGroups': ['apps'],
                        'resources': ['statefulsets',
                            'daemonsets',
                            'deployments',
                            'replicasets'],
                        'verbs': ['list', 'watch']
                    },
                    {
                        'apiGroups': ['batch'],
                        'resources': ['cronjobs', 'jobs'],
                        'verbs': ['list', 'watch']
                    },
                    {
                        'apiGroups': ['autoscaling'],
                        'resources': ['horizontalpodautoscalers'],
                        'verbs': ['list', 'watch']
                    },
                    {
                        'apiGroups': ['authentication.k8s.io'],
                        'resources': ['tokenreviews'],
                        'verbs': ['create']
                    },
                    {
                        'apiGroups': ['authorization.k8s.io'],
                        'resources': ['subjectaccessreviews'],
                        'verbs': ['create']
                    },
                    {
                        'apiGroups': ['policy'],
                        'resources': ['poddisruptionbudgets'],
                        'verbs': ['list', 'watch']
                    },
                    {
                        'apiGroups': ['certificates.k8s.io'],
                        'resources': ['certificatesigningrequests'],
                        'verbs': ['list', 'watch']
                    },
                    {
                        'apiGroups': ['storage.k8s.io'],
                        'resources': ['storageclasses', 'volumeattachments'],
                        'verbs': ['list', 'watch']
                    },
                    {
                        'apiGroups': ['admissionregistration.k8s.io'],
                        'resources': ['mutatingwebhookconfigurations',
                            'validatingwebhookconfigurations'],
                        'verbs': ['list', 'watch']
                    },
                    {
                        'apiGroups': ['networking.k8s.io'],
                        'resources': ['networkpolicies', 'ingresses'],
                        'verbs': ['list', 'watch']
                    },
                    {
                        'apiGroups': ['coordination.k8s.io'],
                        'resources': ['leases'],
                        'verbs': ['list', 'watch']
                    }]
                }, name=self.BUILDITEM_CLUSTER_ROLE, source=self.SOURCE_NAME, instance=self.basename())
            ])

        if self.option_get('config.authorization.roles_bind') is not False:
            ret.extend([
                Object({
                    'apiVersion': 'rbac.authorization.k8s.io/v1',
                    'kind': 'ClusterRoleBinding',
                    'metadata': {
                        'name': self.object_name('cluster-role-binding'),
                    },
                    'roleRef': {
                        'apiGroup': 'rbac.authorization.k8s.io',
                        'kind': 'ClusterRole',
                        'name': self.object_name('cluster-role'),
                    },
                    'subjects': [{
                        'kind': 'ServiceAccount',
                        'name': self.object_name('service-account'),
                        'namespace': self.namespace(),
                    }]
                }, name=self.BUILDITEM_CLUSTER_ROLE_BINDING, source=self.SOURCE_NAME, instance=self.basename())
            ])

        return ret

    def internal_build_service(self) -> List[ObjectItem]:
        ret = [
            Object({
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'metadata': {
                    'name': self.object_name('deployment'),
                    'namespace': self.namespace(),
                    'labels': {
                        'app': self.object_name('pod-label-app'),
                    },
                },
                'spec': {
                    'selector': {
                        'matchLabels': {
                            'app': self.object_name('pod-label-app'),
                        }
                    },
                    'template': {
                        'metadata': {
                            'labels': {
                                'app': self.object_name('pod-label-app'),
                            },
                            'annotations': ValueData({
                                'prometheus.io/scrape': QuotedStr('true'),
                                'prometheus.io/path': QuotedStr('/metrics'),
                                'prometheus.io/port': QuotedStr('8080'),
                            }, enabled=self.option_get('config.prometheus_annotation') is not False),
                        },
                        'spec': {
                            'containers': [{
                                'name': 'kube-state-metrics',
                                'image': self.option_get('container.kube-state-metrics'),
                                'livenessProbe': {
                                    'httpGet': {
                                        'path': '/healthz',
                                        'port': 8080
                                    },
                                    'initialDelaySeconds': 5,
                                    'timeoutSeconds': 5
                                },
                                'ports': [{
                                    'containerPort': 8080,
                                    'name': 'http-metrics'
                                },
                                {
                                    'containerPort': 8081,
                                    'name': 'telemetry'
                                }],
                                'readinessProbe': {
                                    'httpGet': {
                                        'path': '/',
                                        'port': 8081
                                    },
                                    'initialDelaySeconds': 5,
                                    'timeoutSeconds': 5
                                },
                                'securityContext': {
                                    'runAsUser': 65534
                                },
                                'resources': ValueData(value=self.option_get('kubernetes.resources.deployment'),
                                                       disabled_if_none=True),
                            }],
                            'nodeSelector': self.option_get('config.node_selector'),
                            'serviceAccountName': ValueData(value=self.object_name('service-account'),
                                                            enabled=self.object_name('service-account') is not None),
                        }
                    }
                }
            }, name=self.BUILDITEM_DEPLOYMENT, source=self.SOURCE_NAME, instance=self.basename()), Object({
                'apiVersion': 'v1',
                'kind': 'Service',
                'metadata': {
                    'name': self.object_name('service'),
                    'namespace': self.namespace(),
                },
                'spec': {
                    'clusterIP': 'None',
                    'ports': [{
                        'name': 'http-metrics',
                        'port': 8080,
                        'targetPort': 'http-metrics'
                    },
                    {
                        'name': 'telemetry',
                        'port': 8081,
                        'targetPort': 'telemetry'
                    }],
                    'selector': {
                        'app': self.object_name('pod-label-app')
                    },
                }
            }, name=self.BUILDITEM_SERVICE, source=self.SOURCE_NAME, instance=self.basename())]
        return ret
