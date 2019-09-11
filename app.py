from flask import render_template
from flask import Markup
from flask import redirect
from flask import url_for
from flask import request
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from whoosh.index import create_in
from whoosh.index import open_dir
from whoosh import highlight
from whoosh.fields import *
import os
import re

# Setup web app along with Sqlite database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./tmp/canons.db'
db = SQLAlchemy(app)

# Create tables for use for canons

# Table: Canon
# Description: Used to store all the canons in the CCC
# Parameters:
#       canon_num  - The number of the canon according to the CCC
#       content    - The text of the canon from the CCC
#       section_id - The section_id of the section that the canon
#                    belongs to in the CCC
class Canon(db.Model):
        canon_num = db.Column(db.Integer, primary_key=True)
        content = db.Column(db.Text)
        section_id = db.Column(db.Integer)

        def __repr__(self):
                return '{0} {1}'.format(self.canon_num, self.content)

# Table: SectionTitle
# Description: Used to store all the section headers in the CCC
# Parameters:
#       id    - The assigned id for a particular section title
#       title - The title of the section in the CCC
class SectionTitle(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.Text)

        def __repr__(self):
                return '{0}'.format(self.title)

class FootNote(db.Model):
        footnote = db.Column(db.Text, primary_key=True)
        canon_num = db.Column(db.Integer)
        sentence_location = db.Column(db.Integer)
        id = db.Column(db.Integer)

        def __repr__(self):
                return '{0}'.format(self.footnote)

db.create_all()

# Set up the indexing tools
schema = Schema(content=TEXT(stored=True), canon_num=STORED, section_id=STORED)
# If there is no indexing files found, create and write to them
if len(os.listdir('./indexdir')) == 0:
        ix = create_in("indexdir", schema)
        writer = ix.writer()
        for canon in Canon.query.all():
                writer.add_document(content=str(canon.content), canon_num=canon.canon_num, section_id=canon.section_id)
        writer.commit()
# Otherwise, open the currently existing indexing files
else:
        ix = open_dir("indexdir")

def check_mode(template):
        maintenance_mode = int(os.environ['MAINTENANCE_MODE'])
        if maintenance_mode == 1:
                return redirect(url_for('maintenance'))
        else:
                return template

def insert_string(substring, text, index):
        return text[:index] + substring + text[index:]


# Home page
@app.route('/')
def index():
    return check_mode(render_template('index.html'))

# Search page
@app.route('/search', methods=['GET'])
def search():
    if request.method == "GET":
        from whoosh.qparser import QueryParser
        # With the Whoosh search object...
        with ix.searcher() as searcher:
                # Create query parser to search for canons from GET request arguments
                query = QueryParser("content", ix.schema).parse(request.args["query"])
                results = searcher.search(query, limit=20, terms=True)
                results.formatter = highlight.UppercaseFormatter()
                query_result = []
                # Go through section headers and separate canons according to proper sections
                for section_header in SectionTitle.query.all():
                        section = {"title": section_header.title, "results": []}
                        for result in results:
                                if result["section_id"] == section_header.id:
                                        section["results"].append(result)
                        if len(section["results"]) > 0:
                                query_result.append(section)
                return check_mode(render_template('search.html', search_text=request.args["query"], highlight_canon_num=(query_result[0]["results"][0]["canon_num"] if len(query_result) > 0 else ""), highlight=(query_result[0]["results"][0].highlights("content") if len(query_result) else "No Result"), has_results=(len(query_result) > 0), sections=query_result))

# Canon page
@app.route('/canon', methods=['GET'])
def canon():
    if request.method == "GET":
        footnotes = FootNote.query.filter_by(canon_num=int(request.args["canon"]))
        canon = Canon.query.filter_by(canon_num=int(request.args["canon"])).first()
        for index, footnote in enumerate(footnotes):
                canon.content = insert_string("<sup><a class='footnote-item' href='#'>" + str(footnote.id) + "</a></sup>", canon.content, footnote.sentence_location)
        return check_mode(render_template('canon.html', search_text=request.args["query"], canon=canon, footnotes=footnotes, footnotes_length=footnotes.count()))

# Maintenance page
@app.route('/maintenance', methods=['GET'])
def maintenance():
        return render_template('maintenance.html')

if __name__ == '__main__':
    app.run()