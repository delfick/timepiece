# coding: spec

from tests.helpers import TestCase

from timepiece.sections.base import a_section, BaseSpec, ssv_spec, none_spec, JoinerSpec, SectionSpec, section_repr, fieldSpecs_from, default_available_sections

from input_algorithms.errors import BadSpecValue
from input_algorithms.dictobj import dictobj
from input_algorithms import spec_base as sb
from input_algorithms.meta import Meta
from delfick_error import DelfickError
import uuid
import mock

describe TestCase, "a_section":
    it "stores a name":
        name = mock.Mock(name="name")
        decorator = a_section(name)
        self.assertIs(decorator.name, name)

    it "stores the kls's FieldSpec into default_available_sections with that name":
        defaults = {}
        name = mock.Mock(name="mock")
        replaced_name = mock.Mock(name="replaced_name")
        name.replace.return_value = replaced_name

        kls = mock.Mock(name="kls")
        fieldspec = mock.Mock(name="fieldspec")
        kls.FieldSpec.return_value = fieldspec

        with mock.patch("timepiece.sections.base.default_available_sections", defaults):
            self.assertEqual(a_section(name)(kls), kls)
            self.assertEqual(kls._section_name, replaced_name)

        name.replace.assert_called_once_with("Spec", "")
        self.assertEqual(defaults, {name: fieldspec})

describe TestCase, "BaseSpec":
    it "has a FieldSpec":
        val = str(uuid.uuid1())
        class Example(BaseSpec):
            field1 = dictobj.Field(sb.string_spec())

        example = Example.FieldSpec().normalise(Meta.empty(), {"field1": val})
        self.assertEqual(example.field1, val)

    describe "simplify":
        it "defaults to just returning itself":
            instance = BaseSpec()
            self.assertIs(instance.simplify(), instance)

    describe "or_with":
        it "complains":
            class Thing(BaseSpec): pass
            class Blibber(BaseSpec): pass
            with self.fuzzyAssertRaisesError(BadSpecValue, "Sorry, can't do Thing | Blibber"):
                Thing().or_with(Blibber())

    describe "combine_with":
        it "complains":
            class Thing(BaseSpec): pass
            class Blibber(BaseSpec): pass
            with self.fuzzyAssertRaisesError(BadSpecValue, "Sorry, can't do Thing & Blibber"):
                Thing().combine_with(Blibber())

    describe "using":
        it "uses the FieldSpec and an empty Meta":
            res = mock.Mock(name="res")
            emptymeta = mock.Mock(name="emptymeta")
            fieldspec = mock.Mock(name="fieldspec")
            fieldspec.normalise.return_value = res

            class Thing(BaseSpec): pass

            with mock.patch.object(Thing, "FieldSpec", lambda: fieldspec):
                with mock.patch("timepiece.sections.base.EmptyMeta", emptymeta):
                    self.assertIs(Thing.using(one=1, two=2), res)

            fieldspec.normalise.assert_called_once_with(emptymeta, {"one": 1, "two": 2})

describe TestCase, "ssv_spec":
    it "defaults choices and spec to None":
        spec = ssv_spec()
        self.assertIs(spec.spec, None)
        self.assertIs(spec.choices, None)

    it "takes in choices and spec":
        spec = mock.Mock(name='spec')
        choices = mock.Mock(name="choices")

        the_spec = ssv_spec(choices=choices, spec=spec)
        self.assertIs(the_spec.choices, choices)
        self.assertIs(the_spec.spec, spec)

    it "converts a string into a list separated by ; with no checking if no choices":
        val = "one; two; three;four"
        self.assertEqual(ssv_spec().normalise_filled(Meta.empty(), val), ["one", "two", "three", "four"])

    it "complains if a value isn't a valid choice if we have choices":
        choices = ["o", "t", "tt"]
        val = "o; s; se"
        error1 = BadSpecValue("Expected one of the available choices", got="s", available=choices, meta=Meta.empty().indexed_at(1))
        error2 = BadSpecValue("Expected one of the available choices", got="se", available=choices, meta=Meta.empty().indexed_at(2))

        with self.fuzzyAssertRaisesError(BadSpecValue, _errors=[error1, error2]):
            ssv_spec(choices=choices).normalise(Meta.empty(), val)

    it "makes sure each item in the list is of spec if that is specified":
        spec = sb.integer_spec()
        val = "1;6;y"
        error1 = BadSpecValue("Expected an integer", got=str, meta=Meta.empty().indexed_at(2))

        with self.fuzzyAssertRaisesError(BadSpecValue, _errors=[error1]):
            ssv_spec(spec=spec).normalise(Meta.empty(), val)

describe TestCase, "none_spec":
    it "normalises None into None":
        self.assertIs(none_spec().normalise(Meta.empty(), None), None)

    it "complains about values that aren't none":
        val = mock.Mock(name="val")
        with self.fuzzyAssertRaisesError(BadSpecValue, "Expected None", got=val, meta=Meta.empty()):
            none_spec().normalise(Meta.empty(), val)

describe TestCase, "JoinerSpec":
    it "uses or_with if the joiner is OR":
        first = mock.Mock(name="first")
        first_normalised = mock.Mock(name="first_normalised")
        first_normalised.return_value = first

        second = mock.Mock(name="second")
        second_normalised = mock.Mock(name="second_normalised")
        second_normalised.return_value = second

        orded = mock.Mock(name="orded")
        first_normalised.or_with.return_value = orded

        fakeSectionSpec = mock.Mock(name="SectionSpec")
        normalise = lambda s, v: {first: first_normalised, second: second_normalised}[v]
        fakeSectionSpec.normalise.side_effect = normalise

        val = ("OR", first, second)

        with mock.patch("timepiece.sections.base.SectionSpec", lambda: fakeSectionSpec):
            self.assertIs(JoinerSpec().normalise(Meta.empty(), val), orded)

        first_normalised.or_with.assert_called_once_with(second_normalised)

    it "uses combine_with if the joiner is OR":
        first = mock.Mock(name="first")
        first_normalised = mock.Mock(name="first_normalised")

        second = mock.Mock(name="second")
        second_normalised = mock.Mock(name="second_normalised")

        orded = mock.Mock(name="orded")
        first_normalised.combine_with.return_value = orded

        fakeSectionSpec = mock.Mock(name="SectionSpec")
        normalise = lambda s, v: {first: first_normalised, second: second_normalised}[v]
        fakeSectionSpec.normalise.side_effect = normalise

        val = ("AND", first, second)

        with mock.patch("timepiece.sections.base.SectionSpec", lambda: fakeSectionSpec):
            self.assertIs(JoinerSpec().normalise(Meta.empty(), val), orded)

        first_normalised.combine_with.assert_called_once_with(second_normalised)

    it "complains if the joiner is not OR or AND":
        first = mock.NonCallableMock(name="first", spec=[])
        second = mock.NonCallableMock(name="second", spec=[])
        try:
            JoinerSpec().normalise(Meta.empty(), ("arbitrary", first, second))
        except BadSpecValue as error:
            self.assertEqual(len(error.errors), 3)
            error = error.errors[0]
            self.assertEqual(type(error), BadSpecValue)
            self.assertEqual(error.message, "Expected one of the available choices")
            self.assertEqual(error.kwargs, {"available": ["OR", "AND"], "got": "arbitrary", "meta": Meta.empty().indexed_at(0)})

    it "converts ErrorKls into BadSpecValue":
        class EKls(DelfickError):
            pass

        class Joiner(JoinerSpec):
            ErrorKls = EKls

        first = mock.Mock(name="first")
        first_normalised = mock.Mock(name="first_normalised")
        first_normalised.return_value = first

        second = mock.Mock(name="second")
        second_normalised = mock.Mock(name="second_normalised")
        second_normalised.return_value = second

        first_normalised.combine_with.side_effect = EKls("lol")

        fakeSectionSpec = mock.Mock(name="SectionSpec")
        normalise = lambda s, v: {first: first_normalised, second: second_normalised}[v]
        fakeSectionSpec.normalise.side_effect = normalise

        val = ("AND", first, second)

        with self.fuzzyAssertRaisesError(BadSpecValue, "Failed to join", error=EKls("lol")):
            with mock.patch("timepiece.sections.base.SectionSpec", lambda: fakeSectionSpec):
                JoinerSpec().normalise(Meta.empty(), val)

describe TestCase, "SectionSpec":
    it "defaults available_sections to the default_available_sections":
        spec = SectionSpec()
        self.assertIs(spec.available_sections, default_available_sections)

    it "takes in available sections":
        sections = mock.Mock(name="sections")
        section = SectionSpec(available_sections = sections)
        self.assertIs(section.available_sections, sections)

    describe "normalising":
        it "just returns value if value is a dictobj":
            class Thing(dictobj): pass
            thing = Thing()
            self.assertIs(SectionSpec().normalise(Meta.empty(), thing), thing)

        it "defaults kwargs to nothing if val is a tuple of one":
            class Thing(BaseSpec): pass
            sections = {"thing": Thing.FieldSpec()}
            res = SectionSpec(available_sections=sections).normalise(Meta.empty(), ("thing", ))
            self.assertIs(type(res), Thing)

        it "totes works with integers in the kwargs":
            class Thing(BaseSpec):
                field1 = dictobj.Field(sb.integer_spec())
            sections = {"thing": Thing.FieldSpec()}
            res = SectionSpec(available_sections=sections).normalise(Meta.empty(), ("thing", {"field1": 20}))
            self.assertEqual(res.field1, 20)

        it "works with strings in the kwargs":
            class Thing(BaseSpec):
                field1 = dictobj.Field(sb.string_or_int_as_string_spec())
            sections = {"thing": Thing.FieldSpec()}
            res = SectionSpec(available_sections=sections).normalise(Meta.empty(), ("thing", {"field1": 20}))
            self.assertEqual(res.field1, "20")

        it "works with booleans in the kwargs":
            class Thing(BaseSpec):
                field1 = dictobj.Field(sb.boolean())
            sections = {"thing": Thing.FieldSpec()}
            res = SectionSpec(available_sections=sections).normalise(Meta.empty(), ("thing", {"field1": False}))
            self.assertEqual(res.field1, False)

        it "works with tuples in the kwargs":
            class Blah(BaseSpec):
                one = dictobj.Field(sb.integer_spec())
                two = dictobj.Field(sb.string_spec())

            class Thing(BaseSpec):
                field1 = dictobj.Field(fieldSpecs_from(Blah))

            sections = {"thing": Thing.FieldSpec(), "blah": Blah.FieldSpec()}
            res = SectionSpec(available_sections=sections).normalise(Meta.empty(), ("thing", {"field1": ("blah", {"one": 20, "two": "three"})}))
            self.assertEqual(res.field1, Blah(one=20, two="three"))

        it "works with dictobj in the kwargs":
            class Blah(BaseSpec):
                one = dictobj.Field(sb.integer_spec())
                two = dictobj.Field(sb.string_spec())

            class Thing(BaseSpec):
                field1 = dictobj.Field(fieldSpecs_from(Blah))

            sections = {"thing": Thing.FieldSpec(), "blah": Blah.FieldSpec()}
            blah = Blah(one=56, two="four")
            res = SectionSpec(available_sections=sections).normalise(Meta.empty(), ("thing", {"field1": blah}))
            self.assertIs(res.field1, blah)

        it "complains about unknown section types":
            with self.fuzzyAssertRaisesError(BadSpecValue, "Unknown section type", available=[], wanted="thing"):
                SectionSpec(available_sections={}).normalise(Meta.empty(), ("thing", {"field1": 5}))

describe TestCase, "section_repr":
    it "formats the repr for a dictobj into a function like signature":
        class Thing(BaseSpec):
            field1 = dictobj.Field(sb.boolean())
            field2 = dictobj.Field(sb.integer_spec())
            field3 = dictobj.Field(lambda: fieldSpecs_from(Thing), wrapper=sb.optional_spec)
            __repr__ = section_repr
            _section_name = "set_by_the_a_section_decorator"

        thing = Thing.FieldSpec().normalise(Meta.empty(), {"field1": False, "field2": 20, "field3": Thing(field1=True, field2=42, field3=sb.NotSpecified)})
        self.assertEqual(repr(thing), 'set_by_the_a_section_decorator({"field1": False, "field2": 20, "field3": set_by_the_a_section_decorator({"field1": True, "field2": 42})})')

describe TestCase, "fieldSpecs_from":
    it "returns one FieldSpec if only one spec":
        spec = mock.Mock(name="spec")
        fieldspec = mock.Mock(name="FieldSpec")
        spec.FieldSpec.return_value = fieldspec
        self.assertIs(fieldSpecs_from(spec).spec, fieldspec)

    it "returns an or_spec if many spec":
        spec1 = mock.Mock(name="spec1")
        fieldspec1 = mock.Mock(name="FieldSpec1")
        spec1.FieldSpec.return_value = fieldspec1

        spec2 = mock.Mock(name="spec2")
        fieldspec2 = mock.Mock(name="FieldSpec2")
        spec2.FieldSpec.return_value = fieldspec2

        spec = fieldSpecs_from(spec1, spec2).spec
        self.assertEqual(type(spec), sb.or_spec)

