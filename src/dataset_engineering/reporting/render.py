import json,csv,io,html
def quality_as_json(r):return json.dumps(r.model_dump(),indent=2,default=str)
def quality_as_markdown(r):return '# Quality Report\n\n'+ '\n'.join(f'- {m.field}: {m.completeness_rate:.3f}' for m in r.completeness)
def quality_as_html(r):return '<html><body><h1>Quality Report</h1>'+''.join(f'<p>{html.escape(m.field)}: {m.completeness_rate:.3f}</p>' for m in r.completeness)+'</body></html>'
def quality_as_csv(r):
 o=io.StringIO();w=csv.writer(o);w.writerow(['field','completeness_rate']);w.writerows((m.field,m.completeness_rate) for m in r.completeness);return o.getvalue()
def report_as_json(r):return quality_as_json(r)
def report_as_markdown(r):return quality_as_markdown(r)
def evaluation_as_json(r):return json.dumps(r.model_dump(),indent=2,default=str)
def evaluation_as_markdown(r):return '# Evaluation\n\n'+r.status
def evaluation_as_csv(r):return 'status\n'+r.status+'\n'
def evaluation_as_html(r):return '<html><body><h1>Evaluation</h1><p>'+html.escape(r.status)+'</p></body></html>'
