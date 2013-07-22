# Layout #

## head.html and bottom.html ##

The layout is split into two files: head.html and bottom.html.
The final page is generated from this files and the content: head.html + content (HTML, maybe from Markdown) + bottom.html.

## Variables ##

There are some variables that are replaced during the generation of the output:

<table>
    <tr>
        <th>Variable</th>
        <th>Usage</th>
        <th>Example</th>
    </tr>
    <tr>
        <td>&#37;ROOT&#37;</td>
        <td>Link to the root directory of the homepage.
        Don't write a / between &#37;ROOT&#37; and the URL behind this variable.</td>
        <td><pre>&lt;a href="&#37;ROOT&#37;index"&gt;&lt;/a&gt;</td>
    </tr>
    <tr>
        <td>&#37;CUR&#37;</td>
        <td>Link to the current directory of the page.
        You need this because stawebg moves every page to an other directory that is not an index page.</td>
        <td><pre>&lt;a href="&#37;CUR&#37;file.txt"&gt;Download&lt;/a&gt;</pre></td>
    </tr>
    <tr>
        <td>&#37;TITLE&#37;</td>
        <td>Title for the current page, used e.g. in layout.</td>
        <td><pre>&lt;title&gt;&#37;TITLE&#37;&lt;/title&gt;</pre></td>
    </tr>
    <tr>
        <td>&#37;SITETITLE&#37;</td>
        <td>Title of the homepage, used e.g. for header. The title of the site is written in the <a href="%CUR%configuration">configuration file config.json</a>.</td>
        <td><pre>&lt;h1&gt;&#37;SITETITLE&#37;&lt;/h1&gt;</pre></td>
    </tr>
    <tr>
        <td>&#37;SITESUBTITLE&#37;</td>
        <td>Subtitle of the homepage, used e.g. for header. The subtitle of the site is written in the <a href="%CUR%configuration">configuration file config.json</a>.</td>
        <td><pre>&lt;h1&gt;&#37;SITESUBTITLE&#37;&lt;/h1&gt;</pre></td>
    </tr>
    <tr>
        <td>&#37;MENU&#37;</td>
        <td>The generated menu for the current page.
        This is a nested list.
        The current page will have the class "active"</td>
        <td><pre>&lt;div class="menu"&gt;&#37;MENU&#37;&lt;/div&gt;</pre></td>
    </tr>
</table>

# Stylesheets and images #

TODO
