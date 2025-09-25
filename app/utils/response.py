from flask import jsonify, Response
from typing import Union, List

def create_response(status:str, data:Union[dict, List[dict], None]=None, message:str=None, status_code=200) -> Response:
  """Crea una respuesta para el cliente.
  
  `success`: Respuesta exitosa.
  
  `fail`: Respuesta fallida.
  
  `error`: Respuesta con error.  
   
  
  Args:
  
  `status`: str - Estado de la respuesta.
  
  `data`: dict, List[dict], None - Datos de la respuesta.
  
  `message`: str - Mensaje de la respuesta.
  
  `status_code`: int - Código de estado de la respuesta.
    
  """
  
  if status in ('fail', 'error'):    
    response = {
        'status': status,
        'message': message,
        'data': data
    }
  elif status == 'success':
    response = {
        'status': status,
        'data': data
    }
  else:
    raise Exception('Invalid status.')
    
  return jsonify(response), status_code
