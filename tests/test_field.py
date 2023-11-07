import pytest
from unittest import TestCase
from onyx import OnyxField, exceptions
from onyx.field import OnyxOperator


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

    def test_eq_operation(self):
        self.assertEqual(
            OnyxField(sample_id="sample-123"),
            OnyxField(sample_id="sample-123"),
        )

        with pytest.raises(exceptions.OnyxFieldError):
            assert OnyxField(sample_id="sample-123") == {"sample_id": "sample-123"}

    def test_and_operation(self):
        self.assertEqual(
            (
                OnyxField(sample_id="sample-123")
                & OnyxField(run_name="run-456")
                & OnyxField(country="England")
            ).query,
            {
                OnyxOperator.AND: [
                    {"sample_id": "sample-123"},
                    {"run_name": "run-456"},
                    {"country": "England"},
                ]
            },
        )

        with pytest.raises(exceptions.OnyxFieldError):
            OnyxField(sample_id="sample-123") & {"run_name": "run-456"}  #  type: ignore

    def test_or_operation(self):
        self.assertEqual(
            (
                OnyxField(sample_id="sample-123")
                | OnyxField(run_name="run-456")
                | OnyxField(country="England")
            ).query,
            {
                OnyxOperator.OR: [
                    {"sample_id": "sample-123"},
                    {"run_name": "run-456"},
                    {"country": "England"},
                ]
            },
        )

        with pytest.raises(exceptions.OnyxFieldError):
            OnyxField(sample_id="sample-123") | {"run_name": "run-456"}  #  type: ignore

    def test_xor_operation(self):
        self.assertEqual(
            (
                OnyxField(sample_id="sample-123")
                ^ OnyxField(run_name="run-456")
                ^ OnyxField(country="England")
            ).query,
            {
                OnyxOperator.XOR: [
                    {"sample_id": "sample-123"},
                    {"run_name": "run-456"},
                    {"country": "England"},
                ]
            },
        )

        with pytest.raises(exceptions.OnyxFieldError):
            OnyxField(sample_id="sample-123") ^ {"run_name": "run-456"}  #  type: ignore

    def test_not_operation(self):
        self.assertEqual(
            (~OnyxField(sample_id="sample-123")).query,
            {OnyxOperator.NOT: {"sample_id": "sample-123"}},
        )
        self.assertEqual(
            (~~OnyxField(sample_id="sample-123")).query,
            {"sample_id": "sample-123"},
        )
        self.assertEqual(
            (~~~OnyxField(sample_id="sample-123")).query,
            {OnyxOperator.NOT: {"sample_id": "sample-123"}},
        )
        self.assertEqual(
            (~~~~OnyxField(sample_id="sample-123")).query,
            {"sample_id": "sample-123"},
        )
        self.assertEqual(
            ~OnyxField(sample_id="sample-123"), ~~~OnyxField(sample_id="sample-123")
        )
        self.assertEqual(
            OnyxField(sample_id="sample-123"), ~~OnyxField(sample_id="sample-123")
        )

    def test_all_operations(self):
        self.assertEqual(
            (
                (
                    OnyxField(sample_id="sample-123")
                    & OnyxField(run_name__contains="45")
                    & OnyxField(run_name__contains="56")
                )
                ^ (~(OnyxField(country="England") | OnyxField(country="Wales")))
            ).query,
            {
                OnyxOperator.XOR: [
                    {
                        OnyxOperator.AND: [
                            {"sample_id": "sample-123"},
                            {"run_name__contains": "45"},
                            {"run_name__contains": "56"},
                        ]
                    },
                    {
                        OnyxOperator.NOT: {
                            OnyxOperator.OR: [
                                {"country": "England"},
                                {"country": "Wales"},
                            ]
                        }
                    },
                ]
            },
        )
