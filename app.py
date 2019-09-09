from flask import render_template
from flask import request
from flask import Flask
app = Flask(__name__)
app.config['WHOOSH_BASE'] = 'path/to/whoosh/base'

class Canon(db.Model):
        __tablename__ = 'canon'
        __searchable__ = ['content']

        canon_num = app.db.Column(app.db.Integer, primary_key=True)
        content = app.db.Column(app.db.Text)

        def __repr__(self):
                return '{0}(title={1})'.format(self.__class__.__name__, self.content)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    if request.method == "GET":
        return render_template('search.html', search_text=request.args["query"])

@app.route('/canon', methods=['GET'])
def canon():
    return render_template('canon.html', search_text=request.args["query"], canon=request.args["canon"])

if __name__ == '__main__':
    app.run()