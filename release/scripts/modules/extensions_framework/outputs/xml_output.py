# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 Extensions Framework
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# ***** END GPL LICENCE BLOCK *****
#
import xml.etree.cElementTree as ET
import xml.dom.minidom as MD

class xml_output(object):
	"""This class serves to describe an XML output, it uses
	cElementTree and minidom to construct and format the XML
	data.
	
	"""
	
	"""The format dict describes the XML structure that this class
	should generate, and which properties should be used to fill
	the XML data structure
	
	"""
	format = {}
	
	def __str__(self):
		return ET.tostring(self.root)
	
	def write_pretty(self, file):
		"""Write a formatted XML string to file"""
		xml_dom = MD.parseString(ET.tostring(self.root, encoding='utf-8'))
		xml_dom.writexml(file, addindent=' ', newl='\n', encoding='utf-8')
	
	def pretty(self):
		"""Return a formatted XML string"""
		xml_str = MD.parseString(ET.tostring(self.root))
		return xml_str.toprettyxml()
	
	def get_format(self):
		"""This should be overridden in classes that produce XML
		conditionally
		
		"""
		return self.format
	
	def compute(self, context):
		"""Compute the XML output from the input format"""
		self.context = context
		
		self.root = ET.Element(self.root_element)
		self.parse_dict(self.get_format(), self.root)
		
		return self.root
	
	"""Formatting functions for various data types"""
	format_types = {
		'bool': lambda c,x: str(x).lower(),
		'collection': lambda c,x: x,
		'enum': lambda c,x: x,
		'float': lambda c,x: x,
		'int': lambda c,x: x,
		'pointer': lambda c,x: x,
		'string': lambda c,x: x,
	}
	
	def parse_dict(self, d, elem):
		"""Parse the values in the format dict and collect the
		formatted data into XML structure starting at self.root
		
		"""
		for key in d.keys():
			# tuple provides multiple child elements
			if type(d[key]) is tuple:
				for cd in d[key]:
					self.parse_dict({key:cd}, elem)
				continue # don't create empty element for tuple child
			
			x = ET.SubElement(elem, key)
			
			# dictionary provides nested elements
			if type(d[key]) is dict:
				self.parse_dict(d[key], x)
				
			# list provides direct value insertion
			elif type(d[key]) is list:
				x.text = ' '.join([str(i) for i in d[key]])
			
			# else look up property
			else:
				for p in self.properties:
					if d[key] == p['attr']:
						if 'compute' in p.keys():
							x.text = str(p['compute'](self.context, self))
						else:
							x.text = str(
								self.format_types[p['type']](self.context,
									getattr(self, d[key]))
							)
