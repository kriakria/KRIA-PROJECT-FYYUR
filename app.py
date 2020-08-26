#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import func, and_
from datetime import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='venue', lazy=True)

    def get_venue(self, city, state):
      return self.query.filter(self.city == city, self.state == state).all()

    def __repr__ (self):
      return f'<Venue id {self.id}, Venue name {self.name}, Venue city {self.city}, Venue state {self.state}, Venue genres {self.genres}, Venue shows {self.shows}>'


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__ (self):
      return f'<Artist id {self.id}, Artist name {self.name}, Artist city {self.city}, Artist state {self.state}, Artist shows {self.shows}, Artist genres {self.genres}>'


class Show(db.Model):
  __tablename__ = 'shows'

  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)

  def __repr__ (self):
    return f'<ShowID {self.id}, artist_id {self.artist_id}, venue_id {self.venue_id} start_time {self.start_time}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  
  venues = Venue.query.all()      

  city_and_state = []
  data = []
  
  for venue in venues:       
      if venue.city + venue.state in city_and_state:
        index = city_and_state.index(venue.city + venue.state)        
        data[index]["venues"].append({
          'id': venue.id,
          'name': venue.name,
          'num_upcoming_shows': Show.query.filter_by(venue_id = venue.id).count()
        })
      else:                
        city_and_state.append(venue.city + venue.state)        
        data.append({
          'city': venue.city,
          'state': venue.state,
          'venues': [{            
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': Show.query.filter_by(venue_id = venue.id).count()
          }]
        })          
    
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  search_term = request.form.get('search_term', '')
  
  # filtering venues by the search term and counting the filtered venues
  results = Venue.query.filter(func.lower(Venue.name).contains(search_term.lower(), autoescape=True)).all()
  count = len(results)
  
  venues_list = []
  
  for result in results:
    venues_list.append({
      'id': result.id,
      'name': result.name,
      'num_upcoming_show': Show.query.filter_by(venue_id = result.id).count()
    })

  return render_template('pages/search_venues.html', results=venues_list, search_term=search_term, count=count)
   
  

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):  
  
  venue = Venue.query.filter_by(id = venue_id).first()

  today = datetime.today()
  past_shows = []  
  upcoming_shows = []

  shows = Show.query.filter_by(venue_id = venue.id).join(Artist, Show.artist_id == Artist.id).add_columns(Artist.id, Artist.name.label('artist_name'), Artist.image_link, Show.start_time).all()
  for show in shows:    
    date = show.start_time
    date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')        
    if date_obj < today:      
      past_shows.append({
        'artist_id': show[1],
        'artist_name': show[2],
        'artist_image_link': show[3],
        'start_time': show[4]
      })
    else:                         
      upcoming_shows.append({
        'artist_id': show[1],
        'artist_name': show[2],
        'artist_image_link': show[3],
        'start_time': show[4]
      })

  data = {
  'id': venue_id,
  'name': venue.name,
  'genres': venue.genres,
  'address': venue.address,
  'city': venue.city,
  'state': venue.state,
  'phone': venue.phone,
  'website_link': venue.website_link,
  'facebook_link': venue.facebook_link,
  'seeking_talent': venue.seeking_talent,
  'seeking_description': venue.seeking_description,
  'image_link': venue.image_link,
  'past_shows': past_shows,
  'upcoming_shows': upcoming_shows,
  'past_shows_count': len(past_shows),
  'upcoming_shows_count': len(upcoming_shows)
  }
  return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():  

  error = False
  try:
    name=request.form.get('name')
    city=request.form.get('city')
    state=request.form.get('state')
    address=request.form.get('address')
    phone=request.form.get('phone')
    image_link=request.form.get('image_link')
    genres=request.form.getlist('genres')
    facebook_link=request.form.get('facebook_link')
    website_link=request.form.get('website_link')

    venue=Venue(name=name, city=city, state=state, address=address, phone=phone,
    image_link=image_link, genres=genres, facebook_link=facebook_link, website_link=website_link)
    db.session.add(venue)
    db.session.commit()

  # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  
  except:
    error = True
    db.session.rollback()

  # on unsuccessful db insert, flash an error  
    flash('Venue ' + request.form['name'] + ' could not be listed')  
    
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  
  error = False
  
  venue = Venue.query.get(venue_id)
  
  try:
    flash("the venue has been deleted")
    Venue.query.filter_by(id=venue_id).delete()    
    db.session.commit()
    flash('The venue ' + venue.name + ' has been successfully deleted!')
  
  except:
    error = True
    db.session.rollback()
    flash('The venue ' + venue.name + ' could not be deleted')  
  finally:    
    db.session.close()  
  
  if error:
    abort(500)

  else:    
    return render_template('pages/venues.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():  
  
  artists = Artist.query.all()

  data = []

  for artist in artists:
    data.append({
      'id': artist.id,
    'name': artist.name
    })
    
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():  
  
  search_term = request.form.get('search_term', '')  

  search_result = Artist.query.filter(func.lower(Artist.name).contains(search_term.lower(), autoescape=True)).all()
  count = len(search_result)
  artist_list = []

  for result in search_result:
    artist_list.append({
      'id': result.id,
      'name': result.name,
      'num_upcoming_shows': Show.query.filter_by(artist_id = result.id).count()
    })
  
  return render_template('pages/search_artists.html', results=artist_list, count=count, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):  
  
  artist = Artist.query.filter_by(id = artist_id).first()    
  today = datetime.today()
  past_shows = []  
  upcoming_shows =[]

  shows_of_the_artist = Show.query.filter_by(artist_id = artist_id).join(Venue, Show.venue_id == Venue.id).add_columns(Venue.id, Venue.name, Venue.image_link, Show.start_time).all()          
  for show in shows_of_the_artist:
    date = show.start_time
    date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')        
    if date_obj < today:                               
      past_shows.append({
        'venue_id': show[1],
        'venue_name': show[2],
        'venue_image_link': show[3],
        'start_time': show[4]
      })
    else:                    
      upcoming_shows.append({
        'venue_id': show[1],
        'venue_name': show[2],
        'venue_image_link': show[3],
        'start_time': show[4]
      })
  data = {
    'id': artist.id,
    'name': artist.name,
    'genres': artist.genres,
    'city': artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    'seeking_description': artist.seeking_description,
    'image_link': artist.image_link,
    'past_shows': past_shows,                
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),        
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  
  artist = Artist.query.filter_by(id = artist_id).first()
  
  data={
    "id": artist_id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }

  return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  
  error = False
  
  artist = Artist.query.filter_by(id = artist_id).first()

  try:
    artist.name=request.form.get('name')
    artist.city=request.form.get('city')
    artist.state=request.form.get('state')
    artist.phone=request.form.get('phone')
    artist.genres=request.form.get('genres')
    artist.facebook_link=request.form.get('facebook_link')
    artist.website_link=request.form.get('website_link')
    artist.image_link=request.form.get('image_link')
    artist.seeking_venue=request.form.get('seeking_venue')
    artist.seeking_description=request.form.get('seeking_description')
    
    db.session.commit()

  # on successful db insert, flask success
    flash('Artist ' + request.form['name'] + ' was successfully updated!')

  except:
    error = True
    db.session.rollback()
    flash('Artist ' + request.form['name'] + ' could not be updated')

  finally:
    db.session.close()

  if error:
    abort(500)

  else:
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  venue = Venue.query.filter_by(id = venue_id).first()

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website_link": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }
  
  return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  
  error = False

  venue = Venue.query.filter_by(id = venue_id).first()

  try:
    venue.name=request.form.get('name')
    venue.address=request.form.get('address')
    venue.city=request.form.get('city')
    venue.state=request.form.get('state')
    venue.phone=request.form.get('phone')
    venue.genres=request.form.get('genres')
    venue.facebook_link=request.form.get('facebook_link')
    venue.image_link=request.form.get('image_link')
    venue.seeking_talent=request.form.get('seeking_talent')
    venue.seeking_description=request.form.get('seeking_description')    

    db.session.commit()

    flash('Venue ' + request.form['name'] + ' was successfully updated!')

  except:
    error = True
    db.session.rollback()
    flash('Venue ' + request.form['name'] + ' could not be updated')

  finally:
    db.session.close()

  if error:
    abort(500)

  else:
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  
  error = False
  try:
    name=request.form.get('name')
    city=request.form.get('city')
    state=request.form.get('state')
    phone=request.form.get('phone')
    genres=request.form.get('genres')
    website_link=request.form.get('website_link')
    facebook_link=request.form.get('facebook_link')
    image_link=request.form.get('image_link')

    artist=Artist(name=name, city=city, state=state, phone=phone,
    genres=genres, website_link=website_link, facebook_link=facebook_link, image_link=image_link)
    db.session.add(artist)
    db.session.commit()

  # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  
  except:
    error = True
    db.session.rollback()
    flash('Artist ' + request.form['name'] + ' could not be listed')  
    
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    return render_template('pages/home.html')  

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():  
  
  shows = db.session.query(Venue, Artist, Show).join(Show, Venue.id == Show.venue_id).join(Artist, Show.artist_id == Artist.id).all()
  showdata = []
  print(shows)
  for show in shows:
    print('Artist: {} Venue: {}'.format(show[0].name, show[1].id))
    showdata.append({"venue_id": show[0].id, "venue_name": show[0].name, "artist_id": show[1].id, "artist_name": show[1].name, "artist_image_link": show[1].image_link, "start_time": show[2].start_time})
  print(showdata)
  return render_template('pages/shows.html', shows=showdata)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  error = False
  try:
    artist_id=request.form.get('artist_id')
    venue_id=request.form.get('venue_id')
    start_time=request.form.get('start_time')

    show=Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()

    flash('Show was successfully listed!')
  
  except:
    error = True
    db.session.rollback()
    flash('Show could not be listed')  
  
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    return render_template('pages/home.html')
  
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
