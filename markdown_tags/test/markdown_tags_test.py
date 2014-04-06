# !/usr/bin/env python
#unit tests for markdown_tags
from __future__ import print_function
import sys
import tempfile
import os
import unittest
import subprocess

from pyquery import PyQuery as pq

import markdown_tags as m

import markdown
test_dir = os.path.dirname(__file__)
markdown_discount_binary = os.path.join(test_dir,"markdown/bin/markdown")

if os.path.exists(markdown_discount_binary):
    use_binary = True
else:
    use_binary = False

def compile_markdown(markdown_txt):
    if use_binary:
        with tempfile.NamedTemporaryFile() as src:
            src.write(markdown_txt)
            src.flush()
            with tempfile.NamedTemporaryFile() as output_file:
                subprocess.check_call([markdown_discount_binary, "-o", output_file.name, src.name])
                return output_file.read()
    else:
        return markdown.markdown(markdown_txt)

class Test_MarkdownTagsComplicated(unittest.TestCase):
    def test_bold_italic_text(self):
        tags = m.MD(m.Bold(m.Italic("This is important!!!")))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)
        #self.assertEqual("***This is important!!!***", markdown)
        html = pq(compile_markdown(markdown_str), parser='html_fragments')

        bold = html("strong")
        self.assertIsNotNone(bold)
        self.assertEqual(1, len(bold))

        italic = html("em")
        self.assertIsNotNone(italic)
        self.assertEqual(1, len(italic))
        self.assertEqual(italic[0].text, "This is important!!!")

    def test_paragraphs(self):
        tags = m.Md(m.Paragraph(m.Italic("Italian"), m.Bold("Boring, Portland")))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)
        print("markdown_str is :\n" + markdown_str)
        print("compile_markdown(markdown_str) is :\n" + compile_markdown(markdown_str))
        #html = html5lib.parse(compile_markdown(markdown_str), namespaceHTMLElements=False)
        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        paragraphs = html("p")
        self.assertEqual(2, len(paragraphs))

        italic = paragraphs[0].find("em")
        self.assertIsNotNone(italic)
        self.assertEqual(italic.text,"Italian")

        bold = paragraphs[1].find("strong")
        self.assertIsNotNone(bold)
        self.assertEqual(bold.text,"Boring, Portland")

class Test_MarkdownTagsSingle(unittest.TestCase):
    def test_paragraphs(self):
        tags = m.MD(m.Paragraph(s) for s in ["First","Security", "Tree"])
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        paragraphs = html("p")
        self.assertEqual(3, len(paragraphs))

        self.assertEqual(paragraphs[0].text, "First")
        self.assertEqual(paragraphs[1].text, "Security")
        self.assertEqual(paragraphs[2].text, "Tree")

    def test_hr(self):
        tags = m.MD(m.Paragraph("First"),
                m.HorizontalRuleLine,
                m.Paragraph("Security"))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        horizontal_rule = html("hr")
        self.assertIsNotNone(horizontal_rule, "there should be a horizontal line(rule)")

    def test_italic(self):
        tags = m.MD(m.Italic("I"))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        emphasis = html("em")

        self.assertIsNotNone(emphasis, "there should be emphasis")
        self.assertEqual(emphasis.text, "I")

    def test_bold(self):
        tags = m.MD(m.Bold("B"))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        strong = html("strong")

        self.assertIsNotNone(strong, "there should be strong tags")
        self.assertEqual(strong.text, "B")

    def test_unordered_list(self):
        tags = m.MD(m.UnorderedList("A", "B", "C"))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        unordered_lists = html("ul")
        self.assertEqual(1, len(unordered_lists))

        unordered_list = unordered_lists[0]
        items = unordered_list("li")
        self.assertEqual(3, len(items))

        self.assertEqual(["A","B","C"], [i.text for i in items])

    def test_ordered_list(self):
        tags = m.MD(m.OrderedList("A", "B", "C"))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        ordered_lists = html("ol")
        self.assertEqual(1, len(ordered_lists))

        ordered_list = ordered_lists[0]
        items = ordered_list("li")
        self.assertEqual(3, len(items))

        self.assertEqual(["A","B","C"], [i.text for i in items])

    def test_superscript(self):
        tags = m.MD("5 squared ","5",m.Superscript("2"))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        p = html("sup")
        self.assertIsNotNone(p)
        self.assertEqual("2", p.text)

    def test_link(self):
        tags = m.MD(m.Link("example.com", "The example website"))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        link = html("a")
        link_url = link.attr("href")
        link_text = link.text

        self.assertEqual("example.com", link_url )
        self.assertEqual("The example website", link_text)

    def test_image(self):
        tags = m.MD(m.Link("./pic1", "pic 1"))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        link = html("a")
        link_url = link.attr("url")
        link_alt = link.attr("alt")

        self.assertEqual("./pic1", link_url)
        self.assertEqual("pic 1", link_alt)



class Test_RedditMarkdown(unittest.TestCase):
    def test_reddit_disallows_images(self):
        with self.assertRaises(m.IllegalMarkdownFormattingException):
            tags = m.Paragraph(m.Image("http://en.wikipedia.org/wiki/File:Example.jpg", "Example Image"), "yo")
            markdown_str = m.tags_to_markdown(tags, format_md="reddit")
            html = pq(compile_markdown(markdown_str), parser='html_fragments')


if __name__ == "__main__":
    unittest.main()
