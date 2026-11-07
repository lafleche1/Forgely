import unittest
from forgely_dofocus import catalogue,key
from forgely_dofocus_store import state_key

class CollectionTests(unittest.TestCase):
    def test_targets_are_bounded_uncollected_and_do_not_repeat_recorded_runes(self):
        from preparer_collecte_dofocus import collection_targets
        data=catalogue();targets=collection_targets(data,limit=40)
        self.assertEqual(len(targets),40)
        seen=set()
        existing={(key(s['item']),state_key({r['stat']:r['value'] for r in s['rows']},s['pool']),rune)
                  for s in data['snapshots'] for r in s['rows'] for rune in r['runes']}
        for target in targets:
            signature=(key(target['item']),state_key(target['jets'],target['pool']),target['rune'])
            self.assertNotIn(signature,existing);self.assertNotIn(signature,seen);seen.add(signature)
            self.assertEqual(target['kind'],'collection_target')
            self.assertEqual(target['status'],'not_collected')
            self.assertNotIn('display',target);self.assertNotIn('SC',target)
            self.assertTrue(target['question'])

    def test_first_targets_cover_distinct_families_with_evidence_gaps(self):
        from preparer_collecte_dofocus import collection_targets
        targets=collection_targets(catalogue(),limit=10)
        self.assertEqual(len({t['stat'] for t in targets}),10)
        self.assertTrue(all(t['recorded_family_cases']==0 for t in targets))

    def test_zero_and_invalid_limits(self):
        from preparer_collecte_dofocus import collection_targets
        self.assertEqual(collection_targets(catalogue(),limit=0),[])
        for bad in (-1,True,2.5):
            with self.assertRaises(ValueError):collection_targets(catalogue(),limit=bad)
