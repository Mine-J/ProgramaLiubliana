from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
from datetime import datetime
import time

load_dotenv()

def esperar_hasta_hora_apertura():
    """
    Espera hasta las 6:00 AM si el script se ejecuta antes de esa hora
    """
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
    """
    Busca el slot de horario correcto en la página de bookings y hace la reserva
    Retorna True si la reserva fue exitosa, False en caso contrario
    """
    try:
        page.wait_for_selector('#bookings', timeout=5000)
        print(f"\n  Buscando slot de horario {hora_inicio_clase} - {hora_fin_clase}...")
        
        slots = page.query_selector_all('div.row.no-gutters.align-items-center')
        
        for slot in slots:
            horario_element = slot.query_selector('p.font-weight-semibold.mb-0')
            
            if horario_element:
                horario_texto = horario_element.inner_text().strip()
                
                if hora_inicio_clase in horario_texto and hora_fin_clase in horario_texto:
                    boton_cancel = slot.query_selector('button.btn.btn-primary.btn-sm:has-text("Cancel")')
                    
                    if boton_cancel:
                        print(f"  ✓ Slot {horario_texto} ya está reservado")
                        print(f"  ✓ Reserva confirmada - Botón 'Cancel' visible")
                        return True
                    
                    boton_book = slot.query_selector('button.btn.btn-primary:has-text("Book")')
                    
                    if boton_book:
                        texto_boton = boton_book.inner_text().strip()
                        
                        if 'Book' in texto_boton:
                            print(f"  ✓ Slot encontrado: {horario_texto}")
                            print(f"  Haciendo click en 'Book'...")
                            boton_book.click()
                            
                            try:
                                page.wait_for_selector('button:has-text("Yes")', timeout=5000)
                                page.click('button:has-text("Yes")')
                                print("  ✓ Click en 'Yes' realizado")
                            except Exception as e:
                                print(f"  ⚠ No apareció el botón 'Yes' para confirmar: {e}")
                            
                            page.wait_for_timeout(2000)
                            
                            # Espera a que Angular actualice el DOM
                            page.wait_for_timeout(1500)

                            # Volver a capturar todos los slots actualizados
                            slots_actualizados = page.query_selector_all('div.row.no-gutters.align-items-center')

                            # Buscar de nuevo el slot por su horario
                            for slot_act in slots_actualizados:
                                horario_element = slot_act.query_selector('p.font-weight-semibold.mb-0')
                                if horario_element:
                                    horario_texto_act = horario_element.inner_text().strip()

                                    if hora_inicio_clase in horario_texto_act and hora_fin_clase in horario_texto_act:
                                        boton_cancel_verificacion = slot_act.query_selector('button.btn.btn-primary.btn-sm:has-text("Cancel")')
                                        
                                        if boton_cancel_verificacion:
                                            print(f"  ✓ Reserva confirmada - Botón 'Cancel' visible")
                                            return True
                                        else:
                                            print(f"  ⚠ Click realizado pero no se confirmó la reserva")
                                            return False
                        else:
                            print(f"  ℹ Slot encontrado pero el botón dice: '{texto_boton}'")
                            return False
                    else:
                        print(f"  ✗ Slot encontrado pero no tiene botón 'Book' disponible")
                        return False
        
        print(f"  ✗ No se encontró el slot de horario {hora_inicio_clase} - {hora_fin_clase}")
        
        print(f"\n  Horarios disponibles en este evento:")
        for slot in slots:
            horario_element = slot.query_selector('p.font-weight-semibold.mb-0')
            if horario_element:
                print(f"    - {horario_element.inner_text().strip()}")
        
        return False
        
    except Exception as e:
        print(f"  ✗ Error al buscar el slot: {str(e)}")
        return False

def abrir_pagina():
    esperar_hasta_hora_apertura()
    
    max_intentos = 4
    intento_actual = 1
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Iniciando sesión...")
        page.goto('https://popr.uni-lj.si/unauth/440877/login')
        
        page.wait_for_selector('input#mat-input-0')
        page.click('input#mat-input-0')
        usuario = os.getenv('APP_USERNAME')
        page.fill('input#mat-input-0', usuario)
        
        page.wait_for_selector('input#mat-input-1')
        page.click('input#mat-input-1')
        password = os.getenv('APP_PASSWORD')
        page.fill('input#mat-input-1', password)
        
        page.wait_for_selector('button.t_440877_login')
        page.click('button.t_440877_login')
        
        page.wait_for_timeout(2000)
        print("✓ Sesión iniciada correctamente\n")
        
        while intento_actual <= max_intentos:
            print(f"\n{'='*60}")
            print(f"INTENTO {intento_actual} de {max_intentos}")
            print(f"{'='*60}\n")
            
            try:
                page.goto('https://popr.uni-lj.si/user/home.html?currentUserLocale=es')
                page.wait_for_timeout(2000)
                
                page.wait_for_selector('a.nav-link.dropdown-toggle[title="Book"]')
                page.click('a.nav-link.dropdown-toggle[title="Book"]')
                
                page.wait_for_selector('a.nav-link[title="Events"][href="/menu/user/events/book"]')
                page.click('a.nav-link[title="Events"][href="/menu/user/events/book"]')
                
                page.wait_for_selector('#search-result')
                
                horarios_por_dia = {
                    6: ('21:00', '22:30'),
                    0: ('18:00', '19:30'),
                    1: ('15:00', '16:30'),
                    2: ('10:30', '12:00'),
                    3: ('19:30', '21:00'),
                    4: ('12:00', '13:00'),
                }
                
                hoy = datetime.now()
                dia_semana = hoy.weekday()
                fecha_hoy = hoy.strftime('%d-%b-%Y').lower()
                
                if dia_semana not in horarios_por_dia:
                    dias_nombres = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
                    print(f"Hoy es {dias_nombres[dia_semana]} y no tienes clase de Fitnes programada.")
                    page.wait_for_timeout(3000)
                    browser.close()
                    return
                
                hora_inicio, hora_fin = horarios_por_dia[dia_semana]
                print(f"Buscando eventos de Fitnes para hoy {fecha_hoy}")
                print(f"Horario de tu clase: {hora_inicio} - {hora_fin}")
                
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
                
                eventos_encontrados = 0
                for evento in eventos:
                    titulo_element = evento.query_selector('h2')
                    fecha_element = evento.query_selector('._event-date-wrapper strong')
                    
                    if titulo_element and fecha_element:
                        titulo = titulo_element.inner_text()
                        fecha = fecha_element.inner_text()
                        
                        if 'Fitnes' in titulo and fecha == fecha_hoy:
                            horas_elements = evento.query_selector_all('._event-date-wrapper strong')
                            if len(horas_elements) >= 3:
                                hora_inicio_evento = horas_elements[1].inner_text()
                                hora_fin_evento = horas_elements[2].inner_text()
                                
                                if horario_coincide(hora_inicio_evento, hora_fin_evento, hora_inicio, hora_fin):
                                    print(f"✓ Encontrado: {titulo} - {fecha}")
                                    print(f"  Horario del evento: {hora_inicio_evento} - {hora_fin_evento}")
                                    print(f"  Tu clase: {hora_inicio} - {hora_fin}")
                                    
                                    enlace = evento.query_selector('a')
                                    if enlace:
                                        print(f"  Haciendo click en el evento...")
                                        enlace.click()
                                        eventos_encontrados += 1
                                        
                                        print(f"  Esperando a que cargue la página del evento...")
                                        page.wait_for_timeout(3000)
                                        
                                        if reservar_slot(page, hora_inicio, hora_fin):
                                            print("\n" + "="*60)
                                            print("✓✓✓ RESERVA COMPLETADA EXITOSAMENTE ✓✓✓")
                                            print("="*60 + "\n")
                                            page.wait_for_timeout(3000)
                                            browser.close()
                                            return
                                        else:
                                            print("  ✗ No se pudo reservar en este evento")
                                            break
                                else:
                                    print(f"✗ Descartado: {titulo} - Horario {hora_inicio_evento} - {hora_fin_evento} no coincide")
                
                if eventos_encontrados == 0:
                    print(f"\n✗ No se encontraron eventos de Fitnes disponibles para tu horario")
                    print(f"  Fecha: {fecha_hoy}")
                    print(f"  Horario buscado: {hora_inicio} - {hora_fin}")
                else:
                    print(f"\n✗ Se encontraron {eventos_encontrados} evento(s) pero no se pudo completar la reserva")
                
                if intento_actual < max_intentos:
                    tiempo_espera = 5
                    print(f"\n⏳ Esperando {tiempo_espera} segundos antes del siguiente intento...")
                    page.wait_for_timeout(tiempo_espera * 1000)
                    intento_actual += 1
                else:
                    print(f"\n✗✗✗ SE AGOTARON LOS {max_intentos} INTENTOS SIN ÉXITO ✗✗✗")
                    break
                    
            except Exception as e:
                print(f"\n✗ Error en el intento {intento_actual}: {str(e)}")
                if intento_actual < max_intentos:
                    tiempo_espera = 5
                    print(f"⏳ Esperando {tiempo_espera} segundos antes de reintentar...")
                    page.wait_for_timeout(tiempo_espera * 1000)
                    intento_actual += 1
                else:
                    print(f"\n✗✗✗ SE AGOTARON LOS {max_intentos} INTENTOS CON ERRORES ✗✗✗")
                    break
        
        page.wait_for_timeout(3000)
        browser.close()

if __name__ == "__main__":
    abrir_pagina()