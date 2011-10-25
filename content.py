import xml.dom.minidom as minidom
import os, os.path
import utils

class OPSContent(object):
    '''A class for instantiating content xml documents in the OPS Preferred
    Vocabulary'''
    def __init__(self, documentstring, outdirect, metadata, backdata):
        self.inputstring = documentstring
        self.doc = minidom.parse(self.inputstring)
        self.outdir = os.path.join(outdirect, 'OPS')
        self.outputs = {'Synopsis': os.path.join(outdirect, 'OPS', 'synop.xml'), 
                        'Main': os.path.join(outdirect, 'OPS', 'main.xml'), 
                        'Biblio': os.path.join(outdirect, 'OPS', 'biblio.xml'), 
                        'Tables': os.path.join(outdirect, 'OPS', 'tables.xml')}
        self.metadata = metadata
        self.backdata = backdata
        
        self.createSynopsis(self.metadata, self.backdata)
        self.createMain(self.doc)
        self.createBiblio(self.doc)
        
    def createSynopsis(self, meta, back):
        '''Create an output file containing a representation of the article 
        synopsis'''
        
        #Initiate the document, returns the document and its body element
        synop, synbody = self.initiateDocument('Synopsis file')
        
        #Create and place the title in the body element
        art_title = meta.article_meta.title
        titlenode = synop.createElement('h1')
        titlenode.appendChild(synop.createTextNode(art_title))
        synbody.appendChild(titlenode)
        
        affiliation_index = []
        #corresp_dict = {}
        
        #Create authors
        authors = meta.article_meta.art_auths
        author_container = synop.createElement('h2')
        first = True
        #con_char = [u'*', u'\u2020', u'\u2021']
        #ccnt = 0
        for author in authors:
            if not first:
                author_container.appendChild(synop.createTextNode(', '))
            else:
                first = False
            name = author.get_name()
            affs = author.affiliation
            contact = author.contact
            author_container.appendChild(synop.createTextNode(name))
            for aff in affs:
                if aff not in affiliation_index:
                    affiliation_index.append(aff)
                sup = synop.createElement('sup')
                aref = synop.createElement('a')
                aref.setAttribute('href', 'synop.xml#{0}'.format(aff))
                aref.appendChild(synop.createTextNode(str(affiliation_index.index(aff) + 1)))
                sup.appendChild(aref)
                author_container.appendChild(sup)
            for contact in author.contact:
                sup = synop.createElement('sup')
                aref = synop.createElement('a')
                aref.setAttribute('href', 'synop.xml#{0}'.format(contact))
                #character = con_char[ccnt]
                #aref.appendChild(synop.createTextNode(character))
                aref.appendChild(synop.createTextNode('*'))
                sup.appendChild(aref)
                author_container.appendChild(sup)
                #corresp_dict[contact] = character
                #ccnt += 1
                
        synbody.appendChild(author_container)
        
        #Create a node for the affiliation text
        aff_line = synop.createElement('p')
        art_affs = meta.article_meta.art_affs
        for item in art_affs:
            if 'aff' in item.rid:
                sup = synop.createElement('sup')
                sup.setAttribute('id', item.rid)
                sup.appendChild(synop.createTextNode(str(art_affs.index(item) + 1)))
                aff_line.appendChild(sup)
                aff_line.appendChild(synop.createTextNode(item.address))
        synbody.appendChild(aff_line)
        
        #Create the Abstract
        abstract = meta.article_meta.abstract
        abstitle = synop.createElement('h2')
        abstitle.appendChild(synop.createTextNode('Abstract'))
        synbody.appendChild(abstitle)
        synbody.appendChild(abstract)
        abstract.tagName = 'div'
        abstract.setAttribute('id', 'abstract')
        for title in abstract.getElementsByTagName('title'):
            title.tagName = 'h3'
        for sec in abstract.getElementsByTagName('sec'):
            sec.tagName = 'div'
        for para in abstract.getElementsByTagName('p'):
            para.tagName = 'big'
        for italic in abstract.getElementsByTagName('italic'):
            italic.tagName = 'i'
        
        #Create a node for the Editor
        ped = synop.createElement('p')
        ped.setAttribute('id', 'editor')
        bed = synop.createElement('b')
        editor_line = synop.createTextNode('Editor: ')
        bed.appendChild(editor_line)
        ped.appendChild(bed)
        first = True
        for editor in meta.article_meta.art_edits:
            name = editor.get_name()
            affs = editor.affiliation
            ped.appendChild(synop.createTextNode('{0}, '.format(name)))
            for aff in affs:
                for item in meta.article_meta.art_affs:
                    if item.rid == aff:
                        address = item.address
                        if first:
                            ped.appendChild(synop.createTextNode('{0}'.format(address)))
                            first = False
                        else:
                            ped.appendChild(synop.createTextNode('; {0}'.format(address)))
        synbody.appendChild(ped)
        
        #Create a node for the dates
        datep = synop.createElement('p')
        datep.setAttribute('id', 'dates')
        hist = meta.article_meta.history
        dates = meta.article_meta.art_dates
        datelist = [('Received', hist['received']), 
                    ('Accepted', hist['accepted']), 
                    ('Published', dates['epub'])]
        
        for _bold, _data in datelist:
            bold = synop.createElement('b')
            bold.appendChild(synop.createTextNode('{0} '.format(_bold)))
            datep.appendChild(bold)
            datestring = _data.niceString()
            datep.appendChild(synop.createTextNode('{0} '.format(datestring)))
        synbody.appendChild(datep)
        
        #Create a node for the Copyright text:
        copp = synop.createElement('p')
        copp.setAttribute('id', 'copyright')
        copybold = synop.createElement('b')
        copybold.appendChild(synop.createTextNode('Copyright: '))
        copp.appendChild(copybold)
        copystr = u'{0} {1} {2}'.format(u'\u00A9', 
                                        meta.article_meta.art_copyright_year, 
                                        meta.article_meta.art_copyright_statement)
        copp.appendChild(synop.createTextNode(copystr))
        synbody.appendChild(copp)
        
        #Create a node for the Funding text
        fundp = synop.createElement('p')
        fundp.setAttribute('id', 'funding')
        fundbold = synop.createElement('b')
        fundbold.appendChild(synop.createTextNode('Funding: '))
        fundp.appendChild(fundbold)
        fundp.appendChild(synop.createTextNode(back.funding))
        synbody.appendChild(fundp)
        
        #Create a node for the Competing Interests text
        compip = synop.createElement('p')
        compip.setAttribute('id', 'competing-interests')
        compibold = synop.createElement('b')
        compibold.appendChild(synop.createTextNode('Competing Interests: '))
        compip.appendChild(compibold)
        compip.appendChild(synop.createTextNode(back.competing_interests))
        synbody.appendChild(compip)
        
        #Create a node for the correspondence text
        corr_line = synop.createElement('p')
        art_corresps = meta.article_meta.art_corresps
        art_corr_nodes = meta.article_meta.correspondences
        
        # PLoS does not appear to list more than one correspondence... >.<
        corr_line.setAttribute('id', art_corresps[0].rid)
        corresp_text = utils.serializeText(art_corr_nodes[0])
        corr_line.appendChild(synop.createTextNode(corresp_text))
        
        #Handle conversion of ext-link to <a>
        ext_links = synop.getElementsByTagName('ext-link')
        for ext_link in ext_links:
            ext_link.tagName = u'a'
            ext_link.removeAttribute('ext-link-type')
            href = ext_link.getAttribute('xlink:href')
            ext_link.removeAttribute('xlink:href')
            ext_link.removeAttribute('xlink:type')
            ext_link.setAttribute('href', href)
        
        # If they did, this approach might be used
        #for item in art_corresps:
        #    sup = synop.createElement('sup')
        #    sup.setAttribute('id', item.rid)
        #    sup.appendChild(synop.createTextNode(corresp_dict[item.rid]))
        #    corr_line.appendChild(sup)
        #    if item.address:
        #        add = synop.createTextNode('Address: {0} '.format(item.address))
        #        corr_line.appendChild(add)
        #    if item.email:
        #        add = synop.createTextNode('E-mail: {0} '.format(item.email))
        #        corr_line.appendChild(add)
        synbody.appendChild(corr_line)
        
        with open(self.outputs['Synopsis'],'wb') as out:
            out.write(synop.toprettyxml(encoding = 'utf-8'))

    def createMain(self, doc):
        '''Create an output file containing the main article body content'''
        #Initiate the document, returns the document and its body element
        main, mainbody = self.initiateDocument('Main file')
        
        body = doc.getElementsByTagName('body')[0]
        for item in body.childNodes:
            mainbody.appendChild(item.cloneNode(deep = True))
            
        for sec in mainbody.getElementsByTagName('sec'):
            sec.tagName = 'div' #Universally convert <sec> to <div>
            try:
                sec.removeAttribute('sec-type')
            except:
                pass
        for italic in mainbody.getElementsByTagName('italic'):
            italic.tagName = 'i' #Universally convert <italic> to <i>
        
        #Scan through the Document converting the section title nodes to 
        #proper format tags
        self.divTitleScan(mainbody, depth = 0)
        
        #Handle conversion of figures to html image format
        figs = mainbody.getElementsByTagName('fig')
        for item in figs:
            parent = item.parentNode
            sibling = item.nextSibling
            fid = item.getAttribute('id')
            label_text = utils.getTagData(item.getElementsByTagName('label'))
            img = None
            name = fid.split('-')[-1]
            startpath = os.path.abspath('./') 
            os.chdir(self.outdir)
            for path, _subdirs, filenames in os.walk('images'):
                for filename in filenames:
                    if os.path.splitext(filename)[0] == name:
                        img = os.path.join(path, filename)
            os.chdir(startpath)
            #Create and insert the img node before the fig node's sibling
            imgnode = main.createElement('img')
            imgnode.setAttribute('src', img)
            imgnode.setAttribute('id', fid)
            imgnode.setAttribute('alt', 'A Figure')
            parent.insertBefore(imgnode, sibling)
            #Convert caption to <div class="caption">...</div>
            caption = item.getElementsByTagName('caption')[0]
            caption.tagName = u'div'
            caption.setAttribute('class', 'caption')
            bold_label_text = main.createElement('b')
            bold_label_text.appendChild(main.createTextNode('{0}.'.format(label_text)))
            caption.insertBefore(bold_label_text, caption.firstChild)
            for title_tag in caption.getElementsByTagName('title'):
                title_tag.tagName = u'b'
            parent.insertBefore(caption, sibling)
            #prohib_eles = [u'object-id', u'graphic', u'label'] 
            #for each in item.childNodes:
                #if not each.nodeType == each.TEXT_NODE:
                    #if each.tagName not in prohib_eles:
                        #parent.insertBefore(each.cloneNode(deep = True), sibling)
                
            parent.removeChild(item)
            
        #Handle conversion of <table-wrap> to html image with reference to 
        #external file containing original html table
        tables = mainbody.getElementsByTagName('table-wrap')
        for item in tables:
            parent = item.parentNode
            sibling = item.nextSibling
            table_id = item.getAttribute('id')
            label = item.getElementsByTagName('label')[0]
            label_text = utils.getText(label)
            title = item.getElementsByTagName('title')
            title_text = utils.getTagData(title)
            #Create a Table Label, includes label and title, place before the image
            table_label = main.createElement('div')
            table_label.setAttribute('class', 'table_label')
            table_label.setAttribute('id', table_id)
            table_label_b = main.createElement('b')
            table_label_b.appendChild(main.createTextNode(label_text))
            table_label.appendChild(table_label_b)
            table_label.appendChild(main.createTextNode(title_text))
            parent.insertBefore(table_label, sibling)
            
            name = table_id.split('-')[-1]
            img = None
            startpath = os.path.abspath('./') 
            os.chdir(self.outdir)
            for path, _subdirs, filenames in os.walk('images'):
                for filename in filenames:
                    if os.path.splitext(filename)[0] == name:
                        img = os.path.join(path, filename)
            os.chdir(startpath)
            #Create and insert the img node before the table-wrap node's sibling
            imgnode = main.createElement('img')
            imgnode.setAttribute('src', img)
            imgnode.setAttribute('alt', 'A Table')
            parent.insertBefore(imgnode, sibling)
            
            #Handle the HTML version of the table
            table_doc, table_doc_main = self.initiateDocument('HTML Versions of Tables')
            try:
                html_table = item.getElementsByTagName('table')[0]
                html_table.removeAttribute('alternate-form-of')
                html_table.setAttribute('id', 'h{0}'.format(name))
                for btag in html_table.getElementsByTagName('bold'):
                    btag.tagName = u'b'
                table_doc_main.appendChild(html_table)
                link = main.createElement('a')
                link.setAttribute('href', 'tables.xml#h{0}'.format(name))
                link.appendChild(main.createTextNode('HTML version of {0}'.format(label_text)))
                parent.insertBefore(link , sibling)
            except:
                pass
            
            parent.removeChild(item)
            
        with open(self.outputs['Tables'],'wb') as output:
            output.write(table_doc.toprettyxml(encoding = 'utf-8'))
            
        #Need to intelligently handle conversion of <xref> elements
        xrefs = mainbody.getElementsByTagName('xref')
        for elem in xrefs:
            elem.tagName = u'a' #Convert the tag to <a>
            ref_type = elem.getAttribute('ref-type')
            refid = elem.getAttribute('rid')
            if ref_type == u'bibr':
                dest = u'biblio.xml#{0}'.format(refid)
            elif ref_type == u'fig':
                dest = u'main.xml#{0}'.format(refid)
            elif ref_type == u'supplementary-material':
                dest = u'main.xml#{0}'.format(refid)
            elif ref_type == u'table':
                dest = u'main.xml#{0}'.format(refid)
            elif ref_type == 'aff':
                dest = u'synop.xml#{0}'.format(refid)
            elem.removeAttribute('ref-type')
            elem.removeAttribute('rid')
            elem.setAttribute('href', dest)
        
        caps = mainbody.getElementsByTagName('caption')
        for cap in caps:
            cap.tagName = u'div'
        
        #Handle the display of inline equations
        inline_equations = mainbody.getElementsByTagName('inline-formula')
        for each in inline_equations:
            parent = each.parentNode
            sibling = each.nextSibling
            
            inline_graphic = each.getElementsByTagName('inline-graphic')[0]
            xlink_href_id = inline_graphic.getAttribute('xlink:href')
            name = xlink_href_id.split('.')[-1]
            img = None
            startpath = os.path.abspath('./') 
            os.chdir(self.outdir)
            for path, _subdirs, filenames in os.walk('images'):
                for filename in filenames:
                    if os.path.splitext(filename)[0] == name:
                        img = os.path.join(path, filename)
            os.chdir(startpath)
            
            imgnode = main.createElement('img')
            imgnode.setAttribute('src', img)
            imgnode.setAttribute('alt', 'An inline formula')
            
            parent.insertBefore(imgnode, sibling)
            parent.removeChild(each)
            
        
        #Handle the display of out of line equations
        #Requires separating children to two <p> tags flanking the displayed 
        #formula
        disp_equations = mainbody.getElementsByTagName('disp-formula')
        for disp in disp_equations:
            
            parent = disp.parentNode
            sibling = disp.nextSibling
            
            if sibling:
                new_parent = main.createElement('p')
                disp_index = parent.childNodes.index(disp)
                for child in parent.childNodes[(disp_index +1):]:
                    new_parent.appendChild(child)
            else:
                new_parent = None
            
            grandparent = parent.parentNode
            parent_sib = parent.nextSibling
            if parent_sib:
                disp_p_node = main.createElement('p')
                grandparent.insertBefore(disp_p_node, parent_sib)
                if new_parent:
                    grandparent.insertBefore(new_parent, parent_sib)
            
            else:
                grandparent.appendChild(disp_p_node_)
                grandparent.appendChild(newparent)
            
            graphic = disp.getElementsByTagName('graphic')[0]
            
            xlink_href_id = graphic.getAttribute('xlink:href')
            name = xlink_href_id.split('.')[-1]
            img = None
            startpath = os.path.abspath('./') 
            os.chdir(self.outdir)
            for path, _subdirs, filenames in os.walk('images'):
                for filename in filenames:
                    if os.path.splitext(filename)[0] == name:
                        img = os.path.join(path, filename)
            os.chdir(startpath)
            
            imgnode = main.createElement('img')
            imgnode.setAttribute('src', img)
            imgnode.setAttribute('alt', 'A display formula')
            
            disp_p_node.appendChild(imgnode)
            parent.removeChild(disp)
            
        #Need to handle lists in the document
        lists = mainbody.getElementsByTagName('list')
        for list in lists:
            try:
                title = utils.getTagData(list.getElementsByTagName('title'))
                list.setAttribute('title', title)
                list.removeChild('title')
            except:
                pass
            try:
                list_id = list.getAttribute('id')
                list_content = list.getAttribute('list-content')
                list_type = list.getAttribute('list-type')
                prefix_word = list.getAttribute('prefix-word')
            except:
                pass
            
            if list_type == u'order':
                list.tagName = u'ol'
            elif list_type == u'bullet':
                list.tagName = u'ul'
            elif list_type == u'alpha-lower':
                list.tagName = u'ol'
            elif list_type == u'alpha-upper':
                list.tagName = u'ol'
            elif list_type == u'roman-lower':
                list.tagName = u'ol'
            elif list_type == u'roman-upper':
                list.tagName = u'ol'
            elif list_type == u'simple':
                list.tagName = u'ul'
                list.setAttribute('style','simple')
            else:
                list.tagName = 'ul'
                print('Unknown List Type in document!')
                prefix_word = '!' + prefix_word
            
            list_items = list.getElementsByTagName('list-item')
            for list_item in list_items:
                list_item.tagName = u'li'
            
            try:
                list.removeAttribute('list-content')
            except:
                pass
            try:
                list.removeAttribute('list-type')
            except:
                pass
            try:
                list.removeAttribute('prefix-word')
            except:
                pass
        
        #Convert supplementary-material tags to div tags
        #for now they will just be "sanitized", but in the future they
        #should try to provide valid links to the materials
        supp_mats = mainbody.getElementsByTagName('supplementary-material')
        for supp_mat in supp_mats:
            supp_id = supp_mat.getAttribute('id')
            supp_mat.tagName = u'div'
            label = supp_mat.getElementsByTagName('label')[0]
            label.tagName = u'b'
            bolds = supp_mat.getElementsByTagName('bold')
            for bold in bolds:
                bold.tagName = u'b'
            italics = supp_mat.getElementsByTagName('italic')
            for italic in italics:
                italic.tagName = u'i'
            try:
                supp_mat.removeAttribute('mimetype')
            except:
                pass
            try:
                supp_mat.removeAttribute('position')
            except:
                pass
            try:
                plos_jrns= {'pgen': 'http://www.plosgenetics.org/', 
                            'pone': 'http://www.plosone.org/', 
                            'pbio': 'http://www.plosbiology.org/', 
                            'pcbi': 'http://www.ploscompbiol.org/', 
                            'ppat': 'http://www.plospathogens.org/', 
                            'pmed': 'http://www.plosmedicine.org/', 
                            'pntd': 'http://www.plosntds.org/'}
                jrn = supp_id.split('.')[0]
                plos_fetch = 'article/fetchSingleRepresentation.action?uri='
                xlink = supp_mat.getAttribute('xlink:href')
                href = u'{0}{1}{2}'.format(plos_jrns[jrn], plos_fetch, xlink)
                anchor = main.createElement('a')
                anchor.setAttribute('href', href)
                supp_mat.insertBefore(anchor, label)
                anchor.appendChild(label)
                supp_mat.removeAttribute('xlink:href')
            except:
                pass
            try:
                supp_mat.removeAttribute('xlink:type')
            except:
                pass
        
        ext_links = main.getElementsByTagName('ext-link')
        for ext_link in ext_links:
            ext_link.tagName = u'a'
            ext_link.removeAttribute('ext-link-type')
            href = ext_link.getAttribute('xlink:href')
            ext_link.removeAttribute('xlink:href')
            ext_link.removeAttribute('xlink:type')
            ext_link.setAttribute('href', href)
            
        bolds = main.getElementsByTagName('bold')
        for bold in bolds:
            bold.tagName = 'b'
        
        with open(self.outputs['Main'],'wb') as out:
            out.write(main.toprettyxml(encoding = 'utf-8'))
        
    def createBiblio(self, doc):
        '''Create an output file containing the article bibliography'''
        #Initiate the document, returns the document and its body element
        biblio, bibbody = self.initiateDocument('Bibliography file')
        
        back = doc.getElementsByTagName('back')[0]
        
        bib_title = doc.createElement('h2')
        bib_title.appendChild(doc.createTextNode('References'))
        bibbody.appendChild(bib_title)
        
        refs = back.getElementsByTagName('ref')
        for item in refs:
            bibbody.appendChild(self.parseRef(item, biblio))
        
        #for item in back.childNodes:
        #    if not item.nodeType == item.TEXT_NODE:
        #        if not item.tagName == u'fn-group':bold
        #            bibbody.appendChild(item.cloneNode(deep = True))
        
        
        with open(self.outputs['Biblio'],'wb') as out:
            out.write(biblio.toprettyxml(encoding = 'utf-8'))
            
    def parseRef(self, fromnode, doc):
        '''Interprets the references in the article back reference list into 
        comprehensible xml'''
        
        #Create a paragraph tag to contain the reference text data
        ref_par = doc.createElement('p')
        #Set the fragment identifier for the paragraph tag
        ref_par.setAttribute('id', fromnode.getAttribute('id'))
        #Pull the label node into a node_list
        label = fromnode.getElementsByTagName('label')
        #Collect the citation tag and its citation type
        citation = fromnode.getElementsByTagName('citation')[0]
        citation_type = citation.getAttribute('citation-type')
        
        #Format the reference string if it is a Journal citation type
        if citation_type == u'journal':
            ref_string = u''
            #Append the Label text
            ref_string += u'{0}. '.format(utils.getTagData(label))
            #Collect the author names and construct a formatted string
            auths = fromnode.getElementsByTagName('name')
            for auth in auths:
                surname = auth.getElementsByTagName('surname')
                given = auth.getElementsByTagName('given-names')
                name_str = u'{0} {1}'.format(utils.getTagData(surname),
                                             utils.getTagData(given))
                if auth.nextSibling:
                    name_str += u', '
                else:
                    name_str += u' '
                ref_string += name_str
            #Determine existence of <etal/> and append string if true
            etal = fromnode.getElementsByTagName('etal')
            if etal:
                ref_string += u'et al. '
            #Extract the year data
            year = fromnode.getElementsByTagName('year')
            ref_string += u'({0}) '.format(utils.getTagData(year))
            #Extract the article title
            art_title = fromnode.getElementsByTagName('article-title')
            ref_string += u'{0} '.format(utils.getTagData(art_title))
            #Extract the source data
            source = fromnode.getElementsByTagName('source')
            ref_string += u'{0} '.format(utils.getTagData(source))
            #Extract the volume data
            volume = fromnode.getElementsByTagName('volume')
            ref_string += u'{0}'.format(utils.getTagData(volume))
            #Issue data may be present, handle both options
            issue = fromnode.getElementsByTagName('issue')
            if issue:
                ref_string += u'({0}): '.format(utils.getTagData(issue))
            else:
                ref_string += u': '
            #Extract the fpage data
            fpage = fromnode.getElementsByTagName('fpage')
            ref_string += u'{0}'.format(utils.getTagData(fpage))
            #lpage data may be present, handle both options
            lpage = fromnode.getElementsByTagName('lpage')
            if lpage:
                ref_string += u'-{0}.'.format(utils.getTagData(lpage))
            else:
                ref_string += u'.'
            
            ref_par.appendChild(doc.createTextNode(ref_string))
        
        elif citation_type == u'other':
            ref_string = u'{0}. '.format(utils.getTagData(label))
            ref_string += self.refOther(citation, stringlist = [])
            ref_par.appendChild(doc.createTextNode(ref_string[:-2]))
            
        return ref_par
            
    def refOther(self, node, stringlist = []):
        '''Attempts to broadly handle Other citation types and produce a 
        human intelligible string output'''
        
        for item in node.childNodes:
            if item.nodeType == item.TEXT_NODE and not item.data == u'\n':
                if item.data.lstrip():
                    if item.parentNode.tagName == u'year':
                        stringlist.append(u'({0})'.format(item.data))
                        stringlist.append(u', ')
                    elif item.parentNode.tagName == u'source':
                        stringlist.append(u'[{0}]'.format(item.data))
                        stringlist.append(u', ')
                    elif item.parentNode.tagName == u'article-title':
                        stringlist.append(u'\"{0}\"'.format(item.data))
                        stringlist.append(u', ')
                    else:
                        stringlist.append(item.data)
                        stringlist.append(u', ')
            else:
                self.refOther(item, stringlist)
        return u''.join(stringlist)
        
    def divTitleScan(self, fromnode, depth = 0):
        taglist = ['h2', 'h3', 'h4', 'h5', 'h6']
        for item in fromnode.childNodes:
            try:
                if item.tagName == u'div':
                    divtitle = item.getElementsByTagName('title')[0]
                    divtitle.tagName = taglist[depth]
                    depth += 1
                    self.divTitleScan(item, depth)
                    depth -= 1
            except AttributeError:
                pass

    def initiateDocument(self, titlestring):
        '''A method for conveniently initiating a new xml.DOM Document'''
        
        impl = minidom.getDOMImplementation()
        
        mytype = impl.createDocumentType('html', 
                                         '-//W3C//DTD XHTML 1.1//EN', 
                                         'http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd')
        doc = impl.createDocument(None, 'html', mytype)
        
        root = doc.lastChild #IGNORE:E1101
        root.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml')
        root.setAttribute('xml:lang', 'en-US')
        
        head = doc.createElement('head')
        root.appendChild(head)
        
        title = doc.createElement('title')
        title.appendChild(doc.createTextNode(titlestring))
        
        link = doc.createElement('link')
        link.setAttribute('rel', 'stylesheet')
        link.setAttribute('href','css/article.css')
        link.setAttribute('type', 'text/css')
        
        meta = doc.createElement('meta')
        meta.setAttribute('http-equiv', 'Content-Type')
        meta.setAttribute('content', 'application/xhtml+xml')
        
        headlist = [title, link, meta]
        for tag in headlist:
            head.appendChild(tag)
        root.appendChild(head)
        
        body = doc.createElement('body')
        root.appendChild(body)
        
        return doc, body