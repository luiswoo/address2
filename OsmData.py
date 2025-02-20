#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xml.sax
import copy

LON = 1
LAT = 2
REF = 3
TAG = 4
ACTION = 5
VERSION = 6
USER = 7
UID = 8
CHANGESET = 9
CREATE = 0
MODIFY = 1
DELETE = 2
NODES = 0
WAYS = 1
RELATIONS = 2


class OsmData(xml.sax.ContentHandler):
    def __init__(self):
        self.nodes = {}
        self.ways = {}
        self.relations = {}
        self.comments = []
        self.bbox = [0, 0, 0, 0]  # minlon, minlat, maxlon, maxlat
        self.currnodeid = -1
        self.currwayid = -1
        self.currrelationid = -1
        self.currentObj = None
        self.currentId = None

    def addnode(self, Id=0):
        if Id == 0:
            while self.nodes.get(self.currnodeid) is not None:
                self.currnodeid -= 1
            self.nodes[self.currnodeid] = {LON: 0, LAT: 0, ACTION: CREATE, TAG: {}}
            return self.currnodeid
        else:
            self.nodes[Id] = {ACTION: MODIFY}
            return Id

    def addway(self, Id=0):
        if Id == 0:
            while self.ways.get(self.currwayid) is not None:
                self.currwayid -= 1
            self.ways[self.currwayid] = {ACTION: CREATE, TAG: {}, REF: []}
            return self.currwayid
        else:
            self.ways[Id] = {ACTION: MODIFY}
            return Id

    def mergedata(self, other):
        self.nodes.update(copy.deepcopy(other.nodes))
        self.ways.update(copy.deepcopy(other.ways))
        self.relations.update(copy.deepcopy(other.relations))

    def addcomment(self, text):
        self.comments.append(text)

    def read(self, sourceStream):
        parser = xml.sax.make_parser()
        parser.setContentHandler(self)
        try:
            for line in sourceStream:
                parser.feed(line)
        except xml.sax.SAXException as e:
            print(f"Ошибка XML: {e}")
        finally:
            parser.close()

    def write(self, targetStream):
        targetStream.write("<osm version=\"0.6\">\n")

        # Creating
        for node in self.nodes.items():
            if node[1].get(ACTION) != CREATE:
                continue
            targetStream.write(self.xmlnode(node))
        for way in self.ways.items():
            if way[1].get(ACTION) != CREATE:
                continue
            targetStream.write(self.xmlway(way))
        for relation in self.relations.items():
            if relation[1].get(ACTION) != CREATE:
                continue
            targetStream.write(self.xmlrelation(relation))

        # Modifying
        for node in self.nodes.items():
            if node[1].get(ACTION) != MODIFY:
                continue
            targetStream.write(self.xmlnode(node))
        for way in self.ways.items():
            if way[1].get(ACTION) != MODIFY:
                continue
            targetStream.write(self.xmlway(way))
        for relation in self.relations.items():
            if relation[1].get(ACTION) != MODIFY:
                continue
            targetStream.write(self.xmlrelation(relation))

        # Deleting
        for relation in self.relations.items():
            if relation[1].get(ACTION) != DELETE:
                continue
            targetStream.write(self.xmlrelation(relation))
        for way in self.ways.items():
            if way[1].get(ACTION) != DELETE:
                continue
            targetStream.write(self.xmlway(way))
        for node in self.nodes.items():
            if node[1].get(ACTION) != DELETE:
                continue
            targetStream.write(self.xmlnode(node))
        for text in self.comments:
            targetStream.write("<!--" + text + "-->\n")
        targetStream.write("</osm>")

    def xmlnode(self, node):
        string = "<node id='" + str(node[0]) + "' "
        for attr, value in node[1].items():
            if attr == ACTION:
                if value == MODIFY:
                    string += "action='modify' "
                elif value == DELETE:
                    string += "action='delete' "
            elif attr == VERSION:
                string += "version='" + str(value) + "' "
            elif attr == CHANGESET:
                string += "changeset='" + str(value) + "' "
            elif attr == UID:
                string += "uid='" + str(value) + "' "
            elif attr == LAT:
                string += "lat='" + str(value) + "' "
            elif attr == LON:
                string += "lon='" + str(value) + "' "
            elif attr == USER:
                string += "user='" + str(value) + "' "
            elif attr == "timestamp" or attr == "visible":
                string += attr + "='" + str(value) + "' "

        if node[1][TAG]:
            string += ">\n"
            for k, v in node[1][TAG].items():
                string += "<tag k='" + str(k) + "' v='" + str(v) + "' />\n"
            string += "</node>\n"
        else:
            string += "/>\n"
        return string

    def xmlway(self, way):
        string = "<way id='" + str(way[0]) + "' "
        for attr, value in way[1].items():
            if attr == ACTION:
                if value == MODIFY:
                    string += "action='modify' "
                elif value == DELETE:
                    string += "action='delete' "
            elif attr == VERSION:
                string += "version='" + str(value) + "' "
            elif attr == CHANGESET:
                string += "changeset='" + str(value) + "' "
            elif attr == UID:
                string += "uid='" + str(value) + "' "
            elif attr == USER:
                string += "user='" + str(value) + "' "
            elif attr == "timestamp" or attr == "visible":
                string += attr + "='" + str(value) + "' "
        string += ">\n"
        for ref in way[1][REF]:
            string += "<nd ref='" + str(ref) + "' />\n"
        for k, v in way[1][TAG].items():
            string += "<tag k='" + str(k) + "' v='" + str(v) + "' />\n"
        string += "</way>\n"
        return string

    def xmlrelation(self, relation):
        string = "<relation id='" + str(relation[0]) + "' "
        for attr, value in relation[1].items():
            if attr == ACTION:
                if value == MODIFY:
                    string += "action='modify' "
                elif value == DELETE:
                    string += "action='delete' "
            elif attr == VERSION:
                string += "version='" + str(value) + "' "
            elif attr == CHANGESET:
                string += "changeset='" + str(value) + "' "
            elif attr == UID:
                string += "uid='" + str(value) + "' "
            elif attr == USER:
                string += "user='" + str(value) + "' "
            elif attr == "timestamp" or attr == "visible":
                string += attr + "='" + str(value) + "' "
        string += ">\n"
        for ref in relation[1][REF][NODES]:
            string += "<member type='node' ref='" + str(ref[0]) + "' role='" + str(ref[1]) + "' />\n"
        for ref in relation[1][REF][WAYS]:
            string += "<member type='way' ref='" + str(ref[0]) + "' role='" + str(ref[1]) + "' />\n"
        for ref in relation[1][REF][RELATIONS]:
            string += "<member type='relation' ref='" + str(ref[0]) + "' role='" + str(ref[1]) + "' />\n"
        for k, v in relation[1][TAG].items():
            string += "<tag k='" + str(k) + "' v='" + str(v) + "' />\n"
        string += "</relation>\n"
        return string

    def startElement(self, tag, attributes):
        if tag == "node":
            self.currentObj = {}
            self.currentId = int(attributes.get("id"))
            self.currentObj[VERSION] = int(attributes.get("version", 0))
            self.currentObj[CHANGESET] = int(attributes.get("changeset", 0))
            self.currentObj[UID] = int(attributes.get("uid", 0))
            self.currentObj[LAT] = float(attributes.get("lat", 0))
            self.currentObj[LON] = float(attributes.get("lon", 0))
            self.currentObj[USER] = attributes.get("user", "")

            if self.currentObj[LAT] < self.bbox[1] or self.bbox[1] == 0:
                self.bbox[1] = self.currentObj[LAT]
            if self.currentObj[LAT] > self.bbox[3] or self.bbox[3] == 0:
                self.bbox[3] = self.currentObj[LAT]
            if self.currentObj[LON] < self.bbox[0] or self.bbox[0] == 0:
                self.bbox[0] = self.currentObj[LON]
            if self.currentObj[LON] > self.bbox[2] or self.bbox[2] == 0:
                self.bbox[2] = self.currentObj[LON]

            self.currentObj[TAG] = {}

        elif tag == "way":
            self.currentObj = {}
            self.currentId = int(attributes.get("id"))
            self.currentObj[VERSION] = int(attributes.get("version", 0))
            self.currentObj[CHANGESET] = int(attributes.get("changeset", 0))
            self.currentObj[UID] = int(attributes.get("uid", 0))
            self.currentObj[USER] = attributes.get("user", "")
            self.currentObj[TAG] = {}
            self.currentObj[REF] = []

        elif tag == "relation":
            self.currentObj = {}
            self.currentId = int(attributes.get("id"))
            self.currentObj[VERSION] = int(attributes.get("version", 0))
            self.currentObj[CHANGESET] = int(attributes.get("changeset", 0))
            self.currentObj[UID] = int(attributes.get("uid", 0))
            self.currentObj[USER] = attributes.get("user", "")
            self.currentObj[TAG] = {}
            self.currentObj[REF] = [[], [], []]  # [Nodes, Ways, Relations]

        elif tag == "tag":
            self.currentObj[TAG][attributes.get("k")] = attributes.get("v")

        elif tag == "nd":
            self.currentObj[REF].append(int(attributes.get("ref")))

        elif tag == "member":
            mtype = attributes.get("type")
            ref = int(attributes.get("ref"))
            role = attributes.get("role")
            if mtype == "node":
                self.currentObj[REF][NODES].append((ref, role))
            elif mtype == "way":
                self.currentObj[REF][WAYS].append((ref, role))
            elif mtype == "relation":
                self.currentObj[REF][RELATIONS].append((ref, role))

    def endElement(self, tag):
        if self.currentId is not None:
            if tag == "node":
                self.nodes[self.currentId] = self.currentObj
            elif tag == "way":
                self.ways[self.currentId] = self.currentObj
            elif tag == "relation":
                self.relations[self.currentId] = self.currentObj
        self.currentObj = None
        self.currentId = None


class Map():
    def __init__(self):
        self.number = 0
        self.omap = {}

    def __getitem__(self, oldkey):
        newkey = self.omap.get(oldkey)
        if newkey is None:
            self.number -= 1
            newkey = self.number
            self.omap[oldkey] = newkey
        return newkey
