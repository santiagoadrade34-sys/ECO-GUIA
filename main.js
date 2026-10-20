// =======================================================
// 1. RELOJ DIGITAL EN TIEMPO REAL
// =======================================================
function updateClock() {
    const clockElement = document.getElementById('digital-clock');
    if (!clockElement) return; // Evita errores si el elemento no existe

    const now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';

    hours = hours % 12;
    hours = hours ? hours : 12; // Convierte las 0 horas en 12
    minutes = minutes < 10 ? '0' + minutes : minutes; // Añade un cero a la izquierda si es menor a 10

    const timeString = `${hours}:${minutes} ${ampm}`;
    clockElement.textContent = timeString;
}

// Ejecuta el reloj inmediatamente y luego se actualiza cada segundo
document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 1000);
});

// =======================================================
// 2. CÁLCULO DINÁMICO DE LA BARRA DE DESPLAZAMIENTO (SCROLL)
// =======================================================
window.addEventListener('scroll', function() {
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    
    let percentage = 0;
    if (docHeight > 0) {
        percentage = Math.round((scrollTop / docHeight) * 100);
    }
    
    // 1. Actualiza el indicador numérico de texto en el navbar
    const textIndicator = document.getElementById('scroll-percentage');
    if (textIndicator) {
        textIndicator.textContent = `${percentage}%`;
    }
    
    // 2. Modifica el ancho físico de la barra horizontal en tiempo real
    const progressBar = document.getElementById('scroll-progress-bar');
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
    }
});

// =======================================================
// 3. LÓGICA PARA DESLIZAR LA BARRA DE BÚSQUEDA
// =======================================================

document.addEventListener('DOMContentLoaded', () => {
    const btnSearch = document.getElementById('btn-search');
    const searchDropdown = document.getElementById('search-dropdown');

    if (btnSearch && searchDropdown) {
        btnSearch.addEventListener('click', function(e) {
            e.preventDefault(); // Evita que la página salte o recargue
            
            // Abre o cierra la barra agregando/quitando la clase active
            searchDropdown.classList.toggle('active');
            
            // 🌟 CORREGIDO: Buscamos tu input usando su ID exacto de la línea 101
            if (searchDropdown.classList.contains('active')) {
                setTimeout(() => {
                    const inputReal = document.getElementById('navGlobalSearchInput');
                    if (inputReal) inputReal.focus();
                }, 120);
            }
        });
        
        // Blindaje extra para que la imagen de la lupa no robe el clic del enlace
        const imgInside = btnSearch.querySelector('img');
        if (imgInside) {
            imgInside.style.pointerEvents = 'none';
        }
    }
});




// =======================================================
// 4. LÓGICA DEL PANEL DEL CARRITO LATERAL (ESTILO SHEIN)
// =======================================================
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.querySelector('.cart-sidebar');
    const overlay = document.querySelector('.cart-overlay');
    const cartTrigger = document.getElementById('navbar-cart-trigger') || document.getElementById('btn-cart');

    function mostrarTicket() {
        if (sidebar) sidebar.classList.add('active');
        if (overlay) overlay.classList.add('active');
    }

    function ocultarTicket() {
        if (sidebar) sidebar.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
    }

    // 🌟 CORREGIDO: Los eventos se aplican estrictamente DENTRO de la llave del condicional if
    if (cartTrigger) {
        cartTrigger.addEventListener('mouseenter', mostrarTicket);
        cartTrigger.addEventListener('mouseleave', function() {
            setTimeout(() => {
                if (sidebar && !sidebar.matches(':hover') && !cartTrigger.matches(':hover')) {
                    ocultarTicket();
                }
            }, 150);
        });
    }

    if (sidebar) {
        sidebar.addEventListener('mouseenter', mostrarTicket);
        sidebar.addEventListener('mouseleave', ocultarTicket);
    }
});

// =======================================================
// 5. CONTROL COMPLETO DEL PANEL LATERAL DE MENÚ
// =======================================================
document.addEventListener('DOMContentLoaded', () => {
    const botonMenu = document.getElementById('btn-menu');
    const botonCerrar = document.getElementById('btn-close-menu');
    const menuLateral = document.getElementById('menu-sidebar');
    const capaOscura = document.getElementById('menu-overlay');

    function cerrarMenuCompleto() {
        if (menuLateral) menuLateral.classList.remove('active');
        if (capaOscura) capaOscura.classList.remove('active');
    }

    if (botonMenu && menuLateral) {
        botonMenu.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            menuLateral.classList.add('active');
            if (capaOscura) capaOscura.classList.add('active');
        });
    }

    // 🌟 CORREGIDO: Se reubicó el listener adentro del bloque de protección para evitar errores null
    if (botonCerrar) {
        botonCerrar.addEventListener('click', function(e) {
            e.preventDefault();
            cerrarMenuCompleto();
        });
    }

    // 🌟 CORREGIDO: Blindaje para la capa oscura al hacer clic
    if (capaOscura) {
        capaOscura.addEventListener('click', cerrarMenuCompleto);
    }

    // Control dinámico de clics en zonas externas muertas
    document.addEventListener('click', function(e) {
        if (menuLateral && menuLateral.classList.contains('active')) {
            if (!menuLateral.contains(e.target) && e.target !== botonMenu && (botonMenu && !botonMenu.contains(e.target))) {
                cerrarMenuCompleto();
            }
        }
    });
});
// =======================================================
// 6. CONTROL ASÍNCRONO DE COMPRA CON ANIMACIÓN AVANZADA
// =======================================================
document.addEventListener('DOMContentLoaded', () => {
    const cartForms = document.querySelectorAll('form[action*="agregar_al_carrito"]');

    cartForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const submitBtn = this.querySelector('button[type="submit"]') || this;
            const formData = new FormData(this);

            fetch(this.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // --- ANIMACIÓN 1: PARTÍCULA VOLADORA ---
                    const targetCart = document.getElementById('navbar-cart-trigger') || document.getElementById('btn-cart');
                    
                    if (submitBtn && targetCart) {
                        const btnRect = submitBtn.getBoundingClientRect();
                        const cartRect = targetCart.getBoundingClientRect();

                        const flyBadge = document.createElement('div');
                        flyBadge.textContent = '+1';

                        Object.assign(flyBadge.style, {
                            position: 'fixed',
                            top: (btnRect.top + btnRect.height / 2) + 'px',
                            left: (btnRect.left + btnRect.width / 2) + 'px',
                            background: '#00ffcc',
                            color: '#000000',
                            fontFamily: 'monospace',
                            fontSize: '0.85rem',
                            fontWeight: 'bold',
                            width: '24px',
                            height: '24px',
                            borderRadius: '50%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            zIndex: '999999',
                            pointerEvents: 'none',
                            boxShadow: '0 0 10px #00ffcc',
                            transition: 'all 0.8s cubic-bezier(0.19, 1, 0.22, 1)'
                        });

                        document.body.appendChild(flyBadge);

                        requestAnimationFrame(() => {
                            flyBadge.style.top = (cartRect.top + cartRect.height / 2) + 'px';
                            flyBadge.style.left = (cartRect.left + cartRect.width / 2) + 'px';
                            flyBadge.style.transform = 'scale(0.4)';
                            flyBadge.style.opacity = '0';
                        });

                        setTimeout(() => {
                            flyBadge.remove();
                            // Actualizar el número visual del carrito en el navbar si existe la etiqueta
                            const badge = document.querySelector('.cart-count');
                            if (badge && data.total_items_navbar) {
                                badge.textContent = `[${data.total_items_navbar}]`;
                            }
                        }, 800);
                    }

                    // --- ANIMACIÓN 2: ALERTA FLOTANTE EN LA PANTALLA ---
                    const notification = document.createElement('div');
                    notification.innerHTML = '<span style="color: #00ffcc; margin-right: 8px;">➔</span> ÁÑADIDO AL CARRITO';

                    Object.assign(notification.style, {
                        position: 'fixed',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%) scale(0.9)',
                        background: '#0a0a0a',
                        color: '#ffffff',
                        border: '1px dashed #2d2d30',
                        fontFamily: 'monospace',
                        fontSize: '0.9rem',
                        fontWeight: 'bold',
                        letterSpacing: '1px',
                        padding: '16px 32px',
                        zIndex: '999998',
                        opacity: '0',
                        boxShadow: '0 10px 40px rgba(0,0,0,0.9)',
                        transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
                    });

                    document.body.appendChild(notification);

                    requestAnimationFrame(() => {
                        notification.style.opacity = '1';
                        notification.style.transform = 'translate(-50%, -50%) scale(1)';
                    });

                    setTimeout(() => {
                        notification.style.opacity = '0';
                        notification.style.transform = 'translate(-50%, -50%) scale(0.9)';
                        setTimeout(() => notification.remove(), 300);
                    }, 2500);
                }
            })
            // 🌟 CORREGIDO: Mantenemos tu console.error original de forma asíncrona segura
            .catch(error => console.error("Error en la transmisión asíncronas:", error));
        });
    });
});

// =======================================================
// 7. CONTROLES NUMÉRICOS TRADICIONALES DEL CARRITO LOCAL
// =======================================================
function changeQty(itemId, amount) {
    const qtySpan = document.getElementById(`qty-${itemId}`);
    const priceP = document.getElementById(`price-${itemId}`);
    if (!qtySpan || !priceP) return;
    
    let currentQty = parseInt(qtySpan.textContent);
    let basePrice = parseInt(priceP.getAttribute('data-base-price'));
    
    currentQty += amount;
    if (currentQty < 1) return; 
    
    qtySpan.textContent = currentQty;
    let newPrice = basePrice * currentQty;
    priceP.textContent = `$${newPrice.toLocaleString('es-CO')} COP`;
    
    if (typeof updateSubtotal === 'function') updateSubtotal();
}

function removeItem(itemId) {
    const element = document.getElementById(itemId);
    if (element) {
        element.remove();
        if (typeof updateSubtotal === 'function') updateSubtotal();
    }
}
   

/* ==========================================================================
   SHIRRY SECURITY - TRANSICIÓN DE TERMINAL PARA RECUPERACIÓN
   ========================================================================== */
document.addEventListener("DOMContentLoaded", function() {
    const recoveryCard = document.querySelector(".recovery-card");
    
    if (recoveryCard) {
        const recoveryForms = recoveryCard.querySelectorAll("form");
        
        recoveryForms.forEach(form => {
            form.addEventListener("submit", function(e) {
                // Interceptamos un milisegundo para activar el parpadeo de datos
                e.preventDefault();
                
                // Añadimos la clase de animación de estática industrial
                recoveryCard.classList.add("glitch-transition");
                
                // Enviamos el formulario formalmente tras terminar el glitch visual
                setTimeout(() => {
                    form.submit();
                }, 250); 
            });
        });
    }
});

/* ==========================================================================
   SHIRRY SECURITY - GENERADOR Y CONTROL DE CAPTCHA LOCAL
   ========================================================================== */
function inicializarCaptchaShirry() {
    const captchaBlock = document.getElementById("captcha-secure-block");
    const captchaDisplay = document.getElementById("captcha-code-display");
    const loginForm = document.getElementById("form-login"); // Cambia al ID real de tu formulario de login

    // Función simple para simular un captcha visual local al fallar
    function generarCodigoLocal() {
        const caracteres = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; // Excluimos O, 0, I, 1 para evitar confusiones
        let resultado = "";
        for (let i = 0; i < 5; i++) {
            resultado += caracteres.charAt(Math.floor(Math.random() * caracteres.length));
        }
        return resultado;
    }

    // Simulador de activación: Si en tus alertas Flash el servidor ya habla de "intentos", lo activamos de inmediato
    const alertaTerminal = document.querySelector(".alert-terminal-error");
    if (alertaTerminal && (alertaTerminal.innerText.includes("intentos") || alertaTerminal.innerText.includes("ALERTA"))) {
        if (captchaBlock && captchaDisplay) {
            const codigoCorrecto = generarCodigoLocal();
            captchaDisplay.innerText = codigoCorrecto;
            captchaBlock.classList.add("active");
            
            // Blindamos el submit del formulario en el cliente para obligar a meter el código correcto
            if (loginForm) {
                loginForm.addEventListener("submit", function(e) {
                    const inputUsuario = document.getElementById("captcha-input").value.trim().toUpperCase();
                    if (inputUsuario !== codigoCorrecto) {
                        e.preventDefault();
                        alert("🔴 ACCESO DENEGADO: Código Captcha inválido. Recargando terminal de seguridad.");
                        window.location.reload();
                    }
                });
            }
        }
    }
}

// Arrancar el validador tras cargar el DOM
document.addEventListener("DOMContentLoaded", inicializarCaptchaShirry);


/* ==========================================================================
   SHIRRY CORE - INTERACTIVIDAD ASÍNCRONA VISTA RÁPIDA TEMU-STYLE
   ========================================================================== */
document.addEventListener("DOMContentLoaded", function() {
    const qvModal = document.getElementById("quickview-modal-system");
    const qvClose = document.getElementById("qv-close-trigger");
    
    if (!qvModal) {
        console.warn("[SHIRRY-SYS] Advertencia: Contenedor 'quickview-modal-system' no detectado en el DOM.");
        return;
    }

    // 1. DETECTOR GLOBAL DE CLICS: CAPTURA LA PÍLDORA BLANCA O EL BOTÓN DEL CARRITO
    document.addEventListener("click", function(e) {
        // Buscamos si el clic ocurrió en la píldora de Temu o en el botón del carrito con desvío
        const botonValido = e.target.closest(".btn-quickview-temu") || 
                            e.target.closest(".btn-trigger-qv") || 
                            e.target.classList.contains("btn-quickview-temu") || 
                            e.target.classList.contains("btn-trigger-qv");
        
        if (e.target && botonValido) {
            // Cancelamos cualquier comportamiento nativo por seguridad
            e.preventDefault();
            
            // Extraemos el botón contenedor real que tiene guardado el data-id
            const button = e.target.closest(".btn-quickview-temu") || e.target.closest(".btn-trigger-qv") || e.target;
            const productoId = button.getAttribute("data-id");
            
            console.log(`[SHIRRY-SYS] Desvío de flujo: Desplegando Vista Rápida para ID: ${productoId}`);
            
            if (productoId) {
                // Consulta asíncrona a la API de Flask
                fetch(`/api/producto/${productoId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) return console.error(data.error);
                        
                        // Inyectar la información de MySQL en la estructura de base.html
                        document.getElementById("qv-target-title").innerText = data.nombre;
                        document.getElementById("qv-target-sku").innerText = `CORE_SYS // ID_NODE: 0x00${data.id}`;
                        document.getElementById("qv-target-price").innerText = `$${Number(data.precio).toLocaleString('es-CO')} COP`;
                        document.getElementById("qv-target-main-img").src = `/static/imagenes/productos/${data.imagen}`;
                        
                        // Sincronizar el ID del producto en el botón interno "Añadir a la bolsa"
                        const cartBtn = document.getElementById("qv-add-to-cart-trigger");
                        if (cartBtn) cartBtn.setAttribute("data-id", data.id);
                        
                        // Cargar las miniaturas correspondientes
                        const thumbsContainer = document.getElementById("qv-target-thumbs");
                        if (thumbsContainer) {
                            thumbsContainer.innerHTML = `
                                <img src="/static/imagenes/productos/${data.imagen}" class="qv-thumb-img active">
                                <img src="/static/imagenes/productos/${data.imagen}" class="qv-thumb-img">
                            `;
                        }
                        
                        // Cargar selectores de talla dinámicos de la base de datos
                        const sizesContainer = document.getElementById("qv-target-sizes");
                        if (sizesContainer) {
                            sizesContainer.innerHTML = `<button class="qv-size-btn active">${data.talla}</button>`;
                        }
                        
                        // REVELACIÓN: Abrir la ventana modal en fucsia neón
                        qvModal.classList.add("active");
                    })
                    .catch(err => console.error("[SHIRRY-SYS] Error crítico en la redirección asíncrona:", err));
            }
        }
    });


    // 2. INTERCAMBIO DINÁMICO DE MINIATURAS
    document.addEventListener("click", function(e) {
        if (e.target && e.target.classList.contains("qv-thumb-img")) {
            document.querySelectorAll(".qv-thumb-img").forEach(img => img.classList.remove("active"));
            e.target.classList.add("active");
            document.getElementById("qv-target-main-img").src = e.target.src;
        }
    });

    // 3. EVENTOS DE CIERRE RÍGIDOS
    if (qvClose) {
        qvClose.addEventListener("click", () => qvModal.classList.remove("active"));
    }
    
    // Cerrar si hacen clic en la zona negra traslúcida exterior
    qvModal.addEventListener("click", (e) => {
        if (e.target === qvModal) qvModal.classList.remove("active");
    });
});

    // 4. LOGICA ASÍNCRONA CON MENSAJE DE CONFIRMACIÓN DE TERMINAL
    const qvAddToCartBtn = document.getElementById("qv-add-to-cart-trigger");
    
    if (qvAddToCartBtn) {
        qvAddToCartBtn.addEventListener("click", function() {
            const productoId = this.getAttribute("data-id");
            const botonOriginal = this;
            
            if (productoId) {
                // Guardamos el texto original para poder restaurarlo después
                const textoOriginal = botonOriginal.innerHTML;
                
                // Cambiamos el estado del botón a modo de carga industrial
                botonOriginal.disabled = true;
                botonOriginal.innerText = "PROCESANDO_INYECCIÓN...";
                
                fetch(`/carrito/agregar/${productoId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => {
                    if (!response.ok) throw new Error("HTTP_ERR");
                    return response.json();
                })
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                        botonOriginal.disabled = false;
                        botonOriginal.innerHTML = textoOriginal;
                        return;
                    }
                    
                    // 🚀 ÉXITO: Cambiamos los estilos del botón al formato fucsia/verde de SHIRRY
                    botonOriginal.style.backgroundColor = "#000000";
                    botonOriginal.style.color = "#00ff00"; // Texto en verde fósforo de consola
                    botonOriginal.style.border = "3px solid #00ff00";
                    botonOriginal.innerText = "→ AÑADIDO AL CARRITO";
                    
                    // Actualizar el contador del Navbar al instante
                    if (typeof actualizarMiniCarritoHTML === "function") {
                        actualizarMiniCarritoHTML(data);
                    } else {
                        const contadorBadge = document.querySelector(".cart-count-badge") || document.querySelector("[class*='cart'] span"); 
                        if (contadorBadge && data.total_items) {
                            contadorBadge.innerText = data.total_items;
                        }
                    }
                    
                    // Esperamos 1.2 segundos para que el usuario disfrute del mensaje y luego cerramos
                    setTimeout(() => {
                        if (qvModal) qvModal.classList.remove("active");
                        
                        // Restauramos el botón a su estado normal para cuando vuelvan a abrir otra prenda
                        botonOriginal.disabled = false;
                        botonOriginal.style.backgroundColor = "";
                        botonOriginal.style.color = "";
                        botonOriginal.style.border = "";
                        botonOriginal.innerHTML = textoOriginal;
                    }, 1200);
                })
                .catch(err => {
                    console.error("Error en inyección:", err);
                    botonOriginal.disabled = false;
                    botonOriginal.innerHTML = textoOriginal;
                });
            }
        });
    }
