#!/usr/bin/env python
# unit tests for markdown_tags
from __future__ import print_function
import tempfile
import os
import unittest
import contextlib
import errno
import sys
import zipfile
import subprocess
import shutil
import urllib
import stat

from pyquery import PyQuery as pq

sys.path.append("../..")
import markdown_tags as m
import markdown_tags.reddit_specific as rmd

test_dir = os.path.abspath(os.path.dirname(__file__))
markdown_discount_implementation_folder = os.path.join(test_dir, "markdown_implementations/discount")
markdown_discount_implementation_configure = os.path.join(markdown_discount_implementation_folder, "configure")
markdown_discount_binary = os.path.join(markdown_discount_implementation_folder, "bin/markdown")
discount_zip_url = "https://github.com/Orc/discount/archive/v2.1.7.zip"
local_discount_zip_path = os.path.join(markdown_discount_implementation_folder, "markdown-discount-v2.1.7.zip")
discount_zip_inner_folder = "discount-2.1.7"


def rmdir(top):
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
    for name in dirs:
        os.rmdir(os.path.join(root, name))


def make_directory_do_not_error_if_directory_exists(path):
    try:
        os.makedirs(path)
    except OSError as ex:
        if ex.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def delete_directory_recursive(path):
    try:
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(path)
    except OSError as ex:
        if ex.errno == errno.ENOENT:
            pass
        else:
            raise


def string_remove_prefix(string, prefix):
    if string.startswith(prefix):
        return string[len(prefix):]

def download_markdown_if_needed():
    if not os.path.exists(markdown_discount_binary):
        print("Markdown implementation Discount binary not found, trying to download and compile it.")
        try:
            delete_directory_recursive(markdown_discount_implementation_folder)
            make_directory_do_not_error_if_directory_exists(markdown_discount_implementation_folder)
        except Exception as ex:
            print("Markdown implementation Discount binary not found " +
                  "and could not delete and remake discount implementation folder:")
            raise

        try:
            urllib.urlretrieve(discount_zip_url, local_discount_zip_path)
        except Exception as ex:
            print("Markdown implementation Discount binary not found and could not be downloaded:")
            raise

        try:
            with zipfile.ZipFile(local_discount_zip_path) as z:
                for f in z.namelist():
                    if f == discount_zip_inner_folder + "/":
                        pass
                    if f.endswith('/'):
                        make_directory_do_not_error_if_directory_exists(os.path.join(
                            markdown_discount_implementation_folder, f))
                    else:
                        z.extract(f, path=markdown_discount_implementation_folder)

            shutil.move(os.path.join(markdown_discount_implementation_folder, discount_zip_inner_folder),
                        os.path.join(markdown_discount_implementation_folder, "src"))

            configure_path = os.path.join(markdown_discount_implementation_folder, "src", "configure.sh")
            st = os.stat(configure_path)
            os.chmod(configure_path, st.st_mode | stat.S_IEXEC)

            cmd = ("cd " + os.path.join(markdown_discount_implementation_folder, "src") + ";" +
                   "./configure.sh --prefix=" + markdown_discount_implementation_folder + "; make; make install")
            print("!!!!!!!!!!!!!!! Calling :  '" + cmd + "' !!!!!!!!!!!!!!!!!!!!")
            subprocess.check_call(cmd, shell=True)

            print("Compiled Discount Markdown implementation.")
        except Exception as ex:
            print("Markdown implementation Discount binary not found and could not compile it:")
            raise

@contextlib.contextmanager
def context(*extra_ctx):
    try:
        yield
    except Exception as e:
        for c in extra_ctx:
            print(str(c) + "\n")
        raise e


def compile_markdown(markdown_txt):
    download_markdown_if_needed()
    with tempfile.NamedTemporaryFile() as src:
        src.write(markdown_txt)
        src.flush()
        with tempfile.NamedTemporaryFile() as output_file:
            subprocess.check_call([markdown_discount_binary, "-o", output_file.name, src.name])
            html_generated = output_file.read()
            return html_generated


class Test_MarkdownTagsComplicated(unittest.TestCase):
    def test_bold_italic_text(self):
        tags = m.MD(m.Paragraph(m.Bold(m.Italic("This is important!!!"))))
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
        tags = m.MD(m.Paragraph(m.Italic("Italian")), m.Paragraph(m.Bold("Boring, Portland")))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        paragraphs = html("p")
        self.assertEqual(2, len(paragraphs))

        italic = paragraphs[0].find("em")
        self.assertIsNotNone(italic)
        self.assertEqual(italic.text, "Italian")

        bold = paragraphs[1].find("strong")
        self.assertIsNotNone(bold)
        self.assertEqual(bold.text, "Boring, Portland")

    def test_unordered_list_ordered_list_unordered_list(self):
        tags = m.MD(m.UnorderedList.with_title("Maslow's hierarchy of needs partial outline",
                                               m.OrderedList.with_title("Needs",
                                                   m.UnorderedList.with_title("Physiological needs",
                                                                              "Air",
                                                                              "Water"),
                                                   m.UnorderedList.with_title("Safety needs",
                                                                              "Personal security",
                                                                              "Financial security",
                                                                              "Health and well-being",
                                                                              "Safety net against accidents/illness " +
                                                                                "and their adverse impacts"),
                                                   "Love and belonging",
                                                   "Esteem",
                                                   "Self-actualization"),
                                               "Research",
                                               "Criticism"))
        with context("tags:", tags):
            markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)
            with context("markdown_str:", markdown_str):
                generated_html_str = compile_markdown(markdown_str)
                with context("generated_html_str:", generated_html_str):
                    html = pq(generated_html_str, parser='html_fragments')

                    unordered_lists = html("ul")
                    self.assertEqual(3, len(unordered_lists))

                    #TODO insert a few more checks


class Test_MarkdownTagsSingle(unittest.TestCase):
    def test_paragraphs(self):
        tags = m.MD(*[m.Paragraph(s) for s in ["First", "Security", "Tree"]])
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        paragraphs = html("p")
        self.assertEqual(3, len(paragraphs))

        self.assertEqual(paragraphs[0].text, "First")
        self.assertEqual(paragraphs[1].text, "Security")
        self.assertEqual(paragraphs[2].text, "Tree")

    def test_hr(self):
        tags = m.MD(m.HorizontalRuleLine())
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        horizontal_rule = html("hr")
        self.assertIsNotNone(horizontal_rule, "there should be a horizontal line(rule)")

    def test_italic(self):
        tags = m.MD(m.Paragraph(m.Italic("I")))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        emphasis = html("em")

        self.assertIsNotNone(emphasis, "there should be emphasis")
        self.assertEqual(emphasis.text(), "I")

    def test_bold(self):
        tags = m.MD(m.Paragraph(m.Bold("B")))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        strong = html("strong")

        self.assertIsNotNone(strong, "there should be strong tags")
        self.assertEqual(strong.text(), "B")

    def test_unordered_list(self):
        tags = m.MD(m.UnorderedList("A", "B", "C"))

        with context("tags:", tags):
            markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)
            with context("markdown_str:", markdown_str):
                generated_html_str = compile_markdown(markdown_str)
                with context("generated_html_str:", generated_html_str):
                    html = pq(generated_html_str, parser='html_fragments')

                    unordered_lists = html("ul")
                    self.assertEqual(1, len(unordered_lists))

                    list_items = unordered_lists("li")
                    self.assertEqual(3, len(list_items))

                    self.assertEqual(["A", "B", "C"], [i.text() for i in list_items.items()])

    def test_ordered_list(self):
        tags = m.MD(m.OrderedList("A", "B", "C"))
        with context("tags:", tags):
            markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)
            with context("markdown_str:", markdown_str):
                generated_html_str = compile_markdown(markdown_str)
                with context("generated_html_str:", generated_html_str):
                    html = pq(generated_html_str, parser='html_fragments')

                    ordered_lists = html("ol")
                    self.assertEqual(1, len(ordered_lists))

                    list_items = ordered_lists("li")
                    self.assertEqual(3, len(list_items))

                    self.assertEqual(["A", "B", "C"], [i.text().strip() for i in list_items.items()])

    def test_superscript(self):
        tags = m.MD(m.Paragraph("5 squared ", "5", rmd.Superscript("2")))
        with context("tags:", tags):
            markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)
            with context("markdown_str:", markdown_str):
                generated_html_str = compile_markdown(markdown_str)
                with context("generated_html_str:", generated_html_str):
                    html = pq(generated_html_str, parser='html_fragments')

                    p = html("sup")
                    self.assertIsNotNone(p)
                    self.assertEqual("2", p.text())

    def test_link(self):
        tags = m.MD(m.Paragraph(m.Link("example.com", "The example website")))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        link = html("a")
        link_url = link.attr("href")
        link_text = link.text()

        self.assertEqual("example.com", link_url)
        self.assertEqual("The example website", link_text)

    def test_image(self):
        tags = m.MD(m.Paragraph(m.Image("./pic1", "pic 1")))
        markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.basic)

        html = pq(compile_markdown(markdown_str), parser='html_fragments')
        img = html("img")
        img_url = img.attr("src")
        img_alt = img.attr("alt")

        self.assertEqual("./pic1", img_url)
        self.assertEqual("pic 1", img_alt)


class Test_RedditMarkdown(unittest.TestCase):
    def test_reddit_disallows_images(self):
        with self.assertRaises(m.IllegalMarkdownFormattingException):
            tags = m.MD(m.Paragraph(m.Image("http://en.wikipedia.org/wiki/File:Example.jpg", "Example Image"), "yo"))
            markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)
            html = pq(compile_markdown(markdown_str), parser='html_fragments')

    def test_reddit_strikethrough(self):
        tags = m.MD(m.Paragraph("What is your favorite ", rmd.Strikethrough("colour"), " color?"))
        with context("tags:", tags):
            markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)
            with context("markdown_str:", markdown_str):
                generated_html_str = compile_markdown(markdown_str)
                with context("generated_html_str:", generated_html_str):
                    html = pq(generated_html_str, parser='html_fragments')
                    self.assertEqual("colour", html("del").text())


if __name__ == "__main__":
    download_markdown_if_needed()
    unittest.main()
