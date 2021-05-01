import datetime
import os
import boto3
import requests

from flask import abort, Flask, render_template, redirect, request, session, url_for
from boto3.dynamodb.conditions import Key, Attr


app = Flask(__name__)
app.secret_key = "super secret key"


dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
login_table = dynamodb.Table('login')
sub_table = dynamodb.Table('subscribe')
music_table = dynamodb.Table('music')


# Create an item in Login table when new user register
def store_userdetails( email, username, password):
    
    response = login_table.put_item(
        Item={
            'email': email,
            'user_name': username,
            'password': password
        }
    )

    return response


# Create an item in Subscribe table when new song is subscribed
def store_subscribe( fetch_res, username):
    
    for result in fetch_res:
        response = sub_table.put_item(
            Item={
                'user_name': username,
                'title': result['title'],
                'year': result['year'],
                'artist': result['artist']
            }
        )

    return response


# Delete item from Subscribe table when subscription is removed
def delete_subscribe( username, title):

    response = sub_table.delete_item(

        Key={
            'user_name': username,
            'title': title
        }
    )
    return response


def fetch_email(email):

    response = login_table.query(
        KeyConditionExpression=Key('email').eq(email)
    )

    return response['Items']


def fetch_song(title, year, artist):
    
    response = music_table.scan(
        FilterExpression=Attr('title').eq(title) & Attr('year').eq(year) & Attr('artist').eq(artist)
    )

    return response['Items']


def fetch_songty(title, year,):
    
    response = music_table.scan(
        FilterExpression=Attr('title').eq(title) & Attr('year').eq(year)
    )

    return response['Items']
    

def fetch_songta(title, artist):
    
    response = music_table.scan(
        FilterExpression=Attr('title').eq(title) & Attr('artist').eq(artist)
    )

    return response['Items']


def fetch_songya(year, artist):
    
    response = music_table.scan(
        FilterExpression=Attr('year').eq(year) & Attr('artist').eq(artist)
    )

    return response['Items']


def fetch_songt(title):
    
    response = music_table.scan(
        FilterExpression=Attr('title').eq(title)
    )

    return response['Items']


def fetch_songy(year):
    
    response = music_table.scan(
        FilterExpression=Attr('year').eq(year)
    )

    return response['Items']


def fetch_songa(artist):
    
    response = music_table.scan(
        FilterExpression=Attr('artist').eq(artist)
    )

    return response['Items']


def fetch_subscribed(username):
    
    response = sub_table.scan(
        FilterExpression=Attr('user_name').eq(username)
    )

    return response['Items']

    
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
           
        result_return = fetch_email(email)
    
        if result_return:
            for r in result_return:
            
                if password == r['password']:
                    session.clear()
                    session['loggedin'] = True
                    session['id'] = email
                    session['username'] = r['user_name']
                    session['count'] = 1
                    return redirect(url_for('main'))
                else:
                    error = 'Password is Invalid'
        else:
            error = 'ID is invalid'
    
    return render_template('index.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        result_return = fetch_email(email)
    
        if result_return:
            error = 'Email already exist'
        else:
            put_response = store_userdetails( email, username, password )     
            print("New user added successfully")

            return redirect(url_for('login'))
    
    return render_template('register.html', error=error)    


@app.route('/main', methods=['GET', 'POST'])
def main():
        
    username = session['username']
    img_url = "https://s3823026-artist.s3.amazonaws.com/"
    fetch_res = " "
    error = None

    fetch_sub = fetch_subscribed(username)
    
    
    if request.method == 'POST' and 'query' in request.form:
        title = request.form['title']
        year = request.form['year']
        artist = request.form['artist']

        if (title and year and artist):
            fetch_res = fetch_song(title, year, artist)
        elif (title and year):
            fetch_res = fetch_songty(title, year)
        elif (title and artist):
            fetch_res = fetch_songta(title, artist)
        elif (year and artist):
            fetch_res = fetch_songya(year, artist)
        elif title:
            fetch_res = fetch_songt(title)
        elif year:
            fetch_res = fetch_songy(year)
        elif artist:
            fetch_res = fetch_songa(artist)

        if fetch_res :
            error = None
        else:
            error = "No result is retrieved. Please query again"

    if request.method == 'POST' and 'subscribe' in request.form:
        
        title = request.form['title']
    
        put_response = fetch_songt(title)

        add_response = store_subscribe(put_response, username)
        print("New song subscribed successfully")
        return redirect(url_for('main'))

    if request.method == 'POST' and 'remove' in request.form:
        title = request.form['title']
        print("delete" , title)

        del_response = delete_subscribe(username, title)
        print("Subscription removed successfully")
        
        return redirect(url_for('main'))

    
    return render_template('main.html', username=username, url=img_url, data=fetch_res, sdata=fetch_sub, error=error)
    

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('username', None)
   
   # Redirect to login page
   return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
