import hashlib
import datetime
import os
import random
import string

import flask

from flask import Flask
from flask import *
from sqlalchemy.sql.expression import true
from flask_login import UserMixin, LoginManager, login_required, login_user, current_user, logout_user

from sqlalchemy import create_engine, Column, String, Integer, DATETIME, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session



app = Flask(__name__)

#セッションのためのシークレットキー
app.config['SECRET_KEY'] = os.urandom(24) #urandomだと再起動した時に変わってしまうらしい

engine = create_engine('sqlite:///app.db') # user.db というデータベースを使うという宣言です
Base = declarative_base() # データベースのテーブルの親です

#magic
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, Base): # UserMixinを継承
    __tablename__ = 'users' # テーブル名は users です
    id = Column(Integer, primary_key=True) #primary_key=True
    tag = Column(String)
    name = Column(String, unique=True)
    email = Column(String)
    passw = Column(String)

    """
    def get_id(self):
        return (self.id)
        """

    def __repr__(self):
        return "Content<{}, {}, {}, {}>".format(self.tag, self.name, self.passw, self.email)
    
class Content(Base):
    __tablename__ = 'contents'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    content = Column(String)
    timestamp = Column(DATETIME)
    thread = Column(Integer)

    def __repr__(self):
        return "Content<{}, {}, {}, {}, {}>".format(self.id, self.name, self.content, self.timestamp, self.thread)

class Friend_Request(Base):
    __tablename__ = 'friend_requests'
    id = Column(Integer, primary_key=True)
    sender_name = Column(String)
    recipient_name = Column(String)

class Friend(Base):
    __tablename__ = 'friends'
    id = Column(Integer, primary_key=True)
    name1 = Column(String)
    name2 = Column(String)



Base.metadata.create_all(engine) # 実際にデータベースを構築します
SessionMaker = sessionmaker(bind=engine) # Pythonとデータベースの経路です
#session = SessionMaker() # 経路を実際に作成しました
session = scoped_session(SessionMaker)

#user1 = User(email="thisisme@test.com", name="Python") # emailと nameを決めたUserのインスタンスを作りましょう(idは自動で1から順に振られます)
#session.add(user1) # user1 をデータベースに入力するための準備をします
#session.commit() # 実際にデータベースにデータを入れます。

#タグ生成
def make_tag():
    randlst = [random.choice(string.ascii_letters + string.digits) for i in range(4)]
    return ''.join(randlst)

@app.route("/GenerateTag")
@login_required
def generate_tag():
    new_tag = make_tag()
    user = session.query(User).filter(User.name == current_user.name).first()
    user.tag = new_tag
    session.commit()
    return redirect(url_for("home"))




# テキストチャンネル
@app.route("/<num>",methods=["GET","POST"])
def thread_page(num):

    """
    if num == "login":
        return redirect(url_for('login'))
        """
    print("def thread_page")
    cont = session.query(Content).filter(Content.thread == num).all()#table Contentから検索
    if request.method == "GET":
        return render_template("chat-index.html", cont=cont, thread=num)
    
    print("POST HELLO")
    user = session.query(User).filter(User.email == request.form["email"]).first()

    if user:
        if user.passw != str(hashlib.sha256(request.form["pass"].strip().encode("utf-8")).digest()):
            #return redirect(url_for('login'))
            return render_template("chat-index.html", cont=cont, thread=num)
    else:
        user = User(tag="tag-test", name=request.form["name"], email=request.form["email"], passw=str(hashlib.sha256(request.form["pass"].strip().encode("utf-8")).digest()))
        session.add(user)
    
    print(num)
    mess = Content(name=request.form["name"], content=request.form["content"], timestamp=datetime.datetime.now(),thread=num)
    session.add(mess)
    session.commit()
    cont = session.query(Content).filter(Content.thread == num).all()
    return render_template("chat-index.html", cont=cont, thread=num)


#サインアップ
@app.route("/signup", methods=["GET","POST"])
def signup():
    if(request.method == 'GET'):
        return render_template("signup.html")
    
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    c_password = request.form["confirmation-password"]

    user = session.query(User).filter(User.name == name).first()
    if user:
        flash('User name is already used.')
        return render_template("signup.html")

    if password != c_password:
        flash('Password does not match.')
        return render_template("signup.html")

    tag = make_tag()
    user = User(tag=tag, name=name, email=email, passw=str(hashlib.sha256(password.strip().encode("utf-8")).digest()))
    session.add(user)
    session.commit()

    login_user(user, true)

    return redirect('home')

# ログイン
@app.route("/login", methods=["GET","POST"])
def login():
    if(request.method == 'GET'):
        return render_template("login.html")

    # 名前とパスワードでログイン
    nname = request.form["name"]
    npassw = request.form["password"]

    # 指定された名前に一致するものを探す
    user = session.query(User).filter(User.name == nname).first()
    
    if user: # 存在する
        print("id",user.id)
        if user.passw == str(hashlib.sha256(request.form["password"].strip().encode("utf-8")).digest()):
            login_user(user, true)
            return redirect(url_for('home')) #ログインしたらhomeへ
        else:
            flash('Password is incorrect.')
            return redirect(url_for('login')) #失敗したら再読み込み
    else:
        flash('User does not exist.')
        return redirect(url_for('login')) #失敗したら再読み込み

# ログアウト
@app.route("/logout", methods=["GET"])
@login_required # ログインが必要
def logout():
    logout_user()
    return redirect(url_for('login'))

#ユーザの判別
@login_manager.user_loader
def load_user(user_id):
    return session.query(User).get(user_id) #idでユーザを判別
    
#権限なし
@login_manager.unauthorized_handler
def unauth():
    #return "You can not access this page..." 
    return redirect(url_for("login"))# 権限がないとき

#ユーザのホーム
@app.route("/home", methods=["GET"])
@login_required #ログインが必要
def home():
    sent_req = session.query(Friend_Request).filter(Friend_Request.sender_name == current_user.name).all()
    received_req = session.query(Friend_Request).filter(Friend_Request.recipient_name == current_user.name).all()
    
    friend_q = session.query(Friend).filter(or_(Friend.name1 == current_user.name, Friend.name2 == current_user.name))
    friend_all = []
    for f in friend_q:
        if f.name1 == current_user.name: # name2が相手
            friend_all.append(f.name2)
        else:
            friend_all.append(f.name1)

    #print(sent_req)
    return render_template("home.html", name=current_user.name, tag=current_user.tag, myreq = sent_req, friendreq = received_req, myfriend = friend_all) # current_userで現在のユーザを取得

#フレンド申請
@app.route("/make-friend-request", methods=["GET","POST"])
@login_required
def make_friend_request():
    name_and_tag = request.form["friend"]
    if len(name_and_tag) <= 5:
        flash("Invalid Request")
        return redirect(url_for("home"))
    if name_and_tag[len(name_and_tag) - 5] != '#':
        flash("Invalid Request")
        return redirect(url_for("home"))
    
    tag = name_and_tag[len(name_and_tag) - 4:len(name_and_tag)]
    name = name_and_tag[0:len(name_and_tag) - 5]
    print(name,tag)
    
    user = session.query(User).filter(User.name==name, User.tag==tag).first()
    if not user:
        flash("No User")
        return redirect(url_for("home"))
    
    search_req = session.query(Friend_Request).filter(Friend_Request.sender_name == current_user.name, Friend_Request.recipient_name == name).first()
    if search_req:
        #print(search_req.sender_name,search_req.recipient_name)
        flash("Already sent")
        return redirect(url_for("home"))
    
    search_req2 = session.query(Friend_Request).filter(Friend_Request.sender_name == name, Friend_Request.recipient_name == current_user.name).first()
    if search_req2:
        #print(search_req.sender_name,search_req.recipient_name)
        flash("Already received")
        return redirect(url_for("home"))

    req = Friend_Request(sender_name=current_user.name, recipient_name=name)
    session.add(req)
    session.commit()

    flash("Success")
    return redirect(url_for("home"))

#フレンド申請をキャンセル
@app.route("/cancel-friend-request/<who>", methods=["GET"])
@login_required
def cancel_friend_request(who):
    req = session.query(Friend_Request).filter(Friend_Request.sender_name == current_user.name, Friend_Request.recipient_name == who).first()
    session.delete(req)
    session.commit()
    return redirect(url_for("home"))

#フレンド申請を拒否
@app.route("/reject-friend-request/<who>", methods=["GET"])
@login_required
def reject_friend_request(who):
    req = session.query(Friend_Request).filter(Friend_Request.sender_name == who, Friend_Request.recipient_name == current_user.name).first()
    session.delete(req)
    session.commit()
    return redirect(url_for("home"))

#フレンド追加
@app.route("/add-friend/<who>", methods=["GET"])
@login_required
def add_friend(who):
    pair = Friend(name1=current_user.name, name2=who)
    session.add(pair)
    session.commit()
    return redirect(url_for("home"))


#テキストチャンネル(テスト)
@app.route("/<mytag>/<yourtag>", methods=["GET"])
def test(mytag,yourtag):
    return mytag + " " + yourtag



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8888, threaded=True)


