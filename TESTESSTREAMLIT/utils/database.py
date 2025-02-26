import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
#from sqlalchemy.ext.declarative import 
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# Configuração do banco de dados SQLite
DATABASE_URL = "sqlite:///power_bi_admin.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modelos do banco de dados
class Empresa(Base):
    __tablename__ = "empresas"  # Corrigido para __tablename__

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    client_id = Column(String, nullable=False)
    client_secret = Column(String, nullable=False)
    tenant_id = Column(String, nullable=False)
    workspace_id = Column(String, nullable=False)

class Relatorio(Base):
    __tablename__ = "relatorios"  # Corrigido para __tablename__

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    report_id = Column(String, nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"))

    empresa = relationship("Empresa", back_populates="relatorios")

Empresa.relatorios = relationship("Relatorio", order_by=Relatorio.id, back_populates="empresa")

# Criação do banco de dados
Base.metadata.create_all(bind=engine)
