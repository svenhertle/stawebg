# Content and files #

## Content ##

TODO: Markdown -> other markup languages

Files with content can be written in HTML or Markdown.
The file extensions must be .html and .md.
But you can change this in the [configuration file](%CUR%configuration).

Files with a filename that begins with _ are not visible in the menu.
The link to this file doesn't contain the _.
Here's an example:

<pre>
sites/title/_about.html -> sites/title/about/index.html
</pre>

## Other files ##

All other files are copied as they are.
You can define an exclude list for this files (see [configuration](%CUR%configuration)).
