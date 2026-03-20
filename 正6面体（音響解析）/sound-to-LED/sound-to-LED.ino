#include <WiFi.h>      // ESP32の場合。ESP8266の場合は <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <Adafruit_NeoPixel.h>

// --- 設定項目 ---
const char* ssid     = "musiclab";         // WiFiのSSID
const char* password = "soundnet";     // WiFiのパスワード
const int udpPort    = 5005;                     // Python側と合わせる

#define LED_PIN     9    // LEDテープのデータピン
#define NUM_LEDS    30    // LEDの個数
#define BRIGHTNESS  100   // 全体の明るさ (0-255)

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);
WiFiUDP udp;
char packetBuffer[255]; 

void setup() {
  Serial.begin(115200);

  // WiFi接続
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected.");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP()); // ここで表示されたIPをPythonのUDP_IPに書き込む

  udp.begin(udpPort);
  
  strip.begin();
  strip.setBrightness(BRIGHTNESS);
  strip.show(); // 初期化（消灯）
}

void loop() {
  int packetSize = udp.parsePacket();
  if (packetSize) {
    int len = udp.read(packetBuffer, 255);
    if (len > 0) {
      packetBuffer[len] = 0;
    }

    // 文字列 "R,G,B" をパース
    int r, g, b;
    if (sscanf(packetBuffer, "%d,%d,%d", &r, &g, &b) == 3) {
      // 全てのLEDに色をセット
      for(int i=0; i<NUM_LEDS; i++) {
        strip.setPixelColor(i, strip.Color(r, g, b));
      }
      strip.show();
      
      // デバッグ用
      Serial.printf("Received RGB: %d, %d, %d\n", r, g, b);
    }
  }
}