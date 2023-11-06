import pytest
from unittest import TestCase
from onyx import OnyxField, exceptions


class OnyxFieldTestCase(TestCase):
    def test_init(self):
        self.assertEqual(
            OnyxField(sample_id="sample-123").query, {"sample_id": "sample-123"}
        )
        self.assertEqual(OnyxField(ct_value=123.456).query, {"ct_value": 123.456})
        self.assertEqual(OnyxField(published_date=None).query, {"published_date": None})
        self.assertEqual(
            OnyxField(published_date__range=["2023-01-01", "2023-09-18"]).query,
            {"published_date__range": "2023-01-01,2023-09-18"},
        )

        with pytest.raises(exceptions.OnyxFieldError):
            OnyxField()

        with pytest.raises(exceptions.OnyxFieldError):
            OnyxField(sample_id="sample-123", another_field="another_value")

    def test_double_negative(self):
        self.assertEqual(
            OnyxField(sample_id="sample-123"), ~~OnyxField(sample_id="sample-123")
        )
