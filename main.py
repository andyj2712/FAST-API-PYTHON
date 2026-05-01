from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fpdf import FPDF 
from sqlalchemy.orm import Session
import models
import schemas
from database import engine, SessionLocal

# Creamos las tablas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Cotizaciones",
    description="Backend con FastAPI y SQLAlchemy"
)

# --- CONFIGURACIÓN CORS ---
# Aquí le decimos a FastAPI qué aplicaciones externas tienen permiso de conectarse
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción aquí pondrías el dominio de tu app, por ahora permitimos todos ("*")
    allow_credentials=True,
    allow_methods=["*"], # Permite POST, GET, PUT, DELETE, etc.
    allow_headers=["*"],
)

# Dependencia: Esto es como la Inyección de Dependencias en Laravel.
# Nos abre una conexión a la base de datos por cada petición y la cierra al terminar.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- RUTAS DE PRODUCTOS ---

@app.post("/productos/", response_model=schemas.Producto)
def crear_producto(producto: schemas.ProductoCreate, db: Session = Depends(get_db)):
    # 1. Armamos el modelo de SQLAlchemy con los datos validados de Pydantic
    db_producto = models.Producto(**producto.model_dump())
    
    # 2. Lo guardamos en la base de datos (Equivalente a $producto->save())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    
    # 3. Lo devolvemos al frontend
    return db_producto

@app.get("/productos/", response_model=list[schemas.Producto])
def listar_productos(db: Session = Depends(get_db)):
    # Equivalente a Producto::all() en Eloquent
    productos = db.query(models.Producto).all()
    return productos

@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    # Buscamos el producto
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    # Lo eliminamos y guardamos cambios
    db.delete(producto)
    db.commit()
    
    return {"mensaje": "Producto eliminado correctamente"}

# --- RUTAS DE COTIZACIONES ---

@app.post("/cotizaciones/", response_model=schemas.CotizacionResponse)
def crear_cotizacion(cotizacion: schemas.CotizacionCreate, db: Session = Depends(get_db)):
    
    # 1. Guardamos la "Cabecera" de la cotización
    db_cotizacion = models.Cotizacion(
        cliente_nombre=cotizacion.cliente_nombre,
        usuario_id=cotizacion.usuario_id
    )
    db.add(db_cotizacion)
    db.commit()
    db.refresh(db_cotizacion) # Recargamos para obtener el ID recién creado

    # 2. Recorremos el array de repuestos/servicios que nos mandó el frontend
    for detalle in cotizacion.detalles:
        precio_actual = 0.0
        
        # Si es un repuesto (producto)
        if detalle.producto_id:
            # Buscamos el producto en la BD (Equivalente a Producto::find($id))
            prod = db.query(models.Producto).filter(models.Producto.id == detalle.producto_id).first()
            if not prod:
                raise HTTPException(status_code=404, detail=f"El repuesto con ID {detalle.producto_id} no existe")
            precio_actual = prod.precio_unitario
            
        # (Aquí luego puedes agregar el mismo 'if' pero para servicio_id)

        # Guardamos la fila en la tabla detalle, "congelando" el precio histórico
        db_detalle = models.CotizacionDetalle(
            cotizacion_id=db_cotizacion.id,
            producto_id=detalle.producto_id,
            servicio_id=detalle.servicio_id,
            cantidad=detalle.cantidad,
            precio_unitario_historico=precio_actual
        )
        db.add(db_detalle)
    
    # Guardamos todos los detalles en la base de datos
    db.commit()
    
    return db_cotizacion

# --- RUTAS DE USUARIOS ---

@app.post("/usuarios/", response_model=schemas.UsuarioResponse)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    # Simulación de encriptación rápida para la prueba
    fake_hashed_password = usuario.password + "_fakehash"
    
    db_usuario = models.Usuario(
        username=usuario.username,
        password_hash=fake_hashed_password
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    
    return db_usuario

@app.get("/cotizaciones/{cotizacion_id}/pdf")
def descargar_pdf_cotizacion(cotizacion_id: int, db: Session = Depends(get_db)):
    
    # 1. Buscamos la cabecera de la cotización
    cotizacion = db.query(models.Cotizacion).filter(models.Cotizacion.id == cotizacion_id).first()
    
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    # 2. Empezamos a armar el PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Configurar fuente
    pdf.set_font("helvetica", "B", 16)
    
    # Título principal
    pdf.cell(0, 10, "COTIZACIÓN DE PRODUCTOS Y SERVICIOS", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5) # Salto de línea
    
    # Datos del cliente y fecha
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"Cliente: {cotizacion.cliente_nombre}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Fecha: {cotizacion.fecha_generacion.strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)

    # 3. Encabezado de la tabla de detalles
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(80, 10, "Descripción", border=1)
    pdf.cell(30, 10, "Cant.", border=1, align="C")
    pdf.cell(40, 10, "Precio Unit.", border=1, align="C")
    pdf.cell(40, 10, "Subtotal", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

    # 4. Llenar la tabla con los detalles
    pdf.set_font("helvetica", "", 12)
    total_cotizacion = 0.0

    # Buscamos los detalles relacionados a esta cotización
    detalles = db.query(models.CotizacionDetalle).filter(models.CotizacionDetalle.cotizacion_id == cotizacion_id).all()

    for detalle in detalles:
        # Por ahora asumimos que es un repuesto para simplificar
        # Buscamos el nombre del producto en la base de datos
        producto = db.query(models.Producto).filter(models.Producto.id == detalle.producto_id).first()
        nombre_item = producto.nombre if producto else "Item desconocido"
        
        subtotal = detalle.cantidad * detalle.precio_unitario_historico
        total_cotizacion += subtotal
        
        pdf.cell(80, 10, nombre_item, border=1)
        pdf.cell(30, 10, str(detalle.cantidad), border=1, align="C")
        pdf.cell(40, 10, f"${detalle.precio_unitario_historico:.2f}", border=1, align="C")
        pdf.cell(40, 10, f"${subtotal:.2f}", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

    # 5. Fila del Total
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(150, 10, "TOTAL", border=1, align="R")
    pdf.cell(40, 10, f"${total_cotizacion:.2f}", border=1, align="C")

    # 6. Generar el archivo y enviarlo al navegador
    pdf_bytes = bytes(pdf.output())
    
    return Response(
        content=pdf_bytes, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"inline; filename=cotizacion_{cotizacion_id}.pdf"}
    )