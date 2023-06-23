from input_algorithms.many_item_spec import many_item_formatted_spec
from input_algorithms.validators import default_validators
from input_algorithms.spec_base import default_specs

from docutils.statemachine import ViewList
from docutils.parsers.rst import Directive
from textwrap import dedent
from docutils import nodes
import six

default_specs.append((many_item_formatted_spec.__name__, many_item_formatted_spec))

class ShowDirective(Directive):
    """Directive for outputting all the specs found in input_algorithms.spec_base.default_specs"""
    def run(self):
        sections = []
        for name, spec in self.showing:
            sect = nodes.section()
            sect['ids'].append(name)

            title = nodes.title()
            title += nodes.Text(name)
            sect += title

            viewlist = ViewList()
            for line in dedent(spec.__doc__).split("\n"):
                if line:
                    viewlist.append("    {0}".format(line), name)
                else:
                    viewlist.append("", name)
            self.state.nested_parse(viewlist, self.content_offset, sect)
            sections.append(sect)

        return sections

class ShowSpecsDirective(ShowDirective):
    showing = default_specs

class ShowValidatorsDirective(ShowDirective):
    showing = default_validators

def setup(app):
    """Setup the show_specs directive"""
    app.add_directive('show_specs', ShowSpecsDirective)
    app.add_directive('show_validators', ShowValidatorsDirective)

