from django.template import Template, Context
from django.template.loader import get_template
from django.core.paginator import Paginator, InvalidPage
from django.http import HttpResponse, HttpResponseRedirect

pagination_size_default = 5

formats = ["csv",]
try:
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.platypus import Table as PDFTable
    formats.append("pdf")
except ImportError:
    pass
    
from tempfile import mkstemp

import os
import csv
import StringIO

def paginate(queryset, number, size=pagination_size_default):
    pages = Paginator(queryset, pagination_size_default)
    result = { "pages": pages, "count": queryset.count, "jump": jump(pages, number) }
    if pages.num_pages > 1:
        result["paginated"] = True
    else:
        result["paginated"] = False
    try:
        result["page"] = pages.page(number)
    except InvalidPage:
        # no page, go to 1
        result["page"] = pages.page(1)
    return result

def jump(pages, index):
    res = { "start_ellipsis": False, "end_ellipsis": False }
    nums = pages.page_range
    side = 5
    index -= 1
    start = index - side
    if start > 0:
        res["start_ellipsis"] = True
        
    if start < 0:
        start = 0
        
    end = index + side + 1
    if end > (len(nums) + 1):
        res["pages_bit"] = nums[start:]        
    else:
        res["pages_bit"] = nums[start:end]
        res["end_ellipsis"] = True
        
    return res

class Table:
    def __init__(self, template_body, heads, 
                 html=None, csv=None, pdf=None):
        self.template_body = get_template(template_body)
        
        self.heads = heads
        for x in range(0, len(self.heads)):
            dct = self.heads[x]
            # to do make, a url safe key
            dct["asc"] = True
            self.heads[x] =  dct
            
        self.template_wrapper = get_template("table_wrapper.html")
    
    def __call__(self, request, key, queryset):
        format = request.GET.get("format_%s" % key, "html") 
        method = getattr(self, "handle_%s" % format, None)
        if method:
            return format, method(request, key, queryset)
        else:
            raise NotImplementedError, "The format: %s is not handled" % format
    
    def handle_csv(self, request, key, queryset):
        output = StringIO.StringIO()
        csvio = csv.writer(output)
        header = False
        for obj in queryset:
            fields = obj._meta.fields
            if not header:
                csvio.writerow([f.name for f in fields])
                header = True
            values = [ getattr(obj, f.name) for f in fields ]
            csvio.writerow(values)

        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=report.csv'    
        response.write(output.getvalue())
        return response
        
    def handle_pdf(self, request, key, queryset):
        if "pdf" not in formats:
            raise ImportError, "The site is not configured to handle pdf."
    
        # this is again some quick and dirty sample code    
        elements = []
        styles = getSampleStyleSheet()
        filename = mkstemp(".pdf")[-1]
        doc = SimpleDocTemplate(filename)

        elements.append(Paragraph("Message Log", styles['Title']))

        data = []
        header = False
        for obj in queryset:
            fields = obj._meta.fields
            if not header:
                data.append([f.name for f in fields])
                header = True
            values = [ getattr(obj, f.name) for f in fields ]
            data.append(values)

        table = PDFTable(data)
        elements.append(table)
        doc.build(elements)

        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=report.pdf'
        response.write(open(filename).read())
        os.remove(filename)
        return response
    
    def handle_html(self, request, key, queryset):
        # get the default page number
        default = request.GET.get("page_%s" % key, 1)
        try:
            default = int(default)
        except (TypeError, ValueError):
            default = 1
        
        for h in self.heads:
            column = h["column"]
            sort_key = "sort_%s_%s" % (key, column)
            value = request.GET.get(sort_key, None)
            h["asc"] = True            
            if value == "asc":
                queryset = queryset.order_by(column)
                break
            elif value == "desc":
                queryset = queryset.order_by("-%s" % column)
                h["asc"] = False
                break        
            
        paginated = paginate(queryset, default)
        rows = []
        for row in paginated["page"].object_list:
            data = {"object": row}
            rows.append(self.template_body.render(Context(data)))

        self.context = {
            "columns": self.heads,
            "rows": rows,
            "object_list": paginated,
            "table_key": key,
            "formats": formats
        }
        return self.template_wrapper.render(Context(self.context))

tables = {}
def register(name, head, body):
    global tables
    tables[name] = Table(head, body)
    
def get(model):
    return tables[model]