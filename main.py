import os 
from pathlib import Path
import subprocess
import datetime
import json
import sqlite3

import pandas as pd

conn = sqlite3.connect(os.path.realpath('retrograde.db'))

URL = ''
PROJECT_LOCATION = os.getcwd()

os.chdir(PROJECT_LOCATION + '/jupyter')

my_path = Path(PROJECT_LOCATION)

jupyter_notebooks = [p for p in (my_path/'jupyter').iterdir() if p.suffix == '.ipynb']



cursor = conn.cursor()

create_table_sql = '''
	CREATE TABLE IF NOT EXISTS "main" (
	"index" INTEGER,
	  "link" TEXT,
	  "script" TEXT,
	  "categories" TEXT,
	  "create_date" TEXT,
	  "updated_date" TEXT,
	  "last_ran_date" TEXT,
	  "stakeholders" TEXT,
	  "status" TEXT,
	  "full_path" TEXT,
	  "file_create" TIMESTAMP,
	  "file_modified" TIMESTAMP
	);
	'''

create_index_sql = '''CREATE INDEX IF NOT EXISTS "ix_main_index" ON "main" ("index");'''

cursor.execute(create_table_sql)
cursor.execute(create_index_sql)
cursor.close()


def get_script_metadata(script):
	script_json = json.loads(script.read_text())
	script_title = script_json['cells'][0]['source'][0][2:]
	metadata_text = script_json['cells'][2]['outputs'][0]['text']
	metadata_text = [i.strip().split(': ') for i in metadata_text if i != '\n']
	metadata_text = [i for i in metadata_text if len(i)>1]
	metadata_dict = {k: v for k,v in metadata_text}
	# metadata_dict['Categories'] = metadata_dict['Categories'].split(',')
	# metadata_dict['Stakeholders'] = metadata_dict['Stakeholders'].split(',')
	return metadata_dict


def make_title_name(filename):
	return filename.replace('.ipynb', '').replace('_', ' ').title()


OUTPUT_DIR=PROJECT_LOCATION

# In case you don't want to use a CDN

# scripts_tuple = (
# 	("https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js", URL + 'require.min.js'),
# 	("https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js", URL + 'jquery.min.js'),
# 	("https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/latest.js?config=TeX-AMS_HTML", URL + 'latest.js'),
# 	('https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.6/MathJax.js?config=TeX-AMS_HTML&latest', URL + 'latest.js')
# )


def create_records_df(jupyter_notebooks):
	records = []
	for i in jupyter_notebooks:
		metadata_dict = get_script_metadata(i)
		insert_tuple = (
						URL + i.name.replace('ipynb', 'html'), 
						make_title_name(i.name),
						metadata_dict['Categories'],
						metadata_dict['Script Created'],
						metadata_dict['Script Last Modified'],
						metadata_dict['Script Last Ran'],
						metadata_dict['Stakeholders'],
						metadata_dict['Status'],
						str(i),
						datetime.datetime.fromtimestamp(i.lstat().st_ctime),
						datetime.datetime.fromtimestamp(i.lstat().st_mtime)
						)
		records.append(insert_tuple)
	columns=['link', 'script', 'categories', 'create_date', 'updated_date', 'last_ran_date', 'stakeholders', 'status', 'full_path', 'file_create', 'file_modified']
	df = pd.DataFrame.from_records(records, columns=columns)
	return df


def render_notebooks(notebooks):
	for jupyter_notebook in notebooks:
		nbconvert_cmd = "jupyter nbconvert {jupyter_notebook} --output-dir={output_dir} --to=html --TemplateExporter.exclude_input=True --no-prompt".format(jupyter_notebook=jupyter_notebook, output_dir=OUTPUT_DIR)
		subprocess.call(nbconvert_cmd, shell=True)
		html_output_file = jupyter_notebook.name.replace('ipynb', 'html')
		html_output_file = os.path.join(OUTPUT_DIR, html_output_file)
		html_output_file = Path(html_output_file)
		content = html_output_file.read_text()
		# for script_name in scripts_tuple:
		# 	content = content.replace(script_name[0], script_name[1])
		html_output_file.write_text(content)


def make_link(href, text, new_tab=True):
	return f"<a href='{href}' target='_blank'>{text}</a>" if new_tab else f"<a href='{href}'>{text}</a>"


def create_index_file(df, output_name='index'):
	df_link = df
	df_link['script'] = df.apply(lambda x: make_link(x['link'], x['script']), axis=1)
	df_link = df_link.drop(['link', 'full_path', 'file_create', 'file_modified'], axis=1)
	df_link.columns = [i.replace('_', ' ').title() for i in df.columns.values][1:-3]
	table_code = df_link.to_html(table_id='main_table', classes=['table', 'display'], render_links=True, escape=False, index=False, border=0)
	toc_code = '''
	<html>
	<head>
		<title>ACX Analytics Reports</title>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>
		<script src="https://cdn.datatables.net/1.10.21/js/jquery.dataTables.min.js"></script>
		<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
		<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
		<link rel="stylesheet" href="https://cdn.datatables.net/1.10.21/css/jquery.dataTables.min.css">
	</head>
	<body>
		
	<div class="container">
	<h1>Below are various analyses</h1>
	'''
	toc_code += table_code
	toc_code += '''</div>'''
	toc_code += '''<script> $(document).ready(function() {$( '#main_table' ).DataTable(); } ); </script>'''
	toc_code += '''</body></html>'''
	print('')
	print(f'There are currently {df.shape[0]} scripts in the {output_name}.html file. Creating file now.')
	with open(os.path.join(my_path, f'{output_name}.html'), 'w') as f:
		f.write(toc_code)
	print(f'Rendering of {output_name}.html completed.')

def get_modified_notebooks(df):
	df_last_modified = pd.read_sql('select script, file_modified file_last_modified from main', conn)
	df_last_modified.file_last_modified = pd.to_datetime(df_last_modified.file_last_modified)
	df = df.merge(df_last_modified, how='left')
	modified_notebooks = set(Path(i) for i in df[df.file_modified != df.file_last_modified].full_path)
	return modified_notebooks

df = create_records_df(jupyter_notebooks)

modified_notebooks = get_modified_notebooks(df)

if modified_notebooks:
	print(f'{len(modified_notebooks)} notebook{"s have" if len(modified_notebooks) > 1 else " has"} been modified. Rendering now.')
	render_notebooks(modified_notebooks)
	df = create_records_df(jupyter_notebooks)
	df.to_sql('main', conn, if_exists='replace')
	create_index_file(df)
else:
	print('No notebooks to render. Exiting.')


