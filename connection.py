from parse_rest.connection import register
from parse_rest.datatypes import Object

PARSE_APP_ID = '0mkFhot3vjLg97Dg3iCr7O5iABrvcP0xID6d4EqR'
PARSE_REST_API_KEY = '3w3ykTpvt6EeGTLlkdJdUA0Oqezgm02Y7wblKnjM'

register(PARSE_APP_ID, PARSE_REST_API_KEY)

class Listing(Object):
	def update_parameters(self, details):
		for k,v in details.iteritems():
			print "key: ", k, ", val: ", v
			setattr(self, k, v)

	def get_parameters(self):
		# fields_to_return = ['objectId', 'price', 'about', 'cond', 'delivery', 'incl', 'questions', 'title', 'photos']
		d = {}
		try:
			d['about'] = self.about
			d['cond'] = self.cond
			d['delivery'] = self.delivery
			d['incl'] = self.incl
			d['question'] = self.question
			d['title'] = self.title
			d['photos'] = self.photos
			d['price'] = self.price
		except:
			pass
		return d

class User(Object):
	pass