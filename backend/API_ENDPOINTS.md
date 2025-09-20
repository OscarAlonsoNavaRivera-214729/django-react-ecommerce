# =============================================================================
# E-COMMERCE API ENDPOINTS DOCUMENTATION
# =============================================================================
# STATUS: Vendor endpoints completamente implementados
# PURPOSE: Documentación completa de todos los endpoints disponibles
# BUSINESS LOGIC: Organización por audiencia y funcionalidad
# NEXT STEPS: Implementar customer y admin endpoints
# =============================================================================

## VENDOR ENDPOINTS (Completamente implementados)

### Gestión Básica de Productos

**1. Lista de productos del vendor**
```
GET /api/products/vendor/
Query params opcionales:
- status: draft|pending|active|inactive|rejected
- category: {category_id}
- search: {término_búsqueda}
- page: {número_página}
- page_size: {productos_por_página}

Response: Lista paginada con estadísticas del vendor
```

**2. Crear nuevo producto**
```
POST /api/products/vendor/create/
Body: {
  "name": "Nombre del producto",
  "description": "Descripción del producto",
  "price": "99.99",
  "stock": 100,
  "category_id": 1,
  "brand_id": 2 (opcional)
}

Response: Producto creado en estado 'draft'
```

**3. Detalle de producto**
```
GET /api/products/vendor/{product_id}/

Response: Información completa incluyendo estado de moderación
```

**4. Actualizar producto**
```
PUT/PATCH /api/products/vendor/{product_id}/update/
Body: Campos a actualizar (mismo formato que crear)

Restricción: Solo productos en estado 'draft' o 'rejected'
```

### Gestión de Imágenes

**5. Agregar imagen al producto**
```
POST /api/products/vendor/{product_id}/images/
Body: {
  "image_url": "https://ejemplo.com/imagen.jpg",
  "alt_text": "Texto alternativo",
  "order": 1
}

Nota: La primera imagen se marca automáticamente como primaria
```

**6. Eliminar imagen**
```
DELETE /api/products/vendor/{product_id}/images/{image_id}/delete/

Nota: Si elimina la imagen primaria, se asigna otra automáticamente
```

**7. Establecer imagen primaria**
```
POST /api/products/vendor/{product_id}/images/{image_id}/set-primary/

Nota: Desmarca todas las demás como no primarias
```

### Workflow de Estados

**8. Enviar producto para aprobación**
```
POST /api/products/vendor/{product_id}/submit/

Validaciones:
- Debe estar en estado 'draft'
- Debe tener al menos una imagen
- Descripción no puede estar vacía
- Precio debe ser > 0
- Stock debe ser >= 0

Resultado: Cambia estado a 'pending' para moderación admin
```

## USER ENDPOINTS (Ya implementados previamente)

```
POST /api/users/register/          - Registro de usuario
POST /api/users/login/             - Login de usuario  
POST /api/users/logout/            - Logout de usuario
GET  /api/users/profile/           - Perfil de usuario
PUT  /api/users/profile/update/    - Actualizar perfil
```

## CUSTOMER ENDPOINTS (Próximos a implementar)

```
GET /api/products/                 - Lista pública de productos activos
GET /api/products/categories/      - Lista de categorías
GET /api/products/{slug}/          - Detalle público de producto
GET /api/products/brands/          - Lista de marcas
GET /api/products/search/          - Búsqueda avanzada de productos
```

## ADMIN ENDPOINTS (Próximos a implementar)

```
GET  /api/products/admin/products/           - Lista todos los productos
POST /api/products/admin/products/{id}/approve/  - Aprobar producto
POST /api/products/admin/products/{id}/reject/   - Rechazar producto
GET  /api/products/admin/vendors/            - Lista vendedores
POST /api/products/admin/vendors/{id}/verify/    - Verificar vendedor
```

## CÓDIGOS DE ESTADO Y PERMISOS

### Autenticación requerida:
- Todos los endpoints vendor requieren JWT token
- Solo usuarios con rol 'vendor' pueden acceder
- Solo vendors verificados pueden crear productos
- Solo pueden gestionar SUS propios productos

### Estados de producto:
- **draft**: Borrador, puede editarse
- **pending**: En revisión, solo admin puede cambiar
- **active**: Aprobado y visible públicamente
- **inactive**: Desactivado por admin
- **rejected**: Rechazado, puede volver a editarse

### Códigos HTTP:
- 200: Éxito
- 201: Creado exitosamente
- 400: Error de validación
- 403: Sin permisos
- 404: No encontrado
- 500: Error del servidor