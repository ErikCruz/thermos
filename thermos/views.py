from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import login_required, login_user, logout_user, current_user

from thermos import app, db, login_manager
from forms import BookmarkForm, LoginForm, SignUpForm
from models import User, Bookmark, Tag

@login_manager.user_loader
def load_user(userid):
	return User.query.get(int(userid))

@app.route("/index")
@app.route("/")
def index():
	return render_template("index.html",new_bookmarks=Bookmark.newest(5))

@app.route('/add', methods=['GET','POST'])
@login_required
def add():
	form = BookmarkForm()
	if form.validate_on_submit():
		url = form.url.data
		description = form.description.data
		tags = form.tags.data
		bm = Bookmark(user=current_user,url=url,description=description,tags=tags)
		db.session.add(bm)
		db.session.commit()
		flash("Bookmark Successfully Added")
		return redirect(url_for('index'))
	return render_template('add.html',form=form)

@app.route('/user/<username>')
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	return render_template("user.html",user=user)

@app.route('/login', methods=['GET','POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.get_by_username(form.username.data)
		if user is not None:
			login_user(user, form.remember_me.data)
			flash("Welcome Back %s" % user.username)
			return redirect(request.args.get('next') or url_for('user',username=user.username))
		flash("Incorrect username or password")
	return render_template("login.html",form=form)

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))

@app.route('/signup', methods=['GET','POST'])
def signup():
	form = SignUpForm
	if form.validate_on_submit():
		user = User(email=form.email.data,username=form.username.data,password=form.password.data)
		db.session.add(user)
		db.session.commit()
		flash("Welcome %s" % user.username)
		return redirect(url_for('login'))
	return render_template("signup.html",form=form)

@app.route('/edit/<int:bookmark_id>', methods=['GET','POST'])
@login_required
def edit_bookmark(bookmark_id):
	bookmark = Bookmark.query.get_or_404(bookmark_id)
	if current_user != bookmark.user:
		abort(403)
	form = BookmarkForm(obj=bookmark)
	if form.validate_on_submit():
		form.populate_obj(bookmark)
		db.session.commit()
		flash("Stored %s" % bookmark.description)
		return redirect(url_for('user',username=current_user.username))
	return render_template('edit.html',form=form,title='Edit Bookmark')

@app.route('/tag/<name>')
def tag(name):
	tag = Tag.query.filter_by(name=name).first_or_404()
	return render_template('tag.html',tag=tag)

@app.route('/delete/<int:bookmark_id>')
def delete_bookmark(bookmark_id):
	bookmark = Bookmark.query.get_or_404(bookmark_id)
	if current_user != bookmark.user:
		abort(404)
	if request.method == 'POST':
		db.session.delete(bookmark)
		db.session.commit()
		flash("Bookmark Successfully Deleted")
		return redirect(url_for('user',username=current_user.username))
	else:
		flash("Please confirm deleting the bookmark")
	return render_template("confirm_delete.html",bookmark=bookmark,nolinks=True)

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

@app.context_processor
def inject_tags():
	return dict(all_tags=Tag.all)