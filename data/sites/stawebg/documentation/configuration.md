# Configuration #

All configuration files are written in  [JSON](http://www.json.org/).
There are three levels of configuration files: global, per site and per directory.
Per site configuration *replaces* the global configuration, per directory configuration *extends* the per site and global configuration.
But there are some options that can only be in one of this levels, e.g. the markup compilers must be specified in the global configuration.

## Global config: stawebg.json in root directory ##

This file sets the configuration for the complete stawebg project.
The default configuration looks like this:

<pre>
{
    "dirs": {
        "sites":    "sites",
        "layouts":  "layouts",
        "out":      "out"
    },
    "files": {
        "index":    ["index.html", "index.md"],
        "content":  [".html", ".md"],
        "hidden":   [],
        "exclude":  ["stawebg.json"]
    },
    "markup": {
        ".md": ["markdown"]
    }
}
</pre>

### dirs ###

You can change the names of this directories if you want.
This may be important for the *out* directory.
You can use an absolute path too.

### files ###

#### index ####
*index* is a list of files that are index files.
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

#### hidden ####
This files or directories are not visible in the menu.

#### exclude ####
This is a list of all file extensions that are not copied.
For example, you can exlude all PHP files:

<pre>
"exclude":  [".php"]
</pre>

### markup ###
A list of file extensions and used markup compilers.
The default configuration uses the program markdown to translate Markdown to HTML.
The markup compiler gets the source text into stdin and has to write the output to stdout.
If an error occurs the error message must be written to stderr.
Of course the output must be HTML code.
You can use this also to translate manpages to html for example.


## Per site: *title*.json for each site ##

Each site has a configuration file for site specific things.
This file has the path sites/*title*.json for the site *title* and looks like this:

<pre>
{
    "title":    "test site",
    "subtitle": "demo of stawebg"
    "layout":   "default"
}
</pre>

The title and subtitle can be used in the [layout](%CUR%layout).
The layout name is the name of the directory in layout/ that contains the file template.html and layout related files like CSS files.

You can overwrite the following options from the global configuration here:

<pre>
"files": {
    "index":    ["index.html", "index.md"],
    "content":  [".html", ".md"],
    "hidden":   [],
    "exclude":  ["stawebg.json"]
}
</pre>

## Per directory: stawebg.json in subdirectory ##

TODO
