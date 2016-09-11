# coding: spec

from tests.helpers import TestCase

from timepiece.grammar import TimeSpecVisitor
from timepiece.spec import make_timepiece

from input_algorithms.dictobj import dictobj
from input_algorithms import spec_base as sb
from input_algorithms.meta import Meta

describe TestCase, "TimeSpecGrammar":
    describe "Parsing into nodes":
        it "works":
            TimeSpecVisitor().grammar.parse("func1(attr1: val1, attr2: val2) | func2() & blah()".replace(" ", ""))
            # No exception == success!
            assert True

    describe "Turning nodes into dictobjs":
        it "works":
            available_sections = {}

            def combined(kls, first, second):
                return kls.FieldSpec().normalise(Meta({}, []), {"first": first, "second": second})

            class BaseSpec(dictobj.Spec):
                specifies = ("repeat", )
                def simplify(self): return self
                def or_with(self, other): return combined(ORd, self, other)
                def combine_with(self, other): return combined(ANDd, self, other)

            class ANDd(BaseSpec):
                first = dictobj.Field(sb.any_spec)
                second = dictobj.Field(sb.any_spec)

            class ORd(BaseSpec):
                first = dictobj.Field(sb.any_spec)
                second = dictobj.Field(sb.any_spec)

            class func1_spec(BaseSpec):
                attr1 = dictobj.Field(sb.string_spec)
                attr2 = dictobj.Field(sb.string_spec)
            available_sections["func1"] = func1_spec.FieldSpec()

            class func2_spec(BaseSpec):
                something = dictobj.Field(sb.integer_spec)
            available_sections["func2"] = func2_spec.FieldSpec()

            class blah_spec(BaseSpec):
                pass
            available_sections["blah"] = blah_spec.FieldSpec()

            result = make_timepiece(sections=available_sections).time_spec_to_object("(func1(attr1: val1, attr2: val2) | func2(something: 2)) & blah()")
            self.assertEqual(type(result), ANDd)

            self.assertEqual(type(result.first), ORd)
            self.assertEqual(type(result.first.first), func1_spec)
            self.assertEqual(type(result.first.second), func2_spec)
            self.assertEqual(type(result.second), blah_spec)

            self.assertEqual(result.first.first.attr1, "val1")
            self.assertEqual(result.first.first.attr2, "val2")

            self.assertEqual(result.first.second.something, 2)
