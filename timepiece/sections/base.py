from input_algorithms.errors import BadSpecValue
from input_algorithms import spec_base as sb
from input_algorithms.dictobj import dictobj
from input_algorithms.meta import Meta

from delfick_error import DelfickError

EmptyMeta = Meta.empty()

default_available_sections = {}
class a_section(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, kls):
        default_available_sections[self.name] = kls.FieldSpec()
        kls._section_name = self.name.replace("Spec", "")
        return kls

class BaseSpec(dictobj.Spec):

    def simplify(self):
        return self

    def or_with(self, other):
        raise BadSpecValue("Sorry, can't do {0} | {1}".format(self.__class__.__name__, other.__class__.__name__))

    def combine_with(self, other):
        raise BadSpecValue("Sorry, can't do {0} & {1}".format(self.__class__.__name__, other.__class__.__name__))

    @classmethod
    def using(kls, **kwargs):
        return kls.FieldSpec().normalise(EmptyMeta, kwargs)

class ssv_spec(sb.Spec):
    """Semicolon separated values"""
    def setup(self, choices=None, spec=None):
        self.spec = spec
        self.choices = choices

    def normalise_filled(self, meta, val):
        if self.choices is None:
            res = [v.strip() for v in val.split(";")]
        else:
            res = sb.listof(sb.string_choice_spec(self.choices)).normalise(meta, [v.strip() for v in val.split(";")])

        if self.spec is None:
            return res

        return sb.listof(self.spec).normalise(meta, res)

class none_spec(sb.Spec):
    def normalise(self, meta, val):
        if val is None:
            return None
        else:
            raise BadSpecValue("Expected None", got=val, meta=meta)

class JoinerSpec(sb.Spec):
    ErrorKls = DelfickError

    def normalise_filled(self, meta, val):
        section_spec = SectionSpec()
        val = sb.tuple_spec(sb.string_choice_spec(["OR", "AND"]), section_spec, section_spec).normalise(meta, val)
        typ, first, second = val
        try:
            if typ == "OR":
                return first.simplify().or_with(second.simplify())
            else:
                return first.simplify().combine_with(second.simplify())
        except self.ErrorKls as error:
            raise BadSpecValue("Failed to join", error=error)

class SectionSpec(sb.Spec):
    ErrorKls = DelfickError

    def setup(self, available_sections=None):
        if available_sections is None:
            self.available_sections = default_available_sections
        else:
            self.available_sections = available_sections

    def normalise_filled(self, meta, val):
        if isinstance(val, dictobj):
            return val

        if isinstance(val, tuple) and len(val) is 1:
            val = (val[0], {})

        val = sb.tuple_spec(
              sb.string_spec()
            , sb.dictof(
                  sb.string_spec()
                , sb.match_spec(
                      (int, sb.integer_spec())
                    , (str, sb.string_spec())
                    , (tuple, SectionSpec())
                    , (dictobj, sb.any_spec())
                    )
                )
            ).normalise(meta, val)

        if val[0] not in self.available_sections:
            raise BadSpecValue("Unknown section type", meta=meta, wanted=val[0])
        return self.available_sections[val[0]].normalise(meta, val[1])

def section_repr(self):
    return "{0}({1})".format(self.__class__._section_name, {k:v for k, v in self.items() if not k.startswith("_")})

def fieldSpecs_from(*specs):
    if len(specs) is 1:
        return specs[0].FieldSpec()
    else:
        return sb.or_spec(*[fieldSpecs_from(spec) for spec in specs])
