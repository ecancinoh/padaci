-- PADACI – Script de creación de base de datos MySQL
-- Ejecuta esto en MySQL Workbench o terminal MySQL antes de realizar las migraciones

CREATE DATABASE IF NOT EXISTS padaci_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Opcional: crear usuario dedicado (cambia la contraseña)
-- CREATE USER 'padaci_user'@'localhost' IDENTIFIED BY 'TuContraseña123!';
-- GRANT ALL PRIVILEGES ON padaci_db.* TO 'padaci_user'@'localhost';
-- FLUSH PRIVILEGES;

USE padaci_db;
SELECT 'Base de datos padaci_db creada correctamente.' AS mensaje;
