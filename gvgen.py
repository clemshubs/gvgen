#!/usr/bin/python
# -*- coding: utf-8 -*-
# $Id$
"""
GvGen - Generate dot file to be processed by graphviz
Copyright (c) 2012 Sebastien Tricaud <sebastien at honeynet org>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 2 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
"""

from __future__ import print_function
from six import iteritems
from sys import stdout

gvgen_version = "0.9.3"

debug = 0
debug_tree_unroll = 0

class GvGen:
    """
    Graphviz dot language Generation Class
    For example of usage, please see the __main__ function
    """

    def __init__(self, legend_name=None, options="compound=true;"): # allow links between clusters
        self.max_line_width = 10
        self.max_arrow_width = 2
        self.line_factor = 1
        self.arrow_factor = 0.5
        self.initial_line_width = 1.2
        self.initial_arrow_width = 0.8

        self.options = {}
        for option in options.split(";"):
            option = option.strip()
            if not option:
                continue
            key, value = option.split("=", 1)
            self.setOptions(**{key: value})

        self.__id = 0
        self.__nodes = []
        self.__links = []
        self.fd = stdout                           # File descriptor to output dot
        self.padding_str = "   "                   # Left padding to make children and parent look nice
        self.__styles = {}
        self.__default_style = []
        self.smart_mode = 0                      # Disabled by default

        # The graph has a legend
        if legend_name:
            self.legend = self.newItem(legend_name)

    def setOptions(self, **options):
        for key, value in iteritems(options):
            self.options[key] = value

    def __node_new(self, name, parent=None, distinct=None):
        """
        Create a new node in the data structure
        @name: Name of the node, that will be the graphviz label
        @parent: The node parent
        @distinct: if true, will not create and node that has the same name

        Returns: The node created
        """

        # We first check for distincts
        if distinct:
            if self.__nodes:
                for e in self.__nodes:
                    props = e['properties']
                    if props['label'] == name:
                        # We found the label name matching, we return -1
                        return -1

        # We now insert into gvgen datastructure
        self.__id += 1
        node = {'id': self.__id,        # Internal ID
                'parent': parent,       # Node parent for easy graphviz clusters
                'style': None,          # Style that GvGen allow you to create
                'properties': {         # Custom graphviz properties you can add, which will overide previously defined styles
                       'label': name
                   }
                }

        self.__nodes.append(node)

        return node

    def __link_smart(self, link):
        """
        Creates a smart link if smart_mode activated:
          if a -> b exists, and we now add a <- b,
          instead of doing:  a -> b
                               <-
          we do: a <-> b
        """

        linkfrom = self.__link_exists(link['from_node'], link['to_node'])
        linkto = self.__link_exists(link['to_node'], link['from_node'])

        if self.smart_mode:
            if linkto:
                self.__links.remove(linkto)
                self.propertyAppend(link, "dir", "both")

            pw = self.propertyGet(linkfrom, "penwidth")
            if pw:
                pw = float(pw)
                pw += self.line_factor
                if pw < self.max_line_width:
                    self.propertyAppend(linkfrom, "penwidth", str(pw))
            else:
                self.propertyAppend(link, "penwidth", str(self.initial_line_width))

            aw = self.propertyGet(linkfrom, "arrowsize")
            if aw:
                aw = float(aw)
                if aw < self.max_arrow_width:
                    aw += self.arrow_factor
                    self.propertyAppend(linkfrom, "arrowsize", str(aw))
            else:
                self.propertyAppend(link, "arrowsize", str(self.initial_arrow_width))

        if not linkfrom:
            self.__links.append(link)

    def __link_new(self, from_node, to_node, label=None, cl_from_node=None, cl_to_node=None):
        """
        Creates a link between two nodes
        @from_node: The node the link comes from
        @to_node: The node the link goes to

        Returns: The link created
        """

        link = {'from_node': from_node,
                'to_node': to_node,
                'style': None,             # Style that GvGen allow you to create
                'properties': {},         # Custom graphviz properties you can add, which will overide previously defined styles
                'cl_from_node': None,      # When linking from a cluster, the link appears from this node
                'cl_to_node': None,        # When linking to a cluster, the link appears to go to this node
                }

        if label:
            link['properties']['label'] = label

        if cl_from_node:
            link['cl_from_node'] = cl_from_node
        if cl_to_node:
            link['cl_to_node'] = cl_to_node

        # We let smart link work for us
        self.__link_smart(link)

        return link

    def __link_exists(self, from_node, to_node):
        """
        Find if a link exists
        @from_node: The node the link comes from
        @to_node: The node the link goes to

        Returns: true if the given link already exists
        """

        for link in self.__links:
            if link['from_node'] == from_node and link['to_node'] == to_node:
                return link

        return None

    def __has_children(self, parent):
        """
        Find children to a given parent
        Returns the children list
        """
        children_list = []
        for e in self.__nodes:
            if e['parent'] == parent:
                children_list.append(e)

        return children_list

    def newItem(self, name, parent=None, distinct=None):
        node = self.__node_new(name, parent, distinct)

        return node

    def newLink(self, src, dst, label=None, cl_src=None, cl_dst=None):
        """
        Link two existing nodes with each other
        """

        return self.__link_new(src, dst, label, cl_src, cl_dst)

    def debug(self):
        for e in self.__nodes:
            print("element = {0}".format(e['id']))

    #
    # Start: styles management
    #
    def styleAppend(self, stylename, key, val):
        if stylename not in self.__styles:
            self.__styles[stylename] = []

        self.__styles[stylename].append([key, val])

    def styleApply(self, stylename, node_or_link):
        node_or_link['style'] = stylename

    def styleDefaultAppend(self, key, val):
        self.__default_style.append([key, val])

    #
    # End: styles management
    #

    #
    # Start: properties management
    #
    def propertiesAsStringGet(self, node, props,level=0):
        """
        Get the properties string according to parent/children
        props is the properties dictionary
        """

        allProps = {}

        #
        # Default style come first, they can then be overriden
        #
        if self.__default_style:
            allProps.update(self.__default_style)

        #
        # First, we build the styles
        #
        if node['style']:
            stylename = node['style']
            allProps.update(self.__styles[stylename])

        #
        # Now we build the properties:
        # remember they override styles
        #
        allProps.update(props)

        if self.__has_children(node):
            propStringList = [level*self.padding_str+"%s=\"%s\";\n" % (k, v) for k, v in iteritems(allProps)]
            properties = ''.join(propStringList)
        else:
            if props:
                propStringList = ["%s=\"%s\"" % (k, v) for k, v in iteritems(allProps)]
                properties = '[' + ','.join(propStringList) + ']'
            else:
                properties = ''

        return properties

    def propertiesLinkAsStringGet(self, link):
        props = {}

        if link['style']:
            stylename = link['style']

            # Build the properties string for node
            props.update(self.__styles[stylename])

        props.update(link['properties'])

        properties = ''
        if props:
            properties += ','.join(["%s=\"%s\"" % (str(k),str(val)) for k, val in iteritems(props)])
        return properties

    def propertyForeachLinksAppend(self, node, key, val):
        for l in self.__links:
            if l['from_node'] == node:
                props = l['properties']
                props[key] = val

    def propertyAppend(self, node_or_link, key, val):
        """
        Append a property to the wanted node or link
        mynode = newItem(\"blah\")
        Ex. propertyAppend(mynode, \"color\", \"red\")
        """
        props = node_or_link['properties']
        props[key] = val

    def propertyGet(self, node_or_link, key):
        """
        Get the value of a given property
        Ex. prop = propertyGet(node, \"color\")
        """
        try:
            props = node_or_link['properties']
            return props[key]
        except:
            return None

    def propertyRemove(self, node_or_link, key):
        """
        Remove a property to the wanted node or link
        mynode = newItem(\"blah\")
        Ex. propertyRemove(mynode, \"color\")
        """
        props = node_or_link['properties']
        del props[key]

    #
    # End: Properties management
    #

    #
    # For a good legend, it has to be top to bottom whatever the rankdir
    #

    def legendAppend(self, legendstyle, legenddescr, labelin=None):
        
    # Determining if we need links according to rankdir
        needLinks=True

        if "rankdir" not in self.options:
            needLinks=False
        else:
            if self.options['rankdir'] == "LR":
                needLinks=False
            elif self.options['rankdir'] == "RL":
                needLinks=False
            elif self.options['rankdir'] == "TB":
                needLinks=True
            elif self.options['rankdir'] == "BT":
                needLinks=True

        # if the label is in the shape
        if labelin:

        # creating shape with label
            item = self.newItem(legenddescr, self.legend)
            self.styleApply(legendstyle, item)

        # if links needed
            if needLinks: 
                
        # we link all the nodes if they are here
                if self.__has_children(self.legend):

                    # remember the previous one
                    previousNode = None
                    for node in self.__has_children(self.legend):
                        # and if they are more than two
                        if previousNode:
                            link=self.newLink(previousNode,node)
                            self.propertyAppend(link, "dir", "none")
                            self.propertyAppend(link, "style", "invis")

                        #remembering node for next iteration
                        previousNode=node
            
        else:
        #creating shapes and labels separately
            style = self.newItem("", self.legend)
            descr = self.newItem(legenddescr, self.legend)
            self.styleApply(legendstyle, style)
            link = self.newLink(style, descr)

        #linking labels and shapes
            self.propertyAppend(link, "dir", "none")
            self.propertyAppend(link, "style", "invis")
            self.propertyAppend(descr, "shape", "plaintext")
   
            #if links needed
            if needLinks: 
            # removing constraints
                self.propertyAppend(link, "constraint", "false")

                # we link all the nodes if they are here
                if  self.__has_children(self.legend):
                
                    # remember the previous one
                    previousNode = None
                    previousLabel = None
        
                    for node in self.__has_children(self.legend):
                        # if it has no text, meaning its a shape
                        if node['properties']['label'] == "":
                            # and if they are more than two
                            if previousNode:
                                link=self.newLink(previousNode,node)
                                self.propertyAppend(link, "dir", "none")
                                self.propertyAppend(link, "style", "invis")

                            #remembering ...
                            previousNode=node

                        else:
                            # else its labels 
                            if previousLabel:
                                link=self.newLink(previousLabel,node)
                                self.propertyAppend(link, "dir", "none")
                                self.propertyAppend(link, "style", "invis")

                            #remembering previous label for next iteration
                            previousLabel=node
    
    def dotLinks(self, node):
        """
        Write links between nodes
        """
        for l in self.__links:
            if l['from_node'] == node:
                # Check if we link form a cluster
                children = self.__has_children(node)
                if children:
                    if l['cl_from_node']:
                        src = l['cl_from_node']['id']
                    else:
                        src = children[0]['id']
                    cluster_src = node['id']
                else:
                    src = node['id']
                    cluster_src = ''

                # Check if we link to a cluster
                children = self.__has_children(l['to_node'])
                if children:
                    if l['cl_to_node']:
                        dst = l['cl_to_node']['id']
                    else:
                        dst = children[0]['id']
                    cluster_dst = l['to_node']['id']
                else:
                    dst = l['to_node']['id']
                    cluster_dst = ''

                self.fd.write(self.padding_str + "node%d->node%d" % (src, dst))

                props = self.propertiesLinkAsStringGet(l)

                # Build new properties if we link from or to a cluster
                if cluster_src:
                    if props:
                        props += ','
                    props += "ltail=cluster%d" % cluster_src
                if cluster_dst:
                    if props:
                        props += ','
                    props += "lhead=cluster%d" % cluster_dst

                if props:
                    self.fd.write(" [%s]" % props)

                self.fd.write(";\n")

    def dot(self, fd=stdout):
        """
        Translates the datastructure into dot
        """
        try:
            self.fd = fd

            self.fd.write("/* Generated by GvGen v.%s (http://www.picviz.com/sections/opensource/gvgen.html) */\n\n" % (gvgen_version))

            self.fd.write("digraph G {\n")

            if self.options:
                for key, value in iteritems(self.options):
                    self.fd.write(self.padding_str + "%s=%s;\n" % (key, value))

            # We loop on root nodes (i.e. without parent)
            for e in self.__nodes:
                if not e['parent']:
                    self.trace(e)

            # We write the connection between nodes
            for e in self.__nodes:
                self.dotLinks(e)

            # We put all the nodes belonging to the parent
            self.fd.write("}")
        finally:
            # Remove our reference to file descriptor
            self.fd = None

    # as we say in french : de deux choses l une
    # either it is a subgraph, either it is a node
    # if it has children, it is a subgraph and I call trace again
    # else I draw nodes.
    def trace(self,node,level=1):
    
        if self.__has_children(node):
            # if child then subgraph
            # padding and subgraph 
            self.fd.write("\n"+level * self.padding_str + "subgraph cluster%d {\n" % node['id'])
            # properties
            self.fd.write("%s" % self.propertiesAsStringGet(node, node['properties'],level+1))

            # looping on children
            for child in self.__has_children(node):
                self.trace(child,level+1)

            # closing subgraph
            self.fd.write(level * self.padding_str + "}\n\n")
        else:
            
            # if no child then its a node
            self.fd.write(level * self.padding_str + "node%d %s;\n" % (node['id'], self.propertiesAsStringGet(node,node['properties'],level)))

if __name__ == "__main__":
    graph = GvGen()

    graph.smart_mode = 1

    graph.styleDefaultAppend("color", "blue")

    parents = graph.newItem("Parents")
    father = graph.newItem("Bob", parents)
    mother = graph.newItem("Alice", parents)
    children = graph.newItem("Children")
    child1 = graph.newItem("Carol", children)
    child2 = graph.newItem("Eve", children)
    child3 = graph.newItem("Isaac", children)
    postman = graph.newItem("Postman")
    graph.newLink(father, child1)
    graph.newLink(child1, father)
    graph.newLink(father, child1)
    graph.newLink(father, child2)
    graph.newLink(mother, child2)
    myl = graph.newLink(mother, child1)
    graph.newLink(mother, child3)
    graph.newLink(postman, child3, "Email is safer")
    graph.newLink(parents, postman)    # Cluster link

    graph.propertyForeachLinksAppend(parents, "color", "blue")

    graph.propertyForeachLinksAppend(father, "label", "My big link")
    graph.propertyForeachLinksAppend(father, "color", "red")

    graph.propertyAppend(postman, "color", "red")
    graph.propertyAppend(postman, "fontcolor", "white")

    graph.styleAppend("link", "label", "mylink")
    graph.styleAppend("link", "color", "green")
    graph.styleApply("link", myl)
    graph.propertyAppend(myl, "arrowhead", "empty")

    graph.styleAppend("Post", "color", "blue")
    graph.styleAppend("Post", "style", "filled")
    graph.styleAppend("Post", "shape", "rectangle")
    graph.styleApply("Post", postman)

    graph.dot()
