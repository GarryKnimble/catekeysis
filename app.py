from flask import render_template
from flask import request
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from whoosh.index import create_in
from whoosh.index import open_dir
from whoosh import highlight
from whoosh.fields import *
import os
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./tmp/canons.db'
db = SQLAlchemy(app)

class Canon(db.Model):
        canon_num = db.Column(db.Integer, primary_key=True)
        content = db.Column(db.Text)
        section_id = db.Column(db.Integer)

        def __repr__(self):
                return '{0} {1}'.format(self.canon_num, self.content)

class SectionTitle(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.Text)

        def __repr__(self):
                return '{0}'.format(self.title)

db.create_all()

schema = Schema(content=TEXT(stored=True), canon_num=STORED, section_id=STORED)
if len(os.listdir('./indexdir')) == 0:
        ix = create_in("indexdir", schema)
else:
        ix = open_dir("indexdir")
writer = ix.writer()
for canon in Canon.query.all():
        writer.add_document(content=str(canon.content), canon_num=canon.canon_num, section_id=canon.section_id)
writer.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    if request.method == "GET":
        from whoosh.qparser import QueryParser
        with ix.searcher() as searcher:
                query = QueryParser("content", ix.schema).parse(request.args["query"])
                results = searcher.search(query, limit=20, terms=True)
                results.formatter = highlight.HtmlFormatter(tagname="span", classname="search-text")
                query_result = []
                for section_header in SectionTitle.query.all():
                        section = {"title": section_header.title, "results": []}
                        for result in results:
                                if result["section_id"] == section_header.id:
                                        section["results"].append(result)
                        if len(section["results"]) > 0:
                                query_result.append(section)
                return render_template('search.html', search_text=request.args["query"], sections=query_result)

@app.route('/canon', methods=['GET'])
def canon():
    canon = Canon.query.filter_by(canon_num=int(request.args["canon"])).first()
    return render_template('canon.html', search_text=request.args["query"], canon=canon)

if __name__ == '__main__':
    app.run()