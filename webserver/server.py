from ast import Global
from flask import Flask, flash, request, render_template, g, redirect, Response, jsonify, session, abort
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
import json, random, os
app = Flask(__name__)

# Connect to Postgresql DB
DB_USER = "zz2830"
DB_PASSWORD = "5032"
DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"
engine = create_engine(DATABASEURI)

USER_ID = -1

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request
  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


@app.route("/all_equipments.html")
def display_equipments():
	if not session.get('logged_in'):
		return render_template('login.html')
	else:
		print(request.args)
		cursor = g.conn.execute("select * from equipments")
		all_equip = list(cursor)
		cursor.close()
		print(all_equip)
		return render_template('all_equipments.html', data = all_equip)

@app.route('/all_recipes.html')
def display_recipes():
	if not session.get('logged_in'):
		return render_template('login.html')
	else:
		cursor = g.conn.execute("select * from recipes")
		all_recipes = list(cursor)
		cursor.close()
		print(all_recipes)
		return render_template('all_recipes.html',  data = all_recipes)

@app.route('/add_recipe.html')
def add():
	if not session.get('logged_in'):
		return render_template('login.html')
	else:
		cursor = g.conn.execute("select bid, name from bean_roasts")
		beans = list(cursor)
		cursor.close()
		cursor = g.conn.execute("select eid, name from equipments where grinder = 1")
		grinders = list(cursor)
		cursor.close()
		cursor = g.conn.execute("select eid, name from equipments where brewer = 1")
		brewers = list(cursor)
		cursor.close()	
		return render_template('add_recipe.html', beans = beans, grinders = grinders, brewers = brewers)

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
	p_name= str(request.form['name'])
	p_brew_time= str(request.form['brew_time'])
	p_yield = str(request.form['yield'])
	p_description = str(request.form['description'])
	p_guide= str(request.form['guide'])
	p_filter_coffee= str(request.form['filter_coffee'])
	p_espresso = str(request.form['espresso'])
	p_image = str(request.form['image'])
	p_bean = str(request.form['bean'])
	p_bean_amount = str(request.form['bean_amount'])
	p_grinder = str(request.form['grinder'])
	p_grinder_setting = str(request.form['grinder_setting'])
	p_brewer = str(request.form['brewer'])
	p_brewer_setting = str(request.form['brewer_setting'])
	

	cursor = g.conn.execute("select id from recipes order by id desc limit 1")
	cur_id = list(cursor)[0][0]
	cursor.close()
	id = cur_id + 1

	print(id, p_name, p_brew_time, p_yield, p_description, p_guide, p_filter_coffee, p_espresso, p_image)

	cursor = g.conn.execute("insert into recipes(id, name, brew_time, yield, description, guide, filter_coffee, espresso_coffee, photo_url) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (id, p_name, p_brew_time, p_yield, p_description, p_guide, p_filter_coffee, p_espresso, p_image))
	cursor.close()
	cursor = g.conn.execute("insert into requires_bean(bid, id, amount) values (%s,%s,%s)", p_bean, id, p_bean_amount)
	cursor.close()
	cursor = g.conn.execute("insert into requires_equipment(eid, id, setting) values (%s,%s,%s)", p_grinder, id, p_grinder_setting)
	cursor.close()
	cursor = g.conn.execute("insert into requires_equipment(eid, id, setting) values (%s,%s,%s)", p_brewer, id, p_brewer_setting)
	cursor.close()
	cursor = g.conn.execute("insert into make(uid, id, time) values(%s, %s, now())", USER_ID, id)
	cursor.close()
	return display_recipe(id)

  
@app.route('/display_recipe/<id>.html')
def display_recipe(id):
	global USER_ID
	cursor = g.conn.execute("select * from recipes where id = %s", id)
	recipe = list(cursor)
	cursor.close()
	cursor = g.conn.execute("select bean_roasts.bid as bean_bid, bean_roasts.name as bean_name, tmp.amount as amount from bean_roasts, (select requires_bean.bid as bid, requires_bean.amount as amount from requires_bean, recipes where recipes.id = %s and recipes.id = requires_bean.id) tmp where bean_roasts.bid = tmp.bid", id)
	bean = list(cursor)
	cursor.close()
	cursor = g.conn.execute("select equipments.eid as equipment_eid, equipments.name as equipment_name, tmp.setting as setting from equipments, (select requires_equipment.eid as eid, requires_equipment.setting as setting from requires_equipment, recipes where recipes.id = %s and recipes.id = requires_equipment.id) tmp where equipments.eid = tmp.eid", id)
	equipments = list(cursor)
	cursor.close()
	cursor = g.conn.execute("select users.name as creator, make.uid as creator_uid, time from users, make, recipes where make.id = recipes.id and recipes.id = %s and make.uid = users.uid", id)
	creator = list(cursor)
	cursor.close()
	cursor = g.conn.execute("select comment_posted.uid, users.name as username, comment_posted.time as time, comment_posted.content as content, tmp.liked, comment_posted.cid from comment_posted, users, (select count(*) as liked from like_comment, comment_posted where like_comment.cid = comment_posted.cid and comment_posted.id = %s and like_comment.uid = %s ) as tmp where comment_posted.id = %s and users.uid = comment_posted.uid order by time desc", id, USER_ID, id)
	comments = list(cursor)
	cursor.close()
	cursor = g.conn.execute("select count(*) from like_recipe where like_recipe.id = %s", id)
	likes = list(cursor)
	cursor.close()
	cursor = g.conn.execute("select * from like_recipe where like_recipe.id = %s and like_recipe.uid = %s", id, USER_ID)
	result1 = list(cursor)
	liked = False if len(result1) == 0 else True 
	cursor.close()
	cursor = g.conn.execute("select * from saves where saves.id = %s and saves.uid = %s", id, USER_ID)
	result2 = list(cursor)
	saved = False if len(result2) == 0 else True
	cursor.close()
	return render_template("display_recipe.html", liked = liked, saved = saved, likes = likes, recipe = recipe, bean = bean, equipments = equipments, creator = creator, comments = comments)

@app.route('/like_comment/<cid>/<id>')
def like_comment(cid, id):
	global USER_ID
	cursor = g.conn.execute("insert into like_comment(uid, cid) values (%s, %s)", USER_ID, cid)
	cursor.close()
	return display_recipe(id)

@app.route('/like_recipe/<id>')
def like_recipe(id):
	global USER_ID
	cursor = g.conn.execute("insert into like_recipe(uid, id) values (%s, %s)", USER_ID, id)
	cursor.close()
	return display_recipe(id)

@app.route('/unlike_recipe/<id>')
def unlike_recipe(id):
	global USER_ID
	cursor = g.conn.execute("delete from like_recipe where uid = %s and id = %s", USER_ID, id)
	cursor.close()
	return display_recipe(id)

@app.route('/save_recipe/<id>')
def save_recipe(id):
	global USER_ID
	cursor = g.conn.execute("insert into saves(uid, id) values(%s, %s)", USER_ID, id)
	cursor.close()
	return display_recipe(id)

@app.route('/unsave_recipe/<id>')
def unsave_recipe(id):
	global USER_ID
	cursor = g.conn.execute("delete from saves where uid = %s and id = %s", USER_ID, id)
	cursor.close()
	return display_recipe(id)
	
@app.route('/post_comment/<id>', methods=['POST'])
def post_comment(id):
	global USER_ID
	comment = str(request.form['comment'])
	cursor = g.conn.execute("insert into comment_posted(id, uid, time, content) values (%s, %s, now(), %s)", id, USER_ID, comment)
	cursor.close()
	return display_recipe(id) 

@app.route('/display_bean/<id>.html')
def display_bean(id):
  cursor = g.conn.execute("select * from bean_roasts where bid=" + str(id))
  bean = list(cursor)
  cursor.close()
  cursor = g.conn.execute("select recipes.name, recipes.id from recipes, requires_bean where requires_bean.bid = %s and requires_bean.id = recipes.id", id)
  recipes = list(cursor)
  cursor.close()
  return render_template("display_bean.html", data = bean, recipes = recipes) 
 
@app.route('/display_equipment/<id>.html')
def display_equipment(id):
  cursor = g.conn.execute("select * from equipments where eid=" + str(id))
  equipment = list(cursor)
  cursor.close()
  cursor = g.conn.execute("select recipes.name, recipes.id from recipes, requires_equipment where requires_equipment.eid = %s and requires_equipment.id = recipes.id", id)
  recipes = list(cursor)
  cursor.close()
  return render_template("display_equipment.html", data = equipment, recipes = recipes)

@app.route('/display_profile')
def display_profile():
	if not session.get('logged_in'):
		return render_template('login.html')
	else:
		cursor = g.conn.execute("select name, bio from users where uid = %s", USER_ID)
		user = list(cursor)
		cursor.close()
		cursor = g.conn.execute("select users.name as following_name, follow.uid_2 as following_id from users, follow where follow.uid_1 = %s and users.uid = follow.uid_2", USER_ID)
		following = list(cursor)
		cursor.close()
		cursor = g.conn.execute("select recipes.name as saved_recipe_name, recipes.id as saved_recipe_id from recipes, saves where saves.uid = %s and saves.id = recipes.id", USER_ID)
		saved_recipes = list(cursor)
		cursor.close()
		cursor = g.conn.execute("select recipes.name as my_recipe_name, recipes.id as my_recipe_id from recipes, make where make.uid = %s and make.id = recipes.id", USER_ID)
		my_recipes = list(cursor)
		cursor.close()
		return render_template("display_profile.html", user = user, following = following, saved_recipes = saved_recipes, my_recipes = my_recipes)

@app.route('/display_user/<uid>.html')
def display_user(uid):
	cursor = g.conn.execute("select name, bio, uid from users where uid = %s", uid)
	user = list(cursor)
	cursor.close()
	cursor = g.conn.execute("select * from follow where uid_1 = %s and uid_2 = %s", USER_ID, uid)
	result = list(cursor)
	cursor.close()
	following = True if len(result) > 0 else False
	cursor = g.conn.execute("select recipes.name as recipe_name, recipes.id as recipe_id from recipes, make where make.uid = %s and make.id = recipes.id", uid)
	recipes = list(cursor)
	cursor.close()
	return render_template("display_user.html", user = user, following = following, recipes = recipes)

@app.route('/follow/<uid>')
def follow_user(uid):
	global USER_ID
	cursor = g.conn.execute("insert into follow(uid_1, uid_2) values (%s, %s)", USER_ID, uid)
	cursor.close()
	return display_user(uid)

@app.route('/all_beans.html')
def display_beans():
	if not session.get('logged_in'):
		return render_template('login.html')
	else:
		cursor = g.conn.execute("select * from bean_roasts")
		all_bean = list(cursor)
		cursor.close()
		print(all_bean)
		return render_template('all_beans.html', data = all_bean)

@app.route('/')
def home():
	if not session.get('logged_in'):
		return render_template('login.html')
	else:
		cursor = g.conn.execute("select name from users where uid = %s", USER_ID)
		qresult = list(cursor)
		name = qresult[0][0]
		print("Logged in as", name, USER_ID)
		cursor.close()
		cursor = g.conn.execute("select id, name, description, photo_url from recipes order by random() limit 4")
		featured_recipes = list(cursor) 
		cursor.close()
		cursor = g.conn.execute("select user_name, recipes.id as recipe_id, recipes.name as recipe_name, recipes.photo_url as recipe_photo, recipes.description as recipe_description, tmp2.time as time from recipes, (select make.id as id, make.time as time, users.name as user_name from users, make, (select uid_2 from follow where uid_1 = %s) tmp where make.uid = tmp.uid_2 and users.uid = make.uid) tmp2 where tmp2.id = recipes.id order by time desc", USER_ID)
		feed = list(cursor)
		cursor.close()
		return render_template('home.html',  name = name, user_id = USER_ID, featured_recipes = featured_recipes, feed = feed) 

@app.route('/login', methods=['POST'])
def do_main_login():
	global USER_ID
	POST_USERNAME = str(request.form['username'])
	POST_PASSWORD = str(request.form['password'])
	cursor = g.conn.execute("select uid from users where email = %s and password = %s", POST_USERNAME, POST_PASSWORD)
	uid_result = list(cursor)
	cursor.close()
	if len(uid_result) > 0:
		session['logged_in'] = True
		USER_ID = uid_result[0][0]
		print("logged in user id:", USER_ID)
	else:
		flash("Invalid credentials!")
	return home()

@app.route('/signup', methods=['POST'])
def signup():
	global USER_ID
	POST_USERNAME = str(request.form['username'])
	POST_PASSWORD = str(request.form['password'])
	POST_NAME= str(request.form['name'])
	POST_BIO = str(request.form['bio'])
	cursor = g.conn.execute("select uid from users where email = %s", POST_USERNAME)
	uid_result = list(cursor)
	cursor.close()
	if len(uid_result) > 0:
		flash("User already exists!")
	else:
		cursor = g.conn.execute("select count(*) from users")
		user_count = list(cursor)[0][0]
		cursor.close()
		cursor = g.conn.execute("insert into users(uid, email, bio, name, password) values(%s, %s, %s, %s, %s)", (user_count+1, POST_USERNAME, POST_BIO, POST_NAME, POST_PASSWORD))	
		cursor.close()
		flash("Sign up successful!")
	return home()

@app.route('/logout')
def logout():
	session['logged_in'] = False
	return home()

if __name__ == '__main__':
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
		"""
		This function handles command line parameters.
		Run the server using
			python server.py
		Show the help text using
			python server.py --help
		"""

		HOST, PORT = host, port
		print("running on %s:%d", HOST, PORT)
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

	run()