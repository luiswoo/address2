#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       address.py {Center}
#       
#       Copyright 2012 Hind <foxhind@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import sys
import math
import projections
import urllib, urllib2, cookielib, Cookie
import json
from OsmData import OsmData, LON, LAT, TAG

if sys.version_info[0] < 3:
  reload(sys)
  sys.setdefaultencoding("utf-8")          # a hack to support UTF-8 

class client:
	def __init__(self, proxy=None, user_agent='Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.2.3) Gecko/20100423 Ubuntu/10.04 (lucid) Firefox/3.6.3'):
		self.redirect_handler = urllib2.HTTPRedirectHandler()
		self.http_handler	 = urllib2.HTTPHandler()
		self.opener = urllib2.build_opener(self.http_handler, self.redirect_handler)
		if proxy:
			self.proxy_handler = urllib2.ProxyHandler(proxy)
			self.opener.add_handler(self.proxy_handler)
		self.opener.addheaders = [('User-agent', user_agent)]
		urllib2.install_opener(self.opener)
	def request(self, url, params={}, timeout=5):
		if params:
			params = urllib.urlencode(params)
			html = urllib2.urlopen(url, params, timeout)
		else:
			html = urllib2.urlopen(url)
		return html.read()

def main():
	if len(sys.argv) != 2:
		return 0
	
	coords = (sys.argv[1].split(','))
	# lon = float(coords[0])
	# lat = float(coords[1])
	# coords_m = projections.from4326((lon,lat), "EPSG:3857")
	
	tData = OsmData()
	httpc = client()
	
	# text = httpc.request('http://pkk5.rosreestr.ru/arcgis/rest/services/Cadastre/CadastreSelected/MapServer/1/query?text=&geometry='+str(coords_m[0])+','+str(coords_m[1])+'&geometryType=esriGeometryPoint&inSR=&spatialRel=esriSpatialRelIntersects&relationParam=&objectIds=&where=&time=&returnCountOnly=false&returnIdsOnly=false&returnGeometry=false&maxAllowableOffset=&outSR=&outFields=*&f=pjson')
	
	text = httpc.request('http://pkk5.rosreestr.ru/api/features/1?text='+coords[1]+'%20'+coords[0]+'&tolerance=4&limit=11')
	
	data = json.loads(text)
	if 'features' in data:
		ids = []
		for result in data['features']:
			#if len(result['value']) >= 11:
				try:
					ids.append(result['attrs']['id']);
				except KeyError:
					continue

		if len(ids) > 0:
			addresses = []
			for id in ids:
				#text = httpc.request('http://maps.rosreestr.ru/arcgis/rest/services/Cadastre/CadastreInfo/MapServer/2/query?f=json&where=PARCELID%20IN%20(%27'+id+'%27)&returnGeometry=false&spatialRel=esriSpatialRelIntersects&outFields=FULLADDRESS,CATEGORY,UTIL_BY_DOC');
				
				text = httpc.request('http://pkk5.rosreestr.ru/api/features/1/'+id);
				
				data = json.loads(text)
				
				if 'feature' in data:
					address = {}
					try:
						s = data['feature']['attrs']['address'].split(',')
						address['addr:housenumber'] = s.pop().strip()
						address['addr:street'] = s.pop().strip()
						address['addr:full'] = data['feature']['attrs']['address']
						address['fixme'] = 'yes'
					except KeyError:
						continue
					try:
					#	address['category'] = feature['attributes']['CATEGORY']
						address['utilization'] = data['feature']['attrs']['util_by_doc']
					except KeyError:
						pass
					addresses.append(address)
				else:
					tData.addcomment('Feature is empty')
					continue
			count = len(addresses)
			if count == 1:
				nodeid = tData.addnode()
				tData.nodes[nodeid][LON] = coords[0]
				tData.nodes[nodeid][LAT] = coords[1]
				tData.nodes[nodeid][TAG] = addresses[0]
				comment = addresses[0]['addr:street'] + ', ' + addresses[0]['addr:housenumber']
				if addresses[0]['utilization'] <> None:
					comment += ' - ' + addresses[0]['utilization']
				tData.addcomment(comment)
			else:
				for i in range(count):
					angle = 2*math.pi*i/count
					x = float(coords[0]) + 0.00001 * math.cos(angle)
					y = float(coords[1]) + 0.00001 * math.sin(angle)
					#node = projections.to4326((x, y), "EPSG:3857")
					nodeid = tData.addnode()
					tData.nodes[nodeid][LON] = x
					tData.nodes[nodeid][LAT] = y
					tData.nodes[nodeid][TAG] = addresses[i]
					comment = addresses[i]['addr:street'] + ', ' + addresses[i]['addr:housenumber']
					if addresses[i]['utilization'] <> None:
						comment += ' - ' + addresses[i]['utilization']
					tData.addcomment(comment)
		else:
			tData.addcomment('Unknown error')
	else:
		tData.addcomment('Features is empty')
	tData.write(sys.stdout)
	return 0

if __name__ == '__main__':
	main()