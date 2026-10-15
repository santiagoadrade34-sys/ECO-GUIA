-- 1. CREACIÓN E INICIALIZACIÓN DE LA BASE DE DATOS
DROP DATABASE IF EXISTS shirry_studios_db_;
CREATE DATABASE shirry_studios_db_;
USE shirry_studios_db_;

-- 2. TABLA DE USUARIOS (Actualizada exactamente como tu última imagen)
ALTER TABLE usuarios 
ADD COLUMN telefono VARCHAR(20) NOT NULL,
ADD COLUMN fecha_nacimiento DATE NOT NULL,
ADD COLUMN ciudad VARCHAR(100) NOT NULL,
ADD COLUMN direccion TEXT NOT NULL,
ADD COLUMN intentos_fallidos INT DEFAULT 0,
ADD COLUMN fecha_ultimo_fallo DATETIME NULL,
ADD COLUMN rol ENUM('usuario', 'admin') DEFAULT 'usuario';


-- 3. TABLA DE PRODUCTOS GLOBALES (SHIRRY INTERACTIVE INVENTORY)
DROP TABLE IF EXISTS productos;

CREATE TABLE productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL, -- ej. 'Hoodies', 'Pantalones'
    coleccion VARCHAR(100) NOT NULL, -- ej. 'SS26 Core'
    precio INT NOT NULL,
    talla VARCHAR(20) NOT NULL, -- 🌟 ¡AQUÍ ESTÁ LA MAGIA! ej. 'L', '32', 'Única'
    estado VARCHAR(20) DEFAULT 'Activo', -- 'Activo' o 'Agotado'
    imagen VARCHAR(255) NOT NULL, -- ej. 'camiseta-blanca.webp'
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA DE TOKENS TEMPORALES (SISTEMA DE SEGURIDAD RECUPERAR ACCESO)
CREATE TABLE recuperacion_claves (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    codigo_token VARCHAR(10) NOT NULL,
    fecha_creacion DATETIME NOT NULL,
    expirado BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

