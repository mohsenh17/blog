import os
from flask import render_template, flash, redirect, url_for, request
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, UpdateAcountForm, EmptyForm, FollowResponseForm
import secrets
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, FollowRequest
from PIL import Image

@app.route('/')
@app.route('/index')
@login_required
def index():
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    form = EmptyForm()
    user_profilePic = url_for('static', filename='profile_pics/'+user.profile_pic)
    return render_template('user.html', user=user, posts=posts, user_profilePic=user_profilePic, form=form)

def save_profile_pic(form_profile_pic):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_profile_pic.filename)
    profile_pic_fn = random_hex+ f_ext
    profile_pic_path = os.path.join(app.root_path,'static/profile_pics', profile_pic_fn)
    #form_profile_pic.save(profile_pic_path)
    output_size = (125, 125)
    i = Image.open(form_profile_pic)
    i.thumbnail(output_size)
    i.save(profile_pic_path)
    return profile_pic_fn

def remove_profile_pic(profile_pic_fn):
    profile_pic_path = os.path.join(app.root_path,'static/profile_pics', profile_pic_fn)
    print(profile_pic_path)
    if os.path.isfile(profile_pic_path):
        #os.system("rm {}".format(profile_pic_path)) linux
        os.remove(profile_pic_path)

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAcountForm()
    user_profilePic = url_for('static', filename='profile_pics/'+current_user.profile_pic)
    if form.validate_on_submit():
        if form.profile_pic.data:
            remove_profile_pic(current_user.profile_pic)
            profile_pic_fileName=save_profile_pic(form.profile_pic.data)
            current_user.profile_pic = profile_pic_fileName
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('account.html', form=form, profile_pic=user_profilePic)

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@app.route('/followRequests/', methods=['GET', 'POST'])
@login_required
def followRequests():
    followRequestsList = FollowRequest.query.filter_by(followed_id=current_user.id).all()
    usersRequestedToFollow =[] 
    for item in followRequestsList:
        usersRequestedToFollow.append(User.query.filter_by(id=item.follower_id).first())
    print(usersRequestedToFollow)
    form = FollowResponseForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if form.follow_response.data:
            if user in usersRequestedToFollow:
                current_user.followResponse(user, True)
                #current_user.follow(user)
                db.session.commit()
                return redirect(url_for('followRequests'))
    return render_template('followRequests.html',form=form, usersRequestedToFollow=usersRequestedToFollow)


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        if current_user.is_following(user):
            current_user.unfollow(user)
        else:
            current_user.cancel_follow_request(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))