from pydantic import BaseModel
from typing import Optional
from typing import List

# --- USUARIO ---

class UsuarioCreate(BaseModel):
    username: str
    password: str

class UsuarioResponse(BaseModel):
    id: int
    username: str
    
    class Config:
        from_attributes = True

        
# 1. Esquema Base (Lo que comparten la creación y la lectura)
class ProductoBase(BaseModel):
    nombre: str
    numero_pieza: Optional[str] = None
    marca: str
    modelo: str
    año: int
    precio_unitario: float

# 2. Esquema para CREAR un producto (lo que recibimos del frontend)
class ProductoCreate(ProductoBase):
    pass # Por ahora hereda todo igual, pero podríamos agregar validaciones extra aquí

# 3. Esquema para LEER un producto (lo que devolvemos al frontend)
class Producto(ProductoBase):
    id: int

    class Config:
        # ¡ESTO ES CLAVE! Le dice a Pydantic que lea los datos desde un modelo de SQLAlchemy
        from_attributes = True

# Esquema de lo que recibe por cada producto/servicio en la cotización
class CotizacionDetalleCreate(BaseModel):
    producto_id: Optional[int] = None
    servicio_id: Optional[int] = None
    cantidad: int
    # Nota: No le pedimos el precio al frontend por seguridad. 
    # El backend lo buscará en la base de datos.

# 2. Esquema de la Cotización completa que envía el celular
class CotizacionCreate(BaseModel):
    cliente_nombre: str
    usuario_id: int # Simularemos que el vendedor ya inició sesión y manda su ID
    detalles: List[CotizacionDetalleCreate]

# 3. Esquema de respuesta (Lo que le devolvemos al celular tras guardar)
class CotizacionResponse(BaseModel):
    id: int
    cliente_nombre: str
    
    class Config:
        from_attributes = True