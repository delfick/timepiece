# coding: spec

from tests.helpers import TestCase

from timepiece.sections import final

from datetime import datetime
import mock

describe TestCase, "is_filtered functionality":
    describe "FilterSpec":
        describe "filtering by minute":
            it "says filtered when minute matches":
                dt = datetime(2000, 1, 1, 1, 1, 1)
                spec = final.FilterSpec.using(minutes="1")
                assert spec.is_filtered(dt)

            it "says filtered when minute matches any of the values":
                dt1 = datetime(2000, 1, 1, 1, 10, 1)
                dt2 = datetime(2000, 1, 1, 1, 5, 1)
                dt3 = datetime(2000, 1, 1, 1, 19, 1)
                spec = final.FilterSpec.using(minutes="10;5;19")

                assert spec.is_filtered(dt1)
                assert spec.is_filtered(dt2)
                assert spec.is_filtered(dt3)

            it "not filtered when minute doesn't matches any of the values":
                dt1 = datetime(2000, 1, 1, 1, 11, 1)
                dt2 = datetime(2000, 1, 1, 1, 6, 1)
                dt3 = datetime(2000, 1, 1, 1, 20, 1)
                spec = final.FilterSpec.using(minutes="10;5;19")

                assert not spec.is_filtered(dt1)
                assert not spec.is_filtered(dt2)
                assert not spec.is_filtered(dt3)

        describe "filtering by hour":
            it "says filtered when hour matches":
                dt = datetime(2000, 1, 1, 1, 1, 1)
                spec = final.FilterSpec.using(hours="1")
                assert spec.is_filtered(dt)

            it "says filtered when hour matches any of the values":
                dt1 = datetime(2000, 1, 1, 10, 1, 1)
                dt2 = datetime(2000, 1, 1, 5, 1, 1)
                dt3 = datetime(2000, 1, 1, 19, 1, 1)
                spec = final.FilterSpec.using(hours="10;5;19")

                assert spec.is_filtered(dt1)
                assert spec.is_filtered(dt2)
                assert spec.is_filtered(dt3)

            it "not filtered when hour doesn't matches any of the values":
                dt1 = datetime(2000, 1, 1, 11, 1, 1)
                dt2 = datetime(2000, 1, 1, 6, 1, 1)
                dt3 = datetime(2000, 1, 1, 20, 1, 1)
                spec = final.FilterSpec.using(hours="10;5;19")

                assert not spec.is_filtered(dt1)
                assert not spec.is_filtered(dt2)
                assert not spec.is_filtered(dt3)

        describe "filtering by week":
            it "says filtered if gregorian week matches":
                dt = mock.Mock(name="date")
                fake_gregorian_week = mock.Mock(name="gregorian_week", return_value=1)
                spec = final.FilterSpec.using(weeks="1")

                with mock.patch("timepiece.sections.final.gregorian_week", fake_gregorian_week):
                    assert spec.is_filtered(dt)

                fake_gregorian_week.assert_called_once_with(dt)

            it "says filtered if gregorian week matches any of the values":
                dt = mock.Mock(name="date")
                fake_gregorian_week = mock.Mock(name="gregorian_week", return_value=5)
                spec = final.FilterSpec.using(weeks="1;5;17")

                with mock.patch("timepiece.sections.final.gregorian_week", fake_gregorian_week):
                    assert spec.is_filtered(dt)

                fake_gregorian_week.assert_called_once_with(dt)

            it "says not filtered if gregorian week doesn't match any of the values":
                dt = mock.Mock(name="date")
                fake_gregorian_week = mock.Mock(name="gregorian_week", return_value=9)
                spec = final.FilterSpec.using(weeks="1;5;17")

                with mock.patch("timepiece.sections.final.gregorian_week", fake_gregorian_week):
                    assert not spec.is_filtered(dt)

                fake_gregorian_week.assert_called_once_with(dt)

        describe "filtering by month":
            it "says filtered when month matches":
                dt = datetime(2000, 1, 1, 1, 1, 1)
                spec = final.FilterSpec.using(months="1")
                assert spec.is_filtered(dt)

            it "says filtered when month matches any of the values":
                dt1 = datetime(2000, 10, 1, 1, 1, 1)
                dt2 = datetime(2000, 5, 1, 1, 1, 1)
                dt3 = datetime(2000, 12, 1, 1, 1, 1)
                spec = final.FilterSpec.using(months="10;5;12")

                assert spec.is_filtered(dt1)
                assert spec.is_filtered(dt2)
                assert spec.is_filtered(dt3)

            it "not filtered when month doesn't matches any of the values":
                dt1 = datetime(2000, 11, 1, 1, 1, 1)
                dt2 = datetime(2000, 6, 1, 1, 1, 1)
                dt3 = datetime(2000, 9, 1, 1, 1, 1)
                spec = final.FilterSpec.using(months="10;5;12")

                assert not spec.is_filtered(dt1)
                assert not spec.is_filtered(dt2)
                assert not spec.is_filtered(dt3)

        describe "filtering by day_name":
            it "says filtered when day_name matches":
                dt = datetime(2000, 1, 1, 1, 1, 1)
                spec = final.FilterSpec.using(day_names="sat")
                assert spec.is_filtered(dt)

            it "says filtered when day_name matches any of the values":
                dt1 = datetime(2000, 10, 1, 1, 1, 1)
                dt2 = datetime(2000, 5, 1, 1, 1, 1)
                dt3 = datetime(2000, 12, 1, 1, 1, 1)
                spec = final.FilterSpec.using(day_names="mon;fri;sun")

                assert spec.is_filtered(dt1)
                assert spec.is_filtered(dt2)
                assert spec.is_filtered(dt3)

            it "not filtered when day_name doesn't matches any of the values":
                dt1 = datetime(2000, 11, 1, 1, 1, 1)
                dt2 = datetime(2000, 6, 1, 1, 1, 1)
                dt3 = datetime(2000, 9, 1, 1, 1, 1)
                spec = final.FilterSpec.using(day_names="mon;tues;sat;sun")

                assert not spec.is_filtered(dt1)
                assert not spec.is_filtered(dt2)
                assert not spec.is_filtered(dt3)

        describe "filtering by day_number":
            it "says filtered when day_number matches":
                dt = datetime(2000, 1, 1, 1, 1, 1)
                spec = final.FilterSpec.using(day_numbers="1")
                assert spec.is_filtered(dt)

            it "says filtered when day_number matches any of the values":
                dt1 = datetime(2000, 10, 1, 1, 1, 1)
                dt2 = datetime(2000, 5, 1, 1, 1, 1)
                dt3 = datetime(2000, 12, 1, 1, 1, 1)
                spec = final.FilterSpec.using(day_numbers="275;122;336")

                assert spec.is_filtered(dt1)
                assert spec.is_filtered(dt2)
                assert spec.is_filtered(dt3)

            it "not filtered when day_number doesn't matches any of the values":
                dt1 = datetime(2000, 11, 1, 1, 1, 1)
                dt2 = datetime(2000, 6, 1, 1, 1, 1)
                dt3 = datetime(2000, 9, 1, 1, 1, 1)
                spec = final.FilterSpec.using(day_numbers="1;2;78;90")

                assert not spec.is_filtered(dt1)
                assert not spec.is_filtered(dt2)
                assert not spec.is_filtered(dt3)

        describe "multiple filters":
            it "must match all the filters to succeed":
                dt = datetime(2000, 1, 1, 1, 1)
                spec = final.FilterSpec.using(day_numbers="1", months="1", minutes="1")
                assert spec.is_filtered(dt)

            it "fails if any filter isn't true":
                dt = datetime(2000, 1, 1, 1, 1)
                spec = final.FilterSpec.using(day_numbers="4", months="1", minutes="1")
                assert not spec.is_filtered(dt)

