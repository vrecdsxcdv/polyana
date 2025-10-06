from dataclasses import dataclass
@dataclass
class OrderDTO:
    id:int|None=None
    code:str=""
    user_id:int|None=None
    what_to_print:str=""
    quantity:int=0
    format:str=""
    sides:str=""
    paper:str=""
    deadline_at:str|None=None
    contact:str=""
    notes:str=""
    lamination:str="none"
    bigovka_count:int=0
    corner_rounding:bool=False
    sheet_format:str=""
    custom_size_mm:str=""
    material:str=""
    print_color:str="color"
    status:str="NEW"
    needs_operator:bool=False