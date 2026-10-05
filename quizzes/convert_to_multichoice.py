#!/usr/bin/env python3
"""Convert Moodle XML 'multichoiceset' (all-or-nothing) questions to regular
'multichoice' (multiple answers allowed, partial credit).

Correct answers get +100/n, incorrect answers get -100/n (n = number of correct
answers), so selecting everything scores 0. Moodle only accepts specific grade
values on import, so the strings below are the ones Moodle itself writes.

Usage: python3 convert_to_multichoice.py   (run from quizzes/)
Reads questions-*.xml, writes multichoice/<same name>.xml and
all-questions-multichoice.xml (everything in one file, for Moodle import)
"""
import glob
import os
import re

CATEGORY = "$course$/top/Multiple choice (partial credit)"
GRADES = {1: "100", 2: "50", 3: "33.33333", 4: "25", 5: "20"}

os.makedirs("multichoice", exist_ok=True)
combined = []

for path in sorted(glob.glob("questions-*.xml")):
    xml = open(path, encoding="utf-8").read()
    fractions = re.findall(r'<answer fraction="(\d+)"', xml)
    n = fractions.count("100")
    g = GRADES[n]

    def regrade(m):
        return f'<answer fraction="{g if m.group(1) == "100" else "-" + g if g != "100" else "-100"}"'

    xml = re.sub(r'<answer fraction="(\d+)"', regrade, xml)
    xml = xml.replace('type="multichoiceset"', 'type="multichoice"')
    xml = xml.replace(
        "<shuffleanswers>",
        "<single>false</single>\n    <shuffleanswers>",
    )
    xml = xml.replace(
        "<answernumbering>",
        '<partiallycorrectfeedback format="html">\n      <text><![CDATA[<p>Your answer is partially correct.</p>]]></text>\n    </partiallycorrectfeedback>\n    <shownumcorrect/>\n    <answernumbering>',
    )
    # move shuffleanswers/single order is irrelevant in Moodle XML; add category
    xml = xml.replace(
        "<quiz>\n",
        f"<quiz>\n  <question type=\"category\">\n    <category>\n      <text>{CATEGORY}</text>\n    </category>\n  </question>\n",
        1,
    )
    out = os.path.join("multichoice", os.path.basename(path))
    open(out, "w", encoding="utf-8").write(xml)
    print(out, "correct:", n, "grade:", g)
    combined.append(re.search(r"(  <question type=\"multichoice\">.*?</question>)", xml, re.S).group(1))

# Moodle imports one file at a time, so also write everything into a single file
with open("all-questions-multichoice.xml", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n')
    f.write(f'  <question type="category">\n    <category>\n      <text>{CATEGORY}</text>\n    </category>\n  </question>\n')
    f.write("\n".join(combined) + "\n</quiz>\n")
print("all-questions-multichoice.xml:", len(combined), "questions")
