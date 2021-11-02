# GenUML - Generate PlantUML from Java class files

[![Build Status](https://github.com/samuller/genuml/workflows/test/badge.svg)](https://github.com/samuller/genuml/actions)

This tool aids in creating [PlantUML](https://plantuml.com/) class diagrams by generating UML diagrams from Java class files. Diagrams can be generated from single class files, or generated diagrams can be inserted into PlantUML code based on comments containing the correct "pattern".

```
$ genuml --help
Usage: genuml [OPTIONS] COMMAND [ARGS]...

  Generate PlantUML class diagram DSL from Java class files.

Options:
  --version
  --help     Show this message and exit.

Commands:
  generate  Generate PlantUML for single given Java class file.
  insert    Insert diagrams into PlantUML containing pattern comments.
```

Some functionality, as well as the generated diagram style, are based on [ObjectAid UML Explorer](https://marketplace.eclipse.org/content/objectaid-uml-explorer), an Eclipse plug-in which seems to no longer be supported.
