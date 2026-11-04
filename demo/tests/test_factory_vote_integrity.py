"""Publisher independence comes from known approving identities, never asserted family labels."""
from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.publisher import independent_circuit


def valid():
 return {'status':'approved','author_model':'glm-5.3-flash','votes':[
  {'model':'qwen-3.8-flash','family':'qwen','verdict':'approve'},
  {'model':'claude-haiku-5.5','family':'anthropic','verdict':'approve'}]}


class VoteIntegrityTests(unittest.TestCase):
 def test_preparer_cannot_approve_its_own_acceptance_or_be_the_builder(self):
  item=valid();item['preparer_model']='qwen-3.8-flash'
  self.assertFalse(independent_circuit(item))
  item=valid();item['preparer_model']='glm-5.3-flash'
  self.assertFalse(independent_circuit(item))
  item=valid();item['preparer_model']='invented'
  self.assertFalse(independent_circuit(item))
 def test_known_independent_approvals_are_valid(self):
  self.assertTrue(independent_circuit(valid()))

 def test_author_reject_unknown_and_forged_family_never_approve(self):
  bad=[]
  item=valid();item['votes'][0]['verdict']='reject';bad.append(item)
  item=valid();item['votes'][0].update(model='glm-5.3-flash',family='zhipu');bad.append(item)
  item=valid();item['votes'][0].update(model='invented',family='invented');bad.append(item)
  item=valid();item['votes'][0]['family']='made-up';bad.append(item)
  item=valid();item['votes'][1]=copy.deepcopy(item['votes'][0]);bad.append(item)
  item=valid();item['status']='held';bad.append(item)
  item=valid();item.pop('author_model');bad.append(item)
  item=valid();item['votes'][0].pop('verdict');bad.append(item)
  for index,item in enumerate(bad):
   with self.subTest(index=index):self.assertFalse(independent_circuit(item))


if __name__=='__main__':unittest.main()
