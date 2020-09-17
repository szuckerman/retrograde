# retrograde
### A Static Site Generator for Jupyter Notebooks

Want to share analyses quickly and easily with colleages? Retrograde is the answer. 

Main features:

 - Compiles all notebooks into an easily searchable format
 - Only updated notebooks are rendered to HTML
 - Removes all code blocks from output for easy reading
 - Converts all notebooks to HTML for easy uploading and viewing in browser. No one needs Python or Jupyter to view!
 
## Usage

Clone this repo and run `python main.py`. Your jupyter notebooks go in the `/jupyter` directory.

## Gotchas

1. The first cell of the notebook must be the title.
2. The second cell is all the `import` stuff
3. The third cell must contain the data to be parsed for the summary table:

 ```python
 metadata_dict = {
     'categories': ('Data Science', ),
     'create_date': date(2019,7,23),
     'last_modified': date(2019,11,29),
     'last_ran': datetime.now(),
     'stakeholders': ('philcox', ),
     'status': 'AWAITING_REVIEW'}

 script_metadata(**metadata_dict)
 ```
