# Dr!ft Charging Station LED Controller

A customizable LED lighting controller designed for a **Dr!ft racer charging station**, powered by a **Seeed Studio XIAO ESP32C3** and **MicroPython**.

This project features a **Web Bluetooth (BLE)** interface, allowing you to control the LED strip directly from your web browser (Chrome, Edge, Opera) without installing any native apps.

## 🔋 Features

* **7 Light Modes:** Comet, Static (Power Saving), Breathing, Heartbeat, Rainbow, Police Strobe, and Scanner (Knight Rider).
* **Full Control:** Adjust **Color**, **Speed**, and **Brightness** in real-time.
* **Wireless:** Connects via Bluetooth Low Energy (BLE) using the Web Bluetooth API.
* **Hardware:** Optimized for a 14-LED NeoPixel (WS2812B) ring/strip.

## 🚀 Quick Start

1.  Flash the `main.py` onto your XIAO ESP32C3 (ensure MicroPython is installed).
2.  Open the `index.html` file in a BLE-supported browser (Chrome, Edge) via HTTPS or localhost.
3.  Click **Connect**, pair with `Dr!ft_Lader`, and enjoy the show!

## 📜 License

**MIT License**
Copyright (c) 2026 **Atomregen**
