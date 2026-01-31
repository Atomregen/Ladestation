# --------------------------------------------------------------------------
# MIT License
# 
# Project: Dr!ft Ladestation
# Copyright (c) 2026 Atomregen
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# --------------------------------------------------------------------------

import bluetooth
import time
import machine
import neopixel
import math
import struct
import json
from micropython import const

# --- Konfiguration ---
PIN_LED = 4
NUM_LEDS = 14
CONFIG_FILE = "settings.json"
np = neopixel.NeoPixel(machine.Pin(PIN_LED), NUM_LEDS)

# --- BLE Konstanten ---
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_RX = (bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE,)
_UART_SERVICE = (_UART_UUID, (_UART_RX,),)

# --- Globale Status-Variablen ---
current_color = (255, 0, 0)
current_mode = 0 
current_speed = 128
current_brightness = 128
connected = False

# --- Speicher Funktionen ---
def load_settings():
    global current_mode, current_color, current_speed, current_brightness
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            current_mode = data.get('mode', 0)
            current_color = tuple(data.get('color', [255, 0, 0]))
            current_speed = data.get('speed', 128)
            current_brightness = data.get('brightness', 128)
            print("Einstellungen geladen:", data)
    except (OSError, ValueError):
        print("Keine gespeicherten Einstellungen. Nutze Standards.")

def save_settings():
    # Speichert den aktuellen IST-Zustand
    data = {
        'mode': current_mode,
        'color': current_color,
        'speed': current_speed,
        'brightness': current_brightness
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f)
        print("MANUELL GESPEICHERT!")
    except Exception as e:
        print("Fehler beim Speichern:", e)

class BLEServer:
    def __init__(self):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_rx,),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._advertise()

    def _irq(self, event, data):
        global current_color, current_mode, current_speed, current_brightness, connected
        
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            connected = True
            print("Verbunden")
            
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.remove(conn_handle)
            connected = False
            self._advertise()
            print("Getrennt")
            
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx:
                self._handle_command(value)

    def _handle_command(self, data):
        global current_color, current_mode, current_speed, current_brightness
        
        # Format: [Mode, R, G, B, Speed, Brightness]
        if len(data) >= 6:
            try:
                cmd_mode = data[0]
                
                # --- SPEZIALBEFEHL 255: SPEICHERN ---
                if cmd_mode == 255:
                    save_settings()
                    return # Funktion hier beenden, keine Werte ändern
                
                # Normales Update der Werte
                current_mode = cmd_mode
                current_color = (data[1], data[2], data[3])
                current_speed = data[4]
                current_brightness = data[5]
                
            except Exception as e:
                print("Parse Error:", e)

    def _advertise(self):
        name = "Dr!ft_Lader"
        adv_data = bytearray(b'\x02\x01\x06') + bytearray((len(name) + 1, 0x09)) + name.encode('utf-8')
        self._ble.gap_advertise(100000, adv_data)

# --- Hilfsfunktionen ---

def scale_color(color, animation_factor=1.0):
    global_factor = current_brightness / 255.0
    total_factor = global_factor * animation_factor
    r = int(color[0] * total_factor)
    g = int(color[1] * total_factor)
    b = int(color[2] * total_factor)
    return (r, g, b)

def map_speed(val, min_out, max_out):
    return int(max_out - (val * (max_out - min_out) / 255))

def wheel(pos):
    if pos < 0 or pos > 255: return (0, 0, 0)
    if pos < 85: return (255 - pos * 3, pos * 3, 0)
    if pos < 170: pos -= 85; return (0, 255 - pos * 3, pos * 3)
    pos -= 170; return (pos * 3, 0, 255 - pos * 3)

# --- Animations-Loop ---
def run_animation():
    load_settings() # Beim Start laden
    ble = BLEServer()
    
    head_pos = 0
    last_step_time = 0
    rainbow_offset = 0
    scanner_pos = 0
    scanner_dir = 1
    
    print("Starte Dr!ft Ladestation...")
    
    while True:
        now = time.ticks_ms()
        
        # --- MODUS 0: Komet ---
        if current_mode == 0:
            delay = map_speed(current_speed, 20, 200)
            if time.ticks_diff(now, last_step_time) > delay:
                np.fill((0, 0, 0))
                np[head_pos] = scale_color((255, 255, 255), 1.0)
                for i, factor in enumerate([1.0, 0.4, 0.1]):
                    pos = (head_pos - (i + 1)) % NUM_LEDS
                    np[pos] = scale_color(current_color, factor)
                np.write()
                head_pos = (head_pos + 1) % NUM_LEDS
                last_step_time = now

        # --- MODUS 1: Statisch ---
        elif current_mode == 1:
            np.fill(scale_color(current_color, 0.5))
            np.write()
            time.sleep_ms(100)

        # --- MODUS 2: Atmen ---
        elif current_mode == 2:
            div = map_speed(current_speed, 200, 1500)
            brightness = (math.sin(now / div) + 1) / 2
            brightness = 0.05 + (brightness * 0.95)
            np.fill(scale_color(current_color, brightness))
            np.write()
            time.sleep_ms(20)

        # --- MODUS 3: Herzschlag ---
        elif current_mode == 3:
            cycle_duration = map_speed(current_speed, 600, 2000)
            cycle = now % cycle_duration
            p1 = cycle_duration * 0.125
            p2 = cycle_duration * 0.25
            p3 = cycle_duration * 0.375
            p4 = cycle_duration * 0.5
            
            intensity = 0
            if 0 <= cycle < p1: intensity = cycle / p1
            elif p1 <= cycle < p2: intensity = 1.0 - ((cycle - p1) / (p2 - p1))
            elif p2 <= cycle < p3: intensity = (cycle - p2) / (p3 - p2)
            elif p3 <= cycle < p4: intensity = 1.0 - ((cycle - p3) / (p4 - p3))
            
            intensity = intensity * intensity
            np.fill(scale_color(current_color, intensity))
            np.write()
            time.sleep_ms(20)

        # --- MODUS 4: Regenbogen ---
        elif current_mode == 4:
            delay = map_speed(current_speed, 10, 100)
            if time.ticks_diff(now, last_step_time) > delay:
                for i in range(NUM_LEDS):
                    idx = (i * 256 // NUM_LEDS) + rainbow_offset
                    raw_color = wheel(idx & 255)
                    np[i] = scale_color(raw_color, 1.0)
                np.write()
                rainbow_offset = (rainbow_offset + 1) & 255
                last_step_time = now

        # --- MODUS 5: Polizei ---
        elif current_mode == 5:
            delay = map_speed(current_speed, 50, 400)
            if time.ticks_diff(now, last_step_time) > delay:
                state = (now // delay) % 2
                c_red = scale_color((255, 0, 0), 1.0)
                c_blue = scale_color((0, 0, 255), 1.0)
                for i in range(NUM_LEDS):
                    if i < NUM_LEDS // 2:
                        np[i] = c_red if state == 0 else (0,0,0)
                    else:
                        np[i] = c_blue if state == 1 else (0,0,0)
                np.write()
                last_step_time = now

        # --- MODUS 6: Scanner ---
        elif current_mode == 6:
            delay = map_speed(current_speed, 30, 150)
            if time.ticks_diff(now, last_step_time) > delay:
                np.fill((0, 0, 0))
                np[scanner_pos] = scale_color(current_color, 1.0)
                prev_pos = scanner_pos - scanner_dir
                if 0 <= prev_pos < NUM_LEDS:
                     np[prev_pos] = scale_color(current_color, 0.3)
                np.write()
                scanner_pos += scanner_dir
                if scanner_pos >= NUM_LEDS - 1: scanner_dir = -1
                elif scanner_pos <= 0: scanner_dir = 1
                last_step_time = now

        else:
            time.sleep_ms(100)

if __name__ == "__main__":
    run_animation()
