import glob
import re

html_files = glob.glob("*.html")
links = """  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Huninn&display=swap" rel="stylesheet">\n"""

for f in html_files:
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    if "family=Huninn" not in content:
        content = content.replace("</head>", links + "</head>")
        with open(f, "w", encoding="utf-8") as file:
            file.write(content)

with open("styles.css", "r", encoding="utf-8") as file:
    css = file.read()

css = css.replace("Arial, Helvetica, sans-serif", '"Huninn", sans-serif')
if ".huninn-regular" not in css:
    css += "\n.huninn-regular {\n  font-family: \"Huninn\", sans-serif;\n  font-weight: 400;\n  font-style: normal;\n}\n"

with open("styles.css", "w", encoding="utf-8") as file:
    file.write(css)

for f in html_files:
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    content = content.replace("Arial, sans-serif", '"Huninn", sans-serif')
    content = content.replace("Arial, Helvetica, sans-serif", '"Huninn", sans-serif')
    with open(f, "w", encoding="utf-8") as file:
        file.write(content)
print("Font updated in all HTML and CSS files.")
