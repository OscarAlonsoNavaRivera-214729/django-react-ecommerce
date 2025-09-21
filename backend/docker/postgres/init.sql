-- =============================================================================
-- PostgreSQL Initialization Script
-- =============================================================================
-- Extensiones utilis para un e-commerce
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Configuraciones de performance para desarrollo
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 0;

-- Reload configuration
SELECT pg_reload_conf();

-- Crear database adicional para testing (opcional)
CREATE DATABASE ecommerce_test OWNER ecommerce_user;
