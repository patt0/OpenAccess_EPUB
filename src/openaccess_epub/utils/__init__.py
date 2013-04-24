# -*- coding: utf-8 -*-
"""
Common utility functions
"""
import os.path
import zipfile
from collections import namedtuple
import urllib
import logging
import time
import shutil
import re
import sys

log = logging.getLogger('utils')

Identifier = namedtuple('Identifer', 'id, type')

def cache_location():
    '''Cross-platform placement of cached files'''
    if sys.platform == 'win32':  # Windows
        return os.path.join(os.environ['APPDATA'], 'OpenAccess_EPUB')
    else:  # Mac or Linux
        path = os.path.expanduser('~')
        if path == '~':
            path = os.path.expanduser('~user')
            if path == '~user':
                sys.exit('Could not find the correct cache location')
        return os.path.join(path, '.OpenAccess_EPUB')


def getFileRoot(path):
    """
    This method provides a standard method for acquiring the root name of a
    file from a path string. It will not raise an error if it returns an empty
    string, but it will issue a warning.
    """
    bn = os.path.basename(path)
    root = os.path.splitext(bn)[0]
    if not root:
        w = 'getFileRoot could not derive a root file name from\"{0}\"'
        log.warning(w.format(path))
        print(w.format(path))
    return root


def nodeText(node):
    """
    This is to be used when a node may only contain text, numbers or special
    characters. This function will return the text contained in the node.
    Sometimes this text data contains spurious newlines and spaces due to
    parsing and original xml formatting. This function should strip such
    artifacts.
    """
    #Get data from first child of the node
    try:
        first_child_data = node.firstChild.data
    except AttributeError:  # Usually caused by an empty node
        return ''
    else:
        return '{0}'.format(first_child_data.strip())


def makeEPUBBase(location):
    """
    Contains the  functionality to create the ePub directory hierarchy from
    scratch. Typical practice will not require this method, but use this to
    replace the default base ePub directory if it is not present. It may also
    used as a primer on ePub directory construction:
    base_epub/
    base_epub/mimetype
    base_epub/META-INF/
    base_epub/META-INF/container.xml
    base_epub/OPS/
    base_epub/OPS/css
    base_epub/OPS/css/article.css
    """
    log.info('Making the Base ePub at {0}'.format(location))
    #Create root directory
    if not os.path.isdir(location):
        os.makedirs(location)
    #Create mimetype file in root directory
    mime_path = os.path.join(location, 'mimetype')
    with open(mime_path, 'w') as mimetype:
        mimetype.write('application/epub+zip')
    #Create OPS and META-INF directorys
    os.mkdir(os.path.join(location, 'META-INF'))
    os.mkdir(os.path.join(location, 'OPS'))
    #Create container.xml file in META-INF
    meta_path = os.path.join(location, 'META-INF', 'container.xml')
    with open(meta_path, 'w') as container:
        container.write('''<?xml version="1.0" encoding="UTF-8" ?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
   <rootfiles>
      <rootfile full-path="OPS/content.opf" media-type="application/oebps-package+xml"/>
   </rootfiles>
</container>''')
    #It is considered better practice to leave the instantiation of image
    #directories up to other methods. Such directories are technically
    #optional and may depend on content
    #Create the css directory in OPS, then copy the file from resources
    os.mkdir(os.path.join(location, 'OPS', 'css'))
    css_path = os.path.join(location, 'OPS', 'css', 'article.css')
    with open(css_path, 'w') as css:
        log.info('Fetching a filler CSS file from GitHub')
        dl_css = urllib2.urlopen('https://raw.github.com/SavinaRoja/OpenAccess_EPUB/master/resources/text.css')
        css.write(dl_css.read())


def buildCache(location):
    log.info('Building the cache at {0}'.format(location))
    os.mkdir(location)
    os.mkdir(os.path.join(location, 'img_cache'))
    os.mkdir(os.path.join(location, 'logs'))
    os.mkdir(os.path.join(location, 'css'))
    makeEPUBBase(location)


def createDCElement(document, name, data, attributes = None):
    """
    A convenience method for creating DC tag elements.
    Used in content.opf
    """
    newnode = document.createElement(name)
    newnode.appendChild(document.createTextNode(data))
    if attributes:
        for attr, attrval in attributes.iteritems():
            newnode.setAttribute(attr, attrval)
    return newnode


def stripDOMLayer(oldnodelist, depth=1):
    """
    This method strips layers \"off the top\" from a specified NodeList or
    Node in the DOM. All child Nodes below the stripped layers are returned as
    a NodeList, treating them as siblings irrespective of the original
    hierarchy. To be used with caution.
    """
    newnodelist = []
    while depth:
        try:
            for child in oldnodelist:
                newnodelist += child.childNodes
        except TypeError:
            newnodelist = oldnodelist.childNodes
        depth -= 1
        newnodelist = stripDOMLayer(newnodelist, depth)
        return newnodelist
    return oldnodelist


def serializeText(fromnode, stringlist=None, sep=''):
    """
    Recursively extract the text data from a node and it's children
    """
    if stringlist is None:
        stringlist = []
    for item in fromnode.childNodes:
        if item.nodeType == item.TEXT_NODE and not item.data == '\n':
            stringlist.append(item.data)
        else:
            serializeText(item, stringlist, sep)
    return sep.join(stringlist)


def getTagText(node):
    """
    Grab the text data from a Node. If it is provided a NodeList, it will
    return the text data from the first contained Node.
    """
    data = ''
    try:
        children = node.childNodes
    except AttributeError:
        getTagText(node[0])
    else:
        if children:
            for child in children:
                if child.nodeType == child.TEXT_NODE and child.data != '\n':
                    data = child.data
            return data


def getFormattedNode(node):
    """
    This method is called on a Node whose children may include emphasis
    elements. The contained emphasis elements will be converted to ePub-safe
    emphasis elements. Non-emphasis elements will be untouched.
    """
    #Some of these elements are to be supported through CSS
    emphasis_elements = ['bold', 'italic', 'monospace', 'overline',
                         'sc', 'strike', 'underline']
    spans = {'monospace': 'font-family:monospace',
             'overline': 'text-decoration:overline',
             'sc': 'font-variant:small-caps',
             'strike': 'text-decoration:line-through',
             'underline': 'text-decoration:underline'}

    clone = node.cloneNode(deep=True)
    for element in emphasis_elements:
        for item in clone.getElementsByTagName(element):
            if item.tagName == 'bold':
                item.tagName = 'b'
            elif item.tagName == 'italic':
                item.tagName = 'i'
            elif item in spans:
                item.tagName = 'span'
                item.setAttribute('style', spans[item])
    return clone


def getTagData(node_list):
    '''Grab the (string) data from text elements
    node_list -- NodeList returned by getElementsByTagName
    '''
    data = ''
    try:
        for node in node_list:
            if node.firstChild.nodeType == node.TEXT_NODE:
                data = node.firstChild.data
        return data
    except TypeError:
        getTagData([node_list])


def epubZip(outdirect):
    """Zips up the input file directory into an ePub file."""
    log.info('Zipping up the directory {0}'.format(outdirect))
    epub_filename = outdirect + '.epub'
    epub = zipfile.ZipFile(epub_filename, 'w')
    current_dir = os.getcwd()
    os.chdir(outdirect)
    epub.write('mimetype')
    log.info('Recursively zipping META-INF and OPS')
    recursive_zip(epub, 'META-INF')
    recursive_zip(epub, 'OPS')
    os.chdir(current_dir)
    epub.close()


def recursive_zip(zipf, directory, folder=''):
    """Recursively traverses the output directory to construct the zipfile"""
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            zipf.write(os.path.join(directory, item), os.path.join(directory,
                                                                   item))
        elif os.path.isdir(os.path.join(directory, item)):
            recursive_zip(zipf, os.path.join(directory, item),
                          os.path.join(folder, item))


def suggestedArticleTypes():
    """
    Returns a list of suggested values for article-type
    """
    #See http://dtd.nlm.nih.gov/publishing/tag-library/3.0/n-w2d0.html
    s = ['abstract', 'addendum', 'announcement', 'article-commentary',
         'book-review', 'books-received', 'brief-report', 'calendar',
         'case-report', 'collection', 'correction', 'discussion',
         'dissertation', 'editorial', 'in-brief', 'introduction', 'letter',
         'meeting-report', 'news', 'obituary', 'oration',
         'partial-retraction', 'product-review', 'rapid-communication',
         'rapid-communication', 'reply', 'reprint', 'research-article',
         'retraction', 'review-article', 'translation']
    return(s)


def initiateDocument(titlestring,
                     _publicId='-//W3C//DTD XHTML 1.1//EN',
                     _systemId='http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd'):
    """A method for conveniently initiating a new xml.DOM Document"""
    from xml.dom.minidom import getDOMImplementation

    impl = getDOMImplementation()

    mytype = impl.createDocumentType('article', _publicId, _systemId)
    doc = impl.createDocument(None, 'root', mytype)

    root = doc.lastChild #IGNORE:E1101
    root.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml')
    root.setAttribute('xml:lang', 'en-US')

    head = doc.createElement('head')
    root.appendChild(head)

    title = doc.createElement('title')
    title.appendChild(doc.createTextNode(titlestring))

    link = doc.createElement('link')
    link.setAttribute('rel', 'stylesheet')
    link.setAttribute('href','css/reference.css')
    link.setAttribute('type', 'text/css')

    meta = doc.createElement('meta')
    meta.setAttribute('http-equiv', 'Content-Type')
    meta.setAttribute('content', 'application/xhtml+xml')
    meta.setAttribute('charset', 'utf-8')

    headlist = [title, link, meta]
    for tag in headlist:
        head.appendChild(tag)
    root.appendChild(head)

    body = doc.createElement('body')
    root.appendChild(body)

    return doc, body


def plos_fetch_single_representation(article_doi, item_xlink_href):
    """
    This function will render a formatted URL for accessing the PLoS' server
    SingleRepresentation of an object.
    """
    #A dict of URLs for PLoS subjournals
    journal_urls = {'pgen': 'http://www.plosgenetics.org/article/{0}',
                    'pcbi': 'http://www.ploscompbiol.org/article/{0}',
                    'ppat': 'http://www.plospathogens.org/article/{0}',
                    'pntd': 'http://www.plosntds.org/article/{0}',
                    'pmed': 'http://www.plosmedicine.org/article/{0}',
                    'pbio': 'http://www.plosbiology.org/article/{0}',
                    'pone': 'http://www.plosone.org/article/{0}',
                    'pctr': 'http://clinicaltrials.ploshubs.org/article/{0}'}
    #Identify subjournal name for base URl
    subjournal_name = article_doi.split('.')[1]
    base_url = journal_urls[subjournal_name]

    #Compose the address for fetchSingleRepresentation
    resource = 'fetchSingleRepresentation.action?uri=' + item_xlink_href
    return base_url.format(resource)


def scrapePLoSIssueCollection(issue_url):
    """
    Uses Beautiful Soup to scrape the PLoS page of an issue. It is used
    instead of xml.dom.minidom because of malformed html/xml
    """
    iu = urllib2.urlopen(issue_url)
    with open('temp','w') as temp:
        temp.write(iu.read())
    with open('temp', 'r') as temp:
        soup = BeautifulStoneSoup(temp)
    os.remove('temp')
    #Map the journal urls to nice strings
    jrns = {'plosgenetics': 'PLoS_Genetics', 'plosone': 'PLoS_ONE',
            'plosntds': 'PLoS_Neglected_Tropical_Diseases', 'plosmedicine':
            'PLoS_Medicine', 'plosbiology': 'PLoS_Biology', 'ploscompbiol':
            'PLoS_Computational_Biology', 'plospathogens': 'PLoS_Pathogens'}
    toc = soup.find('h1').string
    date = toc.split('Table of Contents | ')[1].replace(' ', '_')
    key = issue_url.split('http://www.')[1].split('.org')[0]
    name = '{0}_{1}.txt'.format(jrns[key], date)
    collection_name = os.path.join('collections', name)
    with open(collection_name, 'w') as collection:
        links = soup.findAll('a', attrs={'title': 'Read Open Access Article'})
        for link in links:
            href = link['href']
            if href[:9] == '/article/':
                id = href.split('10.1371%2F')[1].split(';')[0]
                collection.write('doi:10.1371/{0}\n'.format(id))