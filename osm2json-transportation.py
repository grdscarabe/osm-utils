#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to convert an OSM file containing relations and nodes related to public
transportation into a JSON file listing the stops and their related lines.
"""

import sys
from lxml import etree
import bz2
import json

def relationElement2Obj(elem):
	"""
	Convert a lxml element in parameter corresponding to a relation into an 
	equivalent data structure.
	"""
	obj = {"stops": []}
	if elem.tag != "relation": return obj
	for child in elem.getchildren():
		if (child.tag == "member") and \
			(child.get("type") == "node") and (child.get("role") == "stop"):
			obj["stops"].append(child.get("ref"))
		elif child.tag == "tag":
			obj[child.get("k")] = child.get("v")
		else:
			sys.stderr.write("REL-%s: ignored children %s\n" % (elem.get("id"), child))
	return obj

def nodeElement2Obj(elem):
	"""
	Convert a lxml element in parameter corresponding to a node into an 
	equivalent data structure.
	"""
	obj = {}
	if elem.tag != "node": return obj
	for child in elem.getchildren():
		obj[child.get("k")] = child.get("v")
	return obj

def osm2transport(fhin):
	"""
	Transform an XML tree of OSM data regarding public transportation into
	a data structure made for easy listing of stops.
	"""
	stops_index = {} # stops indexed by node id
	lines_index = {} # lines (routes) indexed by relation id
	stops2lines = {}
	root = etree.parse(fhin)
	# Extract all routes
	context = etree.iterwalk(root, events=["end"], tag="relation")
	for actions,elem in context:
		lines_index[elem.get("id")] = relationElement2Obj(elem)
		# Add to index
		for stop in lines_index[elem.get("id")]["stops"]:
			if not stops2lines.has_key(stop):
				stops2lines[stop] = []
			stops2lines[stop].append(elem.get("id"))
	# Now extract all stops
	context = etree.iterwalk(root, events=["end"], tag="node")
	for actions,elem in context:
		stops_index[elem.get("id")] = nodeElement2Obj(elem)
	# Finally build the whole data structure
	data = []
	for stopid,stopdata in stops_index.items():
		mstop = {"node_id": int(stopid), "lines": []}
		for k,v in stopdata.items():
			mstop[k] = v
		if stops2lines.has_key(stopid):
			for lineid in stops2lines[stopid]:
				line = {"relation_id": int(lineid)}
				for k,v in lines_index[lineid].items():
					if not k in ["type", "stops"]:
						line[k] = v
				mstop["lines"].append(line)
		data.append(mstop)
	return data

if __name__ == "__main__":
	# Check script configuration
	if len(sys.argv) != 3:
		sys.stderr.write("Usage:\n")
		sys.stderr.write("\t%s <input osm> <output json>\n" % sys.argv[0])
		sys.exit(-1)
	# Open streams
	if sys.argv[1].endswith(".osm.bz2"):
		fhin = bz2.BZ2File(sys.argv[1], 'rb')
	elif sys.argv[1].endswith(".osm"):
		fhin = open(sys.argv[1], 'rb')
	else:
		sys.stderr("Invalid input file: %s\n" % sys.argv[1])
		sys.exit(-1)
	if sys.argv[2].endswith(".json"):
		fhout = open(sys.argv[2], 'wb')
	else:
		sys.stderr("Invalid output file: %s\n" % sys.argv[2])
		sys.exit(-1)
	# Process OSM input
	stops = osm2transport(fhin)
	fhin.close()
	# Export in JSON
	json.dump(stops, fhout)
	fhout.close()

