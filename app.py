from flask import Flask, render_template, request, json, session, redirect, url_for
import re, base64, os, binascii
import connection
from connection import Listing, User
from parse_rest.query import QueryResourceDoesNotExist
import tweepy, boto
from boto.s3.key import Key
app = Flask(__name__)

DOMAIN = os.environ['DOMAIN']
TWITTER_KEYS = {}
TWITTER_KEYS['key'] = os.environ['TWITTER_CONSUMER_KEY']
TWITTER_KEYS['secret'] = os.environ['TWITTER_CONSUMER_SECRET']
AWS = {}
AWS['id'] = os.environ['AWS_ID']
AWS['secret'] = os.environ['AWS_SECRET']
AWS['bucket'] = os.environ['AWS_BUCKET']

app.secret_key = '%\xb3\xc0\x0cf\x19\xb0y\x16K\x8b\xdd\xb7j`\xce\xbc|\xae\xa9&\x92Q\xa4'
auth = tweepy.OAuthHandler(TWITTER_KEYS['key'], TWITTER_KEYS['secret'])


@app.route('/')
def index():
	if active_session():
		username = session['username']
		listings = Listing.Query.filter(poster=username)
		my_listings = []
		for listing in listings:
			d = {}
			d['link'] = DOMAIN + '/' + listing.objectId + '/edit'
			try:
				d['title'] = listing.title
			except:
				d['title'] = 'unfinished listing'
			my_listings.append(d)
		return render_template('homepage_loggedin.html', username=username, pic=session['pic'], my_listings=my_listings)
	return render_template('homepage.html')


@app.route('/twitter_sign_in')
def twitter_sign_in():
	next = request.args.get('next')
	if active_session():
		if next == '/new':
			return redirect(url_for('new_listing'))
		else:
			return redirect(url_for('index'))
	else:
		redirect_url = auth.get_authorization_url(signin_with_twitter=True)
		session['request_token_key'] = auth.request_token.key
		session['request_token_secret'] = auth.request_token.secret
		print "request token key: ", session['request_token_key'], ' request token sec: ', session['request_token_secret']
		return redirect(redirect_url)


@app.route('/login_callback')
def twitter_callback():
	oauth_token = request.args.get('oauth_token')
	oauth_verifier = request.args.get('oauth_verifier')
	#print "oauth token: ", oauth_token, " oauth verifier: ", oauth_verifier
	#TODO: check oauth verifier and token for match
	auth = tweepy.OAuthHandler(TWITTER_KEYS['key'], TWITTER_KEYS['secret'])
	auth.set_request_token(session['request_token_key'], session['request_token_secret'])
	access_token = auth.get_access_token(verifier=oauth_verifier)
	session['access_token_key'] = access_token.key
	session['access_token_secret'] = access_token.secret
	username = auth.get_username()
	api = tweepy.API(auth)
	me = api.me()
	profile_pic = me.profile_image_url
	fullname = me.name
	twitter_id = me.id
	user = None
	try:
		user = User.Query.get(username=username)
	except QueryResourceDoesNotExist:
		user = User(username=username, at_key=access_token.key, 
			at_secret=access_token.secret, pic=profile_pic, 
			fullname=fullname, twitter_id=twitter_id)

	user.save()
	session['username'] = username
	session['pic'] = profile_pic

	#print "access token: ", access_token
	return redirect(url_for('index'))


@app.route('/new')
def new_listing():
	if active_session():
		listing = Listing()
		listing.poster = session['username']
		listing.save()
		objectId = listing.objectId
		redirect_url = '/' + objectId + '/edit'
		return redirect(redirect_url)
	else:
		return redirect('/twitter_sign_in')


@app.route('/<listing_id>/edit')
def edit(listing_id):
	if active_session():
		listing = None
		try:
			listing = Listing.Query.get(objectId=listing_id)
		except QueryResourceDoesNotExist:
			return "error", 400
		if listing.poster != session['username']:
			return "Sorry, you're not allowed to do that", 405
		else:
			listing_details = listing.get_parameters()
			new_post = 'ff'
			if 'photos' in listing_details:
				listing_details['photos'] = convert(json.loads(listing_details['photos']))
			else:
				new_post = True
			return render_template('edit_listing.html', username=session['username'], 
				details = listing_details, listing_id=listing.objectId, pic=session['pic'], new_post=new_post)
	# TODO: redirect to sign up form
	return redirect(url_for('index'))


@app.route('/gl/<listing_id>')
def view_listing(listing_id):
	listing = None
	try:
		listing = Listing.Query.get(objectId=listing_id)
	except QueryResourceDoesNotExist:
		return "no listing found"

	details = {}
	details['title'] = listing.title	
	details['price'] = listing.price
	details['incl'] = listing.incl
	details['cond'] = listing.cond
	details['about'] = listing.about
	details['delivery'] = listing.delivery
	details['questions'] = listing.question
	details['photos'] = json.loads(listing.photos)
	details['poster'] = listing.poster
	if active_session():
		return render_template('view_listing.html', details=details, 
		username=session['username'], pic=session['pic'])
	else:
		return render_template('view_listing.html', details=details)


@app.route('/logout')
def logout():
	session.pop('username', None)
	return redirect(url_for('index'))


@app.route('/api/post', methods=['POST'])
def post():
	if request.method == 'POST':
		form_dict = request.form
		photos = form_dict['photos']
		
		fields = {}
		for k, v in form_dict.iteritems():
			fields[k] = v

		fields['poster'] = session['username']
		listing = None
		try:
			listing = Listing.Query.get(objectId=fields['obj_id'])
		except QueryResourceDoesNotExist:
			listing = Listing()
		
		print "fields: ", fields
		listing.update_parameters(fields)
		
		listing.save()
		url = DOMAIN + '/gl/' + listing.objectId
		return json.dumps({'success': True, 'listing_url': url}), 200
	return "Sorry, that's not allowed", 405


@app.route('/api/upload_pic', methods=['POST'])
def upload_pic_to_s3():
	if request.method == 'POST':
		if active_session() and session['username'] == request.form['username']:
			file_data_url = request.form['file']
			order = request.form['order']
			listing_id = request.form['listing']

			NUM_SUFFIX_CHARS = 5
			random_hash = binascii.b2a_hex(os.urandom(NUM_SUFFIX_CHARS))
			filename = session['username'] + "-" + listing_id + "-" + random_hash + "-" + order + ".png"
			m = re.search('base64,(.*)', file_data_url)
			decoded_img = m.group(1)
			
			f = open(filename, "wb")
			f.write(decoded_img.decode('base64'))
			f.close()

			conn = boto.connect_s3(AWS['id'], AWS['secret'])
			bucket = conn.get_bucket(AWS['bucket'])
			key = filename
			k = Key(bucket)
			k.key = key
			k.set_contents_from_filename(key)
			k.set_acl('public-read')

			os.remove(filename)

			print "Uploaded to S3"
			img_url = 'https://' + AWS['bucket'] + '.s3.amazonaws.com/' + filename

			"""
			listing = Listing.Query.get(objectId=listing_id)
			current_photos = json.loads(listing.photos)
			current_photos.append(img_url)
			listing.photos = json.dumps(current_photos)
			listing.save()
			"""
			return json.dumps({'success': True, 'img_url': img_url}), 200
		print request.form['username'], session['username']
	return json.dumps({'success': False}), 400


def active_session():
	if 'username' in session:
		return True
	else:
		return False

def convert(input):
    if isinstance(input, dict):
        return {convert(key): convert(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [convert(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input


if __name__ == '__main__':
	app.run()