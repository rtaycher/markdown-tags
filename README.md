#Markdown Tags
-----

A small library for writing markdown with a tree structure of python objects that you can transform into a
markdown snippet(string).

I started it by extracting some code I wrote for a reddit bot.

It was partially inspired by looking at the ScalaTags examples(although not using it).

ex. 2 Paragraphs, 1 in Italic the other in Bold.

    import markdown_tags as m

    tags = m.MD(m.Paragraph(m.Italic("Italian")), m.Paragraph(m.Bold("Boring, Portland")))
    markdown_str = tags.tags_to_markdown(recover=False, format_md=m.MarkdownFormats.reddit)

*returns a markdown string that will render as:*

*Italian*

**Boring, Portland**'

ex. of a nested list or a list with multi paragraph items.

    import markdown_tags as m


    tags = m.MD(m.UnorderedList.with_title("Maslow's hierarchy of needs partial outline",
                                           m.OrderedList(
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

*returns a markdown string that will render as:*



Maslow's hierarchy of needs partial outline

+ Needs

    1. Physiological needs

        + Air

        + Water

    2. Safety needs

        + Personal security

        + Financial security

        + Health and well-being

        + Safety net against accidents/illness and their adverse impacts

    3. Love and belonging

    4. Esteem

    5. Self-actualization

+ Research

+ Criticism


*note that the discount markdown implementation used by reddit seems to translate this to html fine but it shows up
a little strange with outer unordered list w/ the same indentation as inner ordered list on reddit.*

Tested with the discount markdown implementation used by reddit.
I might look into testing with other markdown implementations later.
