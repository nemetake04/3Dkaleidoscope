#include "WiFiS3.h"
#include <WiFiUdp.h>
#include <Adafruit_NeoPixel.h>

// --- WiFi設定 ---
char ssid[] = "musiclab";      // WiFiのSSID
char pass[] = "soundnet";  // WiFiのパスワード
unsigned int localPort = 5005;  // 待ち受けポート番号

// --- LED設定 ---
#define PIN        6
#define NUMPIXELS 100
Adafruit_NeoPixel pixels(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

WiFiUDP Udp;
char packetBuffer[255]; 

void setup() {
  Serial.begin(115200);
  pixels.begin();
  pixels.show();

  // WiFi接続
  Serial.print("Connecting to WiFi...");
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    while (true);
  }
  
  while (WiFi.begin(ssid, pass) != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
  
  // 割り当てられたIPアドレスを表示（Python側で使います）
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  Udp.begin(localPort);
}

void loop() {
  int packetSize = Udp.parsePacket();
  if (packetSize) {
    int len = Udp.read(packetBuffer, 255);
    if (len > 0) packetBuffer[len] = 0;

    // "音量,ピッチ" という文字列をパース
    String data = String(packetBuffer);
    int commaIndex = data.indexOf(',');
    if (commaIndex != -1) {
      int volume = data.substring(0, commaIndex).toInt();
      int pitch = data.substring(commaIndex + 1).toInt();

      // 滑らかな色変化の処理
      int brightness = map(volume, -60, 0, 0, 255);
      brightness = constrain(brightness, 0, 255);
      int hue = map(pitch, 0, 2000, 0, 65535);

      for(int i=0; i<NUMPIXELS; i++) {
        pixels.setPixelColor(i, pixels.gamma32(pixels.ColorHSV(hue, 255, brightness)));
      }
      pixels.show();
    }
  }
}