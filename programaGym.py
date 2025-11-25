from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
from datetime import datetime
import time

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

def esperar_hasta_hora_apertura():
    """
    Función que espera hasta las 6:00 AM si el script se ejecuta antes de esa hora.
    Las reservas se abren a las 6:00 AM, por lo que esperamos hasta ese momento.
    """
    # Obtener la hora actual del sistema
    ahora = datetime.now()
    
    # Crear un objeto datetime con la hora de apertura (6:00 AM del día actual)
    hora_apertura = ahora.replace(hour=6, minute=0, second=0, microsecond=0)
    
    # Verificar si la hora actual es anterior a las 6:00 AM
    if ahora < hora_apertura:
        # Calcular cuántos segundos faltan hasta las 6:00 AM
        tiempo_espera = (hora_apertura - ahora).total_seconds()
        
        # Mostrar información al usuario sobre la espera
        print(f"⏰ Son las {ahora.strftime('%H:%M:%S')}")
        print(f"⏰ Las reservas abren a las 06:00:00")
        print(f"⏰ Esperando {int(tiempo_espera)} segundos ({int(tiempo_espera/60)} minutos)...")
        
        # Pausar la ejecución hasta que llegue las 6:00 AM
        time.sleep(tiempo_espera)
        
        print(f"✓ Son las 06:00:00 - Iniciando proceso de reserva...")
    else:
        # Si ya son las 6:00 AM o posterior, continuar directamente
        print(f"✓ Son las {ahora.strftime('%H:%M:%S')} - Horario válido para reservar")

def reservar_slot(page, hora_inicio_clase, hora_fin_clase):
    """
    Función que busca el slot de horario específico en la página de bookings
    y realiza la reserva si está disponible.
    
    Parámetros:
    - page: Objeto de página de Playwright
    - hora_inicio_clase: Hora de inicio de la clase (ej: "15:00")
    - hora_fin_clase: Hora de fin de la clase (ej: "16:00")
    
    Retorna:
    - True: Si la reserva fue exitosa o ya estaba reservada
    - False: Si no se pudo completar la reserva
    """
    try:
        # PASO 1: Esperar a que cargue la sección de bookings en la página
        print(f"\n  📋 PASO 1: Esperando a que cargue la sección de bookings...")
        page.wait_for_selector('#bookings', timeout=5000)
        print(f"  ✓ Sección de bookings cargada")
        
        # PASO 2: Buscar el slot de horario específico
        print(f"\n  🔍 PASO 2: Buscando slot de horario {hora_inicio_clase} - {hora_fin_clase}...")
        
        # Obtener todos los slots de horarios disponibles en la página
        slots = page.query_selector_all('div.row.no-gutters.align-items-center')
        print(f"  ✓ Se encontraron {len(slots)} slots en total")
        
        # PASO 3: Iterar por cada slot para encontrar el correcto
        print(f"\n  🔄 PASO 3: Revisando cada slot...")
        for i, slot in enumerate(slots, 1):
            # Buscar el elemento que contiene el horario dentro del slot
            horario_element = slot.query_selector('p.font-weight-semibold.mb-0')
            
            if horario_element:
                # Obtener el texto del horario (ej: "15:00 - 16:00")
                horario_texto = horario_element.inner_text().strip()
                print(f"  • Slot {i}: {horario_texto}")
                
                # PASO 4: Verificar si este slot coincide con el horario buscado
                if hora_inicio_clase in horario_texto and hora_fin_clase in horario_texto:
                    print(f"\n  ✓ PASO 4: ¡Slot correcto encontrado! {horario_texto}")
                    
                    # PASO 5: Verificar si ya está reservado (botón "Cancel" presente)
                    print(f"\n  🔍 PASO 5: Verificando estado de la reserva...")
                    boton_cancel = slot.query_selector('button.btn.btn-primary.btn-sm:has-text("Cancel")')
                    
                    if boton_cancel:
                        # Si existe el botón Cancel, significa que ya está reservado
                        print(f"  ✓ Slot {horario_texto} YA ESTÁ RESERVADO")
                        print(f"  ✓ Botón 'Cancel' está visible - Reserva confirmada previamente")
                        return True
                    
                    # PASO 6: Buscar el botón "Book" para hacer la reserva
                    print(f"\n  🔍 PASO 6: Buscando botón 'Book' para reservar...")
                    boton_book = slot.query_selector('button.btn.btn-primary:has-text("Book")')
                    
                    if boton_book:
                        # Verificar el texto exacto del botón
                        texto_boton = boton_book.inner_text().strip()
                        print(f"  ✓ Botón encontrado con texto: '{texto_boton}'")
                        
                        # PASO 7: Hacer click en el botón "Book"
                        if 'Book' in texto_boton:
                            print(f"\n  🖱️ PASO 7: Haciendo click en 'Book'...")
                            boton_book.click()
                            print(f"  ✓ Click en 'Book' realizado")
                            
                            # PASO 8: Confirmar la reserva haciendo click en "Yes"
                            print(f"\n  ⏳ PASO 8: Esperando ventana de confirmación...")
                            try:
                                # Esperar a que aparezca el botón de confirmación "Yes"
                                page.wait_for_selector('button:has-text("Yes")', timeout=5000)
                                print(f"  ✓ Ventana de confirmación apareció")
                                
                                # Hacer click en "Yes" para confirmar
                                page.click('button:has-text("Yes")')
                                print(f"  ✓ Click en 'Yes' realizado - Confirmación enviada")
                            except Exception as e:
                                # Si no aparece el botón "Yes", continuar de todas formas
                                print(f"  ⚠️ No apareció el botón 'Yes' para confirmar: {e}")
                            
                            # PASO 9: Esperar a que se procese la reserva
                            print(f"\n  ⏳ PASO 9: Esperando a que se procese la reserva...")
                            page.wait_for_timeout(2000)
                            
                            # PASO 10: Esperar a que Angular actualice el DOM
                            print(f"\n  ⏳ PASO 10: Esperando actualización de la página...")
                            page.wait_for_timeout(1500)
                            print(f"  ✓ Página actualizada")

                            # PASO 11: Volver a capturar todos los slots actualizados
                            print(f"\n  🔄 PASO 11: Recargando slots para verificar cambios...")
                            slots_actualizados = page.query_selector_all('div.row.no-gutters.align-items-center')
                            print(f"  ✓ {len(slots_actualizados)} slots recargados")

                            # PASO 12: Buscar de nuevo el slot por su horario para verificar
                            print(f"\n  🔍 PASO 12: Verificando que la reserva se completó correctamente...")
                            for j, slot_act in enumerate(slots_actualizados, 1):
                                horario_element = slot_act.query_selector('p.font-weight-semibold.mb-0')
                                if horario_element:
                                    horario_texto_act = horario_element.inner_text().strip()

                                    # Si encontramos el mismo slot que reservamos
                                    if hora_inicio_clase in horario_texto_act and hora_fin_clase in horario_texto_act:
                                        print(f"  • Verificando slot {j}: {horario_texto_act}")
                                        
                                        # PASO 13: Verificar que ahora aparece el botón "Cancel"
                                        print(f"\n  🔍 PASO 13: Verificando botón 'Cancel'...")
                                        boton_cancel_verificacion = slot_act.query_selector('button.btn.btn-primary.btn-sm:has-text("Cancel")')
                                        
                                        if boton_cancel_verificacion:
                                            # Si aparece el botón Cancel, la reserva fue exitosa
                                            print(f"  ✓✓✓ RESERVA CONFIRMADA - Botón 'Cancel' ahora visible")
                                            return True
                                        else:
                                            # Si no aparece el botón Cancel, algo falló
                                            print(f"  ✗ Click realizado pero no se confirmó la reserva")
                                            print(f"  ✗ El botón 'Cancel' no apareció")
                                            return False
                        else:
                            # El botón no dice "Book"
                            print(f"  ℹ️ Slot encontrado pero el botón dice: '{texto_boton}'")
                            return False
                    else:
                        # No hay botón "Book" disponible
                        print(f"  ✗ Slot encontrado pero no tiene botón 'Book' disponible")
                        print(f"  ℹ️ Puede que esté completo o no disponible para reservar")
                        return False
        
        # Si llegamos aquí, no se encontró el slot buscado
        print(f"\n  ✗ No se encontró el slot de horario {hora_inicio_clase} - {hora_fin_clase}")
        
        # Mostrar todos los horarios disponibles para debug
        print(f"\n  📋 Horarios disponibles en este evento:")
        for slot in slots:
            horario_element = slot.query_selector('p.font-weight-semibold.mb-0')
            if horario_element:
                print(f"    - {horario_element.inner_text().strip()}")
        
        return False
        
    except Exception as e:
        # Capturar cualquier error que ocurra durante el proceso
        print(f"  ✗ Error al buscar el slot: {str(e)}")
        return False

def abrir_pagina():
    """
    Función principal que ejecuta todo el proceso de reserva:
    1. Espera hasta las 6:00 AM si es necesario
    2. Inicia sesión en la plataforma
    3. Busca eventos de Fitnes para el día actual
    4. Intenta reservar el horario correspondiente
    5. Reintenta hasta 4 veces si es necesario
    """
    
    # FASE 1: ESPERAR HASTA HORA DE APERTURA
    print("\n" + "="*60)
    print("FASE 1: VERIFICACIÓN DE HORA DE APERTURA")
    print("="*60)
    esperar_hasta_hora_apertura()
    
    # FASE 2: CONFIGURACIÓN INICIAL
    print("\n" + "="*60)
    print("FASE 2: CONFIGURACIÓN INICIAL")
    print("="*60)
    
    # Configurar el número máximo de intentos
    max_intentos = 4
    intento_actual = 1
    print(f"✓ Configuración: {max_intentos} intentos máximos")
    
    # FASE 3: INICIAR NAVEGADOR Y SESIÓN
    print("\n" + "="*60)
    print("FASE 3: INICIANDO NAVEGADOR Y SESIÓN")
    print("="*60)
    
    with sync_playwright() as p:
        # Lanzar el navegador en modo headless (sin interfaz gráfica)
        print("🌐 Lanzando navegador Chrome...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("✓ Navegador lanzado correctamente")
        
        # PASO 1: NAVEGAR A LA PÁGINA DE LOGIN
        print("\n📍 PASO 1: Navegando a la página de login...")
        page.goto('https://popr.uni-lj.si/unauth/440877/login')
        print("✓ Página de login cargada")
        
        # PASO 2: RELLENAR CAMPO DE USUARIO
        print("\n📝 PASO 2: Rellenando campo de usuario...")
        page.wait_for_selector('input#mat-input-0')
        page.click('input#mat-input-0')
        usuario = os.getenv('APP_USERNAME')
        page.fill('input#mat-input-0', usuario)
        print(f"✓ Usuario ingresado: {usuario[:3]}***")
        
        # PASO 3: RELLENAR CAMPO DE CONTRASEÑA
        print("\n🔒 PASO 3: Rellenando campo de contraseña...")
        page.wait_for_selector('input#mat-input-1')
        page.click('input#mat-input-1')
        password = os.getenv('APP_PASSWORD')
        page.fill('input#mat-input-1', password)
        print("✓ Contraseña ingresada (oculta)")
        
        # PASO 4: HACER CLICK EN EL BOTÓN DE LOGIN
        print("\n🔐 PASO 4: Iniciando sesión...")
        page.wait_for_selector('button.t_440877_login')
        page.click('button.t_440877_login')
        
        # Esperar a que se procese el login
        page.wait_for_timeout(2000)
        print("✓✓✓ Sesión iniciada correctamente\n")
        
        # FASE 4: BUCLE DE INTENTOS DE RESERVA
        print("\n" + "="*60)
        print("FASE 4: PROCESO DE BÚSQUEDA Y RESERVA")
        print("="*60)
        
        while intento_actual <= max_intentos:
            # Mostrar encabezado del intento actual
            print(f"\n{'='*60}")
            print(f"INTENTO {intento_actual} de {max_intentos}")
            print(f"{'='*60}\n")
            
            try:
                # PASO 5: NAVEGAR A LA PÁGINA PRINCIPAL
                print("📍 PASO 5: Navegando a la página principal...")
                page.goto('https://popr.uni-lj.si/user/home.html?currentUserLocale=es')
                page.wait_for_timeout(2000)
                print("✓ Página principal cargada")
                
                # PASO 6: ABRIR MENÚ "BOOK"
                print("\n🖱️ PASO 6: Haciendo click en el menú 'Book'...")
                page.wait_for_selector('a.nav-link.dropdown-toggle[title="Book"]')
                page.click('a.nav-link.dropdown-toggle[title="Book"]')
                print("✓ Menú 'Book' abierto")
                
                # PASO 7: HACER CLICK EN "EVENTS"
                print("\n🖱️ PASO 7: Haciendo click en 'Events'...")
                page.wait_for_selector('a.nav-link[title="Events"][href="/menu/user/events/book"]')
                page.click('a.nav-link[title="Events"][href="/menu/user/events/book"]')
                print("✓ Página de eventos cargada")
                
                # PASO 8: ESPERAR A QUE CARGUEN LOS RESULTADOS
                print("\n⏳ PASO 8: Esperando resultados de búsqueda...")
                page.wait_for_selector('#search-result')
                print("✓ Resultados de búsqueda cargados")
                
                # PASO 9: DETERMINAR EL HORARIO SEGÚN EL DÍA DE LA SEMANA
                print("\n📅 PASO 9: Determinando horario según el día...")
                
                # Diccionario con los horarios de cada día de la semana
                # 0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves, 4=Viernes, 6=Domingo
                horarios_por_dia = {
                    6: ('21:00', '22:30'),  # Domingo
                    0: ('18:00', '19:30'),  # Lunes
                    1: ('15:00', '16:30'),  # Martes
                    2: ('10:30', '12:00'),  # Miércoles
                    3: ('19:30', '21:00'),  # Jueves
                    4: ('12:00', '13:00'),  # Viernes
                }
                
                # Obtener el día actual
                hoy = datetime.now()
                dia_semana = hoy.weekday()  # 0=Lunes, 6=Domingo
                fecha_hoy = hoy.strftime('%d-%b-%Y').lower()  # Formato: 25-nov-2025
                
                dias_nombres = {
                    0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 
                    3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
                }
                print(f"✓ Hoy es {dias_nombres[dia_semana]} ({fecha_hoy})")
                
                # Verificar si hay clase programada para hoy
                if dia_semana not in horarios_por_dia:
                    print(f"ℹ️ No hay clase de Fitnes programada para {dias_nombres[dia_semana]}")
                    print("🚪 Cerrando navegador...")
                    page.wait_for_timeout(3000)
                    browser.close()
                    return
                
                # Obtener el horario de la clase de hoy
                hora_inicio, hora_fin = horarios_por_dia[dia_semana]
                print(f"✓ Horario de tu clase: {hora_inicio} - {hora_fin}")
                
                # PASO 10: BUSCAR EVENTOS DE FITNES
                print(f"\n🔍 PASO 10: Buscando eventos de Fitnes para {fecha_hoy}...")
                
                # Función auxiliar para verificar si el horario del evento coincide
                def horario_coincide(hora_inicio_evento, hora_fin_evento, hora_inicio_clase, hora_fin_clase):
                    """
                    Verifica si el horario de la clase está dentro del horario del evento.
                    Convierte las horas a minutos para hacer la comparación numérica.
                    """
                    def a_minutos(hora_str):
                        h, m = hora_str.split(':')
                        return int(h) * 60 + int(m)
                    
                    # Convertir todas las horas a minutos
                    inicio_evento = a_minutos(hora_inicio_evento)
                    fin_evento = a_minutos(hora_fin_evento)
                    inicio_clase = a_minutos(hora_inicio_clase)
                    fin_clase = a_minutos(hora_fin_clase)
                    
                    # Verificar si la clase está completamente dentro del evento
                    return inicio_evento <= inicio_clase and fin_clase <= fin_evento
                
                # Obtener todos los eventos de la página
                eventos = page.query_selector_all('.list-group-item')
                print(f"✓ Se encontraron {len(eventos)} eventos en total")
                
                # PASO 11: REVISAR CADA EVENTO
                print(f"\n🔄 PASO 11: Revisando cada evento...")
                eventos_encontrados = 0
                
                for i, evento in enumerate(eventos, 1):
                    # Extraer información del evento
                    titulo_element = evento.query_selector('h2')
                    fecha_element = evento.query_selector('._event-date-wrapper strong')
                    
                    if titulo_element and fecha_element:
                        titulo = titulo_element.inner_text()
                        fecha = fecha_element.inner_text()
                        
                        # Verificar si es un evento de Fitnes y es para hoy
                        if 'Fitnes' in titulo and fecha == fecha_hoy:
                            # Obtener los horarios del evento
                            horas_elements = evento.query_selector_all('._event-date-wrapper strong')
                            
                            if len(horas_elements) >= 3:
                                # horas_elements[0] = fecha
                                # horas_elements[1] = hora inicio
                                # horas_elements[2] = hora fin
                                hora_inicio_evento = horas_elements[1].inner_text()
                                hora_fin_evento = horas_elements[2].inner_text()
                                
                                # Verificar si el horario coincide con nuestra clase
                                if horario_coincide(hora_inicio_evento, hora_fin_evento, hora_inicio, hora_fin):
                                    print(f"\n✓✓✓ Evento #{i} coincide con tu horario:")
                                    print(f"  📋 Nombre: {titulo}")
                                    print(f"  📅 Fecha: {fecha}")
                                    print(f"  🕐 Horario del evento: {hora_inicio_evento} - {hora_fin_evento}")
                                    print(f"  🎯 Tu clase: {hora_inicio} - {hora_fin}")
                                    
                                    # PASO 12: HACER CLICK EN EL EVENTO
                                    print(f"\n🖱️ PASO 12: Abriendo el evento...")
                                    enlace = evento.query_selector('a')
                                    if enlace:
                                        enlace.click()
                                        eventos_encontrados += 1
                                        print(f"✓ Evento abierto")
                                        
                                        # PASO 13: ESPERAR A QUE CARGUE LA PÁGINA DEL EVENTO
                                        print(f"\n⏳ PASO 13: Esperando a que cargue la página del evento...")
                                        page.wait_for_timeout(3000)
                                        print(f"✓ Página del evento cargada")
                                        
                                        # PASO 14: INTENTAR RESERVAR EL SLOT
                                        print(f"\n🎯 PASO 14: Intentando reservar el slot...")
                                        if reservar_slot(page, hora_inicio, hora_fin):
                                            # ÉXITO: Reserva completada
                                            print("\n" + "="*60)
                                            print("✓✓✓ RESERVA COMPLETADA EXITOSAMENTE ✓✓✓")
                                            print("="*60 + "\n")
                                            print("🎉 ¡Tu clase ha sido reservada!")
                                            print("🚪 Cerrando navegador...")
                                            page.wait_for_timeout(3000)
                                            browser.close()
                                            return
                                        else:
                                            # FALLO: No se pudo reservar
                                            print("\n  ✗ No se pudo reservar en este evento")
                                            print("  🔙 Regresando para buscar otros eventos...")
                                            break
                                else:
                                    # El horario del evento no coincide con nuestra clase
                                    print(f"  ✗ Evento #{i} descartado: {titulo}")
                                    print(f"    Horario {hora_inicio_evento} - {hora_fin_evento} no coincide con {hora_inicio} - {hora_fin}")
                
                # PASO 15: VERIFICAR RESULTADOS DE LA BÚSQUEDA
                print(f"\n📊 PASO 15: Verificando resultados...")
                if eventos_encontrados == 0:
                    print(f"\n✗ No se encontraron eventos de Fitnes disponibles")
                    print(f"  📅 Fecha buscada: {fecha_hoy}")
                    print(f"  🕐 Horario buscado: {hora_inicio} - {hora_fin}")
                else:
                    print(f"\n⚠️ Se encontraron {eventos_encontrados} evento(s) pero no se pudo completar la reserva")
                
                # PASO 16: DECIDIR SI REINTENTAR
                if intento_actual < max_intentos:
                    tiempo_espera = 5
                    print(f"\n⏳ PASO 16: Reintentando en {tiempo_espera} segundos...")
                    print(f"  Intento {intento_actual} de {max_intentos} completado")
                    page.wait_for_timeout(tiempo_espera * 1000)
                    intento_actual += 1
                else:
                    # Se agotaron los intentos
                    print(f"\n" + "="*60)
                    print(f"✗✗✗ SE AGOTARON LOS {max_intentos} INTENTOS SIN ÉXITO ✗✗✗")
                    print("="*60)
                    print("\n😞 No se pudo completar la reserva después de todos los intentos")
                    break
                    
            except Exception as e:
                # Manejo de errores durante el proceso
                print(f"\n❌ Error en el intento {intento_actual}: {str(e)}")
                
                if intento_actual < max_intentos:
                    tiempo_espera = 5
                    print(f"\n⏳ Esperando {tiempo_espera} segundos antes de reintentar...")
                    page.wait_for_timeout(tiempo_espera * 1000)
                    intento_actual += 1
                else:
                    print(f"\n" + "="*60)
                    print(f"✗✗✗ SE AGOTARON LOS {max_intentos} INTENTOS CON ERRORES ✗✗✗")
                    print("="*60)
                    break
        
        # FASE FINAL: CERRAR NAVEGADOR
        print("\n" + "="*60)
        print("FASE FINAL: CERRANDO NAVEGADOR")
        print("="*60)
        page.wait_for_timeout(3000)
        browser.close()
        print("✓ Navegador cerrado correctamente")
        print("\n🏁 Proceso finalizado")

# Punto de entrada del programa
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🏋️ SISTEMA DE RESERVAS AUTOMÁTICAS DE GIMNASIO")
    print("="*60)
    abrir_pagina()