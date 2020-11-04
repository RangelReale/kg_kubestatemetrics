import unittest

from kubragen import KubraGen
from kubragen.jsonpatch import FilterJSONPatches_Apply, ObjectFilter, FilterJSONPatch
from kubragen.provider import Provider_Generic

from kg_kubestatemetrics import KubeStateMetricsBuilder, KubeStateMetricsOptions


class TestBuilder(unittest.TestCase):
    def setUp(self):
        self.kg = KubraGen(provider=Provider_Generic())

    def test_empty(self):
        kms_config = KubeStateMetricsBuilder(kubragen=self.kg)
        self.assertEqual(kms_config.object_name('service'), 'kube-state-metrics')
        self.assertEqual(kms_config.object_name('deployment'), 'kube-state-metrics')

    def test_basedata(self):
        kms_config = KubeStateMetricsBuilder(kubragen=self.kg, options=KubeStateMetricsOptions({
            'namespace': 'myns',
            'basename': 'mykms',
        }))
        self.assertEqual(kms_config.object_name('service'), 'mykms')
        self.assertEqual(kms_config.object_name('deployment'), 'mykms')

        FilterJSONPatches_Apply(items=kms_config.build(kms_config.BUILD_SERVICE), jsonpatches=[
            FilterJSONPatch(filters=ObjectFilter(names=[kms_config.BUILDITEM_SERVICE]), patches=[
                {'op': 'check', 'path': '/metadata/name', 'cmp': 'equals', 'value': 'mykms'},
                {'op': 'check', 'path': '/metadata/namespace', 'cmp': 'equals', 'value': 'myns'},
            ]),
        ])
