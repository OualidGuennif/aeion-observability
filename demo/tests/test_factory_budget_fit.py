"""The router never picks a model whose one request cannot fit half of its purpose's cap."""
from decimal import Decimal
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory import models
from factory.models import MODELS, Router, Telemetry, fits_budget, request_floor_usd


class BudgetFitTests(unittest.TestCase):
    def test_haiku_at_four_times_list_price_cannot_review_or_prepare_but_can_author(self):
        # (65536 x 2.50 + 16384 x 0.625) x 4 / 1e6 = 0.696 USD per review request; a vote is 1 USD.
        self.assertEqual(round(request_floor_usd('claude-haiku-5.5', 'review'), 3), Decimal('0.696'))
        self.assertFalse(fits_budget('claude-haiku-5.5', 'review'))
        self.assertFalse(fits_budget('claude-haiku-5.5', 'prepare'))
        self.assertTrue(fits_budget('claude-haiku-5.5', 'author'))
        for model in MODELS:
            if model != 'claude-haiku-5.5':
                self.assertTrue(all(fits_budget(model, p) for p in ('author', 'review', 'prepare')), model)
        router = Router(Telemetry())
        others = [f for m, s in MODELS.items() for f in [s['family']] if m not in ('claude-haiku-5.5',)]
        with self.assertRaises(models.RoutingError):
            router.select('review', exclude_families=others)

    def test_an_unknown_cap_or_multiple_fails_closed(self):
        with mock.patch('factory.budget.settings', side_effect=ValueError('budget_config_invalid')):
            self.assertFalse(fits_budget('glm-5.3-flash', 'review'))
        self.assertFalse(fits_budget('not-a-model', 'author'))
        with mock.patch.dict('app.profiles.PROFILES', {'glm': {**__import__('app.profiles').profiles.PROFILES['glm'],
                                                                'budget_multiplier': None}}):
            self.assertFalse(fits_budget('glm-5.3-flash', 'author'))


if __name__ == '__main__':
    unittest.main()
