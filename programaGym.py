from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import time
import traceback

load_dotenv()

def esperar_hasta_hora_apertura():
    """Espera hasta las 6:00 AM si el script se ejecuta antes"""
    ahora = datetime.now()
    hora_apertura = ahora.replace(hour=6, minute=0, second=0, microsecond=0)
    
    if ahora < hora_apertura:
        tiempo_espera = (hora_apertura - ahora).total_seconds()
        print(f"⏰ Son las {ahora.strftime('%H:%M:%S')}")
        print(f"⏰ Las reservas abren a las 06:00:00")
        print(f"⏰ Esperando {int(tiempo_espera)} segundos ({int(tiempo_espera/60)} minutos)...")
        time.sleep(tiempo_espera)
        print(f"✓ Son las 06:00:00 - Iniciando proceso de reserva...")
    else:
        print(f"✓ Son las {ahora.strftime('%H:%M:%S')} - Horario válido para reservar")

def reservar_slot(page, hora_inicio_clase, hora_fin_clase):
    """Busca y reserva el slot de horario específico"""
    try:
        print(f"\n  📋 [reservar_slot] Inicio de proceso")
        print(f"  📋 [reservar_slot] Objetivo: {hora_inicio_clase} - {hora_fin_clase}")
        print(f"  🌐 [reservar_slot] URL actual antes de buscar bookings: {page.url}")
        print(f"\n  📋 Esperando a que cargue la sección de bookings...")
        page.wait_for_selector('#bookings', timeout=10000)
        page.wait_for_timeout(2000)  # Espera adicional para carga completa
        print(f"  ✓ Sección de bookings cargada")
        print(f"  🌐 [reservar_slot] URL actual después de cargar bookings: {page.url}")
        
        print(f"\n  🔍 Buscando slot de horario {hora_inicio_clase} - {hora_fin_clase}...")
        
        
        # Re-obtener slots cada vez para evitar elementos obsoletos
        def obtener_slots():
            return page.query_selector_all('div.row.no-gutters.align-items-center')
        
        slots = obtener_slots()
        print(f"  ✓ Se encontraron {len(slots)} slots en total")
        if len(slots) == 0:
            print("  ⚠️ [reservar_slot] No hay slots visibles en #bookings en este momento")
        
        print(f"\n  🔄 Revisando cada slot...")
        for i in range(len(slots)):
            try:
                print(f"\n  ------------------------------------------------------------")
                print(f"  🔎 [slot-loop] Iteración {i+1}/{len(slots)}")
                # Re-obtener slots en cada iteración para evitar handles obsoletos
                slots_actuales = obtener_slots()
                print(f"  📊 [slot-loop] Slots visibles ahora: {len(slots_actuales)}")
                if i >= len(slots_actuales):
                    print(f"  ⚠️ [slot-loop] Índice {i} fuera de rango tras recarga, se omite")
                    continue
                    
                slot = slots_actuales[i]
                horario_element = slot.query_selector('p.font-weight-semibold.mb-0')
                
                if horario_element:
                    horario_texto = horario_element.inner_text().strip()
                    print(f"  • Slot {i+1}: {horario_texto}")
                    print(f"  🔍 [slot-loop] ¿Contiene hora inicio '{hora_inicio_clase}'?: {hora_inicio_clase in horario_texto}")
                    print(f"  🔍 [slot-loop] ¿Contiene hora fin '{hora_fin_clase}'?: {hora_fin_clase in horario_texto}")
                    
                    if hora_inicio_clase in horario_texto and hora_fin_clase in horario_texto:
                        print(f"\n  ✓ ¡Slot correcto encontrado! {horario_texto}")
                        
                        print(f"\n  🔍 Verificando estado de la reserva...")
                        boton_cancel = slot.query_selector('button.btn.btn-primary.btn-sm:has-text("Cancel")')
                        print(f"  🔎 [slot-loop] Botón 'Cancel' encontrado: {boton_cancel is not None}")
                        
                        if boton_cancel:
                            print(f"  ✓ Slot {horario_texto} YA ESTÁ RESERVADO")
                            print(f"  ✓ Botón 'Cancel' está visible - Reserva confirmada previamente")
                            return True
                        
                        print(f"\n  🔍 Buscando botón 'Book' para reservar...")
                        boton_book = slot.query_selector('button.btn.btn-primary:has-text("Book")')
                        print(f"  🔎 [slot-loop] Botón 'Book' encontrado: {boton_book is not None}")
                        
                        if boton_book:
                            texto_boton = boton_book.inner_text().strip()
                            print(f"  ✓ Botón encontrado: '{texto_boton}'")
                            
                            if 'Book' in texto_boton:
                                print(f"\n  🖱️ Haciendo click en 'Book'...")
                                boton_book.click()
                                print(f"  ✓ Click en 'Book' realizado")
                                print(f"  🌐 [slot-loop] URL tras click en Book: {page.url}")
                                
                                print(f"\n  ⏳ Esperando ventana de confirmación...")
                                try:
                                    page.wait_for_selector('button:has-text("Yes")', timeout=5000)
                                    print(f"  ✓ Ventana de confirmación apareció")
                                    page.click('button:has-text("Yes")')
                                    print(f"  ✓ Click en 'Yes' realizado")
                                except Exception as e:
                                    print(f"  ⚠️ No apareció botón 'Yes': {e}")
                                    print("  ⚠️ Traceback ventana confirmación:")
                                    print(traceback.format_exc())
                                
                                print(f"\n  ⏳ Esperando procesamiento...")
                                page.wait_for_timeout(3000)
                                
                                print(f"\n  ⏳ Esperando actualización...")
                                page.wait_for_timeout(2000)
                                print(f"  🌐 [slot-loop] URL antes de verificar reserva: {page.url}")

                                print(f"\n  🔄 Verificando reserva...")
                                # Re-obtener slots después de la acción
                                slots_verificacion = obtener_slots()
                                print(f"  📊 [verificacion] Slots detectados para verificar: {len(slots_verificacion)}")
                                
                                for j in range(len(slots_verificacion)):
                                    try:
                                        slot_act = slots_verificacion[j]
                                        horario_element_act = slot_act.query_selector('p.font-weight-semibold.mb-0')
                                        if horario_element_act:
                                            horario_texto_act = horario_element_act.inner_text().strip()
                                            print(f"  • [verificacion] Slot {j+1}: {horario_texto_act}")

                                            if hora_inicio_clase in horario_texto_act and hora_fin_clase in horario_texto_act:
                                                print(f"  ✓ [verificacion] Slot objetivo localizado en posición {j+1}")
                                                boton_cancel_verificacion = slot_act.query_selector('button.btn.btn-primary.btn-sm:has-text("Cancel")')
                                                print(f"  🔎 [verificacion] Botón 'Cancel' visible: {boton_cancel_verificacion is not None}")
                                                
                                                if boton_cancel_verificacion:
                                                    print(f"\n  ✓✓✓ RESERVA CONFIRMADA - Botón 'Cancel' visible")
                                                    return True
                                                else:
                                                    print(f"  ✗ Reserva no confirmada")
                                                    print("  ✗ [verificacion] No apareció 'Cancel' en el slot objetivo tras reservar")
                                                    return False
                                        else:
                                            print(f"  ⚠️ [verificacion] Slot {j+1} sin elemento de horario")
                                    except Exception as e:
                                        print(f"  ⚠️ Error verificando slot {j+1}: {e}")
                                        print("  ⚠️ Traceback verificando slot:")
                                        print(traceback.format_exc())
                                        continue
                            else:
                                print(f"  ℹ️ Botón dice: '{texto_boton}'")
                                print("  ℹ️ [slot-loop] El botón encontrado no contiene la palabra 'Book' exacta")
                                return False
                        else:
                            print(f"  ✗ No hay botón 'Book' disponible")
                            print("  ✗ [slot-loop] El slot existe pero no se puede reservar por ahora")
                            return False
                else:
                    print(f"  ⚠️ [slot-loop] Slot {i+1} no contiene el elemento de horario esperado")
            except Exception as e:
                print(f"  ⚠️ Error procesando slot {i+1}: {e}")
                print("  ⚠️ Traceback procesando slot:")
                print(traceback.format_exc())
                continue
        
        print(f"\n  ✗ No se encontró el slot {hora_inicio_clase} - {hora_fin_clase}")
        print(f"  🌐 [reservar_slot] URL al finalizar sin éxito: {page.url}")
        return False
        
    except Exception as e:
        print(f"  ✗ Error general en reservar_slot: {str(e)}")
        print("  ✗ Traceback general en reservar_slot:")
        print(traceback.format_exc())
        return False

def abrir_pagina():
    """Función principal con REINTENTOS INFINITOS hasta conseguir reserva"""
    
    print("\n" + "="*60)
    print("FASE 1: VERIFICACIÓN DE HORA DE APERTURA")
    print("="*60)
    
    
    print("\n" + "="*60)
    print("FASE 2: CONFIGURACIÓN INICIAL")
    print("="*60)
    print(f"✓ Modo: MÁXIMO 10 INTENTOS")
    print(f"✓ Espera entre intentos: 10-30 segundos")
    print(f"✓ El script se detendrá después de 10 intentos")
    
    print("\n" + "="*60)
    print("FASE 3: INICIANDO NAVEGADOR Y SESIÓN")
    print("="*60)
    
    with sync_playwright() as p:
        print("🌐 Lanzando navegador Chrome...")
        # Configuración optimizada para modo headless
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',  # Evitar detección de bot
                '--disable-dev-shm-usage',  # Para evitar crashes
                '--no-sandbox',  # Para compatibilidad
            ]
        )
        
        # Configurar contexto del navegador con user-agent real
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='es-ES',
            timezone_id='Europe/Ljubljana',
        )
        
        page = context.new_page()
        
        # Inyectar JavaScript para evitar detección de headless
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        print("✓ Navegador lanzado correctamente")
        
        print("\n📍 Navegando a la página de login...")
        page.goto('https://popr.uni-lj.si/unauth/440877/login')
        print("✓ Página de login cargada")
        
        print("\n📝 Rellenando campo de usuario...")
        page.wait_for_selector('input#mat-input-0')
        page.click('input#mat-input-0')
        usuario = os.getenv('APP_USERNAME')
        page.fill('input#mat-input-0', usuario)
        print(f"✓ Usuario ingresado: {usuario[:3]}***")
        
        print("\n🔒 Rellenando campo de contraseña...")
        page.wait_for_selector('input#mat-input-1')
        page.click('input#mat-input-1')
        password = os.getenv('APP_PASSWORD')
        page.fill('input#mat-input-1', password)
        print("✓ Contraseña ingresada")
        
        print("\n🔐 Iniciando sesión...")
        page.wait_for_selector('button.t_440877_login')
        page.click('button.t_440877_login')
        
        # Esperar a que se complete el login
        print("⏳ Esperando a que se complete el login...")
        page.wait_for_timeout(5000)
        print("✓✓✓ Sesión iniciada\n")
        
        print("\n" + "="*60)
        print("FASE 4: BÚSQUEDA CON LÍMITE DE INTENTOS")
        print("="*60)
        
        intento_actual = 1
        MAX_INTENTOS = 10
        
        # BUCLE CON LÍMITE - Termina cuando consigue la reserva o llega a 10 intentos
        while intento_actual <= MAX_INTENTOS:
            print(f"\n{'='*60}")
            print(f"🔄 INTENTO #{intento_actual} DE {MAX_INTENTOS}")
            print(f"{'='*60}")
            print(f"⏰ Hora actual: {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}\n")
            
            try:
                print("📍 Navegando directamente a la página de eventos...")
                page.goto('https://popr.uni-lj.si/user/events.html?execution=e1s1')
                page.wait_for_timeout(3000)
                print("✓ Página de eventos cargada")
                
                print("\n⏳ Esperando resultados de búsqueda...")
                page.wait_for_selector('#search-result', timeout=15000)
                # IMPORTANTE: Esperar más tiempo para que Angular cargue todo el contenido
                page.wait_for_timeout(5000)
                # Esperar a que se carguen los elementos de la lista
                page.wait_for_selector('.list-group-item', timeout=15000)
                print("✓ Resultados cargados")
                
                print("\n📅 Determinando horario según el día...")
                horarios_por_dia = {
                    
                    3: ('21:00', '22:00'),  # Jueves
                    
                }
                
                hoy = datetime.now()
                dia_semana = hoy.weekday()
                meses_es_abrev = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']
                fecha_hoy = f"{hoy.day:02d}-{meses_es_abrev[hoy.month-1]}-{hoy.year}"
                
                dias_nombres = {
                    0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 
                    3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
                }
                print(f"✓ Hoy es {dias_nombres[dia_semana]} ({fecha_hoy})")
                
                if dia_semana not in horarios_por_dia:
                    print(f"\n❌ No hay clase programada para {dias_nombres[dia_semana]}")
                    print("🚪 Cerrando navegador...")
                    context.close()
                    browser.close()
                    return
                
                hora_inicio, hora_fin = horarios_por_dia[dia_semana]
                print(f"✓ Horario de tu clase: {hora_inicio} - {hora_fin}")
                
                print(f"\n🔍 Buscando eventos de Plavanje na Fakulteti za šport para {fecha_hoy}...")
                
                def horario_coincide(hora_inicio_evento, hora_fin_evento, hora_inicio_clase, hora_fin_clase):
                    def a_minutos(hora_str):
                        h, m = hora_str.split(':')
                        return int(h) * 60 + int(m)
                    
                    inicio_evento = a_minutos(hora_inicio_evento)
                    fin_evento = a_minutos(hora_fin_evento)
                    inicio_clase = a_minutos(hora_inicio_clase)
                    fin_clase = a_minutos(hora_fin_clase)
                    
                    return inicio_evento <= inicio_clase and fin_clase <= fin_evento
                
                eventos = page.query_selector_all('.list-group-item')
                print(f"✓ Se encontraron {len(eventos)} eventos en total")
                
                # Scroll para asegurar que todos los eventos estén cargados
                if len(eventos) > 0:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                    # Volver a capturar eventos después del scroll
                    eventos = page.query_selector_all('.list-group-item')
                    print(f"✓ Re-escaneados: {len(eventos)} eventos")
                
                print(f"\n🔄 Revisando eventos...")
                eventos_encontrados = 0
                evento_fitnes_hoy_encontrado = False
                
                # DEBUG: Mostrar primeros 5 eventos para verificar
                print(f"\n🐛 DEBUG: Mostrando primeros 5 eventos:")
                for i, evento in enumerate(eventos[:5], 1):
                    titulo_element = evento.query_selector('h2')
                    fecha_element = evento.query_selector('._event-date-wrapper strong')
                    if titulo_element and fecha_element:
                        titulo = titulo_element.inner_text()
                        fecha = fecha_element.inner_text()
                        print(f"  Evento {i}: '{titulo}' - Fecha: '{fecha}'")
                
                print(f"\n🔍 Buscando evento de Plavanje na Fakulteti za šport para {fecha_hoy}...")
                
                for i in range(len(eventos)):
                    try:
                        # Re-obtener eventos en cada iteración para evitar handles obsoletos
                        eventos_actuales = page.query_selector_all('.list-group-item')
                        if i >= len(eventos_actuales):
                            continue
                            
                        evento = eventos_actuales[i]
                        titulo_element = evento.query_selector('h2')
                        fecha_element = evento.query_selector('._event-date-wrapper strong')
                        
                        if titulo_element and fecha_element:
                            titulo = titulo_element.inner_text()
                            fecha = fecha_element.inner_text()
                            
                            # Verificar si es un evento de natación para hoy
                            if 'Plavanje Na Fakulteti Za Šport' in titulo and fecha == fecha_hoy:
                                evento_fitnes_hoy_encontrado = True
                                print(f"\n✓ Evento de Plavanje na Fakulteti za šport encontrado: '{titulo}' en {fecha}")
                                horas_elements = evento.query_selector_all('._event-date-wrapper strong')
                                
                                if len(horas_elements) >= 3:
                                    hora_inicio_evento = horas_elements[1].inner_text()
                                    hora_fin_evento = horas_elements[2].inner_text()
                                    
                                    if horario_coincide(hora_inicio_evento, hora_fin_evento, hora_inicio, hora_fin):
                                        print(f"\n✓✓✓ EVENTO ENCONTRADO:")
                                        print(f"  📋 {titulo}")
                                        print(f"  📅 {fecha}")
                                        print(f"  🕐 {hora_inicio_evento} - {hora_fin_evento}")
                                        
                                        print(f"\n🖱️ Abriendo el evento...")
                                        enlace = evento.query_selector('a')
                                        if enlace:
                                            esperar_hasta_hora_apertura()
                                            enlace.click()
                                            eventos_encontrados += 1
                                            print(f"✓ Evento abierto")
                                            
                                            print(f"\n⏳ Esperando carga...")
                                            page.wait_for_timeout(5000)
                                            
                                            print(f"\n🎯 Intentando reservar...")
                                            if reservar_slot(page, hora_inicio, hora_fin):
                                                print("\n" + "="*60)
                                                print("🎉🎉🎉 ¡RESERVA COMPLETADA! 🎉🎉🎉")
                                                print("="*60 + "\n")
                                                print(f"✓ Clase reservada: {hora_inicio} - {hora_fin}")
                                                print(f"✓ Fecha: {fecha}")
                                                print(f"✓ Intentos realizados: {intento_actual}")
                                                print("\n🚪 Cerrando navegador...")
                                                page.wait_for_timeout(3000)
                                                context.close()
                                                browser.close()
                                                return  # ¡ÉXITO! Terminar el script
                                            else:
                                                print("\n  ✗ No se pudo completar la reserva")
                                                print("  🔄 Continuando búsqueda...")
                                                break
                    except Exception as e:
                        print(f"  ⚠️ Error procesando evento {i+1}: {e}")
                        continue
                
                # Resultado del intento
                if not evento_fitnes_hoy_encontrado:
                    print(f"\n⚠️ No se encontró evento de Plavanje na Fakulteti za šport para {fecha_hoy}")
                    print(f"💡 Los eventos podrían publicarse en los próximos minutos...")
                    
                    # DEBUG: Guardar screenshot para ver qué está viendo el navegador
                    if intento_actual <= 3:  # Solo en los primeros 3 intentos
                        screenshot_path = f"debug_intento_{intento_actual}.png"
                        page.screenshot(path=screenshot_path)
                        print(f"📸 Screenshot guardado: {screenshot_path}")
                    
                    tiempo_espera = 30  # Esperar 30 segundos si no hay eventos
                elif eventos_encontrados == 0:
                    print(f"\n⚠️ Evento encontrado pero no con el horario {hora_inicio} - {hora_fin}")
                    tiempo_espera = 15
                else:
                    print(f"\n⚠️ No se pudo completar la reserva en este intento")
                    tiempo_espera = 10
                
                # Esperar antes del siguiente intento
                if intento_actual < MAX_INTENTOS:
                    print(f"\n⏳ Esperando {tiempo_espera} segundos antes del siguiente intento...")
                    print(f"💪 Intento #{intento_actual} completado - Continuando...")
                    page.wait_for_timeout(tiempo_espera * 1000)
                else:
                    print(f"\n⏹️ Se alcanzó el límite máximo de {MAX_INTENTOS} intentos")
                    print("🚪 Cerrando navegador...")
                    page.wait_for_timeout(3000)
                    context.close()
                    browser.close()
                    return
                
                intento_actual += 1
                
            except Exception as e:
                print(f"\n❌ Error en el intento #{intento_actual}: {str(e)}")
                
                # Guardar screenshot del error para debug
                try:
                    screenshot_path = f"debug_error_intento_{intento_actual}.png"
                    page.screenshot(path=screenshot_path)
                    print(f"📸 Screenshot del error guardado: {screenshot_path}")
                except:
                    print("⚠️ No se pudo guardar screenshot del error")
                
                if intento_actual < MAX_INTENTOS:
                    tiempo_espera = 15
                    print(f"⏳ Esperando {tiempo_espera} segundos antes de reintentar...")
                    page.wait_for_timeout(tiempo_espera * 1000)
                else:
                    print(f"\n⏹️ Se alcanzó el límite máximo de {MAX_INTENTOS} intentos")
                    print("🚪 Cerrando navegador...")
                    page.wait_for_timeout(3000)
                    context.close()
                    browser.close()
                    return
                
                intento_actual += 1

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🏋️ SISTEMA DE RESERVAS AUTOMÁTICAS")
    print("="*60)
    print("⚡ Modo: MÁXIMO 10 INTENTOS")
    print("🎯 El script se detendrá después de 10 intentos o al conseguir la reserva")
    print("="*60)
    abrir_pagina()
    print("\n✅ Script finalizado - Reserva completada, límite de intentos alcanzado o no hay clase hoy")