from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user
from app import login


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Follow(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class FollowRequest(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    privacy = db.Column(db.Boolean, unique=False, default=True) # by default the user is private
    password_hash = db.Column(db.String(128))
    joinDate = db.Column(db.DateTime, index=True, default=datetime.utcnow().date()) #user's joining date
    profile_pic = db.Column(db.String(120), default='default_profilePic.jpg')
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    
    followed = db.relationship('Follow',
                            foreign_keys=[Follow.follower_id],
                            backref=db.backref('follower', lazy='joined'),
                            lazy='dynamic',
                            cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                            foreign_keys=[Follow.followed_id],
                            backref=db.backref('followed', lazy='joined'),
                            lazy='dynamic',
                            cascade='all, delete-orphan')
    
    sentFollowRequest = db.relationship('FollowRequest',
                            foreign_keys=[FollowRequest.follower_id],
                            backref=db.backref('sentFollowRequest', lazy='joined'),
                            lazy='dynamic',
                            cascade='all, delete-orphan')
    recievedFollowRequest = db.relationship('FollowRequest',
                            foreign_keys=[FollowRequest.followed_id],
                            backref=db.backref('recievedFollowRequest', lazy='joined'),
                            lazy='dynamic',
                            cascade='all, delete-orphan')
    

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def requested_to_follow(self, user):
        return self.sentFollowRequest.filter_by(followed_id=user.id).count() > 0

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(
            follower_id=user.id).first() is not None
    
    def follow(self, user):
        if not self.is_following(user):
            if not self.privacy:
                f = Follow(follower=self, followed=user)
                db.session.add(f)
            else:
                f=FollowRequest(sentFollowRequest=self, recievedFollowRequest=user)
                db.session.add(f)

    def followResponse(self, user, follow_response):
        if not self.is_following(user):
            if follow_response:
                f = Follow(followed=self, follower=user)
                db.session.add(f)
            f = self.recievedFollowRequest.filter_by(follower_id=user.id).first()
            print(f)
            db.session.delete(f)
        
    def cancel_follow_request(self):
        f = self.sentFollowRequest.filter_by(follower_id=current_user.id).first()
        db.session.delete(f)


    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
            return True
    
    

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)