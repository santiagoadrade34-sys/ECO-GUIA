import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_session import Session
import mysql.connector
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

# Llave secreta obligatoria para las sesiones de usuarios y carrito
app.secret_key = 'shirry_secret_key_core_2026'

# =========================================================================
# CONFIGURACIÓN DE LA BASE DE DATOS MAESTRA
# =========================================================================
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'mysql',  # ← Se pone UNA SOLA VEZ aquí
    'database': 'shirry_studios_db'
}

def get_db_connection():
    """Función única que alimenta a todo el sistema."""
    return mysql.connector.connect(**db_config)

# =========================================================================
# CONFIGURACIÓN DE SESIONES PERMANENTES
# =========================================================================
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


# =========================================================================
# 1. RUTAS PÚBLICAS DE NAVEGACIÓN BASE
# =========================================================================

@app.route('/')
def inicio():
    """Página de inicio (index) que inyecta automáticamente las prendas de lanzamiento."""
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)
    
    # Consultamos solo las prendas activas destinadas a Eutanasia
    cursor.execute("SELECT * FROM productos WHERE LOWER(estado) = 'activo' AND LOWER(coleccion) = 'eutanasia'")
    productos_lanzamiento = cursor.fetchall()
    
    cursor.close()
    conexion.close()
    
    # ENVIAMOS LOS DATOS: Apunta a tu index.html pasándole la lista
    return render_template('index.html', productos_nuevos=productos_lanzamiento)

@app.route('/index')
def index():
    """Redirección de seguridad por si algún menú viejo llama a 'index'"""
    # BLINDAJE DIRECTO: Redirigimos a la raíz '/' como texto plano para evitar caídas de url_for
    return redirect('/')


@app.route('/coleccion-nueva')
def coleccion_nueva():
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    # 🚀 MÁGIA DINÁMICA: Trae de MySQL solo las prendas activas asignadas a Eutanasia
    cursor.execute("SELECT * FROM productos WHERE estado = 'Activo' AND coleccion = 'eutanasia'")
    productos_coleccion = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template('coleccion-nueva.html', productos_nuevos=productos_coleccion)


@app.route('/perfil')
def perfil():
    """Ruta protegida para desplegar el panel de control del usuario autenticado."""
    # 1. CORREGIDO: Buscamos la variable exacta de tu sesión local 'usuario_id'
    if not session.get('usuario_id'):
        flash("🔒 Identificación requerida. Por favor inicie sesión para acceder al panel.", "warning")
        return redirect('/login')

    # Capturamos las variables nativas directamente como las maneja tu sistema
    id_usuario = session.get('usuario_id')

    # 2. Conectamos con Laragon para traer los datos limpios en tiempo real
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    try:
        # 🌟 CORREGIDO: Cambiamos 'correo' por 'email' para que coincida con tu tabla real usuarios
        query_usuario = "SELECT id, nombre, email FROM usuarios WHERE id = %s"
        cursor.execute(query_usuario, (id_usuario,))
        usuario_db = cursor.fetchone()

        if not usuario_db:
            # Si no existe en la base de datos, limpiamos la sesión por seguridad
            session.clear()
            flash("La cuenta no coincide con los registros activos.", "danger")
            return redirect('/login')

        # Consulta para el historial de drops comprados por este operador
        query_ordenes = "SELECT id, fecha, total, estado FROM ordenes WHERE id_usuario = %s ORDER BY fecha DESC"
        cursor.execute(query_ordenes, (id_usuario,))
        historial_ordenes = cursor.fetchall()

    except Exception as e:
        print(f"❌ [SHIRRY CORE ERROR]: Error en el módulo de perfil: {str(e)}")
        # Datos de respaldo usando lo que tienes guardado en tus cookies del Navbar
        # 🌟 CORREGIDO: Cambiamos la llave 'correo' por 'email' para mantener simetría
        usuario_db = {
            'id': id_usuario,
            'nombre': session.get('usuario_nombre', 'OPERADOR CORE'),
            'email': session.get('usuario_email', 'desconectado@shirrycore.com')
        }
        historial_ordenes = []
    finally:
        cursor.close()
        conexion.close()

    # 3. Renderizamos pasando los diccionarios limpios de MySQL
    return render_template('perfil.html', usuario=usuario_db, ordenes=historial_ordenes)



@app.route('/login') 
def login():
    # LIMPIEZA DE RESIDUOS DE RECUPERACIÓN AL VOLVER AL LOGIN
    session.pop('recuperar_user_id', None)
    session.pop('recuperar_paso', None)
    
    return render_template('login.html') # Tu render normal


@app.route('/recuperar')
def recuperar_vista():
    # Si no hay paso definido, iniciamos por defecto en el Paso 1
    if 'recuperar_paso' not in session:
        session['recuperar_paso'] = 1
    return render_template('recuperar.html')



# PASO 1: ENVIAR SOLICITUD DE RECUPERACIÓN
@app.route('/recuperar/paso1', methods=['POST'])
def recuperar_paso1():
    email = request.form['email']
    
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
    usuario = cursor.fetchone()
    
    if not usuario:
        cursor.close()
        conexion.close()
        flash("Código de error: 0x404 - Correo no registrado.", "error")
        return redirect(url_for('recuperar_vista'))
        
    token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    now = datetime.now()
    
    cursor.execute("""
        INSERT INTO recuperacion_claves (usuario_id, codigo_token, fecha_creacion)
        VALUES (%s, %s, %s)
    """, (usuario['id'], token, now))
    conexion.commit()
    
    cursor.close()
    conexion.close()
    
    print(f"\n[SHIRRY-SECURITY] TOKEN GENERADO PARA {email}: >>> {token} <<<\n")
    
    session['recuperar_user_id'] = usuario['id']
    session['recuperar_paso'] = 2
    
    flash("CÓDIGO DE ACCESO GENERADO. Revisa tu terminal local.", "success")
    return redirect(url_for('recuperar_vista'))

# PASO 2: VERIFICAR EL TOKEN DE ACCESO
@app.route('/recuperar/paso2', methods=['POST'])
def recuperar_paso2():
    token_ingresado = request.form['token'].strip().upper()
    usuario_id = session.get('recuperar_user_id')
    
    if not usuario_id:
        return redirect(url_for('login'))
        
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT * FROM recuperacion_claves 
        WHERE usuario_id = %s AND expirado = FALSE 
        ORDER BY id DESC LIMIT 1
    """, (usuario_id,))
    registro_token = cursor.fetchone()
    
    if not registro_token or registro_token['codigo_token'] != token_ingresado:
        cursor.close()
        conexion.close()
        flash("Código de error: 0x403 - Token inválido o corrupto.", "error")
        return redirect(url_for('recuperar_vista'))
        
    from datetime import timedelta
    tiempo_limite = registro_token['fecha_creacion'] + timedelta(minutes=15)
    if datetime.now() > tiempo_limite:
        cursor.execute("UPDATE recuperacion_claves SET expirado = TRUE WHERE id = %s", (registro_token['id'],))
        conexion.commit()
        cursor.close()
        conexion.close()
        flash("Código de error: 0x410 - El token ha expirado. Solicita uno nuevo.", "error")
        return redirect(url_for('recuperar_vista'))
        
    session['recuperar_paso'] = 3
    cursor.close()
    conexion.close()
    return redirect(url_for('recuperar_vista'))

# PASO 3: ESTABLECER NUEVA CLAVE
@app.route('/recuperar/paso3', methods=['POST'])
def recuperar_paso3():
    nueva_clave = request.form['nueva_clave']
    usuario_id = session.get('recuperar_user_id')
    
    if not usuario_id or session.get('recuperar_paso') != 3:
        return redirect(url_for('login'))
        
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)
    
    nueva_clave_hash = generate_password_hash(nueva_clave)
    cursor.execute("UPDATE usuarios SET contrasena = %s WHERE id = %s", (nueva_clave_hash, usuario_id))
    cursor.execute("UPDATE recuperacion_claves SET expirado = TRUE WHERE usuario_id = %s", (usuario_id,))
    conexion.commit()
    
    cursor.close()
    conexion.close()
    
    session.pop('recuperar_user_id', None)
    session.pop('recuperar_paso', None)
    
    flash("SISTEMA ACTUALIZADO: Contraseña reestablecida correctamente.", "success")
    return redirect(url_for('login'))


@app.route('/nosotros')
def nosotros():
    """
    Ruta GET: Renderiza de forma directa la vista estática del Manifiesto de Marca
    sin requerir consultas pesadas a la base de datos de Laragon.
    """
    return render_template('nosotros.html')


@app.route('/core-mining')
def core_mining():
    """
    Ruta GET: Renderiza de forma asíncrona la sala de hackeo y minijuego clicker
    para fidelizar al operador mediante recompensas tácticas.
    """
    return render_template('clicker.html')


@app.route('/contacto')
def contacto():
    return render_template('contacto.html')

@app.route('/blog')
def blog():
    """Declarada para evitar BuildError en el menú lateral"""
    return render_template('blog.html')

# =========================================================================
# 2. VISTA DINÁMICA DE LA TIENDA (FUSIONADA CON TU CÓDIGO ANTIGUO)
# =========================================================================

@app.route('/shop')
def shop():
    """Ruta central del catálogo. Realiza la consulta a MySQL en base a los filtros."""
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    # Capturamos los parámetros de la URL enviados por tus controles y JavaScript
    categoria_filtro = request.args.get('cat', '').strip().lower()
    precio_filtro = request.args.get('max_precio', '15000000').strip() # Ampliado el rango por defecto
    busqueda_filtro = request.args.get('q', '').strip().lower()

    # Convertimos el precio a entero de forma segura para evitar quiebres
    try:
        max_precio = int(precio_filtro)
    except ValueError:
        max_precio = 15000000

    # Consulta base adaptada a la estructura real de tu base de datos local
    query = "SELECT * FROM productos WHERE precio <= %s"
    params = [max_precio]

    # Si el usuario seleccionó una categoría específica
    if categoria_filtro and categoria_filtro != 'todos':
        query += " AND LOWER(categoria) = %s"
        params.append(categoria_filtro)

    # Si el usuario escribió un texto en la barra de búsqueda compacta
    if busqueda_filtro:
        query += " AND (LOWER(nombre) LIKE %s OR LOWER(categoria) LIKE %s OR LOWER(id) LIKE %s)"
        params.append(f"%{busqueda_filtro}%")
        params.append(f"%{busqueda_filtro}%")
        params.append(f"%{busqueda_filtro}%")

    # ==========================================================================
    # 🚀 AÑADIDO: CAPTURAR EL PARÁMETRO DE ORDENAMIENTO DE TU MENÚ CYBERPUNK
    # ==========================================================================
    criterio_orden = request.args.get('ordenar', 'recientes').strip().lower()

    if criterio_orden == 'precio-bajo':
        query += " ORDER BY precio ASC"
    elif criterio_orden == 'precio-alto':
        query += " ORDER BY precio DESC"
    elif criterio_orden == 'mas-vendidos':
        query += " ORDER BY id ASC"
    else:
        # Usa la columna real de tu base de datos para ordenar de lo más nuevo a lo más viejo
        query += " ORDER BY fecha_creacion DESC"


    try:
        # Ejecutamos la consulta purificada de MySQL
        cursor.execute(query, tuple(params))
        productos = cursor.fetchall()
    except Exception as e:
        print(f"[MYSQL ERROR]: Error al leer el catálogo completo: {e}")
        productos = []
    finally:
        cursor.close()
        conexion.close()

    # 🚀 SI LA PETICIÓN ES ASÍNCRONA (FETCH JS): Devolvemos solo la grilla limpia al vuelo
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('shop.html', productos=productos, current_sort=criterio_orden)
        
    # Si entran normal escribiendo la URL, carga la página completa como siempre
    return render_template('shop.html', productos=productos, current_sort=criterio_orden)


# 🔥 EL DOBLE BLINDAJE: Flask ahora aceptará la ruta larga y la corta al mismo tiempo
@app.route('/shop/product/<id_producto>')
@app.route('/producto/<id_producto>')
def detalle_producto(id_producto):
    """Ruta dinámica para visualizar la ficha técnica de una prenda específica."""
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True) # dictionary=True para extraer por nombre de columna
    
    try:
        # Buscamos de forma exacta el producto por su ID string (ej: DGSDBGVS)
        query = "SELECT * FROM productos WHERE id = %s"
        cursor.execute(query, (id_producto,))
        producto = cursor.fetchone()

        # Si el usuario digita un ID en la URL que no existe, regresa a la tienda
        if not producto:
            flash("La prenda solicitada no se encuentra disponible en los drops actuales.", "warning")
            return redirect('/shop')

    except Exception as e:
        print(f"[MYSQL ERROR]: Error al cargar la ficha del producto: {e}")
        return redirect('/shop')
    finally:
        cursor.close()
        conexion.close()

    # Renderizamos la nueva plantilla enviándole la información del artículo encontrado
    return render_template('product_detail.html', producto=producto)


@app.route('/api/producto/<int:producto_id>', methods=['GET'])
def obtener_producto_api(producto_id):
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM productos WHERE id = %s", (producto_id,))
    producto = cursor.fetchone()
    
    cursor.close()
    conexion.close()
    
    if not producto:
        # Usamos jsonify directamente porque ya está dentro de tu import global de Flask
        return jsonify({"error": "SYSTEM_ERR // Producto no localizado"}), 404
        
    return jsonify(producto)
    

# =========================================================================
# 3. RUTAS PROTEGIDAS / PRIVADAS
# =========================================================================

@app.route('/probador')
def probador():
    """Ruta que carga el probador virtual consultando las prendas en MySQL."""
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Consultamos todos los productos de la tienda
        query = "SELECT * FROM productos"
        cursor.execute(query)
        todos_los_productos = cursor.fetchall()
        
        # 🧠 Separamos los productos por categorías en listas limpias para el frontend
        prendas_superiores = [p for p in todos_los_productos if p.get('categoria', '').lower() in ['camisas', 'camisetas', 'hoodies', 'blusas']]
        pantalones = [p for p in todos_los_productos if p.get('categoria', '').lower() in ['pantalones', 'jeans', 'cargos']]
        calzado = [p for p in todos_los_productos if p.get('categoria', '').lower() in ['calzado', 'zapatillas', 'botas']]
        
    except Exception as e:
        print(f"[MYSQL ERROR]: Error al cargar datos para el probador: {e}")
        prendas_superiores, pantalones, calzado = [], [], []
    finally:
        cursor.close()
        conexion.close()
        
    # Renderizamos la plantilla enviándole las tres listas dinámicas
    return render_template(
        'probador.html', 
        tops=prendas_superiores, 
        bottoms=pantalones, 
        shoes=calzado
    )


# =========================================================================
#5. CONTROL MÁSTER: PANEL DE ADMINISTRACIÓN INTERACTIVO (SHIRRY OFFICIAL)
# =========================================================================

@app.route('/shirry-admin', methods=['GET', 'POST'])
@app.route('/shirry-admin/<seccion_activa>', methods=['GET', 'POST'])
def admin_dashboard(seccion_activa="productos"):

    # 1. VALIDACIÓN DE SEGURIDAD ESTRICTA
    if 'usuario_email' not in session or session['usuario_email'] != 'admin@shirrystudios.com':
        flash("Acceso denegado.", "error")
        return redirect(url_for('login'))

    seccion = request.args.get('seccion', seccion_activa)

    # 2. CONEXIÓN FRESCA A MYSQL EN LARAGON (Corregido a tu función oficial)
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    lista_productos = []
    lista_usuarios = []
    lista_mensajes = []

    try:
        # Consulta 1: Productos reales
        cursor.execute("SELECT * FROM productos")
        lista_productos = cursor.fetchall()

        # Consulta 2: Usuarios
        cursor.execute("SELECT * FROM usuarios")
        lista_usuarios = cursor.fetchall()

        # Consulta 3: Mensajes
        try:
            cursor.execute("SELECT * FROM mensajes")
            lista_mensajes = cursor.fetchall()
        except Exception:
            lista_mensajes = []

    except Exception as e:
        print(f"Error general al leer los datos de MySQL en Laragon: {str(e)}")
    finally:
        cursor.close()
        conexion.close()

    # 3. RENDERIZADO CON SOPORTE COMPLETO PARA TU JINJA ORIGINAL
    return render_template(
        'admin_dashboard.html',  # <--- CAMBIA ESTO: Asegúrate de que sea tu archivo HTML real
        seccion=seccion,
        seccion_activa=seccion,
        productos=lista_productos,
        usuarios=lista_usuarios,       # Para {% for user in usuarios %}
        usuarios_lista=lista_usuarios, # Soporte por si el HTML busca usuarios_lista
        mensajes=lista_mensajes
    )




# =========================================================================
# 🚀 NUEVA RUTA CORE: GUARDAR PRENDA EN MYSQL SIN ERRORES DE COLUMNAS
# =========================================================================

@app.route('/shirry-admin/add-product', methods=['POST'])
def guardar_nuevo_producto():
    if 'usuario_email' not in session or session['usuario_email'] != 'admin@shirrystudios.com':
        flash("Acceso denegado.", "error")
        return redirect(url_for('login'))

    # Captura segura de datos (Tolerante a nombres en inglés y español)
    prod_id = request.form.get('product_id') or request.form.get('id_producto')
    prod_id = prod_id.strip().upper() if prod_id else None

    nombre = request.form.get('nombre') or request.form.get('productName') or "Prenda Streetwear"
    categoria = request.form.get('categoria') or request.form.get('productCategory') or "camisetas"
    estado = request.form.get('estado') or request.form.get('productStatus') or "Activo"
    coleccion_tag = request.form.get('coleccion') or request.form.get('productCollection') or "regular"

    precio_raw = request.form.get('precio') or request.form.get('productPrice')
    try:
        precio = float(precio_raw) if precio_raw else 0
    except ValueError:
        precio = 0

    # Procesar archivo multimedia de forma segura
    file = request.files.get('imagen_archivo') or request.files.get('productImage')
    filename = 'default_prenda.webp'

    if file and file.filename != '':
        from werkzeug.utils import secure_filename
        # 🌟 CORREGIDO: Dejamos el nombre del archivo original limpio sin pegarle el prod_id adelante
        filename = secure_filename(file.filename)
        
        # Aseguramos la ruta física en la carpeta static
        ruta_guardado = os.path.join(app.root_path, 'static', 'imagenes', 'productos')
        os.makedirs(ruta_guardado, exist_ok=True)
        
        # Creamos la ruta completa para verificar si el archivo ya vive en la carpeta
        ruta_completa_archivo = os.path.join(ruta_guardado, filename)
        
        # 🌟 REUTILIZACIÓN INTELIGENTE: Si la foto ya existe, NO la guardes físicamente otra vez
        if os.path.exists(ruta_completa_archivo):
            print(f"ℹ️ La imagen '{filename}' ya existe en el servidor. Reutilizando archivo existente.")
        else:
            # Solo si es una imagen nueva de verdad que nunca habías subido, se guarda en disco
            file.save(ruta_completa_archivo)


    # Si no hay ID, cancelamos de forma limpia sin bloquear la BD
    if not prod_id:
        flash("Error: El ID del producto es obligatorio.", "danger")
        return redirect('/shirry-admin?seccion=productos')

    # Abrimos la conexión de forma controlada
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    try:
        # 1. Validar si el ID visual ya existe para no colisionar lógica del negocio
        # Nota: Si usas la columna 'id' de la BD como tu serial visual (PROD-101), cámbiala en el WHERE.
        # Si tu tabla real 'productos' NO tiene columna llamada 'id_visual' o similar, puedes omitir esta validación.
        
        # 2. CAPTURA DE TALLAS: Procesa las casillas múltiples del frontend
        tallas_lista = request.form.getlist('tallas') or request.form.getlist('productSizes')
        tallas_string = ", ".join(tallas_lista) if tallas_lista else "UNICA"

        # 3. Inserción limpia alineada a tu archivo .sql real
        query = """
            INSERT INTO productos (nombre, categoria, precio, estado, imagen, coleccion, talla)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """


        # Estricta correspondencia posicional con los 7 marcadores %s del query definitivo
        valores = (nombre, categoria, precio, estado, filename, coleccion_tag, tallas_string)

        cursor.execute(query, valores)
        conexion.commit()
        flash("Producto inyectado con éxito en el sistema.", "success")

    except Exception as e:
        conexion.rollback()
        print(f"❌ Error crítico en la transacción de MySQL: {str(e)}")
        flash("Error interno al guardar en la base de datos.", "danger")
    finally:
        # 🔥 EL BLINDAJE INQUEBRANTABLE: Cerramos TODO pase lo que pase
        cursor.close()
        conexion.close()

    return redirect('/shirry-admin?seccion=productos')



# =========================================================================
# 4. RUTAS DE DEPURACIÓN CRÍTICA EN UN CLIC
# =========================================================================
# =========================================================================
# 👤 CONTROLADOR 1: ELIMINAR USUARIOS (Mantiene tu código original)
# =========================================================================
@app.route('/admin_delete_user/<int:id_usuario>', methods=['POST'])
def admin_delete_user(id_usuario):
    if session.get('usuario_email') == 'admin@shirrystudios.com':
        conexion = get_db_connection()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (id_usuario,))
        conexion.commit()
        cursor.close()
        conexion.close()
        flash(f"Cuenta #{id_usuario} eliminada permanentemente.", "success")
        return redirect(url_for('admin_dashboard', seccion_activa='usuarios'))
    return redirect(url_for('inicio'))

# =========================================================================
# 👕 CONTROLADOR 2: ELIMINAR PRODUCTOS (La nueva ruta que faltaba)
# =========================================================================
import os

@app.route('/shirry-admin/delete-product/<int:id_producto>', methods=['POST'])
def admin_delete_product(id_producto):
    if session.get('usuario_email') == 'admin@shirrystudios.com':
        conexion = get_db_connection()
        cursor = conexion.cursor()

        try:
            # 1. Ejecutamos la consulta para encontrar la prenda
            cursor.execute("SELECT imagen FROM productos WHERE id = %s", (id_producto,))
            producto = cursor.fetchone()

            # 🚀 CORREGIDO: Al usar un cursor normal, producto es una tupla. 
            # El primer campo seleccionado (imagen) está en la posición [0]
            if producto and producto[0]:
                nombre_imagen = producto[0]
                
                # Evitamos borrar la imagen por defecto
                if nombre_imagen != 'default_prenda.webp':
                    # Construimos la ruta física hacia tu carpeta de Laragon
                    ruta_archivo = os.path.join(app.root_path, 'static', 'imagenes', 'productos', nombre_imagen)
                    
                    # Si el archivo existe en Windows, lo borramos de raíz antes de tocar MySQL
                    if os.path.exists(ruta_archivo):
                        os.remove(ruta_archivo)
                        print(f"✅ Archivo físico eliminado con éxito: {ruta_archivo}")

            # 2. Una vez borrado el archivo, purgamos la fila de la base de datos
            cursor.execute("DELETE FROM productos WHERE id = %s", (id_producto,))
            conexion.commit()
            
            flash(f"Registro de prenda #{id_producto} purgado con éxito.", "success")

        except Exception as e:
            conexion.rollback()
            print(f"❌ Error crítico en borrado: {str(e)}")
            flash("Error interno al procesar el borrado en la base de datos.", "danger")
        finally:
            cursor.close()
            conexion.close()
            
        return redirect('/shirry-admin?seccion=productos')
        
    return redirect(url_for('inicio'))


# =========================================================================
# CONTROL MÁSTER: MODIFICACIÓN Y ACTUALIZACIÓN DE USUARIOS EN MYSQL
# =========================================================================
@app.route('/admin_update_user/<int:id_usuario>', methods=['POST'])
def admin_update_user(id_usuario):
    """Ruta protegida para actualizar la información de un cliente en tiempo real."""
    if session.get('usuario_email') == 'admin@shirrystudios.com':
        nuevo_nombre = request.form.get('nuevo_nombre').strip()
        nuevo_email = request.form.get('nuevo_email').strip()
        
        conexion = get_db_connection()
        cursor = conexion.cursor()
        try:
            # Ejecutamos la consulta UPDATE nativa de SQL
            query = "UPDATE usuarios SET nombre = %s, email = %s WHERE id = %s"
            cursor.execute(query, (nuevo_nombre, nuevo_email, id_usuario))
            conexion.commit()
            flash(f"Información del usuario #{id_usuario} actualizada con éxito.", "success")
        except Exception as e:
            conexion.rollback()
            flash(f"Error de actualización en MySQL: {e}", "error")
            
        cursor.close()
        conexion.close()
        return redirect(url_for('admin_dashboard', seccion_activa='usuarios'))
        
    return redirect(url_for('inicio'))

# =========================================================================
# CONTROL MÁSTER: MODIFICACIÓN Y ACTUALIZACIÓN DE PRODUCTOS 
# =========================================================================

@app.route('/admin_update_product/<id_producto>', methods=['POST'])
def admin_update_product(id_producto):
    # 1. Validación de seguridad idéntica a tus rutas estables
    if 'usuario_email' not in session or session['usuario_email'] != 'admin@shirrystudios.com':
        flash("Acceso denegado.", "error")
        return redirect(url_for('login'))

    # # 2. Capturar los nuevos datos ingresados en el formulario de edición
    nuevo_nombre = request.form.get('nuevo_nombre') or request.form.get('nombre')
    nueva_categoria = request.form.get('nueva_categoria') or request.form.get('categoria')
    nuevo_estado = request.form.get('nuevo_estado') or request.form.get('estado')
    nueva_coleccion = request.form.get('nueva_coleccion') or request.form.get('coleccion') or 'regular'

    # 🌟 NUEVO: Procesa las casillas múltiples (checkboxes) del formulario de edición
    tallas_lista = request.form.getlist('nuevas_tallas')
    talla_final = ", ".join(tallas_lista) if tallas_lista else "UNICA"

    nuevo_precio_raw = request.form.get('nuevo_precio') or request.form.get('precio')
    try:
        nuevo_precio = float(nuevo_precio_raw) if nuevo_precio_raw else 0
    except ValueError:
        nuevo_precio = 0

    conexion = get_db_connection()
    cursor = conexion.cursor()

    # # 3. Procesar si el administrador subió una nueva imagen para reemplazar la anterior
    file = request.files.get('nueva_imagen_archivo') or request.files.get('productImage')

    try:
        if file and file.filename != '':
            from werkzeug.utils import secure_filename
            # Generamos el nombre del nuevo archivo de manera segura
            filename = secure_filename(f"{id_producto}_{file.filename}")
            ruta_guardado = os.path.join(app.root_path, 'static', 'imagenes', 'productos')

            # # --- LIMPIEZA AUTOMÁTICA EN DISCO ---
            # Buscamos el nombre de la imagen vieja para no dejar basura en la carpeta
            cursor.execute("SELECT imagen FROM productos WHERE id = %s", (id_producto,))
            prenda_actual = cursor.fetchone()
            
            if prenda_actual and prenda_actual[0]:
                imagen_vieja = prenda_actual[0]
                if imagen_vieja != 'default_prenda.webp' and imagen_vieja != filename:
                    ruta_vieja = os.path.join(ruta_guardado, imagen_vieja)
                    if os.path.exists(ruta_vieja):
                        os.remove(ruta_vieja) # Borra la foto vieja de Windows

            # Guardamos físicamente la nueva imagen en la carpeta
            file.save(os.path.join(ruta_guardado, filename))

            # Query de actualización completa incluyendo la nueva imagen y la columna talla
            query = """
                UPDATE productos 
                SET nombre = %s, categoria = %s, precio = %s, estado = %s, coleccion = %s, talla = %s, imagen = %s 
                WHERE id = %s
            """
            valores = (nuevo_nombre, nueva_categoria, nuevo_precio, nuevo_estado, nueva_coleccion, talla_final, filename, id_producto)
        
        else:
            # Query de actualización conservando la misma imagen existente pero actualizando talla y colección
            query = """
                UPDATE productos 
                SET nombre = %s, categoria = %s, precio = %s, estado = %s, coleccion = %s, talla = %s 
                WHERE id = %s
            """
            valores = (nuevo_nombre, nueva_categoria, nuevo_precio, nuevo_estado, nueva_coleccion, talla_final, id_producto)

        cursor.execute(query, valores)
        conexion.commit()
        flash(f"Prenda #{id_producto} actualizada correctamente en el inventario.", "success")

    except Exception as e:
        conexion.rollback()
        print(f"❌ Error crítico al actualizar en MySQL: {str(e)}")
        flash("Error interno al intentar guardar las modificaciones.", "danger")
    finally:
        cursor.close()
        conexion.close()

    # # 4. Redirección limpia conservando el parámetro de tu pestaña nativa
    return redirect('/shirry-admin?seccion=productos')



# =========================================================================
# 4. SISTEMA DE REGISTRO DE USUARIOS
# =========================================================================
@app.route('/procesar_formulario', methods=['POST'])
def procesar_formulario():
    # 1. CAPTURA DE CAMPOS ORIGINALES Y NUEVOS
    nombre = request.form['nombre']
    email = request.form['email']
    contrasena = request.form['contrasena']
    telefono = request.form['telefono']
    fecha_nacimiento = request.form['fecha_nacimiento']
    ciudad = request.form['ciudad']
    direccion = request.form['direccion']

    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    # 2. VERIFICACIÓN DE USUARIO EXISTENTE
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    usuario_existing = cursor.fetchone()

    if usuario_existing:
        cursor.close()
        conexion.close()
        flash("El correo electrónico ya se encuentra vinculado a otra cuenta.", "error")
        return redirect(url_for('login'))

    # 3. INSERCIÓN MÁSTER DE DATOS EN LA BASE DE DATOS
    try:
        query = """
            INSERT INTO usuarios (
                nombre, email, contrasena, telefono, fecha_nacimiento, ciudad, direccion, fecha_creacion
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            nombre, 
            email, 
            generate_password_hash(contrasena), 
            telefono, 
            fecha_nacimiento, 
            ciudad, 
            direccion, 
            datetime.now(timezone.utc)
        )
        
        cursor.execute(query, valores)
        conexion.commit()

        cursor.close()
        conexion.close()
        flash("Registro completado con éxito. Ya puedes iniciar sesión.", "success")
        return redirect(url_for('login'))

    except Exception as e:
        conexion.rollback()
        cursor.close()
        conexion.close()
        return f"<h1>Error registrando usuario</h1><p>{e}</p>"



# =========================================================================
# 5. SISTEMA DE INICIO DE SESIÓN (LOGIN)
# =========================================================================

@app.route('/procesar_login', methods=['POST'])
def procesar_login():
    email = request.form['email'].strip()
    contrasena = request.form['contrasena'].strip()

    # ACCESO MAESTRO DIRECTO (Se salta los bloqueos)
    if email == "admin@shirrystudios.com" and contrasena == "sc2026":
        session['usuario_id'] = 1
        session['usuario_nombre'] = "Neo Shirry"
        session['usuario_email'] = "admin@shirrystudios.com"
        return redirect(url_for('admin_dashboard'))

    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    usuario_existente = cursor.fetchone()

    if usuario_existente:
        id_usuario = usuario_existente['id']
        intentos = usuario_existente['intentos_fallidos'] or 0
        bloqueado_hasta = usuario_existente['bloqueado_hasta']
        ahora_utc = datetime.now(timezone.utc)

        # 1. VERIFICAR SI LA CUENTA ESTÁ BLOQUEADA
        if bloqueado_hasta:
            # Forzamos que la fecha traída de MySQL tenga zona horaria UTC asignada para poder comparar correctamente
            if bloqueado_hasta.tzinfo is None:
                bloqueado_hasta = bloqueado_hasta.replace(tzinfo=timezone.utc)

            if ahora_utc < bloqueado_hasta:
                tiempo_restante = bloqueado_hasta - ahora_utc
                minutos_restantes = int(tiempo_restante.total_seconds() / 60) + 1
                cursor.close()
                conexion.close()
                flash(f"Cuenta bloqueada temporalmente. Intenta de nuevo en {minutos_restantes} minutos.", "error")
                return redirect(url_for('login'))

        # 2. VALIDAR LA CONTRASEÑA
        if check_password_hash(usuario_existente['contrasena'], contrasena):
            # Contraseña correcta: Reseteamos los intentos fallidos en la Base de Datos
            cursor.execute("UPDATE usuarios SET intentos_fallidos = 0, bloqueado_hasta = NULL WHERE id = %s", (id_usuario,))
            conexion.commit()
            cursor.close()
            conexion.close()

            session['usuario_id'] = id_usuario
            session['usuario_nombre'] = usuario_existente['nombre']
            session['usuario_email'] = usuario_existente['email']
            return redirect(url_for('shop'))
            
        else:
            # Contraseña incorrecta: Sumamos un intento fallido
            nuevos_intentos = intentos + 1
            
            if nuevos_intentos >= 3:
                # Si llega a 3 fallos, calculamos la hora de desbloqueo en UTC (10 minutos al futuro)
                hora_bloqueo = datetime.now(timezone.utc) + timedelta(minutes=10)
                cursor.execute("UPDATE usuarios SET intentos_fallidos = %s, bloqueado_hasta = %s WHERE id = %s", 
                               (nuevos_intentos, hora_bloqueo, id_usuario))
                flash("Has alcanzado el límite de intentos. Cuenta bloqueada por 10 minutos.", "error")
            else:
                cursor.execute("UPDATE usuarios SET intentos_fallidos = %s WHERE id = %s", (nuevos_intentos, id_usuario))
                intentos_restantes = 3 - nuevos_intentos
                flash(f"Contraseña incorrecta. Te quedan {intentos_restantes} intentos.", "error")
            
            conexion.commit()
            cursor.close()
            conexion.close()
            return redirect(url_for('login'))
            
    else:
        cursor.close()
        conexion.close()
        flash("Email o contraseña incorrectos.", "error")
        return redirect(url_for('login'))



# =========================================================================
# 6. SISTEMA DE CIERRE DE SESIÓN (LOGOUT)
# =========================================================================
@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for('inicio'))


# ==========================================================================
# SHIRRY CORE - LOGÍSTICA DE PASARELA Y FACTURACIÓN COMERCIAL
# ==========================================================================

@app.route('/checkout')
def checkout():
    """
    Ruta GET: Renderiza la pasarela de pago extrayendo los productos vigentes
    de la sesión para inyectarlos en la tirilla de carga.
    """
    # Candado de seguridad: si no hay sesión o el carrito está vacío, rebota al inicio
    if 'carrito' not in session or not session['carrito']:
        return redirect('/')
        
    carrito_productos = []
    total_general = 0.0
    
    # Conexión oficial a tu base de datos de Laragon
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # Recorremos cada llave del diccionario guardada por el JS asíncrono
        for clave, item in session['carrito'].items():
            id_producto = item['id']
            cantidad = int(item['cantidad'])
            talla = item.get('talla', 'ÚNICA')
            
            # Consultamos MySQL para asegurar que los precios y nombres sean los reales de la BD
            cursor.execute("SELECT * FROM productos WHERE id = %s", (id_producto,))
            producto_db = cursor.fetchone()
            
            if producto_db:
                subtotal = float(producto_db['precio']) * cantidad
                total_general += subtotal
                
                # Armamos la lista limpia que espera el HTML
                carrito_productos.append({
                    'id': producto_db['id'],
                    'nombre': producto_db['nombre'],
                    'precio': float(producto_db['precio']),
                    'imagen': producto_db['imagen'],
                    'talla': talla,
                    'cantidad': cantidad,
                    'subtotal': subtotal,
                    'clave_carrito': clave
                })
    except Exception as e:
        print(f"[ERROR CRÍTICO EN CHECKOUT BACKEND]: {e}")
    finally:
        cursor.close()
        conexion.close()
        
    # Renderizamos pasando exactamente las mismas variables que configuramos en el html
    return render_template('checkout.html', 
                           productos_carrito=carrito_productos, 
                           total=total_general)


@app.route('/procesar_orden', methods=['POST'])
def procesar_orden():
    """
    Ruta POST: Recibe el formulario de despacho después de la orden de impresión,
    captura las variables y resetea la memoria del carro.
    """
    if 'carrito' not in session or not session['carrito']:
        return redirect('/')
        
    # Captura táctica de las variables enviadas por el formulario
    nombres = request.form.get('nombres')
    apellidos = request.form.get('apellidos')
    email = request.form.get('email')
    telefono = request.form.get('telefono')
    departamento = request.form.get('departamento')
    ciudad = request.form.get('ciudad')
    direccion = request.form.get('direccion')
    notas = request.form.get('notas', '')

    # Impresión de control en la consola de Laragon para verificar recepción limpia
    print("\n" + "="*50)
    print(f"// TRANSMISIÓN NÚCLEO EXÍTOSA - ORDEN PROCESADA //")
    print(f"CLIENTE: {nombres.upper()} {apellidos.upper()}")
    print(f"DESPACHO: {direccion.upper()} - {ciudad.upper()}, {departamento.upper()}")
    print(f"CONTACTO: {email} // TEL: {telefono}")
    print("="*50 + "\n")

    # ======================================================================
    # REINICIO MAESTRO DEL CARRO: Vaciamos la sesión tras la venta exitosa
    # Con esto, el contador estilo SHEIN del Navbar vuelve automáticamente a 0
    # ======================================================================
    session['carrito'] = {}
    session.modified = True

    # Redirigimos al Home de forma limpia con el carro totalmente vacío
    return redirect('/')


# ==========================================
# 7. MODULO COMERCIAL - SISTEMA DE CARRITO
# ==========================================

@app.route('/carrito')
def ver_carrito():
    if 'carrito' not in session:
        session['carrito'] = {}
        
    carrito_productos = []
    total_general = 0.0
    
    # Usando tu función exacta de conexión del sistema
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)
    
    try:
        for clave, item in session['carrito'].items():
            id_producto = item['id']
            talla = item['talla']
            cantidad = item['cantidad']
            
            # Consulta limpia a tu base de datos maestra
            cursor.execute("SELECT * FROM productos WHERE id = %s", (id_producto,))
            producto_db = cursor.fetchone()
            
            if producto_db:
                subtotal = float(producto_db['precio']) * int(cantidad)
                total_general += subtotal
                
                # Inyección de datos respetando tu estructura de diccionarios
                carrito_productos.append({
                    'id': producto_db['id'],
                    'nombre': producto_db['nombre'],
                    'precio': producto_db['precio'],
                    'imagen': producto_db['imagen'],
                    'talla': talla,
                    'cantidad': cantidad,
                    'subtotal': subtotal,
                    'clave_carrito': clave
                })
    finally:
        cursor.close()
        conexion.close()
        
    return render_template('carrito.html', 
                           productos_carrito=carrito_productos, 
                           total=total_general)


@app.route('/actualizar_carrito/<clave_carrito>/<int:cantidad>')
def actualizar_carrito(clave_carrito, cantidad):
    if 'carrito' not in session:
        return redirect(url_for('ver_carrito'))
    
    # Blindaje de stock comercial
    if cantidad < 1 or cantidad > 5:
        return redirect(url_for('ver_carrito'))
    
    if clave_carrito in session['carrito']:
        session['carrito'][clave_carrito]['cantidad'] = cantidad
        session.modified = True  # Actualización forzada en el filesystem
        
    return redirect(url_for('ver_carrito'))


@app.route('/eliminar_del_carrito/<clave_carrito>')
def eliminar_del_carrito(clave_carrito):
    if 'carrito' not in session:
        return redirect(url_for('ver_carrito'))
        
    if clave_carrito in session['carrito']:
        session['carrito'].pop(clave_carrito, None)
        session.modified = True  # Sincronización inmediata de exclusión
        
    return redirect(url_for('ver_carrito'))

# ==========================================
# 7.1. RUTA: INYECTAR PRODUCTO AL CARRITO (POST)
# ==========================================

@app.route('/agregar_al_carrito', methods=['POST'])
def agregar_al_carrito():
    # 1. Asegurar que el objeto carrito exista en el filesystem de la sesión
    if 'carrito' not in session:
        session['carrito'] = {}
        
    # 2. Capturar los datos enviados por el formulario de index.html / shop.html
    id_producto = request.form.get('id_producto')
    talla = request.form.get('talla', 'ÚNICA')
    cantidad = int(request.form.get('cantidad', 1))
    
    if not id_producto:
        return redirect(url_for('ver_carrito'))
        
    # 3. Ir a Laragon a buscar los datos reales de la prenda (Nombre, Precio, Imagen)
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM productos WHERE id = %s", (id_producto,))
        producto_db = cursor.fetchone()
        
        if producto_db:
            # Creamos una clave única uniendo el ID y la Talla (Ej: "4_L" o "12_ÚNICA")
            # Esto evita que prendas con diferentes tallas se mezclen en la misma fila
            clave_carrito = f"{id_producto}_{talla}"
            
            if clave_carrito in session['carrito']:
                # Si el artículo exacto ya estaba en el carro, solo le sumamos la cantidad
                nueva_cantidad = session['carrito'][clave_carrito]['cantidad'] + cantidad
                # Blindamos que el operador no pueda pedir más de 5 unidades del mismo tipo
                if nueva_cantidad <= 5:
                    session['carrito'][clave_carrito]['cantidad'] = nueva_cantidad
            else:
                # Si es un artículo nuevo, lo inyectamos con tu sintaxis de corchetes estricta
                session['carrito'][clave_carrito] = {
                    'id': producto_db['id'],
                    'nombre': producto_db['nombre'],
                    'precio': float(producto_db['precio']),
                    'imagen': producto_db['imagen'],
                    'talla': talla,
                    'cantidad': cantidad,
                    'subtotal': float(producto_db['precio']) * cantidad
                }
                
            # Forzar a Flask-Session a registrar el cambio en la base de datos local
            session.modified = True
            
    except Exception as e:
        print(f"Error crítico al inyectar al carro: {e}")
    finally:
        cursor.close()
        conexion.close()
        
    # 4. RESPUESTA ASÍNCRONA: Ya no recarga la página
    total_items = sum(item.get('cantidad', 1) for item in session['carrito'].values())
    
    from flask import jsonify
    return jsonify({
        'status': 'success',
        'mensaje': 'AÑADIDO_AL_NÚCLEO',
        'total_items_navbar': total_items
    })


# ==========================================================================
# 7.2. CONTEXT PROCESSOR: INYECTOR MAESTRO DE DATOS DEL CARRITO PARA EL NAVBAR
# ==========================================================================
@app.context_processor
def injectar_datos_carrito_global():
    total_items = 0
    total_general = 0.0
    carrito_productos = []
    
    if 'carrito' in session:
        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)
        try:
            for clave, item in session['carrito'].items():
                id_producto = item['id']
                talla = item['talla']
                cantidad = item['cantidad']
                
                cursor.execute("SELECT * FROM productos WHERE id = %s", (id_producto,))
                producto_db = cursor.fetchone()
                
                if producto_db:
                    subtotal = float(producto_db['precio']) * int(cantidad)
                    total_general += subtotal
                    total_items += int(cantidad)
                    
                    carrito_productos.append({
                        'id': producto_db['id'],
                        'nombre': producto_db['nombre'],
                        'precio': producto_db['precio'],
                        'talla': talla,
                        'cantidad': cantidad,
                        'subtotal': subtotal,
                        'clave_carrito': clave
                    })
        finally:
            cursor.close()
            conexion.close()
            
    return dict(
        total_items_navbar=total_items,
        productos_carrito=carrito_productos,
        total=total_general
    )




if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=5000)
