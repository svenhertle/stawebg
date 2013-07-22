# Documentation #

## Directory structure ##

You can find an example site with the correct file structure in the [git repo](https://github.com/svenhertle/stawebg/) in the directory data.

Every stawebg project must have this directory structure:

<pre>
config.json
layouts/
    default/
        head.html
        bottom.html
sites/
    title/
        _config.json
        index.md
</pre>

## Run stawebg ##

You have to call stawebg in the root directory of your project.
stawebg will create the directory out and subdirectories for each site:

<pre>
out/
    title/
        index.html
</pre>

## Multiple sites ##

You can create more than one site with this setup.
Add a new directory to sites/ an stawebg will create a new site.
Both sites can use the same layout.
