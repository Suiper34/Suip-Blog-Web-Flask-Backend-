from flask import Flask, render_template, request
import requests
import json
from datetime import datetime
from email.message import EmailMessage
import smtplib
import os
from dotenv import load_dotenv

load_dotenv('.env')

app: Flask = Flask(__name__)

response = requests.get('https://api.npoint.io/1e4f1e284ac8b96dac33')
response.raise_for_status()
data: json = response.json()

year: int = datetime.now().year


@app.route('/')
def home():
    return render_template(
        'index.html',
        slice_blog_data=list(data)[:3],
        year=year,
    )


@app.route('/post/<int:post_id>')
def show_post(post_id: int):
    """
    Retrieve and display a blog post by its ID.
    """

    post = next(
        (post_item for post_item in data if post_item['id'] == post_id), None)
    if post:
        return render_template('post.html', post=post)
    else:
        return '<h1>Post not found</h1>', 404


@app.route('/about')
def about_page():
    return render_template('about.html', year=year)


@app.route('/contact', methods=['POST', 'GET'])
def contact_page():
    """
    If the request method is POST, retrieves form data (username, email, phone, message),
    logs in to a Gmail SMTP server using credentials from environment variables, and sends
    an email to the provided email address with the submitted message. Renders the contact
    page template with the current year in both GET and POST requests.
    """

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        with smtplib.SMTP_SSL('smtp.gmail.com') as mail_server:
            mail_server.login(user=os.environ.get('MAIL'),
                              password=os.environ.get('PASSWORD'))

            mail = EmailMessage()
            mail['From'] = os.environ.get('MAIL')
            mail['To'] = email
            mail['Subject'] = f'{username} , {phone}'
            mail.set_content(message)

            mail_server.send_message(mail)

        return render_template('contact.html', year=year, is_sent=True)

    return render_template('contact.html', year=year, is_sent=False)


if __name__ == '__main__':
    app.run(debug=True)
