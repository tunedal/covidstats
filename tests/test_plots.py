from unittest import TestCase
from io import StringIO


from plots import process_template


class TemplatingTest(TestCase):
    def process_template(self, template_data, replacements):
        template = StringIO(template_data)
        outfile = StringIO()
        process_template(template, outfile, replacements)
        return outfile.getvalue()

    def test_passes_through_trivial_template(self):
        result = self.process_template("hoho", {})
        self.assertEqual("hoho", result)

    def test_replaces_line_leaving_linebreaks_intact(self):
        template = "one\n<!-- INSERT X -->\nthree"
        result = self.process_template(template, {"x": "two"})
        self.assertEqual("one\ntwo\nthree", result)

    def test_replaces_in_middle_of_line(self):
        template = "fan<!-- INSERT X -->tastic"
        result = self.process_template(template, {"x": "-fricking-"})
        self.assertEqual("fan-fricking-tastic", result)

    def test_replaces_multiple_values(self):
        template = "one two <!-- INSERT X --> four <!-- INSERT Y -->"
        values = {
            "x": "three",
            "y": "five",
        }
        result = self.process_template(template, values)
        self.assertEqual("one two three four five", result)

    def test_allows_optional_spaces_in_tags(self):
        template = "A <!--   INSERT X--> C <!--INSERT Y-->"
        values = {
            "x": "B",
            "y": "D",
        }
        result = self.process_template(template, values)
        self.assertEqual("A B C D", result)

    def test_leaves_ordinary_comments_intact(self):
        template = "Hello <!-- this is a comment-->"
        result = self.process_template(template, {"x": "dummy"})
        self.assertEqual(template, result)

    def test_allows_long_names(self):
        template = "Hello <!-- INSERT MY-LONG-NAME -->"
        result = self.process_template(template, {"my-long-name": "there"})
        self.assertEqual("Hello there", result)

    def test_allows_mixed_case_in_replacements_argument(self):
        template = "Hello <!-- INSERT MY-MIXED-NAME -->"
        result = self.process_template(template, {"my-MiXeD-NAME": "there"})
        self.assertEqual("Hello there", result)
