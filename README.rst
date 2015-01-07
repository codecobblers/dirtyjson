dirtyjson is a JSON decoder meant for extracting JSON-type data from .js files.
The returned data structure includes information about line and column numbers,
so you can output more useful error messages. The input can also include single
quotes, line comments, inline comments, dangling commas, unquoted single-word
keys, and hexadecimal and octal numbers.

The goal of dirtyjson is to read JSON objects out of files that are littered
with elements that do not fit the official JSON standard. By providing line
and column number contexts, a dirty JSON file can be used as source input for
a complex data parser or compiler.
