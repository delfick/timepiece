# coding: spec

from tests.helpers import TestCase

from timepiece.sizing import common_size, convert_amount, valid_sizes, Sizes

from input_algorithms.errors import BadSpecValue
import mock

describe TestCase, "valid_sizes":
    it "is the correct order":
        self.assertEqual(valid_sizes, ["second", "minute", "hour", "day", "week", "month", "year"])

describe TestCase, "common_size":
    it "complains if either size isn't valid":
        min_size = mock.Mock(name="min_size")
        max_size = mock.Mock(name="max_size")
        with self.fuzzyAssertRaisesError(BadSpecValue, "Size must be one of the valid units", first=min_size, second=max_size, valid=valid_sizes):
            common_size(min_size, max_size)

    it "finds the minimum common size":
        examples = [(s.value, s.value, s.value) for s in Sizes]
        for index, size in enumerate(valid_sizes):
            for diff in range(len(valid_sizes)):
                if index > diff:
                    examples.append((size, valid_sizes[index-diff], valid_sizes[index-diff]))
                    examples.append((valid_sizes[index-diff], size, valid_sizes[index-diff]))

        for first, second, common in examples:
            self.assertEqual(common_size(first, second), common)

describe TestCase, "convert_amount":
    it "finds the difference in the new size amount":
        self.assertEqual(convert_amount(Sizes.HOUR.value, Sizes.SECOND.value, 2), 7200)

    it "works with seconds to minutes":
        self.assertEqual(convert_amount(Sizes.SECOND.value, Sizes.MINUTE.value, 3), 0.05)

    it "works with minutes to seconds":
        self.assertEqual(convert_amount(Sizes.MINUTE.value, Sizes.SECOND.value, 3), 180)

    it "works with minutes to hours":
        self.assertEqual(convert_amount(Sizes.MINUTE.value, Sizes.HOUR.value, 3), 0.05)

    it "works with hours to days":
        self.assertEqual(convert_amount(Sizes.MINUTE.value, Sizes.DAY.value, 24 * 60 * 6), 6)

    it "works with days to weeks":
        self.assertAlmostEqual(convert_amount(Sizes.DAY.value, Sizes.WEEK.value, 13), 1.85714285)

    it "works with weeks to years":
        self.assertEqual(convert_amount(Sizes.WEEK.value, Sizes.YEAR.value, 52), 1)
        self.assertEqual(convert_amount(Sizes.WEEK.value, Sizes.YEAR.value, 105), 2)

    it "works with seconds to hours":
        self.assertAlmostEqual(convert_amount(Sizes.SECOND.value, Sizes.HOUR.value, 28795), 7.998611111)

