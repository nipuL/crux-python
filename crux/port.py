import re

class MetaData(object):
	'''The MetaData class processes meta data in a Pkgfile.

It uses 2 attributes, and any subsequent methods (read further) for subclassing:

	META_RE:
		This defines the regulare expression for finding meta data.
		
	META_FUNCTIONS:
		This registers class methods that can be used to further process the data.
		
		Processing functions take the form;
		
			__process_meta_FUNCTION(self, data)
			
		If no function is defined for the meta name it is simply passed into the dict without any further processing.
'''
	META_RE  = '^# *(?P<meta>.*?): *(?P<data>.*?)\n'
	META_FUNCTIONS = (
		'description',
		'url',
		'depends_on',
		'nice_to_have',
	)
	
	def _parse_meta_data(self, data):
		# This looks complicated, but it's really quite simple
		# It finds all the metadata, then filters out any
		# items without any data.
		self.meta_data = dict(filter(lambda x: x[1] or False,map(
					self.__process_meta,
					re.findall(self.META_RE, data, re.M)
		)))
		
	def __process_meta(self, item):
		meta, data = item
		meta = meta.lower()
		meta_fcn = meta.replace(' ','_').lower()
		
		if meta_fcn not in self.META_FUNCTIONS:
			return (meta, data)
			
		try:
			data = getattr(self,"_MetaData__process_meta_%s" % meta_fcn)(data)
		except AttributeError:
			pass
			
		try:
			data = data.decode('iso-8859-1')
		except:
			pass
		return (meta,data)
		
	def __process_meta_depends_on(self, data):
		return [dep.strip() for dep in data.replace(',',' ').split()]

	def __process_meta_nice_to_have(self, data):
		return self.__process_meta_depends_on(data)
		
class Variables(object):
	'''The Variables class is used for processing a Pkgfiles variables.

To subclass it simply override the VAR_RE attribute.

VAR_RE is a dict that uses the variable name as the key and it's associated regular expression as the value.

Variables will be processed further if a method exists in the form:

		__process_variable_VARIABLE(self, data)
		
'''
	VAR_RE = {
		'name': 'name=(.*?)\n',
		'version': 'version=(.*?)\n',
		'release': 'release=(.*?)\n',
		'source': 'source=\((.*?)\)\n',
	}
	
	def _parse_variables(self, data):
		self.variables = dict(filter(lambda x: x[1] or False, 
				[
					(var, self.__process_variable(var, re_str, data))
					for var,re_str in self.VAR_RE.items()
				]
			)
		)
		
	def __process_variable(self, var, re_str, data):
		m = re.search(re_str, data, re.S)
		if not m:
			return None
		try:
			return getattr(
				self, '_Variables__process_variable_%s' % var
			)(m.group(1))
		except AttributeError:
			return m.group(1)
		
	def __process_variable_source(self, source):
		return [
			e.strip()
			for e in source.replace('\\',' ').replace('\t',' ').replace('\n',' ').split()
		]
		
class Functions(object):
	'''The Functions class is used to extract any top level functions from the Pkgfile.

To subclass it, override the FUNCTION_RE attribute which defines the regular expression for functions.

Pkgfiles will generally only have a build function.
'''
	FUNCTION_RE = '(?P<function>\w+) *\(\)[ \n]*{\n(?P<code>.*)\n}'
	
	def _parse_functions(self, data):
		self.functions = dict(re.findall(self.FUNCTION_RE, data, re.S))
		
	def function_lines(self, function):
		return [
			line.replace('\t','').strip()
			for line in self.functions[function].split('\n')
		]
			
class Pkgfile(object):
	def parse_file(self, file):
		data = open(file,'r').read()
		try:
			data.decode('iso-8859-1')
		except:
			pass
		self.parse_string(data)
		
	def parse_string(self, data):
		self._parse_meta_data(data)
		self._parse_variables(data)
		self._parse_functions(data)
	
class PkgfileParser(Pkgfile, MetaData, Variables, Functions):
	pass

# EOF
