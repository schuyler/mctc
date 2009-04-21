from reusable_tables.table import register
from apps.mctc.models.general import Case

register("case_default", "includes/cases_body.html", [
        {"name":"Id", "column":"ref_id"},
        {"name":"Name", "column":"last_name"},
        {"name":"Status", "column":None},
        {"name":"Provider", "column":"provider"},
        {"name":"MUAC", "column":None},
        {"name":"Height", "column":None},
        {"name":"Weight", "column":None},
        {"name":"Symptoms", "column":None},        
        ])