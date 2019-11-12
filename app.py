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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./tmp/paragraphs.db'
db = SQLAlchemy(app)

# Create tables for use for paragraphs

# Table: Paragraph
# Description: Used to store all the paragraphs in the CCC
# Parameters:
#       paragraph_num  - The number of the paragraph according to the CCC
#       content    - The text of the paragraph from the CCC
#       section_id - The section_id of the section that the paragraph
#                    belongs to in the CCC
class Paragraph(db.Model):
        paragraph_num = db.Column(db.Integer, primary_key=True)
        content = db.Column(db.Text)
        section_id = db.Column(db.Integer)

        def __repr__(self):
                return '{0} {1}'.format(self.paragraph_num, self.content)

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
        paragraph_num = db.Column(db.Integer)
        sentence_location = db.Column(db.Integer)
        id = db.Column(db.Integer)

        def __repr__(self):
                return '{0}'.format(self.footnote)

db.create_all()

# Set up the indexing tools
schema = Schema(content=TEXT(stored=True), paragraph_num=STORED, section_id=STORED)
# If there is no indexing files found, create and write to them
if len(os.listdir('./indexdir')) == 0:
        ix = create_in("indexdir", schema)
        writer = ix.writer()
        for paragraph in Paragraph.query.all():
                writer.add_document(content=str(paragraph.content), paragraph_num=paragraph.paragraph_num, section_id=paragraph.section_id)
        writer.commit()
# Otherwise, open the currently existing indexing files
else:
        ix = open_dir("indexdir")

# Checks the current mode and redirects based on that mode.
def check_mode(template):
        maintenance_mode = int(os.environ['MAINTENANCE_MODE'])
        if maintenance_mode == 1:
                return redirect(url_for('maintenance'))
        else:
                return template

# Inserts the footnotes into the content properly
def insert_footnotes(footnote_list, starttag, endtag, text):
        new_string = text
        index_offset = 0
        for footnote in footnote_list:
                content = starttag + str(footnote.id) + endtag
                new_string += text[:footnote.sentence_location + index_offset] + content + text[footnote.sentence_location + index_offset:]
                index_offset += len(content)
        return new_string


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
                # Create query parser to search for paragraphs from GET request arguments
                query = QueryParser("content", ix.schema).parse(request.args["query"] if len(request.args["query"]) > 0 else "*")
                results = searcher.search(query, limit=None, terms=True)
                results.formatter = highlight.UppercaseFormatter()
                query_result = []
                # Go through section headers and separate paragraphs according to proper sections
                for section_header in SectionTitle.query.all():
                        section = {"title": section_header.title, "results": []}
                        for result in results:
                                if result["section_id"] == section_header.id:
                                        section["results"].append(result)
                        if len(section["results"]) > 0:
                                query_result.append(section)
                return check_mode(render_template('search.html', search_text=request.args["query"], highlight_paragraph_num=(query_result[0]["results"][0]["paragraph_num"] if len(query_result) > 0 else ""), highlight=(query_result[0]["results"][0].highlights("content") if len(query_result) else "No Result"), has_results=(len(query_result) > 0), sections=query_result))

# Paragraph page
@app.route('/paragraph', methods=['GET'])
def paragraph():
    if request.method == "GET":
        paragraph = int(request.args["id"])
        footnotes = FootNote.query.filter_by(paragraph_num=paragraph)
        paragraph = Paragraph.query.filter_by(paragraph_num=paragraph).first()
        paragraph.content = insert_footnotes(footnotes, "<sup><a class='footnote-item' href='#'>", "</a></sup>", paragraph.content)
        return check_mode(render_template('paragraph.html', search_text=request.args["query"], paragraph=paragraph, footnotes=footnotes, footnotes_length=footnotes.count()))

# Maintenance page
@app.route('/maintenance', methods=['GET'])
def maintenance():
        return render_template('maintenance.html')

if __name__ == '__main__':
    app.run()