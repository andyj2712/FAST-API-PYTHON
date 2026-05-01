from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

# 1. Tabla de Usuarios
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String) # Nunca guardamos la contraseña en texto plano
    
    # Relación: Un usuario puede crear muchas cotizaciones
    cotizaciones = relationship("Cotizacion", back_populates="creador")


# 2. Tabla de Productos (Repuestos)
class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    numero_pieza = Column(String, index=True, nullable=True) # Sugerencia añadida
    marca = Column(String)
    modelo = Column(String)
    año = Column(Integer)
    precio_unitario = Column(Float)


# 3. Tabla de Servicios
class Servicio(Base):
    __tablename__ = "servicios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    tipo = Column(String)
    tiempo_estimado_horas = Column(Float)
    precio = Column(Float)


# 4. Tabla de Cotizaciones (La cabecera del PDF)
class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id = Column(Integer, primary_key=True, index=True)
    cliente_nombre = Column(String, index=True)
    fecha_generacion = Column(DateTime, default=datetime.datetime.utcnow)
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    
    creador = relationship("Usuario", back_populates="cotizaciones")
    detalles = relationship("CotizacionDetalle", back_populates="cotizacion")


class CotizacionDetalle(Base):
    __tablename__ = "cotizacion_detalles"

    id = Column(Integer, primary_key=True, index=True)
    cotizacion_id = Column(Integer, ForeignKey("cotizaciones.id"))
    
    # Hacemos que puedan ser nulos (nullable=True) porque una línea de la cotización 
    # será de un producto O de un servicio, rara vez de ambos a la vez.
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=True)
    servicio_id = Column(Integer, ForeignKey("servicios.id"), nullable=True)
    
    cantidad = Column(Integer, default=1)
    
    # EL TRUCO: Guardamos el precio histórico para congelarlo en el PDF
    precio_unitario_historico = Column(Float)
    
    # Relación inversa hacia la cabecera de la cotización
    cotizacion = relationship("Cotizacion", back_populates="detalles")

