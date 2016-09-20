# coding: spec

from tests.helpers import TestCase

from timepiece.sections import sections
from timepiece.sizing import Sizes

from datetime import datetime
import time

describe TestCase, "interval functionality":
    describe "AmountSpec":
        it "yields nothing if we exceed end":
            start = datetime(2000, 1, 3, 1, 1, 1)
            end = datetime(2001, 1, 1, 1, 1, 1)
            at = datetime(2000, 1, 1, 1, 1, 1)

            amount = sections.AmountSpec(num=1, size=Sizes.YEAR.value)

            intervals = amount.interval(start, at, end)
            with self.fuzzyAssertRaisesError(StopIteration):
                next(intervals)

        it "yields next value after at":
            start = datetime(2000, 1, 1, 1, 1, 1)
            end = datetime(2002, 1, 1, 1, 1, 1)
            at = datetime(2001, 3, 2, 1, 1, 1)

            amount = sections.AmountSpec(num=1, size=Sizes.MONTH.value)

            intervals = amount.interval(start, at, end)
            self.assertEqual(next(intervals), datetime(2001, 4, 1, 1, 1, 1))
            self.assertEqual(next(intervals), datetime(2001, 5, 1, 1, 1, 1))

        it "is efficient with large amounts of small values":
            start = datetime(2000, 1, 1, 1, 1, 1)
            end = datetime(2001, 1, 1, 1, 1, 1)
            at = datetime(2000, 12, 2, 1, 1, 1)

            amount = sections.AmountSpec(num=1, size=Sizes.SECOND.value)
            start_time = time.time()
            intervals = amount.interval(start, at, end)
            self.assertLess(time.time() - start_time, 0.0001)

            start_time = time.time()
            nxt = next(intervals)
            self.assertLess(time.time() - start_time, 0.0001)

            self.assertEqual(nxt, datetime(2000, 12, 2, 1, 1, 2))
