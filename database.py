from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Aquí le decimos que cree un archivo llamado 'cotizaciones.db' en la raíz
SQLALCHEMY_DATABASE_URL = "sqlite:///./cotizaciones.db"

# Configuramos el motor de la base de datos
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Creamos la "sesión" (como la conexión activa)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para crear nuestros modelos (equivalente a extender de Model en Laravel)
Base = declarative_base()