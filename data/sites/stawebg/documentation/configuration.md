# Configuration #

All configuration files are written in  [JSON](http://www.json.org/).

## config.json in root directory ##

This file sets the configuration for the complete stawebg project.
It looks like this:

<pre>
{
    "dirs": {
        "sites":    "sites",
        "layouts":  "layouts",
        "out":      "out"
    },
    "layout": {
        "head":     "head.html",
        "bottom":   "bottom.html"
    },
    "config": {
        "site":     "_config.json"
    },
    "files": {
        "index":    ["index.html", "index.md"],
        "content":  [".html", ".md"],
        "markup": {
            ".md": "markdown"
        },
        "exclude":  []
    }
}
</pre>

### dirs ###

You can change the names of this directories if you want.

### layout ###

stawebg expects two fils with html code: head.html and bottom.html.
If you don't like this names, you can change them here.
[More about layouts...](%CUR%layout)

### config ###

Each site has his own configuration file for things like the page title.
You can change the expected filename here.

### files ###

This is the really interesting part.

#### index ####
index ist a list of files that are index files.
For all other files stawebg will create subdirectories in the output.
Here's an example:

<pre>
sites/title/index.md -> out/sites/index.html
sites/title/about.md -> out/sites/about/index.html
</pre>

#### content ####
This are the file extensions for files with content.
You can write your pages in HTML and Markdown, the files must have the extension .html or .md.
stawebg will copy all other files as they are.

#### markup ####
A list of file extensions and used markup compilers.
The default configuration uses the program markdown to translate Markdown to HTML.
The markup compiler gets the source text into stdin and has to write the output to stdout.
If an error occurs the error message must be written to stderr.
Of course the output must be HTML code.
You can use this also to translate manpages to html for example.

#### exclude ####
This is a list of all file extensions that are not copied.
For example, you can exlude all PHP files:

<pre>
"exclude":  [".php"]
</pre>

## _config.json for each site ##

Each site has a configuration file for site specific things.
This file has the path sites/title/_config.json and looks like this:

<pre>
{
    "title":    "test site",
    "subtitle": "demo of stawebg"
    "layout":   "default"
}
</pre>

The title and subtitle can be used in the [layout](%CUR%layout).
The layout name is the name of the directory in layout/ that contains the files head.html and bottom.html.
