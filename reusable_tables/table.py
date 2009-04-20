from django.template import Template, Context
from django.template.loader import get_template
from django.core.paginator import Paginator, InvalidPage

pagination_size_default = 20

def paginate(queryset, number, size=pagination_size_default):
    try:
        number = int(number)
    except (TypeError, ValueError):
        # unknown number
        number = 1
        
    pages = Paginator(queryset, pagination_size_default)
    result = { "pages": pages, "count": queryset.count, "jump": jump(pages, number) }
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
    def __init__(self, request, key, 
                 queryset, template_head, template_body, 
                 html=None, csv=None, pdf=None):
        # get the default page number
        self.key = key
        default = request.GET.get(self.get_key(), 1)
        try:
            default = int(default)
        except (TypeError, ValueError):
            default = 1
            
        paginated = paginate(queryset, default)
        self.template_head = get_template(template_head)
        template = get_template(template_body)
        rows = []
        for row in paginated["page"].object_list:
            data = {"object": row}
            rows.append(template.render(Context(data)))
            
        self.context = {
            "head": self.template_head.render(Context({})),
            "rows": rows,
            "object_list": paginated,
            "paginate_key": self.get_key()
        }
    
    def get_key(self):
        return "page_%s" % self.key
    
    def __call__(self):
        template = get_template("table_wrapper.html")
        return template.render(Context(self.context))
        
        
        
            