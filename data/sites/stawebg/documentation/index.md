# Documentation #

## Directory structure ##

You can find an example site with the correct file structure in the [git repo](https://github.com/svenhertle/stawebg/) in the directory data.

Every stawebg project must have this directory structure:

<pre>
stawebg.json
layouts/
    default/
        template.html
sites/
    title.json
    title/
        index.md
</pre>

## Run stawebg ##

You have to call stawebg with the path of the root directory of your project as a parameter.
You don't need this parameter if your work directory is this the root directory.
stawebg will create the directory out and subdirectories for each site:

<pre>
out/
    title/
        index.html
</pre>

## Multiple sites ##

You can create more than one site with this setup.
Add a new directory to sites/ and stawebg will create a new site.
Both sites can use the same layout.
