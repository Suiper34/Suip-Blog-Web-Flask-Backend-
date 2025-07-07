from flask import Flask, render_template
import requests
import json
from datetime import datetime


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


@app.route('/contact')
def contact_page():
    return render_template('contact.html', year=year)


if __name__ == '__main__':
    app.run(debug=True)
